"""Enhanced LLM client with configurable parameters and proven extraction logic."""

import asyncio
import re
import time
import json
import aiohttp
from typing import List, Optional
from dataclasses import dataclass

from .config import AppConfig, ModelConfig, ConcurrencyConfig
from .personas.models import Persona
from .llm.models import QueryResult
from .concurrency import get_concurrency_manager


@dataclass
class ClientResult:
    """Enhanced result with additional metadata."""
    query_result: QueryResult
    extraction_method: str
    raw_content: str
    processing_time: float


class MarketResearchClient:
    """Enhanced LLM client for market research with configurable parameters."""
    
    def __init__(self, config: AppConfig):
        """Initialize the client with configuration."""
        self.config = config
        self.model_config = config.model
        self.concurrency_config = config.concurrency
        
    def create_balanced_prompt(self, persona: Persona, question: str) -> str:
        """Create balanced prompt that encourages but doesn't force format."""
        return f"""You are roleplaying as this Swiss voter:
- Age: {persona.age}, Gender: {persona.gender}
- Canton: {persona.canton}, Language: {persona.language}
- Occupation: {persona.occupation}, Education: {persona.education}
- Political Leaning: {persona.political_leaning}

QUESTION: {question}

Please respond as this persona would. Choose one option (A, B, C, or D) and briefly explain your choice in 1-2 sentences.

Your response:"""
    
    def extract_answer(self, content: str) -> tuple[str, str]:
        """Extract the political party choice from various response formats.
        
        Returns:
            tuple: (extracted_answer, extraction_method)
        """
        content = content.strip()
        
        # Pattern 1: Single letter at start (FIXED - handle leading spaces)
        if re.match(r'^\s*[ABCD]', content):
            # Find first non-space character
            for char in content:
                if char in 'ABCD':
                    return char, 'single_letter_start'
        
        # Pattern 2: JSON format
        json_match = re.search(r'["\']?answer["\']?\s*:\s*["\']?([ABCD])["\']?', content, re.IGNORECASE)
        if json_match:
            return json_match.group(1).upper(), 'json_format'
        
        # Pattern 3: "Answer: X" format
        answer_match = re.search(r'Answer\s*[:\-]?\s*([ABCD])', content, re.IGNORECASE)
        if answer_match:
            return answer_match.group(1).upper(), 'answer_colon'
        
        # Pattern 4: Letter mentioned in first sentence
        first_sentence = content.split('.')[0] if '.' in content else content
        for letter in ['A', 'B', 'C', 'D']:
            if re.search(rf'\b{letter}\b', first_sentence):
                return letter, 'first_sentence'
        
        # Pattern 5: Look for any A/B/C/D in response
        for letter in ['A', 'B', 'C', 'D']:
            if re.search(rf'\b{letter}\)', content) or re.search(rf'\b{letter}\s*\)', content):
                return letter, 'parenthesis_format'
        
        return None, 'no_extraction'
    
    async def query_persona(self, session: aiohttp.ClientSession, persona: Persona, question: str) -> ClientResult:
        """Query a single persona with the given question."""
        start_time = time.time()
        
        prompt = self.create_balanced_prompt(persona, question)
        
        payload = {
            "model": self.model_config.model_id,
            "prompt": prompt,
            "max_tokens": self.model_config.max_tokens,
            "temperature": self.model_config.temperature,
            "top_p": self.model_config.top_p
        }
        
        max_retries = self.concurrency_config.max_retries
        
        for attempt in range(max_retries):
            try:
                async with session.post(
                    f"{self.model_config.endpoint_url}/v1/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(
                        total=self.concurrency_config.timeout_total,
                        connect=self.concurrency_config.timeout_connect
                    )
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['text'].strip()
                        
                        # Smart extraction
                        answer, extraction_method = self.extract_answer(content)
                        
                        processing_time = time.time() - start_time
                        
                        if answer:
                            query_result = QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=answer,
                                response_time=response_time,
                                success=True
                            )
                        else:
                            query_result = QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer=content,
                                response_time=response_time,
                                success=False,
                                error_message=f"No clear choice found in: {content[:100]}..."
                            )
                        
                        return ClientResult(
                            query_result=query_result,
                            extraction_method=extraction_method,
                            raw_content=content,
                            processing_time=processing_time
                        )
                    else:
                        error_text = await response.text()
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5)
                            continue
                        else:
                            query_result = QueryResult(
                                persona_id=persona.id,
                                persona=persona,
                                question=question,
                                answer="",
                                response_time=response_time,
                                success=False,
                                error_message=f"HTTP {response.status}: {error_text}"
                            )
                            return ClientResult(
                                query_result=query_result,
                                extraction_method='http_error',
                                raw_content="",
                                processing_time=time.time() - start_time
                            )
                            
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    query_result = QueryResult(
                        persona_id=persona.id,
                        persona=persona,
                        question=question,
                        answer="",
                        response_time=time.time() - start_time,
                        success=False,
                        error_message=f"Exception after {max_retries} attempts: {str(e)}"
                    )
                    return ClientResult(
                        query_result=query_result,
                        extraction_method='exception',
                        raw_content="",
                        processing_time=time.time() - start_time
                    )
        
        # Should not reach here, but just in case
        query_result = QueryResult(
            persona_id=persona.id,
            persona=persona,
            question=question,
            answer="",
            response_time=time.time() - start_time,
            success=False,
            error_message="Unknown error"
        )
        return ClientResult(
            query_result=query_result,
            extraction_method='unknown_error',
            raw_content="",
            processing_time=time.time() - start_time
        )
    
    async def query_all_personas(self, personas: List[Persona], question: str) -> List[ClientResult]:
        """Query all personas with the given question concurrently using unified concurrency manager."""
        # Get unified concurrency manager
        concurrency_manager = self.config.get_concurrency_manager()
        
        print(f"🚀 Querying {len(personas)} personas with {self.concurrency_config.max_concurrent} max concurrent requests")
        
        async def bounded_query(session: aiohttp.ClientSession, persona: Persona) -> ClientResult:
            # Acquire slot from unified manager
            request_id = await concurrency_manager.acquire(
                request_type="llm_query",
                metadata={"persona_id": persona.id, "question": question[:50]}
            )
            
            try:
                await asyncio.sleep(self.concurrency_config.request_delay)  # Configurable delay
                result = await self.query_persona(session, persona, question)
                
                # Release slot with metrics
                concurrency_manager.release(
                    request_id=request_id,
                    success=result.query_result.success,
                    response_time=result.processing_time,
                    error=result.query_result.error_message
                )
                
                return result
                
            except Exception as e:
                # Release slot on error
                concurrency_manager.release(
                    request_id=request_id,
                    success=False,
                    response_time=time.time() - time.time(),
                    error=str(e)
                )
                raise
        
        connector = aiohttp.TCPConnector(
            limit=self.concurrency_config.max_concurrent * 2,
            limit_per_host=self.concurrency_config.max_concurrent,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.concurrency_config.timeout_total,
            connect=self.concurrency_config.timeout_connect
        )
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={"User-Agent": f"Market-Research-Client/2.0"}
        ) as session:
            print(f"⚡ Processing all {len(personas)} personas simultaneously...")
            tasks = [bounded_query(session, persona) for persona in personas]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            all_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    query_result = QueryResult(
                        persona_id=personas[i].id,
                        persona=personas[i],
                        question=question,
                        answer="",
                        response_time=0,
                        success=False,
                        error_message=f"Exception: {str(result)}"
                    )
                    all_results.append(ClientResult(
                        query_result=query_result,
                        extraction_method='exception',
                        raw_content="",
                        processing_time=0
                    ))
                else:
                    all_results.append(result)
            
            return all_results
    
    async def query_all_personas_stress(self, personas: List[Persona], question: str) -> List[ClientResult]:
        """Query all personas with given question using maximum concurrency (fire all at once)."""
        print(f"🚀 FIRING {len(personas)} REQUESTS SIMULTANEOUSLY - NO RATE LIMITING")
        
        async def direct_query(session: aiohttp.ClientSession, persona: Persona) -> ClientResult:
            """Direct query without any concurrency limits."""
            try:
                result = await self.query_persona(session, persona, question)
                return result
            except Exception as e:
                # Create error result for exceptions
                query_result = QueryResult(
                    persona_id=persona.id,
                    persona=persona,
                    question=question,
                    answer="",
                    response_time=0,
                    success=False,
                    error_message=f"Exception: {str(e)}"
                )
                return ClientResult(
                    query_result=query_result,
                    extraction_method='exception',
                    raw_content="",
                    processing_time=0
                )
        
        # Create session with high connection limits for maximum concurrency
        connector = aiohttp.TCPConnector(
            limit=len(personas) * 2,  # Allow many connections
            limit_per_host=len(personas),  # Allow many to same host
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.concurrency_config.timeout_total,
            connect=self.concurrency_config.timeout_connect
        )
        
        start_time = time.time()
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={"User-Agent": f"Market-Research-Client/2.0-Stress-Test"}
        ) as session:
            print(f"⚡ LAUNCHING ALL {len(personas)} REQUESTS AT ONCE...")
            
            # Fire all requests simultaneously - no semaphore, no delays
            tasks = [direct_query(session, persona) for persona in personas]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and exceptions
            all_results = []
            successful_count = 0
            failed_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Handle exceptions from gather
                    query_result = QueryResult(
                        persona_id=personas[i].id,
                        persona=personas[i],
                        question=question,
                        answer="",
                        response_time=0,
                        success=False,
                        error_message=f"Asyncio Exception: {str(result)}"
                    )
                    all_results.append(ClientResult(
                        query_result=query_result,
                        extraction_method='async_exception',
                        raw_content="",
                        processing_time=0
                    ))
                    failed_count += 1
                else:
                    all_results.append(result)
                    if result.query_result.success:
                        successful_count += 1
                    else:
                        failed_count += 1
            
            total_time = time.time() - start_time
            
            # Print stress test results
            print(f"\n🔥 STRESS TEST RESULTS:")
            print(f"   📊 Total Requests: {len(personas)}")
            print(f"   ✅ Successful: {successful_count}")
            print(f"   ❌ Failed: {failed_count}")
            print(f"   ⏱️ Total Time: {total_time:.2f}s")
            print(f"   🚀 Throughput: {len(personas)/total_time:.1f} requests/second")
            print(f"   📈 Success Rate: {successful_count/len(personas)*100:.1f}%")
            
            return all_results
    
    def print_extraction_stats(self, results: List[ClientResult]):
        """Print extraction method statistics."""
        extraction_methods = {}
        for result in results:
            method = result.extraction_method
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        print(f"\n📊 EXTRACTION METHODS:")
        for method, count in sorted(extraction_methods.items(), key=lambda x: x[1], reverse=True):
            print(f"   {method}: {count}")
    
    def print_summary(self, results: List[ClientResult]):
        """Print summary statistics of the query results."""
        query_results = [r.query_result for r in results]
        successful = [r for r in query_results if r.success]
        failed = [r for r in query_results if not r.success]
        
        print(f"\n📈 QUERY SUMMARY")
        print("=" * 50)
        print(f"✅ Successful: {len(successful)}/{len(query_results)} ({len(successful)/len(query_results)*100:.1f}%)")
        print(f"❌ Failed: {len(failed)}/{len(query_results)} ({len(failed)/len(query_results)*100:.1f}%)")
        
        if successful:
            avg_response_time = sum(r.response_time for r in successful) / len(successful)
            avg_processing_time = sum(r.processing_time for r in results if r.query_result.success) / len([r for r in results if r.query_result.success])
            print(f"⏱️ Avg Response Time: {avg_response_time:.2f}s")
            print(f"⚙️ Avg Processing Time: {avg_processing_time:.2f}s")
        
        # Quality check
        valid_letters = {'A', 'B', 'C', 'D'}
        valid_choices = [r for r in successful if r.answer in valid_letters]
        if len(query_results) > 0:
            quality_rate = len(valid_choices)/len(query_results)*100
            print(f"🎯 Quality Rate: {len(valid_choices)}/{len(query_results)} ({quality_rate:.1f}%)")
        
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
            print(f"🏛️ Left-Leaning Accuracy: {left_correct}/{left_total} ({left_accuracy:.1f}%)")
        
        if right_total > 0:
            right_accuracy = right_correct/right_total*100
            print(f"🏛️ Right-Leaning Accuracy: {right_correct}/{right_total} ({right_accuracy:.1f}%)")
        
        print("=" * 50)
        
        # Print extraction stats
        self.print_extraction_stats(results)
