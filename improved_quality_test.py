#!/usr/bin/env python3
"""Improved response quality test with better prompts and validation."""

import asyncio
import sys
import os
import time
import json
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


class ImprovedLLMClient:
    """LLM Client with better prompting and validation."""
    
    def __init__(self, config):
        self.config = config
        self.endpoint_url = config.endpoint_url.rstrip('/')
    
    def create_strict_prompt(self, persona, question):
        """Create strict prompt that enforces exact format."""
        return f"""You are roleplaying as a Swiss voter with these characteristics:
- Age: {persona.age}, Gender: {persona.gender}
- Canton: {persona.canton}, Language: {persona.language}
- Occupation: {persona.occupation}, Education: {persona.education}
- Political Leaning: {persona.political_leaning}

QUESTION: {question}

RULES:
1. You MUST respond with ONLY one letter: A, B, C, or D
2. DO NOT add explanations or extra text
3. DO NOT use JSON format
4. Your answer must be exactly one character

Your answer (A/B/C/D only):"""
    
    async def query_persona_strict(self, session, persona, question):
        """Query with strict validation and retry logic."""
        import aiohttp
        
        max_retries = 3
        for attempt in range(max_retries):
            start_time = time.time()
            
            prompt = self.create_strict_prompt(persona, question)
            
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "max_tokens": 10,  # Very short to force brevity
                "temperature": 0.1,  # Low temperature for consistency
                "top_p": 0.9,
                "stop": ["A", "B", "C", "D", "\n"]  # Stop at valid answers
            }
            
            try:
                async with session.post(
                    f"{self.endpoint_url}/v1/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['text'].strip()
                        
                        # Strict validation
                        if re.match(r'^[ABCD]$', content):
                            from llm.models import QueryResult
                            return QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=content,
                                response_time=response_time,
                                success=True
                            )
                        elif attempt < max_retries - 1:
                            # Invalid format, retry with even stricter prompt
                            continue
                        else:
                            # Final attempt failed, return error
                            from llm.models import QueryResult
                            return QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=content,
                                response_time=response_time,
                                success=False,
                                error_message=f"Invalid format after {max_retries} attempts: {content}"
                            )
                    else:
                        error_text = await response.text()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # Brief delay before retry
                            continue
                        else:
                            from llm.models import QueryResult
                            return QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer="",
                                response_time=response_time,
                                success=False,
                                error_message=f"HTTP {response.status}: {error_text}"
                            )
                            
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    from llm.models import QueryResult
                    return QueryResult(
                        persona_id=persona.id,
                        persona=persona,
                        question=question,
                        answer="",
                        response_time=time.time() - start_time,
                        success=False,
                        error_message=f"Exception after {max_retries} attempts: {str(e)}"
                    )
    
    async def query_all_personas_strict(self, personas, question):
        """Query all with strict validation and true concurrency."""
        print(f"Querying {len(personas)} personas with STRICT validation")
        print(f"Using max concurrency: {self.config.max_concurrent}")
        
        import aiohttp
        max_concurrent = self.config.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_query(session, persona):
            async with semaphore:
                await asyncio.sleep(0.05)  # Minimal delay
                return await self.query_persona_strict(session, persona, question)
        
        connector = aiohttp.TCPConnector(
            limit=max_concurrent * 2,
            limit_per_host=max_concurrent,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={"User-Agent": "Improved-LLM-Client/2.0"}
        ) as session:
            print(f"Processing all {len(personas)} personas simultaneously...")
            tasks = [bounded_query(session, persona) for persona in personas]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            all_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    from llm.models import QueryResult
                    all_results.append(QueryResult(
                        persona_id=personas[i].id,
                        persona=personas[i],
                        question=question,
                        answer="",
                        response_time=0,
                        success=False,
                        error_message=f"Exception: {str(result)}"
                    ))
                else:
                    all_results.append(result)
            
            return all_results


async def test_improved_quality():
    """Test improved response quality with strict validation."""
    print("🚀 IMPROVED RESPONSE QUALITY TEST")
    print("=" * 60)
    print("🎯 Objective: Test strict prompts + validation + retry")
    print("🔬 Purpose: Increase valid response rate from 16%")
    print("💪 Hardware: RTX 5090 with VLLM")
    print("=" * 60)
    
    # Load existing personas
    from personas import SwissPersonaGenerator
    generator = SwissPersonaGenerator()
    personas = generator.load_personas("personas.json")
    
    if not personas:
        print("❌ No personas found, generating new ones...")
        personas = generator.generate_personas(100)
        generator.save_personas(personas, "personas.json")
    
    # Use only 50 for faster testing
    test_personas = personas[:50]
    
    config = WorkflowConfig(
        persona_count=len(test_personas),
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=50,  # Test with 50 concurrent
        questions=[
            "What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party"
        ]
    )
    
    print(f"\n📋 Improved Test Configuration:")
    print(f"   👥 Personas: {len(test_personas)}")
    print(f"   ⚡ Max Concurrent: {config.max_concurrent}")
    print(f"   🔗 Endpoint: {config.endpoint_url}")
    print(f"   📝 Question: {config.questions[0]}")
    
    print(f"\n⏰ Starting improved quality test...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Use improved client
    client = ImprovedLLMClient(config)
    results = await client.query_all_personas_strict(test_personas, config.questions[0])
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n🏁 IMPROVED QUALITY TEST COMPLETED!")
    print("=" * 60)
    
    # Analyze improved results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    success_rate = len(successful)/len(results)*100
    throughput = len(results)/total_duration
    avg_time = total_duration/len(results)
    
    # Quality check - validate political party choices
    valid_letters = {'A', 'B', 'C', 'D'}
    valid_choices = [r for r in successful if r.answer in valid_letters]
    quality_rate = len(valid_choices)/len(results)*100
    
    print(f"📊 IMPROVED PERFORMANCE METRICS:")
    print(f"   ✅ Success Rate: {len(successful)}/{len(results)} ({success_rate:.1f}%)")
    print(f"   🎯 Quality Rate: {len(valid_choices)}/{len(results)} ({quality_rate:.1f}%)")
    print(f"   🔥 Throughput: {throughput:.1f} personas/second")
    print(f"   ⚡ Avg Time/Persona: {avg_time:.2f}s")
    print(f"   ⏱️ Total Duration: {total_duration:.2f}s")
    
    if successful:
        response_times = [r.response_time for r in successful]
        avg_response_time = sum(response_times)/len(response_times)
        print(f"   📈 Avg Response Time: {avg_response_time:.2f}s")
    
    print(f"\n🎯 IMPROVEMENT COMPARISON:")
    print(f"   Previous Quality: 16.0%")
    print(f"   New Quality: {quality_rate:.1f}%")
    improvement = quality_rate - 16.0
    print(f"   Improvement: {improvement:+.1f}% points")
    
    if quality_rate >= 80:
        print(f"   🟢 EXCELLENT: High-quality responses achieved!")
    elif quality_rate >= 60:
        print(f"   🟡 GOOD: Significant improvement achieved")
    elif quality_rate >= 40:
        print(f"   🟠 FAIR: Moderate improvement achieved")
    else:
        print(f"   🔴 NEEDS WORK: Further optimization required")
    
    # Save results for analysis
    from llm.models import QueryResult
    results_data = []
    for result in results:
        results_data.append({
            "persona_id": result.persona_id,
            "persona": result.persona.__dict__,
            "question": result.question,
            "answer": result.answer,
            "response_time": result.response_time,
            "success": result.success,
            "error_message": result.error_message
        })
    
    with open('improved_responses_q1.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to improved_responses_q1.json")


if __name__ == "__main__":
    asyncio.run(test_improved_quality())
