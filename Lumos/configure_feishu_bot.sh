#!/bin/bash

# Configuration variables
APP_ID="cli_a92c5060b9f85bc8"
APP_SECRET="sMJdsZTgRAwTlS84qQafHdyBXCLDBpGK"

# Function to generate tenant_access_token
echo "Generating tenant_access_token..."
response=$(curl -s -X POST \
  https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/ \
  -H "Content-Type: application/json" \
  -d "{\"app_id\": \"$APP_ID\", \"app_secret\": \"$APP_SECRET\"}")

# Extract tenant_access_token from response
TENANT_ACCESS_TOKEN=$(echo $response | jq -r '.tenant_access_token')

if [ "$TENANT_ACCESS_TOKEN" == "null" ] || [ -z "$TENANT_ACCESS_TOKEN" ]; then
  echo "Failed to generate tenant_access_token. Response: $response"
  exit 1
fi

echo "Access token generated successfully: $TENANT_ACCESS_TOKEN"

# Test sending a message if needed (you can modify the chat_id and content)
# echo "Testing message sending..."
# curl -X POST \
#   https://open.feishu.cn/open-apis/message/v4/send/ \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer $TENANT_ACCESS_TOKEN" \
#   -d '{"chat_id": "CHAT_ID", "content": "{\"text\":\"Hello from OpenClaw!\"}", "msg_type": "text"}'

exit 0