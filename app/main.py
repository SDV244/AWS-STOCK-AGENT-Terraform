import uuid
import time
import httpx
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bedrock_agentcore import BedrockAgentCoreApp
from app.auth import verify_token_sync
from app.config import settings

# ── FastAPI app — mounted inside BedrockAgentCoreApp ──────────────────
fastapi_app = FastAPI(
    title="Amazon Stock AI Agent",
    description="LangGraph ReAct agent for real-time and historical AMZN stock queries",
    version="1.0.0",
)

class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None

@fastapi_app.get("/health")
async def health():
    return {
        "status":     "healthy",
        "model":      settings.bedrock_model_id,
        "kb_id":      settings.knowledge_base_id,
    }

@fastapi_app.post("/stream")
async def invoke_stream(request: QueryRequest):
    """
    FastAPI streaming endpoint — returns Server-Sent Events.
    Auth is handled by Agentcore JWT Inbound Auth (Cognito).
    """
    from langchain_aws import ChatBedrock
    from langchain_core.messages import HumanMessage
    from langgraph.prebuilt import create_react_agent
    from app.agent import TOOLS, SYSTEM_PROMPT

    session_id  = request.session_id or str(uuid.uuid4())
    trace_id    = langfuse_create_trace(session_id, request.query)
    span_id, _  = langfuse_create_span(trace_id, "langgraph-agent", request.query)

    llm = ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        model_kwargs={"max_tokens": 4096, "temperature": 0.1},
    )
    agent = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)

    async def event_generator():
        final_text  = ""
        tool_events = []

        yield f"data: {json.dumps({'event': 'start', 'session_id': session_id, 'trace_id': trace_id})}\n\n"

        async for event in agent.astream(
            {"messages": [HumanMessage(content=request.query)]},
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    for message in node_output["messages"]:
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tc in message.tool_calls:
                                chunk = {
                                    "event": "tool_call",
                                    "node":  node_name,
                                    "tool":  tc["name"],
                                    "args":  str(tc["args"]),
                                }
                                tool_events.append(chunk)
                                yield f"data: {json.dumps(chunk)}\n\n"

                        if hasattr(message, "name") and message.type == "tool":
                            chunk = {
                                "event":   "tool_result",
                                "tool":    message.name,
                                "content": message.content[:500],
                            }
                            tool_events.append(chunk)
                            yield f"data: {json.dumps(chunk)}\n\n"

                        if message.type == "ai" and message.content:
                            final_text = message.content
                            chunk = {
                                "event":   "ai_response",
                                "node":    node_name,
                                "content": message.content,
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"

        langfuse_end_trace(trace_id, span_id, request.query, final_text, tool_events)
        yield f"data: {json.dumps({'event': 'end', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── BedrockAgentCoreApp — Agentcore protocol ──────────────────────────
app = BedrockAgentCoreApp()


# ── Langfuse helpers ──────────────────────────────────────────────────
def langfuse_ingest(events: list):
    try:
        httpx.post(
            f"{settings.langfuse_host}/api/public/ingestion",
            auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
            json={"batch": events},
            timeout=10,
        )
    except Exception:
        pass


def langfuse_create_trace(session_id: str, query: str) -> str:
    trace_id = str(uuid.uuid4())
    langfuse_ingest([{
        "id":        str(uuid.uuid4()),
        "type":      "trace-create",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "body": {
            "id":        trace_id,
            "name":      "stock-agent-query",
            "sessionId": session_id,
            "input":     query,
        }
    }])
    return trace_id


def langfuse_create_span(trace_id: str, name: str, input_data: str) -> tuple:
    span_id    = str(uuid.uuid4())
    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    langfuse_ingest([{
        "id":        str(uuid.uuid4()),
        "type":      "span-create",
        "timestamp": start_time,
        "body": {
            "id":        span_id,
            "traceId":   trace_id,
            "name":      name,
            "startTime": start_time,
            "input":     input_data,
        }
    }])
    return span_id, start_time


def langfuse_end_trace(trace_id: str, span_id: str, query: str, output: str, tool_events: list):
    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    events   = []

    events.append({
        "id":        str(uuid.uuid4()),
        "type":      "span-update",
        "timestamp": end_time,
        "body": {
            "id":      span_id,
            "traceId": trace_id,
            "endTime": end_time,
            "output":  output,
        }
    })

    for tc in tool_events:
        events.append({
            "id":        str(uuid.uuid4()),
            "type":      "event-create",
            "timestamp": end_time,
            "body": {
                "traceId": trace_id,
                "name":    f"tool:{tc.get('tool', 'unknown')}",
                "input":   tc.get("args", ""),
                "output":  tc.get("content", ""),
            }
        })

    events.append({
        "id":        str(uuid.uuid4()),
        "type":      "trace-create",
        "timestamp": end_time,
        "body": {
            "id":     trace_id,
            "output": output,
        }
    })

    langfuse_ingest(events)


# ── Agentcore entrypoint (invoked via SDK or JWT HTTPS) ───────────────
@app.entrypoint
async def invoke(payload: dict) -> dict:
    token = payload.get("token", "")
    if token.startswith("Bearer "):
        token = token[7:]

    # Only validate manually if token provided in payload
    # When using JWT Inbound Auth, Agentcore validates before calling this
    if token and token != "SKIP":
        try:
            verify_token_sync(token)
        except Exception as e:
            return {"error": f"Unauthorized: {str(e)}"}

    query      = payload.get("query", "")
    session_id = payload.get("session_id", str(uuid.uuid4()))

    if not query:
        return {"error": "Missing 'query' in payload"}

    from langchain_aws import ChatBedrock
    from langchain_core.messages import HumanMessage
    from langgraph.prebuilt import create_react_agent
    from app.agent import TOOLS, SYSTEM_PROMPT

    trace_id            = langfuse_create_trace(session_id, query)
    span_id, start_time = langfuse_create_span(trace_id, "langgraph-agent", query)

    llm = ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        model_kwargs={"max_tokens": 4096, "temperature": 0.1},
    )

    agent      = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)
    chunks     = []
    final_text = ""

    async for event in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
    ):
        for node_name, node_output in event.items():
            if "messages" in node_output:
                for message in node_output["messages"]:
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            chunks.append({
                                "event": "tool_call",
                                "node":  node_name,
                                "tool":  tc["name"],
                                "args":  str(tc["args"]),
                            })
                    if hasattr(message, "name") and message.type == "tool":
                        chunks.append({
                            "event":   "tool_result",
                            "tool":    message.name,
                            "content": message.content[:500],
                        })
                    if message.type == "ai" and message.content:
                        final_text = message.content
                        chunks.append({
                            "event":   "ai_response",
                            "node":    node_name,
                            "content": message.content,
                        })

    tool_events = [c for c in chunks if c["event"] in ("tool_call", "tool_result")]
    langfuse_end_trace(trace_id, span_id, query, final_text, tool_events)

    return {
        "session_id": session_id,
        "trace_id":   trace_id,
        "events":     chunks,
    }


if __name__ == "__main__":
    app.run()