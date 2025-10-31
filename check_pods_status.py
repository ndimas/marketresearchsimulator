#!/usr/bin/env python3
"""
Check RunPod Pod Status
This script checks the status of RunPod pods using both runpodctl and direct API calls.
"""

import os
import subprocess
import json
import requests
from typing import Dict, Any, Optional

def run_command(cmd: str, env: Optional[Dict[str, str]] = None) -> tuple[int, str, str]:
    """Run a command and return return code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env or os.environ
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_pods_with_api(api_key: str) -> Dict[str, Any]:
    """Check pods using RunPod API directly"""
    print("🔍 Checking pods via RunPod API...")
    
    # Try different API endpoints
    endpoints = [
        "https://api.runpod.io/v2/pods",
        "https://api.runpod.ai/v2/pods",
        "https://api.runpod.com/v2/pods"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for endpoint in endpoints:
        print(f"  📡 Trying: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"  📊 Status: {response.status_code}")
            print(f"  📄 Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "success": True,
                        "endpoint": endpoint,
                        "data": data,
                        "pods": data if isinstance(data, list) else data.get("pods", [])
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "endpoint": endpoint,
                        "error": f"JSON decode error: {e}",
                        "response_text": response.text
                    }
            else:
                return {
                    "success": False,
                    "endpoint": endpoint,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
            return {
                "success": False,
                "endpoint": endpoint,
                "error": str(e)
            }
    
    return {"success": False, "error": "All endpoints failed"}

def check_pods_with_runpodctl(api_key: str) -> Dict[str, Any]:
    """Check pods using runpodctl"""
    print("🔍 Checking pods via runpodctl...")
    
    # Set up environment for runpodctl
    env = {
        "RUNPOD_API_KEY": api_key,
        "PATH": f"{os.environ.get('PATH', '')}:."
    }
    
    # Try to run runpodctl commands
    commands = [
        "./runpodctl get pod",
        "./runpodctl get pods", 
        "./runpodctl list pods"
    ]
    
    for cmd in commands:
        print(f"  📡 Running: {cmd}")
        returncode, stdout, stderr = run_command(cmd, env)
        
        print(f"  📊 Return code: {returncode}")
        if stdout:
            print(f"  📄 STDOUT: {stdout[:500]}...")
        if stderr:
            print(f"  ❌ STDERR: {stderr[:500]}...")
        
        if returncode == 0:
            return {
                "success": True,
                "command": cmd,
                "stdout": stdout,
                "method": "runpodctl"
            }
    
    return {"success": False, "error": "All runpodctl commands failed"}

def main():
    """Main function"""
    print("🚀 RunPod Pod Status Check")
    print("=" * 50)
    
    # Get API key
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set")
        return 1
    
    print(f"🔑 Using API key: {api_key[:20]}...")
    
    # Check using runpodctl
    runpodctl_result = check_pods_with_runpodctl(api_key)
    
    # Check using direct API
    api_result = check_pods_with_api(api_key)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    # Analyze results
    success_count = 0
    
    if runpodctl_result.get("success"):
        success_count += 1
        print("✅ runpodctl: SUCCESS")
        if runpodctl_result.get("stdout"):
            print(f"📋 Output: {runpodctl_result['stdout']}")
    else:
        print("❌ runpodctl: FAILED")
        print(f"📋 Error: {runpodctl_result.get('error', 'Unknown error')}")
    
    if api_result.get("success"):
        success_count += 1
        print("✅ API: SUCCESS")
        pods = api_result.get("pods", [])
        if isinstance(pods, list) and pods:
            print(f"📋 Found {len(pods)} pod(s):")
            for i, pod in enumerate(pods):
                pod_id = pod.get("id", "unknown")
                pod_name = pod.get("name", "unnamed")
                pod_status = pod.get("desiredState", "unknown")
                pod_gpu = pod.get("gpuType", "unknown")
                print(f"  {i+1}. {pod_name} ({pod_id}) - {pod_status} - {pod_gpu}")
        else:
            print("📋 No pods found or unexpected response format")
            print(f"📋 Raw response: {api_result.get('data', 'No data')}")
    else:
        print("❌ API: FAILED")
        print(f"📋 Error: {api_result.get('error', 'Unknown error')}")
        print(f"📋 Status code: {api_result.get('status_code', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print(f"🎯 OVERALL: {success_count}/2 methods successful")
    
    # Provide recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if success_count == 0:
        print("  ❌ Both runpodctl and API failed")
        print("  🔍 Check API key validity")
        print("  🔍 Check network connectivity")
        print("  🔍 Try updating runpodctl")
    elif success_count == 1:
        print("  ⚠️  Only one method worked - partial configuration issue")
    else:
        print("  ✅ Both methods worked - configuration is good")
        
    print("\n📝 NEXT STEPS:")
    print("  1. If pods exist, use: ./runpodctl get pod <pod-id>")
    print("  2. If no pods, create one with: ./runpodctl create pod ...")
    print("  3. Check RunPod dashboard at https://runpod.io/console")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit(main())
