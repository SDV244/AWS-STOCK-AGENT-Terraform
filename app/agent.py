import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from app.tools import (
    retrieve_realtime_stock_price,
    retrieve_historical_stock_price,
    retrieve_from_knowledge_base,
)
from app.config import settings

TOOLS = [
    retrieve_realtime_stock_price,
    retrieve_historical_stock_price,
    retrieve_from_knowledge_base,
]

SYSTEM_PROMPT = """You are a professional financial research assistant specializing in
Amazon (AMZN) stock analysis. You have access to:

1. Real-time stock price retrieval via yfinance
2. Historical stock price data
3. Amazon's official financial documents (2024 Annual Report, Q2/Q3 2025 Earnings)

Guidelines:
- Always use the appropriate tool to fetch current data — never guess prices
- For questions about Amazon's business, financials, or AI strategy,
  search the knowledge base first
- Combine tool results thoughtfully to give comprehensive answers
- When discussing stock performance vs analyst predictions, use BOTH
  historical price data AND the knowledge base documents
- Be precise with numbers and cite sources
- Format responses clearly with sections when covering multiple topics
"""


async def stream_agent_response(query: str, session_id: str = "default"):
    """Used for local testing only."""
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler as LangfuseCallback
    import os

    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"]       = settings.langfuse_host

    langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    langfuse_handler = LangfuseCallback()

    llm = ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        model_kwargs={"max_tokens": 4096, "temperature": 0.1},
    )

    agent = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)

    async for event in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
        config={"callbacks": [langfuse_handler]},
    ):
        for node_name, node_output in event.items():
            if "messages" in node_output:
                for message in node_output["messages"]:
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            yield {
                                "event": "tool_call",
                                "node":  node_name,
                                "tool":  tc["name"],
                                "args":  str(tc["args"]),
                            }
                    if hasattr(message, "name") and message.type == "tool":
                        yield {
                            "event":   "tool_result",
                            "tool":    message.name,
                            "content": message.content[:500],
                        }
                    if message.type == "ai" and message.content:
                        yield {
                            "event":   "ai_response",
                            "node":    node_name,
                            "content": message.content,
                        }

    try:
        langfuse_client.flush()
    except Exception:
        pass