#!/usr/bin/env python3
"""Ultimate test: 100 concurrent + 5 questions sequentially - FIXED EXTRACTION."""

import asyncio
import sys
import os
import time
import json
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


class UltimateLLMClient:
    """Ultimate LLM Client with proven balanced approach - FIXED EXTRACTION."""
    
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
        
        # Pattern 1: Single letter at start (FIXED - handle leading spaces)
        if re.match(r'^\s*[ABCD]', content):
            # Find first non-space character
            for char in content:
                if char in 'ABCD':
                    return char
        
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
                "max_tokens": 100,
                "temperature": 0.3,
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
                            continue
                        else:
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
        print(f"Querying {len(personas)} personas with ULTIMATE concurrency (100) - FIXED EXTRACTION")
        
        import aiohttp
        max_concurrent = self.config.max_concurrent
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_query(session, persona):
            async with semaphore:
                await asyncio.sleep(0.02)  # Minimal delay
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
            headers={"User-Agent": "Ultimate-LLM-Client-FIXED/4.1"}
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


async def test_ultimate_100_5questions_fixed():
    """Test 100 concurrent + 5 questions sequentially - WITH FIXED EXTRACTION."""
    print("🚀 ULTIMATE 100 CONCURRENT + 5 QUESTIONS TEST - EXTRACTION FIXED")
    print("=" * 80)
    print("🎯 Objective: Test max_concurrent=100 with 5 sequential questions")
    print("🔧 FIX: Regex pattern now handles leading spaces in model responses")
    print("🔬 Purpose: Push RTX 5090 VLLM to absolute limits")
    print("💪 Hardware: RTX 5090 with VLLM")
    print("📊 Previous Best: 100% quality at 50 concurrent")
    print("=" * 80)
    
    # Load 100 personas
    from personas import SwissPersonaGenerator
    generator = SwissPersonaGenerator()
    personas = generator.load_personas("personas.json")
    
    if not personas or len(personas) < 100:
        print("❌ Generating 100 personas...")
        personas = generator.generate_personas(100)
        generator.save_personas(personas, "personas.json")
    
    # Use all 100 personas
    test_personas = personas[:100]
    
    # 5 questions for sequential testing
    questions = [
        "What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party",
        "What should be Switzerland's top priority? A) Economic Growth B) Climate Action C) Social Welfare D) National Security",
        "Which EU policy should Switzerland adopt? A) Free Movement B) Trade Agreement C) Climate Standards D) Digital Integration",
        "What tax system do you prefer? A) Progressive B) Flat C) Consumption D) Wealth Tax",
        "How should Switzerland handle immigration? A) Open Borders B) Skilled Only C) Quota System D) Strict Limits"
    ]
    
    config = WorkflowConfig(
        persona_count=len(test_personas),
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=100,  # ULTIMATE TEST!
        questions=questions
    )
    
    print(f"\n📋 Ultimate Test Configuration:")
    print(f"   👥 Personas: {len(test_personas)}")
    print(f"   ⚡ Max Concurrent: {config.max_concurrent}")
    print(f"   🔗 Endpoint: {config.endpoint_url}")
    print(f"   📝 Questions: {len(questions)} sequential")
    print(f"   🔧 FIX: Extraction now handles leading spaces in responses")
    print(f"   📁 Results will be saved to:")
    print(f"      - ultimate_responses_fixed_q1.json through ultimate_responses_fixed_q5.json")
    
    all_results = {}
    question_start_time = time.time()
    
    # Process each question sequentially
    for q_idx, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"📝 QUESTION {q_idx}/{len(questions)}")
        print(f"❓ {question}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # Use ultimate client with FIXED extraction
        client = UltimateLLMClient(config)
        results = await client.query_all_personas_balanced(test_personas, question)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🏁 QUESTION {q_idx} COMPLETED!")
        print(f"   ⏱️ Duration: {duration:.2f}s")
        
        # Analyze results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        success_rate = len(successful)/len(results)*100
        throughput = len(results)/duration
        avg_time = duration/len(results)
        
        # Quality check
        valid_letters = {'A', 'B', 'C', 'D'}
        valid_choices = [r for r in successful if r.answer in valid_letters]
        quality_rate = len(valid_choices)/len(results)*100
        
        print(f"   ✅ Success Rate: {len(successful)}/{len(results)} ({success_rate:.1f}%)")
        print(f"   🎯 Quality Rate: {len(valid_choices)}/{len(results)} ({quality_rate:.1f}%)")
        print(f"   🔥 Throughput: {throughput:.1f} personas/second")
        
        # Political alignment check
        left_correct = 0
        left_total = 0
        right_correct = 0
        right_total = 0
        
        for result in successful:
            persona = result.persona
            if persona.political_leaning in ['Left', 'Center-Left']:
                left_total += 1
                if result.answer in ['B', 'D']:  # SP or Green
                    left_correct += 1
            elif persona.political_leaning in ['Right', 'Center-Right']:
                right_total += 1
                if result.answer in ['A', 'C']:  # SVP or FDP
                    right_correct += 1
        
        if left_total > 0:
            left_accuracy = left_correct/left_total*100
            print(f"   🏛️ Left-Leaning Accuracy: {left_correct}/{left_total} ({left_accuracy:.1f}%)")
        
        if right_total > 0:
            right_accuracy = right_correct/right_total*100
            print(f"   🏛️ Right-Leaning Accuracy: {right_correct}/{right_total} ({right_accuracy:.1f}%)")
        
        # Save results for this question
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
        
        filename = f'ultimate_responses_fixed_q{q_idx}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Results saved to {filename}")
        
        all_results[f'q{q_idx}'] = {
            'success_rate': success_rate,
            'quality_rate': quality_rate,
            'throughput': throughput,
            'duration': duration,
            'left_accuracy': left_accuracy if left_total > 0 else None,
            'right_accuracy': right_accuracy if right_total > 0 else None
        }
        
        # Brief pause between questions
        if q_idx < len(questions):
            print(f"   ⏸️ Brief pause before next question...")
            await asyncio.sleep(2)
    
    total_time = time.time() - question_start_time
    
    print(f"\n{'🏆'*20}")
    print(f"🏆 ULTIMATE TEST COMPLETED - EXTRACTION FIXED!")
    print(f"{'🏆'*20}")
    
    print(f"\n📊 OVERALL PERFORMANCE SUMMARY:")
    print(f"   ⏱️ Total Duration: {total_time:.2f}s")
    print(f"   👥 Total Personas Processed: {len(test_personas) * len(questions)}")
    print(f"   📝 Questions Processed: {len(questions)}")
    
    # Calculate averages
    avg_success = sum(r['success_rate'] for r in all_results.values()) / len(all_results)
    avg_quality = sum(r['quality_rate'] for r in all_results.values()) / len(all_results)
    avg_throughput = sum(r['throughput'] for r in all_results.values()) / len(all_results)
    
    left_accuracies = [r['left_accuracy'] for r in all_results.values() if r['left_accuracy'] is not None]
    avg_left_accuracy = sum(left_accuracies) / len(left_accuracies) if left_accuracies else 0
    
    print(f"\n📈 AVERAGE PERFORMANCE:")
    print(f"   ✅ Avg Success Rate: {avg_success:.1f}%")
    print(f"   🎯 Avg Quality Rate: {avg_quality:.1f}%")
    print(f"   🔥 Avg Throughput: {avg_throughput:.1f} personas/second")
    print(f"   🏛️ Avg Political Alignment: {avg_left_accuracy:.1f}%")
    
    print(f"\n🎯 100 CONCURRENT TEST RESULT:")
    if avg_quality >= 95 and avg_left_accuracy >= 80:
        print(f"   🟢 EXCELLENT: RTX 5090 handles 100 concurrent perfectly with correct political alignment!")
    elif avg_quality >= 80 and avg_left_accuracy >= 70:
        print(f"   🟡 GOOD: RTX 5090 handles 100 concurrent well with good political alignment")
    elif avg_quality >= 60 and avg_left_accuracy >= 50:
        print(f"   🟠 FAIR: RTX 5090 manages 100 concurrent with moderate political alignment")
    else:
        print(f"   🔴 NEEDS WORK: Political alignment still has issues")
    
    print(f"\n📁 ALL FILES CREATED:")
    for q_idx in range(1, len(questions) + 1):
        print(f"   - ultimate_responses_fixed_q{q_idx}.json")


if __name__ == "__main__":
    asyncio.run(test_ultimate_100_5questions_fixed())
