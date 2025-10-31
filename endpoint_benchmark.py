#!/usr/bin/env python3
"""
Comprehensive endpoint benchmark and debugging tool for LLM API.

This tool helps identify and fix issues with concurrent requests to LLM endpoints.
It includes:
1. Single request testing
2. Concurrent request testing with varying concurrency levels
3. Request format validation
4. Response format validation
5. Performance analysis
6. Error categorization and debugging
"""

import asyncio
import aiohttp
import json
import time
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse
import sys
from pathlib import Path


@dataclass
class BenchmarkRequest:
    """Individual request data for benchmarking."""
    request_id: int
    persona_prompt: str
    question: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    response_text: str = ""
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_time: float = 0.0


@dataclass
class BenchmarkResults:
    """Results of benchmark testing."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_counts: Dict[str, int]
    status_code_counts: Dict[int, int]
    requests: List[BenchmarkRequest]


class EndpointBenchmark:
    """Comprehensive endpoint benchmark and debugging tool."""
    
    def __init__(self, endpoint_url: str, model_id: str):
        """Initialize the benchmark tool."""
        self.endpoint_url = endpoint_url.rstrip('/')
        self.model_id = model_id
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=50,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=120, connect=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def create_test_payload(self, prompt: str, max_tokens: int = 150, temperature: float = 0.8) -> Dict[str, Any]:
        """Create a test payload for the completions endpoint."""
        return {
            "model": self.model_id,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    
    async def test_single_request(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Test a single request to the endpoint."""
        try:
            async with self.session.post(
                f"{self.endpoint_url}/v1/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        response_data = json.loads(response_text)
                        return True, response_data, ""
                    except json.JSONDecodeError as e:
                        return False, {}, f"Invalid JSON response: {e}"
                else:
                    return False, {}, f"HTTP {response.status}: {response_text}"
                    
        except asyncio.TimeoutError:
            return False, {}, "Request timeout"
        except aiohttp.ClientError as e:
            return False, {}, f"Client error: {e}"
        except Exception as e:
            return False, {}, f"Unexpected error: {e}"
    
    async def test_endpoint_connectivity(self) -> bool:
        """Test basic endpoint connectivity."""
        try:
            # Test OPTIONS request
            async with self.session.options(
                f"{self.endpoint_url}/v1/completions",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"OPTIONS request status: {response.status}")
                print(f"Allowed methods: {response.headers.get('Allow', 'Not specified')}")
                
            # Test health check if available
            try:
                async with self.session.get(
                    f"{self.endpoint_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    print(f"Health check status: {response.status}")
                    health_data = await response.json()
                    print(f"Health data: {health_data}")
            except:
                print("No health endpoint available")
                
            return True
            
        except Exception as e:
            print(f"Connectivity test failed: {e}")
            return False
    
    async def benchmark_concurrent_requests(
        self, 
        requests_data: List[Dict[str, str]], 
        max_concurrent: int = 10
    ) -> BenchmarkResults:
        """Benchmark concurrent requests with specified concurrency level."""
        print(f"\n=== Benchmarking {len(requests_data)} requests with concurrency {max_concurrent} ===")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Create benchmark requests
        benchmark_requests = []
        for i, req_data in enumerate(requests_data):
            persona_prompt = req_data['persona_prompt']
            question = req_data['question']
            combined_prompt = f"You are a Swiss citizen persona. {persona_prompt}\n\nQuestion: {question}"
            
            benchmark_requests.append(BenchmarkRequest(
                request_id=i,
                persona_prompt=persona_prompt,
                question=question,
                start_time=time.time()
            ))
        
        async def execute_request(bench_req: BenchmarkRequest) -> BenchmarkRequest:
            """Execute a single benchmark request."""
            async with semaphore:
                combined_prompt = f"You are a Swiss citizen persona. {bench_req.persona_prompt}\n\nQuestion: {bench_req.question}"
                payload = self.create_test_payload(combined_prompt)
                
                bench_req.start_time = time.time()
                success, response_data, error_message = await self.test_single_request(payload)
                bench_req.end_time = time.time()
                bench_req.response_time = bench_req.end_time - bench_req.start_time
                bench_req.success = success
                bench_req.error_message = error_message
                
                if success and 'choices' in response_data and len(response_data['choices']) > 0:
                    bench_req.response_text = response_data['choices'][0].get('text', '').strip()
                
                return bench_req
        
        # Execute all requests concurrently
        start_time = time.time()
        completed_requests = await asyncio.gather(
            *[execute_request(req) for req in benchmark_requests],
            return_exceptions=True
        )
        total_time = time.time() - start_time
        
        # Process results
        successful_requests = []
        error_counts = {}
        status_code_counts = {}
        
        for req in completed_requests:
            if isinstance(req, Exception):
                # Handle exceptions
                error_counts[f"Exception: {type(req).__name__}"] = error_counts.get(f"Exception: {type(req).__name__}", 0) + 1
                continue
                
            if req.success:
                successful_requests.append(req.response_time)
            else:
                # Categorize errors
                error_type = req.error_message.split(':')[0] if req.error_message else 'Unknown'
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                # Extract status code if available
                if 'HTTP ' in req.error_message:
                    try:
                        status_code = int(req.error_message.split(' ')[1])
                        status_code_counts[status_code] = status_code_counts.get(status_code, 0) + 1
                    except:
                        pass
        
        # Calculate statistics
        successful_count = len(successful_requests)
        failed_count = len(completed_requests) - successful_count
        
        if successful_requests:
            avg_response_time = statistics.mean(successful_requests)
            min_response_time = min(successful_requests)
            max_response_time = max(successful_requests)
            median_response_time = statistics.median(successful_requests)
            p95_response_time = self._percentile(successful_requests, 95)
            p99_response_time = self._percentile(successful_requests, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            median_response_time = p95_response_time = p99_response_time = 0
        
        requests_per_second = len(completed_requests) / total_time if total_time > 0 else 0
        
        # Filter out exceptions from requests list
        final_requests = []
        for req in completed_requests:
            if isinstance(req, Exception):
                continue
            final_requests.append(req)
        
        return BenchmarkResults(
            total_requests=len(completed_requests),
            successful_requests=successful_count,
            failed_requests=failed_count,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_counts=error_counts,
            status_code_counts=status_code_counts,
            requests=final_requests
        )
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def print_results(self, results: BenchmarkResults, test_name: str):
        """Print benchmark results in a formatted way."""
        print(f"\n{'='*60}")
        print(f"RESULTS: {test_name}")
        print(f"{'='*60}")
        
        print(f"Total Requests: {results.total_requests}")
        print(f"Successful: {results.successful_requests} ({results.successful_requests/results.total_requests*100:.1f}%)")
        print(f"Failed: {results.failed_requests} ({results.failed_requests/results.total_requests*100:.1f}%)")
        print(f"Requests/Second: {results.requests_per_second:.2f}")
        
        if results.successful_requests > 0:
            print(f"\nResponse Times (seconds):")
            print(f"  Average: {results.avg_response_time:.3f}")
            print(f"  Median: {results.median_response_time:.3f}")
            print(f"  Min: {results.min_response_time:.3f}")
            print(f"  Max: {results.max_response_time:.3f}")
            print(f"  95th percentile: {results.p95_response_time:.3f}")
            print(f"  99th percentile: {results.p99_response_time:.3f}")
        
        if results.error_counts:
            print(f"\nError Breakdown:")
            for error_type, count in sorted(results.error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count}")
        
        if results.status_code_counts:
            print(f"\nHTTP Status Codes:")
            for status_code, count in sorted(results.status_code_counts.items()):
                print(f"  HTTP {status_code}: {count}")
    
    def save_results(self, results: BenchmarkResults, filename: str):
        """Save benchmark results to JSON file."""
        # Convert requests to serializable format
        requests_data = []
        for req in results.requests:
            req_dict = asdict(req)
            requests_data.append(req_dict)
        
        results_dict = {
            "total_requests": results.total_requests,
            "successful_requests": results.successful_requests,
            "failed_requests": results.failed_requests,
            "avg_response_time": results.avg_response_time,
            "min_response_time": results.min_response_time,
            "max_response_time": results.max_response_time,
            "median_response_time": results.median_response_time,
            "p95_response_time": results.p95_response_time,
            "p99_response_time": results.p99_response_time,
            "requests_per_second": results.requests_per_second,
            "error_counts": results.error_counts,
            "status_code_counts": results.status_code_counts,
            "requests": requests_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"Results saved to {filename}")


def create_test_requests(num_requests: int = 50) -> List[Dict[str, str]]:
    """Create test requests with different personas and questions."""
    personas = [
        "I am a 35-year-old software engineer from Zurich, working in fintech.",
        "I am a 28-year-old teacher from Geneva, passionate about education.",
        "I am a 45-year-old farmer from Bern, concerned about agricultural policies.",
        "I am a 22-year-old student from Lausanne, studying environmental science.",
        "I am a 58-year-old banker from Zurich, experienced in international finance.",
        "I am a 31-year-old doctor from Basel, working in public health.",
        "I am a 39-year-old entrepreneur from Zurich, running a tech startup.",
        "I am a 26-year-old artist from Geneva, working in digital media.",
        "I am a 52-year-old politician from Bern, focusing on environmental issues.",
        "I am a 29-year-old lawyer from Zurich, specializing in corporate law."
    ]
    
    questions = [
        "What is your preferred political party in next Swiss election?",
        "What is your opinion on Switzerland's environmental policies?",
        "How do you feel about Switzerland's relationship with the European Union?",
        "What do you think about Swiss banking secrecy policies?",
        "What should be Switzerland's priority for economic development?"
    ]
    
    requests = []
    for i in range(num_requests):
        persona = personas[i % len(personas)]
        question = questions[i % len(questions)]
        requests.append({
            "persona_prompt": persona,
            "question": question
        })
    
    return requests


async def main():
    """Main function to run the benchmark."""
    parser = argparse.ArgumentParser(description="LLM Endpoint Benchmark Tool")
    parser.add_argument("--endpoint", default="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
                       help="Endpoint URL to test")
    parser.add_argument("--model", default="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
                       help="Model ID to use")
    parser.add_argument("--requests", type=int, default=50,
                       help="Number of requests to test")
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 5, 10, 20, 50],
                       help="Concurrency levels to test")
    parser.add_argument("--output", default="benchmark_results",
                       help="Output file prefix")
    
    args = parser.parse_args()
    
    print(f"LLM Endpoint Benchmark Tool")
    print(f"Endpoint: {args.endpoint}")
    print(f"Model: {args.model}")
    print(f"Total requests per test: {args.requests}")
    print(f"Concurrency levels: {args.concurrency}")
    
    # Create test requests
    test_requests = create_test_requests(args.requests)
    
    # Run benchmark
    async with EndpointBenchmark(args.endpoint, args.model) as benchmark:
        # Test connectivity first
        print("\n=== Testing Endpoint Connectivity ===")
        if not await benchmark.test_endpoint_connectivity():
            print("❌ Endpoint connectivity test failed")
            return
        print("✅ Endpoint connectivity test passed")
        
        # Test single request first
        print("\n=== Testing Single Request ===")
        test_payload = benchmark.create_test_payload("You are a helpful assistant. What is 2+2?")
        success, response_data, error = await benchmark.test_single_request(test_payload)
        
        if success:
            print("✅ Single request successful")
            print(f"Response: {response_data.get('choices', [{}])[0].get('text', 'No text')[:100]}...")
        else:
            print(f"❌ Single request failed: {error}")
            return
        
        # Run benchmarks with different concurrency levels
        all_results = {}
        
        for concurrency in args.concurrency:
            print(f"\n{'='*80}")
            print(f"STARTING BENCHMARK WITH CONCURRENCY LEVEL: {concurrency}")
            print(f"{'='*80}")
            
            results = await benchmark.benchmark_concurrent_requests(test_requests, concurrency)
            benchmark.print_results(results, f"Concurrency {concurrency}")
            
            # Save results
            filename = f"{args.output}_concurrency_{concurrency}.json"
            benchmark.save_results(results, filename)
            
            all_results[f"concurrency_{concurrency}"] = asdict(results)
            
            # Wait between tests to avoid overwhelming the endpoint
            if concurrency != args.concurrency[-1]:
                print("\n⏳ Waiting 30 seconds before next test...")
                await asyncio.sleep(30)
        
        # Save all results
        with open(f"{args.output}_summary.json", 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n{'='*80}")
        print("🎉 BENCHMARK COMPLETED!")
        print(f"Results saved to {args.output}_*.json files")
        print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
