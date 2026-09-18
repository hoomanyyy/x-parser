Write-Host "=== X Bot Setup (Windows) ===" -ForegroundColor Green

$API_TOKEN = Read-Host "Enter Telegram Bot Token (API_TOKEN)"
$TWITTER_AUTH_TOKEN = Read-Host "Enter Twitter Auth Token (TWITTER_AUTH_TOKEN)"

if ([string]::IsNullOrWhiteSpace($API_TOKEN) -or [string]::IsNullOrWhiteSpace($TWITTER_AUTH_TOKEN)) {
    Write-Host "Error: Tokens are required!" -ForegroundColor Red
    exit
}

# تولید پسوورد خودکار برای دیتابیس
$DB_PASS = -join ((65..90) + (97..122) + (48..57) \vert{} Get-Random -Count 16 \vert{} ForEach-Object {[char]$_})

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
  my-x-bot

Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Check logs: docker logs -f my-x-bot-container"