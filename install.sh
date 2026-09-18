#!/usr/bin/env bash
set -e

echo "=== X Bot Automated Setup (Linux) ==="

read -p "Enter Telegram Bot Token (API_TOKEN): " API_TOKEN
read -p "Enter Twitter Auth Token (TWITTER_AUTH_TOKEN): " TWITTER_AUTH_TOKEN

if [ -z "$API_TOKEN" ] || [ -z "$TWITTER_AUTH_TOKEN" ]; then
    echo "Error: Tokens are required!"
    exit 1
fi

# تولید پسوورد خودکار برای دیتابیس
DB_PASS=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16)

echo "Building Docker image..."
docker build -t my-x-bot .

echo "Removing old container if exists..."
docker rm -f my-x-bot-container 2>/dev/null || true

echo "Starting container..."
docker run -d \
  --name my-x-bot-container \
  --restart always \
  -e API_TOKEN="$API_TOKEN" \
  -e TWITTER_AUTH_TOKEN="$TWITTER_AUTH_TOKEN" \
  -e DB_PASS="$DB_PASS" \   
  my-x-bot

echo "=== Deployment Complete ==="
echo "Check logs: docker logs -f my-x-bot-container"