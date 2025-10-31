#!/usr/bin/env python3
"""
Deploy Mistral-7B GGUF model on RunPod pod using vLLM serve command
"""

import os
import subprocess
import sys
import time

def deploy_mistral_on_pod():
    """Deploy Mistral-7B GGUF model on the running pod"""
    
    print("🚀 Deploying Mistral-7B GGUF on RunPod Pod")
    print("=" * 50)
    
    # Pod deployment command
    deploy_command = """vllm serve "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF" \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --quantization gguf \\
    --gguf-file-name Mistral-7B-Instruct-v0.3.Q5_K_M.gguf \\
    --max-model-len 8192 \\
    --tensor-parallel-size 1 \\
    --gpu-memory-utilization 0.95 \\
    --disable-log-requests \\
    --enable-chunked-prefill"""
    
    print("📋 Deployment Configuration:")
    print("🤖 Model: MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF")
    print("📁 File: Mistral-7B-Instruct-v0.3.Q5_K_M.gguf")
    print("🔧 Quantization: GGUF")
    print("🌐 Host: 0.0.0.0")
    print("🚪 Port: 8000")
    print("💾 Max Model Length: 8192")
    print("🧠 GPU Memory: 95%")
    print("⚡ Chunked Prefill: Enabled")
    print()
    
    print("🔧 Deployment Command:")
    print(deploy_command)
    print()
    
    # Create deployment script
    script_content = f"""#!/bin/bash
# Mistral-7B GGUF vLLM Deployment Script
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 Starting Mistral-7B GGUF deployment..."
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

{deploy_command}

echo ""
echo "✅ Deployment completed!"
echo "🌐 Server is running on port 8000"
"""
    
    # Write deployment script
    with open('deploy_mistral_pod.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('deploy_mistral_pod.sh', 0o755)
    
    print("📁 Created deployment script: deploy_mistral_pod.sh")
    print()
    
    # Check if we can connect to the pod
    pod_id = "6xw2qp6sncgl7a"  # Extracted from the working endpoint
    
    print(f"🔍 Testing connection to pod: {pod_id}")
    
    # Try to execute the deployment on the pod
    try:
        # Method 1: Try using runpodctl if available
        runpodctl_cmd = f"echo 'y' | ./runpodctl exec bash deploy_mistral_pod.sh --pod_id {pod_id}"
        
        print("🔧 Attempting deployment via runpodctl...")
        result = subprocess.run(runpodctl_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Deployment command sent successfully!")
            print("📋 Output:")
            print(result.stdout)
        else:
            print(f"❌ runpodctl error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("📋 Alternative Manual Deployment:")
    print("If runpodctl doesn't work, manually connect to the pod and run:")
    print("1. Connect to pod via RunPod dashboard")
    print("2. Upload deploy_mistral_pod.sh")
    print("3. Execute: chmod +x deploy_mistral_pod.sh && ./deploy_mistral_pod.sh")
    print()
    
    print("🧪 Testing endpoints after deployment:")
    print("Health: curl -s https://6xw2qp6sncgl7a-8000.proxy.runpod.net/health")
    print("Models: curl -s https://6xw2qp6sncgl7a-8000.proxy.runpod.net/v1/models")
    print("Chat: curl -X POST https://6xw2qp6sncgl7a-8000.proxy.runpod.net/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\": \"MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}], \"max_tokens\": 50}'")

def create_test_script():
    """Create a test script for the deployed model"""
    
    test_content = """#!/bin/bash
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
curl -X POST "$ENDPOINT/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
    "messages": [{"role": "user", "content": "Hello! What model are you?"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content' 2>/dev/null || curl -X POST "$ENDPOINT/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
    "messages": [{"role": "user", "content": "Hello! What model are you?"}],
    "max_tokens": 50
  }'
echo ""
echo ""

echo "✅ Testing completed!"
"""
    
    with open('test_mistral_deployment.sh', 'w') as f:
        f.write(test_content)
    
    os.chmod('test_mistral_deployment.sh', 0o755)
    print("📁 Created test script: test_mistral_deployment.sh")

if __name__ == "__main__":
    deploy_mistral_on_pod()
    create_test_script()
    
    print()
    print("🎉 Deployment files created!")
    print("📁 Files:")
    print("  - deploy_mistral_pod.sh: Deployment script")
    print("  - test_mistral_deployment.sh: Test script")
    print()
    print("🚀 Next steps:")
    print("1. Execute deployment on pod:")
    print("   echo 'y' | ./runpodctl exec bash deploy_mistral_pod.sh --pod_id 6xw2qp6sncgl7a")
    print()
    print("2. Test deployment:")
    print("   ./test_mistral_deployment.sh")
    print()
    print("3. Or manually deploy via RunPod dashboard")
