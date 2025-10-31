#!/usr/bin/env python3
"""Debug political alignment issues in LLM responses."""

import asyncio
import aiohttp
import json
import time

async def test_single_persona():
    """Test a single left-leaning persona to see actual response."""
    
    # Test with a clearly left-leaning persona
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
    
    print("🔍 TESTING SINGLE LEFT-LEANING PERSONA")
    print("=" * 50)
    print("Persona: 33yo Male Journalist from Bern, Political Leaning: Left")
    print("Question: Which Swiss political party?")
    print("Expected: Should lean toward SP (Socialist Party) or Green Party")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(
                "https://kx02ilhnbvqcrw-8000.proxy.runpod.net/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"📡 HTTP Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['text'].strip()
                    
                    print(f"\n📝 RAW LLM RESPONSE:")
                    print(f"'{content}'")
                    print(f"\n📏 Response Length: {len(content)} characters")
                    
                    # Analyze the response
                    if 'A)' in content or content.startswith('A'):
                        print("🎯 DETECTED CHOICE: A) SVP (Conservative)")
                    elif 'B)' in content or content.startswith('B'):
                        print("🎯 DETECTED CHOICE: B) SP (Socialist/Left)")
                    elif 'C)' in content or content.startswith('C'):
                        print("🎯 DETECTED CHOICE: C) FDP (Liberal)")
                    elif 'D)' in content or content.startswith('D'):
                        print("🎯 DETECTED CHOICE: D) Green Party (Environmental/Left)")
                    else:
                        print("❌ NO CLEAR CHOICE DETECTED")
                    
                    # Check if response makes political sense
                    if 'A)' in content or content.startswith('A'):
                        print("\n🚨 POLITICAL MISMATCH!")
                        print("   Left-leaning persona chose Conservative SVP")
                        print("   This suggests poor persona adherence")
                    else:
                        print("\n✅ POLITICALLY CONSISTENT CHOICE")
                        
                else:
                    error_text = await response.text()
                    print(f"\n❌ HTTP ERROR: {response.status}")
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_single_persona())
