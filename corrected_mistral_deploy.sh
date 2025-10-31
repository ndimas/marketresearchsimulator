#!/bin/bash
echo "🚀 Starting Mistral-7B GGUF Deployment..."
echo "⏰ Time: $(date)"
echo "🖥️  Hostname: $(hostname)"
echo "💾 Available disk space:"
df -h /
echo ""
echo "🔧 GPU Information:"
nvidia-smi || echo "❌ nvidia-smi not available"
echo ""
echo "📦 Installing/upgrading vLLM..."
pip install --upgrade vllm==0.6.1.post1
echo ""
echo "🤖 Starting vLLM server with Mistral-7B GGUF..."
echo "📍 Endpoint will be available at: http://localhost:8000"
echo "🔍 Health check: http://localhost:8000/health"
echo "📖 Models: http://localhost:8000/v1/models"
echo "💬 Chat: http://localhost:8000/v1/chat/completions"
echo ""

# Corrected vLLM serve command with proper argument format
vllm serve "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF" \
--host 0.0.0.0 \
--port 8000 \
--quantization gguf \
--gguf-file-name Mistral-7B-Instruct-v0.3.Q5_K_M.gguf \
--max-model-len 8192 \
--tensor-parallel-size 1 \
--gpu-memory-utilization 0.95 \
--disable-log-requests \
--enable-chunked-prefill

echo ""
echo "✅ Deployment completed!"
echo "🌐 Server is running on port 8000"
