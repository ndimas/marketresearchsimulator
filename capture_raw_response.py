#!/usr/bin/env python3
"""Capture raw model responses to debug political alignment."""

import asyncio
import aiohttp
import json
import time

async def capture_raw_response():
    """Capture the actual model response for a left-leaning persona."""
    
    # Use the exact same prompt from our test
    prompt = """You are roleplaying as this Swiss voter:
- Age: 33, Gender: Male
- Canton: Bern, Language: German
- Occupation: Journalist, Education: Master
- Political Leaning: Left

QUESTION: What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party

Please respond as this persona would. Choose one option (A, B, C, or D) and briefly explain your choice in 1-2 sentences.

Your response:"""
    
    payload = {
        "model": "TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        "prompt": prompt,
        "max_tokens": 100,
        "temperature": 0.3,
        "top_p": 0.9
    }
    
    print("🔍 CAPTURING RAW MODEL RESPONSE")
    print("=" * 60)
    print("Persona: 33yo Male Journalist from Bern, Political Leaning: Left")
    print("Expected: Should choose B (SP) or D (Green Party)")
    print("=" * 60)
    
    try:
        # Use same settings as our working test
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Debug-Client/1.0"}
        ) as session:
            
            print("📡 Sending request...")
            start_time = time.time()
            
            async with session.post(
                "https://kx02ilhnbvqcrw-8000.proxy.runpod.net/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_time = time.time() - start_time
                print(f"⏱️ Response time: {response_time:.2f}s")
                print(f"📡 HTTP Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"\n📝 RAW MODEL RESPONSE:")
                    print("-" * 40)
                    content = data['choices'][0]['text']
                    print(repr(content))  # Show raw representation
                    print("\nFormatted:")
                    print(f"'{content}'")
                    print("-" * 40)
                    
                    # Analyze the response
                    print(f"\n🔍 ANALYSIS:")
                    print(f"📏 Length: {len(content)} characters")
                    
                    # Check what's actually in the response
                    if 'A)' in content:
                        print("🎯 Contains 'A)' - SVP (Conservative)")
                    if 'B)' in content:
                        print("🎯 Contains 'B)' - SP (Socialist)")
                    if 'C)' in content:
                        print("🎯 Contains 'C)' - FDP (Liberal)")
                    if 'D)' in content:
                        print("🎯 Contains 'D)' - Green Party")
                    
                    # Show our extraction logic
                    print(f"\n🧪 EXTRACTION TEST:")
                    import re
                    for letter in ['A', 'B', 'C', 'D']:
                        if re.search(rf'\b{letter}\)', content):
                            print(f"   Pattern \\b{letter}\\): MATCH")
                        elif re.search(rf'\b{letter}\b', content):
                            print(f"   Pattern \\b{letter}\\b: MATCH")
                        elif content.startswith(letter):
                            print(f"   Startswith '{letter}': MATCH")
                    
                    # Political alignment check
                    if content.startswith('A') or 'A)' in content:
                        print(f"\n🚨 POLITICAL MISMATCH DETECTED!")
                        print(f"   Left-leaning persona chose Conservative SVP")
                        print(f"   This confirms the alignment problem!")
                    elif content.startswith('B') or 'B)' in content:
                        print(f"\n✅ POLITICALLY CONSISTENT!")
                        print(f"   Left-leaning chose Socialist SP")
                    elif content.startswith('D') or 'D)' in content:
                        print(f"\n✅ POLITICALLY CONSISTENT!")
                        print(f"   Left-leaning chose Green Party")
                    
                else:
                    error_text = await response.text()
                    print(f"\n❌ HTTP ERROR: {response.status}")
                    print(f"Error: {error_text}")
                    
    except asyncio.TimeoutError:
        print("\n⏰ REQUEST TIMEOUT - Endpoint may be overloaded")
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")

if __name__ == "__main__":
    asyncio.run(capture_raw_response())
