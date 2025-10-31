#!/bin/bash
# Test Mistral-7B GGUF Deployment

echo "🧪 Testing Mistral-7B GGUF Deployment"
echo "=================================="

ENDPOINT="https://6xw2qp6sncgl7a-8000.proxy.runpod.net"

echo "1️⃣  Health Check Test"
echo "🔍 Testing: $ENDPOINT/health"
curl -s "$ENDPOINT/health" | head -c 100
echo ""
echo ""

echo "2️⃣  Models Test"
echo "🔍 Testing: $ENDPOINT/v1/models"
curl -s "$ENDPOINT/v1/models" | jq '.data[0].id' 2>/dev/null || curl -s "$ENDPOINT/v1/models" | head -c 200
echo ""
echo ""

echo "3️⃣  Chat Completion Test"
echo "🔍 Testing: $ENDPOINT/v1/chat/completions"
curl -X POST "$ENDPOINT/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
    "messages": [{"role": "user", "content": "Hello! What model are you?"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content' 2>/dev/null || curl -X POST "$ENDPOINT/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
    "messages": [{"role": "user", "content": "Hello! What model are you?"}],
    "max_tokens": 50
  }'
echo ""
echo ""

echo "✅ Testing completed!"
