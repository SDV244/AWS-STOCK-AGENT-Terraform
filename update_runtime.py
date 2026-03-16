
import subprocess

result = subprocess.run([

    "aws", "bedrock-agentcore-control", "update-agent-runtime",

    "--agent-runtime-id", "app_main-X3Fu7U6ukU",

    "--agent-runtime-artifact", "file://artifact.json",

    "--role-arn", "arn:aws:iam::551670267045:role/amzn-stock-agent-agentcore-role",

    "--network-configuration", "file://network.json",

    "--authorizer-configuration", "file://jwt-auth.json",

    "--region", "us-east-1"

], capture_output=True, text=True)

print(result.stdout)

print(result.stderr)

