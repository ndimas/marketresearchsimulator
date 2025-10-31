#!/usr/bin/env python3
"""Create new pod using API directly."""

import subprocess
import sys
import os
import json
import time

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

def create_pod():
    """Create new pod using API."""
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return None
    
    pod_config = {
        "name": "mistral-7b-gguf-working",
        "imageName": "runpod/pytorch:2.3.0-cuda12.1.1-devel-ubuntu22.04",
        "gpuType": "NVIDIA RTX 4090",
        "containerDiskInGb": 50,
        "volumeInGb": 20,
        "ports": "8000/http"
    }
    
    print("🚀 Creating new pod with correct configuration...")
    print("📋 Configuration:")
    print(f"   • Name: {pod_config['name']}")
    print(f"   • Image: {pod_config['imageName']}")
    print(f"   • GPU: {pod_config['gpuType']}")
    print(f"   • Ports: {pod_config['ports']}")
    print(f"   • Disk: {pod_config['containerDiskInGb']}GB")
    
    curl_cmd = f"""curl -X POST "https://api.runpod.io/v2/pods" \\
    -H "Authorization: Bearer {api_key}" \\
    -H "Content-Type: application/json" \\
