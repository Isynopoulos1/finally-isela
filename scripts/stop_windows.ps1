#Requires -Version 5.1
# Stop and remove the FinAlly container. Data volume is preserved.
$ErrorActionPreference = "Stop"

$ContainerName = "finally-app"

$exists = docker ps -aq -f "name=^${ContainerName}$"
if (-not $exists) {
    Write-Host "FinAlly is not running."
    exit 0
}

docker stop $ContainerName | Out-Null
docker rm $ContainerName | Out-Null

Write-Host "FinAlly stopped."
