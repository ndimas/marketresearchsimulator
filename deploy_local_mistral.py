#!/usr/bin/env python3
"""Deploy Mistral-7B GGUF model locally."""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                          capture_output=True, text=True)
        print(f"✅ Success: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False, e.stderr

def main():
    """Main deployment function."""
    print("🚀 Local Mistral-7B GGUF Deployment")
    print("=" * 50)
    
    # Configuration
    model_name = "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF"
    gguf_file = "Mistral-7B-Instruct-v0.3.Q5_K_M.gguf"
    local_dir = "./model"
    
    print(f"📋 Configuration:")
    print(f"   Model: {model_name}")
    print(f"   GGUF File: {gguf_file}")
    print(f"   Local Directory: {local_dir}")
    
    # Create model directory
    model_path = Path(local_dir)
    model_path.mkdir(exist_ok=True)
    print(f"\n📁 Created model directory: {model_path.absolute()}")
    
    # Check if vLLM is installed
    print("\n🔍 Checking vLLM installation...")
    try:
        import vllm
        print(f"✅ vLLM is installed: {vllm.__version__}")
    except ImportError:
        print("❌ vLLM not found. Installing...")
        success, _ = run_command(
            "pip install vllm==0.6.1.post1",
            "Installing vLLM with GGUF support"
        )
        if not success:
            print("❌ Failed to install vLLM")
            return 1
    
    # Install additional dependencies if needed
    print("\n🔍 Checking dependencies...")
    try:
        import huggingface_hub
        print("✅ huggingface_hub is installed")
    except ImportError:
        success, _ = run_command(
            "pip install huggingface_hub",
            "Installing huggingface_hub"
        )
        if not success:
            print("❌ Failed to install huggingface_hub")
    
    # Download the model if not exists
    gguf_path = model_path / gguf_file
    if not gguf_path.exists():
        print(f"\n📥 Downloading {gguf_file}...")
        
        # Create download script
        download_script = f"""
from huggingface_hub import hf_hub_download
import os

model_id = "{model_name}"
filename = "{gguf_file}"
local_dir = "{local_dir}"

print(f"Downloading {{model_id}}/{{filename}} to {{local_dir}}...")
try:
    downloaded_path = hf_hub_download(
        repo_id=model_id,
        filename=filename,
        local_dir=local_dir,
        local_dir_use_symlinks=False
    )
    print(f"✅ Downloaded to: {{downloaded_path}}")
except Exception as e:
    print(f"❌ Download failed: {{e}}")
    exit(1)
"""
        
        with open("download_model.py", "w") as f:
            f.write(download_script)
        
        success, _ = run_command(
            "python download_model.py",
            "Downloading Mistral-7B GGUF model"
        )
        
        # Clean up download script
        Path("download_model.py").unlink(missing_ok=True)
        
        if not success:
            print("❌ Failed to download model")
            return 1
    else:
        print(f"✅ Model already exists: {gguf_path}")
    
    # Create startup script
    startup_script = f"""#!/bin/bash
echo "🚀 Starting Mistral-7B GGUF Server"
echo "Model: {model_name}"
echo "File: {gguf_file}"
echo "Directory: {local_dir}"
echo "Port: 8000"
echo ""

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \\
    --model {model_name} \\
    --quantization gguf \\
    --gguf-file-name {gguf_file} \\
    --max-model-len 8192 \\
    --tensor-parallel-size 1 \\
    --port 8000 \\
    --host 0.0.0.0 \\
    --local-dir {local_dir}
"""
    
    with open("start_mistral_server.sh", "w") as f:
        f.write(startup_script)
    
    # Make startup script executable
    run_command("chmod +x start_mistral_server.sh", "Making startup script executable")
    
    print(f"\n✅ Deployment complete!")
    print(f"\n📁 Files created:")
    print(f"   • Model directory: {model_path.absolute()}")
    print(f"   • GGUF file: {gguf_path}")
    print(f"   • Startup script: {Path('start_mistral_server.sh').absolute()}")
    
    print(f"\n🚀 To start the server:")
    print(f"   ./start_mistral_server.sh")
    
    print(f"\n🌐 API Endpoints:")
    print(f"   • Health: http://localhost:8000/health")
    print(f"   • Chat: http://localhost:8000/v1/chat/completions")
    print(f"   • Models: http://localhost:8000/v1/models")
    print(f"   • Docs: http://localhost:8000/docs")
    
    print(f"\n🧪 Test the server:")
    print(f"   python test_real_endpoint.py http://localhost:8000 {model_name}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
