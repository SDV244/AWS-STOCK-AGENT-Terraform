# Script para actualizar el Agent Runtime de forma automática
$AGENT_ID = "app_main-X3Fu7U6ukU"
$REGION = "us-east-1"

Write-Host "🚀 Iniciando actualización del Agent Runtime: $AGENT_ID" -ForegroundColor Cyan

# 1. Ejecutar el update
aws bedrock-agentcore-control update-agent-runtime `
    --agent-runtime-id $AGENT_ID `
    --agent-runtime-artifact file://artifact.json `
    --role-arn "arn:aws:iam::551670267045:role/amzn-stock-agent-agentcore-role" `
    --network-configuration file://network.json `
    --authorizer-configuration file://jwt-auth.json `
    --environment-variables file://env-config.json `
    --region $REGION

Write-Host "⏳ Esperando a que el status sea READY..." -ForegroundColor Yellow

# 2. Bucle de verificación de status
do {
    $status = (aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id $AGENT_ID --region $REGION | ConvertFrom-Json).status
    Write-Host "Estado actual: $status"
    if ($status -ne "READY") { Start-Sleep -Seconds 5 }
} while ($status -ne "READY")

Write-Host "✅ ¡Despliegue completado con éxito! El agente está listo para recibir consultas." -ForegroundColor Green