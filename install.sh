#!/usr/bin/env bash
set -e

echo "========================================"
echo "       X-Parser Bot Installer"
echo "========================================"
echo

read -p "Telegram Bot Token (API_TOKEN): " API_TOKEN
read -p "Twitter Auth Token (TWITTER_AUTH_TOKEN): " TWITTER_AUTH_TOKEN
read -p "Google API Key (GOOGLE_API_KEY) [for translation]: " GOOGLE_API_KEY

echo
echo "--- Database Settings ---"
read -p "DB Host (e.g. sql.freemysqlhosting.net): " DB_HOST
read -p "DB Port [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}
read -p "DB Name: " DB_NAME
read -p "DB User: " DB_USER
read -p "DB Password: " DB_PASS

read -p "Check Interval in seconds [45]: " CHECK_INTERVAL
CHECK_INTERVAL=${CHECK_INTERVAL:-45}

if [ -z "$API_TOKEN" ] || [ -z "$TWITTER_AUTH_TOKEN" ] || [ -z "$DB_HOST" ] || \
   [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASS" ]; then
    echo
    echo "ERROR: Required fields are missing!"
    echo "API_TOKEN, TWITTER_AUTH_TOKEN, DB_HOST, DB_NAME, DB_USER, DB_PASS are required."
    exit 1
fi

echo
echo "Building Docker image (this may take a few minutes)..."
docker build -t my-x-bot .

echo "Removing old container if exists..."
docker rm -f my-x-bot-container 2>/dev/null || true

echo "Starting container..."
docker run -d \
  --name my-x-bot-container \
  --restart always \
  -e API_TOKEN="$API_TOKEN" \
  -e TWITTER_AUTH_TOKEN="$TWITTER_AUTH_TOKEN" \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASS="$DB_PASS" \
  -e CHECK_INTERVAL="$CHECK_INTERVAL" \
  my-x-bot

echo
echo "========================================"
echo "       Installation Complete"
echo "========================================"
echo "Container name : my-x-bot-container"
echo "DB Host        : $DB_HOST"
echo "DB Name        : $DB_NAME"
echo
echo "Useful commands:"
echo "  docker logs -f my-x-bot-container"
echo "  docker restart my-x-bot-container"
echo "  docker stop my-x-bot-container"
echo