Write-Host "=== X Bot Setup (Windows) ===" -ForegroundColor Green
Write-Host ""

$API_TOKEN = Read-Host "Enter Telegram Bot Token (API_TOKEN)"
$TWITTER_AUTH_TOKEN = Read-Host "Enter Twitter Auth Token (TWITTER_AUTH_TOKEN)"
$DB_PASS = Read-Host "Enter Database Password (DB_PASS)"

if ([string]::IsNullOrWhiteSpace($API_TOKEN) -or 
    [string]::IsNullOrWhiteSpace($TWITTER_AUTH_TOKEN) -or 
    [string]::IsNullOrWhiteSpace($DB_PASS)) {
    Write-Host "Error: All fields are required!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -t my-x-bot .

Write-Host "Removing old container if exists..." -ForegroundColor Yellow
docker rm -f my-x-bot-container 2>$null

Write-Host "Starting container..." -ForegroundColor Yellow
docker run -d `
  --name my-x-bot-container `
  --restart always `
  -e API_TOKEN="$API_TOKEN" `
  -e TWITTER_AUTH_TOKEN="$TWITTER_AUTH_TOKEN" `
  -e DB_PASS="$DB_PASS" `
  -e CHECK_INTERVAL=45 `
  my-x-bot

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Container name : my-x-bot-container"
Write-Host "Check logs     : docker logs -f my-x-bot-container"
Write-Host "Restart        : docker restart my-x-bot-container"
Write-Host "Stop           : docker stop my-x-bot-container"