#!/usr/bin/env python3
"""Simple RTX 5090 VLLM concurrency test - focus on throughput limits."""

import asyncio
import sys
import os
import time
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


async def test_concurrency_level(persona_count, max_concurrent, test_name):
    """Test specific concurrency level on RTX 5090 VLLM."""
    print(f"\n🚀 Testing {test_name}: {persona_count} personas with {max_concurrent} concurrent requests")
    print("=" * 70)
    
    start_time = time.time()
    
    config = WorkflowConfig(
        persona_count=persona_count,
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=max_concurrent,
        questions=[
            "What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party"
        ]
    )
    
    orchestrator = SwissMarketResearchOrchestrator(config)
    await orchestrator.run_full_workflow()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️ {test_name} completed in {duration:.2f} seconds")
    
    # Check response format compliance
    if os.path.exists('responses_q1.json'):
        with open('responses_q1.json', 'r') as f:
            responses = json.load(f)
            successful = [r for r in responses if r['success']]
            
            success_rate = len(successful)/len(responses)*100
            avg_time = duration/persona_count
            throughput = persona_count/duration
            
            print(f"✅ Success Rate: {len(successful)}/{len(responses)} ({success_rate:.1f}%)")
            print(f"⚡ Avg Time/Persona: {avg_time:.2f}s")
            print(f"🔥 Throughput: {throughput:.1f} personas/second")
            
            # Simple format check - just count non-empty responses
            non_empty = [r for r in successful if r['answer'].strip()]
            non_empty_rate = len(non_empty)/len(successful)*100 if successful else 0
            print(f"📝 Non-Empty Responses: {non_empty_rate:.1f}%")
            
            return {
                'concurrent': max_concurrent,
                'success_rate': success_rate,
                'non_empty_rate': non_empty_rate,
                'avg_time': avg_time,
                'throughput': throughput,
                'total_time': duration,
                'passed': success_rate > 95  # Only care about success rate
            }
    
    return None


async def main():
    """Test RTX 5090 VLLM concurrency limits incrementing by 10."""
    print("🎮 RTX 5090 VLLM CONCURRENCY LIMIT TESTING")
    print("=" * 70)
    print("Hardware: RTX 5090 with VLLM")
    print("Testing incremental concurrency: +10 parallel requests per test")
    print("=" * 70)
    
    # Test sequence: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    test_levels = [
        (20, 10, "Level 1 - 10 Concurrent"),
        (30, 20, "Level 2 - 20 Concurrent"),
        (40, 30, "Level 3 - 30 Concurrent"),
        (50, 40, "Level 4 - 40 Concurrent"),
        (60, 50, "Level 5 - 50 Concurrent"),
        (70, 60, "Level 6 - 60 Concurrent"),
        (80, 70, "Level 7 - 70 Concurrent"),
        (90, 80, "Level 8 - 80 Concurrent"),
        (100, 90, "Level 9 - 90 Concurrent"),
        (110, 100, "Level 10 - 100 Concurrent"),
    ]
    
    results = []
    
    for personas, concurrent, name in test_levels:
        try:
            result = await test_concurrency_level(personas, concurrent, name)
            if result:
                results.append(result)
            
            if result and not result['passed']:
                print(f"❌ {name} failed - stopping further tests")
                break
                
            # Brief pause between tests
            print("⏸️ 3 second pause before next test...")
            await asyncio.sleep(3)
                
        except Exception as e:
            print(f"💥 {name} crashed: {str(e)}")
            break
    
    # Analysis
    print("\n" + "=" * 80)
    print("📊 RTX 5090 VLLM CONCURRENCY ANALYSIS")
    print("=" * 80)
    
    if results:
        print(f"{'Concurrent':<12} {'Success':<8} {'Non-Empty':<10} {'Avg Time':<10} {'Throughput':<12} {'Status'}")
        print("-" * 80)
        
        for r in results:
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
            print(f"{r['concurrent']:<12} {r['success_rate']:<7.1f}% {r['non_empty_rate']:<9.1f}% {r['avg_time']:<10.2f}s {r['throughput']:<12.1f} {status}")
        
        # Find optimal point
        successful = [r for r in results if r['passed']]
        if successful:
            max_concurrent = max([r['concurrent'] for r in successful])
            optimal = max(successful, key=lambda x: x['throughput'])
            
            print(f"\n🎯 CONCURRENCY LIMITS FOR RTX 5090 VLLM:")
            print(f"   Maximum Stable: {max_concurrent} concurrent requests")
            print(f"   Optimal Throughput: {optimal['concurrent']} concurrent @ {optimal['throughput']:.1f} personas/sec")
            print(f"   Recommended Production: {max_concurrent - 10} (with safety margin)")
            
            # Hardware utilization estimate
            if max_concurrent >= 80:
                print(f"   🚀 GPU Utilization: Excellent (80%+)")
            elif max_concurrent >= 60:
                print(f"   ⚡ GPU Utilization: Good (60-80%)")
            elif max_concurrent >= 40:
                print(f"   📊 GPU Utilization: Moderate (40-60%)")
            else:
                print(f"   📉 GPU Utilization: Low (<40%)")
    
    print("\n✨ RTX 5090 VLLM testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
