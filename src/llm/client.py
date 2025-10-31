"""LLM client for handling large language model interactions."""

import json
import asyncio
import aiohttp
import time
from typing import List, Optional
from .models import QueryResult, MarketResearchQuery
from personas.models import Persona


class LLMClient:
    """Client for interacting with LLM endpoints."""
    
    def __init__(self, config: MarketResearchQuery):
        """Initialize the LLM client with configuration."""
        self.config = config
        self.endpoint_url = config.endpoint_url.rstrip('/')
        
    async def query_persona(self, session: aiohttp.ClientSession, persona: Persona, question: str) -> QueryResult:
        """Query a single persona with the given question."""
        start_time = time.time()
        
        # Create persona-specific prompt
        user_prompt = f"""Persona: {persona.description}
Age: {persona.age}, Gender: {persona.gender}, Canton: {persona.canton}, Language: {persona.language}
Occupation: {persona.occupation}, Education: {persona.education}, Political Leaning: {persona.political_leaning}

Question: {question}

Respond as this persona would, keeping their background and characteristics in mind."""
        
        # Create combined prompt for completions endpoint
        combined_prompt = f"{self.config.system_prompt}\n\n{user_prompt}"
        
        payload = {
            "model": self.config.model_id,
            "prompt": combined_prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p
        }
        
        try:
            async with session.post(
                f"{self.endpoint_url}/v1/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['text'].strip()
                    
                    # Parse JSON response
                    try:
                        parsed_response = json.loads(content)
                        if isinstance(parsed_response, dict) and 'answer' in parsed_response:
                            answer = parsed_response['answer']
                        else:
                            answer = content  # Fallback if not in expected format
                    except json.JSONDecodeError:
                        answer = content  # Fallback if JSON parsing fails
                    
                    return QueryResult(
                        persona_id=persona.id,
                        persona=persona,
                        question=question,
                        answer=answer,
                        response_time=response_time,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    return QueryResult(
                        persona_id=persona.id,
                        persona=persona,
                        question=question,
                        answer="",
                        response_time=response_time,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            return QueryResult(
                persona_id=persona.id,
                persona=persona,
                question=question,
                answer="",
                response_time=time.time() - start_time,
                success=False,
                error_message="Request timeout"
            )
        except Exception as e:
            return QueryResult(
                persona_id=persona.id,
                persona=persona,
                question=question,
                answer="",
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def query_all_personas(self, personas: List[Persona], question: str) -> List[QueryResult]:
        """Query all personas with the given question concurrently."""
        print(f"Querying {len(personas)} personas with: {question}")
        print(f"Using max concurrency: {self.config.max_concurrent}")
        
        # Create semaphore to limit concurrent requests
        max_concurrent = self.config.max_concurrent  # Use configured value directly
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_query(session: aiohttp.ClientSession, persona: Persona) -> QueryResult:
            async with semaphore:
                # Add delay between requests to avoid overwhelming the endpoint
                await asyncio.sleep(0.1)  # 100ms delay between requests (reduced for speed)
                return await self.query_persona(session, persona, question)
        
        # Create aiohttp session with conservative connection pooling
        connector = aiohttp.TCPConnector(
            limit=max_concurrent * 2,  # Total connection pool
            limit_per_host=max_concurrent,  # Per-host connections
            keepalive_timeout=60,  # Longer keepalive
            enable_cleanup_closed=True,
            force_close=False  # Keep connections alive
        )
        
        # Extended timeout for slow endpoints
        timeout = aiohttp.ClientTimeout(total=180, connect=30, sock_read=120)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={"User-Agent": "LLM-Client/1.0"}
        ) as session:
            # Create tasks for all personas at once (TRUE single batch)
            print(f"Processing all {len(personas)} personas simultaneously...")
            tasks = [bounded_query(session, persona) for persona in personas]
            
            # Execute all queries concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and convert to error results
            all_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
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
    
    def print_summary(self, results: List[QueryResult]):
        """Print summary statistics of the query results."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n=== Query Summary ===")
        print(f"Total queries: {len(results)}")
        print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        
        if successful:
            avg_response_time = sum(r.response_time for r in successful) / len(successful)
            print(f"Average response time: {avg_response_time:.2f}s")
            print(f"Min response time: {min(r.response_time for r in successful):.2f}s")
            print(f"Max response time: {max(r.response_time for r in successful):.2f}s")
        
        if failed:
            print(f"\nCommon errors:")
            error_counts = {}
            for result in failed:
                error_type = result.error_message.split(':')[0] if result.error_message else 'Unknown'
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count}")
