import os, asyncio

os.environ['COGNITO_USER_POOL_ID'] = 'us-east-1_rMAbiCcQn'
os.environ['COGNITO_CLIENT_ID'] = '1qpnps2hg98a5u0ffeg9p1df8'
os.environ['KNOWLEDGE_BASE_ID'] = '0PUUVUOQUL'
os.environ['LANGFUSE_PUBLIC_KEY'] = 'pk-lf-6b3452ab-4d10-408e-9969-7739ae58f054'
os.environ['LANGFUSE_SECRET_KEY'] = 'sk-lf-7433747d-e6f6-4564-b078-f625127ed67a'
os.environ['BEDROCK_MODEL_ID'] = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
os.environ['AWS_REGION'] = 'us-east-1'

async def test():
    from app.main import invoke
    result = await invoke({
        'query': 'What is the stock price for Amazon right now?',
        'token': 'Bearer SKIP',
        'session_id': 'local-debug-test'
    })
    print('Result:', result)

asyncio.run(test())
