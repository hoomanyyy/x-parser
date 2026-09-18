#!/usr/bin/env bash
set -e

echo "=== X Bot Setup (Linux) ==="
echo

read -p "Enter Telegram Bot Token (API_TOKEN): " API_TOKEN
read -p "Enter Twitter Auth Token (TWITTER_AUTH_TOKEN): " TWITTER_AUTH_TOKEN
read -p "Enter Database Password (DB_PASS): " DB_PASS

if [ -z "$API_TOKEN" ] || [ -z "$TWITTER_AUTH_TOKEN" ] || [ -z "$DB_PASS" ]; then
    echo "Error: All fields are required!"
    exit 1
fi

echo
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
  -e CHECK_INTERVAL=45 \
  my-x-bot

echo
echo "=== Deployment Complete ==="
echo "Container name : my-x-bot-container"
echo "Check logs     : docker logs -f my-x-bot-container"
echo "Restart        : docker restart my-x-bot-container"
echo "Stop           : docker stop my-x-bot-container"