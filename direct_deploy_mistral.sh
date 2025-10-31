#!/bin/bash
# Direct deployment script for Mistral-7B GGUF on active pod

echo "🚀 Direct Mistral-7B GGUF Deployment"
echo "======================================"

# Model deployment command
DEPLOY_CMD="vllm serve \"MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF\" \\
--host 0.0.0.0 \\
--port 8000 \\
--quantization gguf \\
--gguf-file-name Mistral-7B-Instruct-v0.3.Q5_K_M.gguf \\
--max-model-len 8192 \\
--tensor-parallel-size 1 \\
--gpu-memory-utilization 0.95 \\
--disable-log-requests \\
--enable-chunked-prefill"

echo "📋 Deployment Command:"
echo "$DEPLOY_CMD"
echo ""

echo "🔧 Installing vLLM..."
pip install --upgrade vllm==0.6.1.post1

echo ""
echo "�� Starting Mistral-7B GGUF server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "🔍 Health check: http://localhost:8000/health"
echo "📖 Models: http://localhost:8000/v1/models"
echo "💬 Chat: http://localhost:8000/v1/chat/completions"
echo ""

# Execute the deployment
eval "$DEPLOY_CMD"

echo ""
echo "✅ Deployment completed!"
echo "🌐 Server is running on port 8000"
