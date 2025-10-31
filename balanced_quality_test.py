#!/usr/bin/env python3
"""Balanced response quality test - better prompts without being too restrictive."""

import asyncio
import sys
import os
import time
import json
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


class BalancedLLMClient:
    """LLM Client with balanced prompting and smart parsing."""
    
    def __init__(self, config):
        self.config = config
        self.endpoint_url = config.endpoint_url.rstrip('/')
    
    def create_balanced_prompt(self, persona, question):
        """Create balanced prompt that encourages but doesn't force format."""
        return f"""You are roleplaying as this Swiss voter:
- Age: {persona.age}, Gender: {persona.gender}
- Canton: {persona.canton}, Language: {persona.language}
- Occupation: {persona.occupation}, Education: {persona.education}
- Political Leaning: {persona.political_leaning}

QUESTION: {question}

Please respond as this persona would. Choose one option (A, B, C, or D) and briefly explain your choice in 1-2 sentences.

Your response:"""
    
    def extract_answer(self, content):
        """Extract the political party choice from various response formats."""
        content = content.strip()
        
        # Pattern 1: Single letter at start
        if re.match(r'^[ABCD]', content):
            return content[0]
        
        # Pattern 2: JSON format
        json_match = re.search(r'["\']?answer["\']?\s*:\s*["\']?([ABCD])["\']?', content, re.IGNORECASE)
        if json_match:
            return json_match.group(1).upper()
        
        # Pattern 3: "Answer: X" format
        answer_match = re.search(r'Answer\s*[:\-]?\s*([ABCD])', content, re.IGNORECASE)
        if answer_match:
            return answer_match.group(1).upper()
        
        # Pattern 4: Letter mentioned in first sentence
        first_sentence = content.split('.')[0] if '.' in content else content
        for letter in ['A', 'B', 'C', 'D']:
            if re.search(rf'\b{letter}\b', first_sentence):
                return letter
        
        # Pattern 5: Look for any A/B/C/D in response
        for letter in ['A', 'B', 'C', 'D']:
            if re.search(rf'\b{letter}\)', content) or re.search(rf'\b{letter}\s*\)', content):
                return letter
        
        return None
    
    async def query_persona_balanced(self, session, persona, question):
        """Query with balanced approach and smart parsing."""
        import aiohttp
        
        max_retries = 2
        for attempt in range(max_retries):
            start_time = time.time()
            
            prompt = self.create_balanced_prompt(persona, question)
            
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "max_tokens": 100,  # Reasonable length for explanations
                "temperature": 0.3,  # Low-moderate for consistency
                "top_p": 0.9
            }
            
            try:
                async with session.post(
                    f"{self.endpoint_url}/v1/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['text'].strip()
                        
                        # Smart extraction
                        answer = self.extract_answer(content)
                        
                        if answer:
                            from llm.models import QueryResult
                            return QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=answer,
                                response_time=response_time,
                                success=True
                            )
                        elif attempt < max_retries - 1:
                            # No clear answer, retry
                            continue
                        else:
                            # Final attempt failed, return as error
                            from llm.models import QueryResult
                            return QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=content,
                                response_time=response_time,
                                success=False,
                                error_message=f"No clear choice found in: {content[:100]}..."
                            )
                    else:
                        error_text = await response.text()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5)
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
                    await asyncio.sleep(0.5)
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
    
    async def query_all_personas_balanced(self, personas, question):
        """Query all with balanced approach."""
        print(f"Querying {len(personas)} personas with BALANCED approach")
        print(f"Using max concurrency: {self.config.max_concurrent}")
        
        import aiohttp
        max_concurrent = self.config.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_query(session, persona):
            async with semaphore:
                await asyncio.sleep(0.05)  # Minimal delay
                return await self.query_persona_balanced(session, persona, question)
        
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
            headers={"User-Agent": "Balanced-LLM-Client/3.0"}
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


async def test_balanced_quality():
    """Test balanced response quality."""
    print("⚖️ BALANCED RESPONSE QUALITY TEST")
    print("=" * 60)
    print("🎯 Objective: Test balanced prompts + smart parsing")
    print("🔬 Purpose: Improve from 16% while allowing natural responses")
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
    
    # Use 50 for testing
    test_personas = personas[:50]
    
    config = WorkflowConfig(
        persona_count=len(test_personas),
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=50,
        questions=[
            "What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party"
        ]
    )
    
    print(f"\n📋 Balanced Test Configuration:")
    print(f"   👥 Personas: {len(test_personas)}")
    print(f"   ⚡ Max Concurrent: {config.max_concurrent}")
    print(f"   🔗 Endpoint: {config.endpoint_url}")
    print(f"   📝 Question: {config.questions[0]}")
    
    print(f"\n⏰ Starting balanced quality test...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Use balanced client
    client = BalancedLLMClient(config)
    results = await client.query_all_personas_balanced(test_personas, config.questions[0])
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n🏁 BALANCED QUALITY TEST COMPLETED!")
    print("=" * 60)
    
    # Analyze results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    success_rate = len(successful)/len(results)*100
    throughput = len(results)/total_duration
    avg_time = total_duration/len(results)
    
    # Quality check
    valid_letters = {'A', 'B', 'C', 'D'}
    valid_choices = [r for r in successful if r.answer in valid_letters]
    quality_rate = len(valid_choices)/len(results)*100
    
    print(f"📊 BALANCED PERFORMANCE METRICS:")
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
    print(f"   Original Quality: 16.0%")
    print(f"   Strict Quality: 0.0%")
    print(f"   Balanced Quality: {quality_rate:.1f}%")
    
    if quality_rate >= 16:
        improvement = quality_rate - 16.0
        print(f"   Improvement vs Original: +{improvement:.1f}% points 🎉")
    else:
        regression = 16.0 - quality_rate
        print(f"   Regression vs Original: -{regression:.1f}% points ⚠️")
    
    if quality_rate >= 60:
        print(f"   🟢 EXCELLENT: High-quality responses achieved!")
    elif quality_rate >= 40:
        print(f"   🟡 GOOD: Significant improvement achieved")
    elif quality_rate >= 20:
        print(f"   🟠 FAIR: Moderate improvement achieved")
    else:
        print(f"   🔴 NEEDS WORK: Further optimization required")
    
    # Show some examples
    print(f"\n📝 SAMPLE RESPONSES:")
    for i, result in enumerate(valid_choices[:5]):
        print(f"   {i+1}. Persona {result.persona_id} ({result.persona.political_leaning}): {result.answer}")
    
    if failed[:3]:
        print(f"\n❌ SAMPLE ERRORS:")
        for i, result in enumerate(failed[:3]):
            print(f"   {i+1}. Persona {result.persona_id}: {result.error_message}")
    
    # Save results
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
    
    with open('balanced_responses_q1.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to balanced_responses_q1.json")


if __name__ == "__main__":
    asyncio.run(test_balanced_quality())
