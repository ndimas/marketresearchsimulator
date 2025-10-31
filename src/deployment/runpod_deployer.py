"""RunPod deployment handler."""

import json
import os
from typing import Dict, Optional
from .models import DeploymentConfig, DeploymentResult


class RunPodDeployer:
    """Handles RunPod deployment operations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the RunPod deployer."""
        self.api_key = api_key or os.getenv('RUNPOD_API_KEY')
        self.base_url = "https://api.runpod.io/graphql"
        
    def deploy_llm(self, config: DeploymentConfig) -> DeploymentResult:
        """Generate optimized RunPod Serverless vLLM config for RTX 4090 max parallel throughput."""
        assert config.gpu_type == "RTX 4090" and config.vram_gb == 24, "Optimized for RTX 4090 24GB"
        
        deployment_config = {
            "name": config.name,
            "imageName": "runpod/pytorch:2.4.1-py3.10-cuda12.4.1-devel-ubuntu22.04",
            "env": {
                "MODEL_NAME": config.model_id,
                "DTYPE": "float16",
                "MAX_MODEL_LEN": "8192",
                "GPU_MEMORY_UTILIZATION": "0.95",
                "TENSOR_PARALLEL_SIZE": "1",
                "MAX_NUM_BATCHED_TOKENS": "32768",
                "MAX_NUM_SEQS": "512",
                "BLOCK_SIZE": "32",
                "DISABLE_LOG_REQUESTS": "true",
                "ENABLE_CHUNKED_PREFILL": "true",
                "PORT": "8000"
            },
            "gpuType": "NVIDIA RTX 4090",
            "minWorkers": config.min_workers,
            "maxWorkers": config.max_workers,
            "gpuCount": config.gpu_count,
            "containerDiskInGb": config.container_disk_gb,
            "volumeInGb": config.volume_gb,
            "volumeMountPath": config.volume_mount_path,
            "ports": config.ports,
            "dockerStartCmd": "python -m vllm.entrypoints.openai.api_server --model $MODEL_NAME --host 0.0.0.0 --port 8000 --dtype $DTYPE --max-model-len $MAX_MODEL_LEN --gpu-memory-utilization $GPU_MEMORY_UTILIZATION --max-num-batched-tokens $MAX_NUM_BATCHED_TOKENS --max-num-seqs $MAX_NUM_SEQS --block-size $BLOCK_SIZE --disable-log-requests $DISABLE_LOG_REQUESTS --enable-chunked-prefill $ENABLE_CHUNKED_PREFILL"
        }
        
        return DeploymentResult(
            config=deployment_config,
            dockerfile=self._generate_dockerfile(),
            deploy_script=self._generate_deploy_script(deployment_config),
            test_script=self._generate_test_script(),
            optimizations="CUDA 12.4, PyTorch 2.4, vLLM 0.6.3, FlashAttn 2.6.3 for max Ada kernels/throughput. High batch params for 100+ concurrent reqs."
        )
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for vLLM deployment."""
        return """# Use custom Dockerfile for vLLM + FlashAttn kernels
FROM runpod/pytorch:2.4.1-py3.10-cuda12.4.1-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    wget \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \\
    vllm==0.6.3 \\
    flash-attn==2.6.3 \\
    aiohttp \\
    fastapi \\
    uvicorn \\
    pydantic \\
    transformers \\
    huggingface_hub \\
    && pip cache purge

# Create workspace directory
WORKDIR /workspace

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "vllm.entrypoints.openai.api_server", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_deploy_script(self, config: Dict) -> str:
        """Generate deployment script for RunPod."""
        return f"""#!/bin/bash
# RunPod Deployment Script for Swiss Market Research LLM

set -e

# Check if API key is set
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY environment variable is not set"
    exit 1
fi

# Model configuration
MODEL_ID="{config['env']['MODEL_NAME']}"
ENDPOINT_NAME="{config['name']}"

echo "Deploying model: $MODEL_ID"
echo "Endpoint name: $ENDPOINT_NAME"

# Create endpoint
ENDPOINT_RESPONSE=$(curl -X POST "https://api.runpod.ai/v2/endpoints" \\
    -H "Authorization: Bearer $RUNPOD_API_KEY" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(config)}')

echo "Endpoint creation response:"
echo "$ENDPOINT_RESPONSE"

# Extract endpoint ID
ENDPOINT_ID=$(echo "$ENDPOINT_RESPONSE" | jq -r '.id')

if [ "$ENDPOINT_ID" = "null" ]; then
    echo "Error: Failed to create endpoint"
    exit 1
fi

echo "Endpoint ID: $ENDPOINT_ID"

# Wait for endpoint to be ready
echo "Waiting for endpoint to be ready..."
while true; do
    STATUS_RESPONSE=$(curl -X GET "https://api.runpod.ai/v2/endpoints/$ENDPOINT_ID" \\
        -H "Authorization: Bearer $RUNPOD_API_KEY")
    
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.ready')
    
    if [ "$STATUS" = "true" ]; then
        echo "Endpoint is ready!"
        break
    fi
    
    echo "Endpoint not ready yet. Waiting 30 seconds..."
    sleep 30
done

# Get endpoint URL
ENDPOINT_URL=$(echo "$STATUS_RESPONSE" | jq -r '.endpoint.url')
echo "Endpoint URL: $ENDPOINT_URL"

# Save endpoint info
cat > endpoint_info.json << EOF
{{
    "endpoint_id": "$ENDPOINT_ID",
    "endpoint_url": "$ENDPOINT_URL",
    "model_id": "$MODEL_ID",
    "status": "ready"
}}
EOF

echo "Deployment complete! Endpoint info saved to endpoint_info.json"
"""
    
    def _generate_test_script(self) -> str:
        """Generate test script for deployed endpoint."""
        return """#!/bin/bash
# Test script for deployed RunPod endpoint

set -e

# Load endpoint info
if [ ! -f "endpoint_info.json" ]; then
    echo "Error: endpoint_info.json not found. Please deploy first."
    exit 1
fi

ENDPOINT_URL=$(cat endpoint_info.json | jq -r '.endpoint_url')
MODEL_ID=$(cat endpoint_info.json | jq -r '.model_id')

echo "Testing endpoint: $ENDPOINT_URL"
echo "Model: $MODEL_ID"

# Health check
echo "Performing health check..."
curl -f "$ENDPOINT_URL/health" || echo "Health check failed"

# Test chat completion
echo "Testing chat completion..."
curl -X POST "$ENDPOINT_URL/v1/chat/completions" \\
    -H "Content-Type: application/json" \\
    -d '{
        "model": "'$MODEL_ID'",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond only in JSON format: {\\"answer\\": \\"your response\\"}"
            },
            {
                "role": "user", 
                "content": "What is the capital of Switzerland?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }'

echo -e "\\nTest completed!"
"""
    
    def create_deployment_files(self, config: DeploymentConfig, output_dir: str = "deployment") -> None:
        """Create all deployment files for the model."""
        os.makedirs(output_dir, exist_ok=True)
        
        deployment_result = self.deploy_llm(config)
        
        # Save Dockerfile
        with open(f"{output_dir}/Dockerfile", "w") as f:
            f.write(deployment_result.dockerfile)
        
        # Save deployment script
        with open(f"{output_dir}/deploy.sh", "w") as f:
            f.write(deployment_result.deploy_script)
        
        # Save test script
        with open(f"{output_dir}/test.sh", "w") as f:
            f.write(deployment_result.test_script)
        
        # Save config
        with open(f"{output_dir}/config.json", "w") as f:
            json.dump(deployment_result.config, f, indent=2)
        
        # Make scripts executable
        os.chmod(f"{output_dir}/deploy.sh", 0o755)
        os.chmod(f"{output_dir}/test.sh", 0o755)
        
        print(f"Deployment files created in {output_dir}/")
        print(f"- Dockerfile: {output_dir}/Dockerfile")
        print(f"- Deploy script: {output_dir}/deploy.sh")
        print(f"- Test script: {output_dir}/test.sh")
        print(f"- Config: {output_dir}/config.json")
        print(f"\nTo deploy: cd {output_dir} && ./deploy.sh")
        print(f"To test: cd {output_dir} && ./test.sh")


def deploy_llm(model_id: str, gpu_type: str = "RTX 4090", vram_gb: int = 24) -> DeploymentResult:
    """Legacy function for backward compatibility."""
    deployer = RunPodDeployer()
    config = DeploymentConfig(
        model_id=model_id,
        gpu_type=gpu_type,
        vram_gb=vram_gb
    )
    return deployer.deploy_llm(config)
