#!/usr/bin/env python3
"""
Deploy Mistral-7B GGUF to the running pod
"""

import subprocess
import sys

def deploy_mistral():
    """Deploy Mistral-7B GGUF model"""
    
    print("🚀 Deploying Mistral-7B GGUF to Pod")
    print("=" * 40)
    
    # Deployment command
    deploy_cmd = '''vllm serve "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF" \\
--host 0.0.0.0 \\
--port 8000 \\
--quantization gguf \\
--gguf-file-name Mistral-7B-Instruct-v0.3.Q5_K_M.gguf \\
--max-model-len 8192 \\
--tensor-parallel-size 1 \\
--gpu-memory-utilization 0.95 \\
--disable-log-requests \\
--enable-chunked-prefill'''
    
    print("�� Deployment Command:")
    print(deploy_cmd)
    print()
    
    # Create script content
    script_content = f'''#!/bin/bash
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

{deploy_cmd}

echo ""
echo "✅ Deployment completed!"
echo "�� Server is running on port 8000"
'''
    
    # Write deployment script
    with open('mistral_deploy.sh', 'w') as f:
        f.write(script_content)
    
    import os
    os.chmod('mistral_deploy.sh', 0o755)
    
    print("📁 Created deployment script: mistral_deploy.sh")
    print()
    print("🔧 To deploy manually:")
    print("1. Connect to pod via RunPod dashboard")
    print("2. Upload mistral_deploy.sh")
    print("3. Execute: chmod +x mistral_deploy.sh && ./mistral_deploy.sh")
    print()
    print("🌐 Current pod endpoint: https://6xw2qp6sncgl7a-8000.proxy.runpod.net")
    print("�� Test with: curl -s https://6xw2qp6sncgl7a-8000.proxy.runpod.net/health")
    print("📖 Models: curl -s https://6xw2qp6sncgl7a-8000.proxy.runpod.net/v1/models")
    print("💬 Chat: curl -X POST https://6xw2qp6sncgl7a-8000.proxy.runpod.net/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\": \"MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}], \"max_tokens\": 50}'")

if __name__ == "__main__":
    deploy_mistral()
