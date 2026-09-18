#Requires -Version 5.1
# Build (if needed) and run the FinAlly Docker container.
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$ImageName = "finally"
$ContainerName = "finally-app"
$VolumeName = "finally-data"
$Port = 8000

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$running = docker ps -q -f "name=^${ContainerName}$"
if ($running) {
    Write-Host "FinAlly is already running at http://localhost:$Port"
    exit 0
}

$stopped = docker ps -aq -f "name=^${ContainerName}$"
if ($stopped) {
    docker rm $ContainerName | Out-Null
}

$imageExists = docker images -q $ImageName
if ($Build -or -not $imageExists) {
    Write-Host "Building $ImageName image..."
    docker build -t $ImageName .
}

$envPath = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envPath)) {
    Write-Warning ".env not found at project root. Copy .env.example to .env and set OPENROUTER_API_KEY."
}

docker run -d `
    --name $ContainerName `
    -p "${Port}:8000" `
    -v "${VolumeName}:/app/db" `
    --env-file $envPath `
    $ImageName

Write-Host "FinAlly is running at http://localhost:$Port"
