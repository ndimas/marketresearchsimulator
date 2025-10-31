#!/usr/bin/env python3
"""Test the extraction bug."""

import re

def test_extraction():
    """Test extraction logic with actual response."""
    
    # This is what the model returned
    content = " B) SP\n\nAs a left-leaning voter, I am drawn to Swiss People's Party (SP) due to their commitment to progressive policies such as social welfare, environmental protection, and fair labor practices."
    
    print("🧪 TESTING EXTRACTION LOGIC")
    print("=" * 50)
    print(f"Content: {repr(content)}")
    print("=" * 50)
    
    # Current extraction logic from ultimate test
    print("\n🔍 CURRENT LOGIC PATTERNS:")
    
    # Pattern 1: Single letter at start
    if re.match(r'^[ABCD]', content):
        print("✅ Pattern 1 MATCH - Single letter at start")
        print(f"   Returns: {content[0]}")
    else:
        print("❌ Pattern 1 FAILED - Single letter at start")
        print(f"   Regex: ^[ABCD]")
        print(f"   Content starts with: {repr(content[:10])}")
    
    # Pattern 2: JSON format
    json_match = re.search(r'["\']?answer["\']?\s*:\s*["\']?([ABCD])["\']?', content, re.IGNORECASE)
    if json_match:
        print("✅ Pattern 2 MATCH - JSON format")
    else:
        print("❌ Pattern 2 FAILED - JSON format")
    
    # Pattern 3: "Answer: X" format
    answer_match = re.search(r'Answer\s*[:\-]?\s*([ABCD])', content, re.IGNORECASE)
    if answer_match:
        print("✅ Pattern 3 MATCH - Answer: X format")
    else:
        print("❌ Pattern 3 FAILED - Answer: X format")
    
    # Pattern 4: Letter mentioned in first sentence
    first_sentence = content.split('.')[0] if '.' in content else content
    for letter in ['A', 'B', 'C', 'D']:
        if re.search(rf'\b{letter}\b', first_sentence):
            print(f"✅ Pattern 4 MATCH - Letter {letter} in first sentence")
            break
    else:
        print("❌ Pattern 4 FAILED - Letter in first sentence")
    
    # Pattern 5: Look for any A/B/C/D in response
    for letter in ['A', 'B', 'C', 'D']:
        if re.search(rf'\b{letter}\)', content) or re.search(rf'\b{letter}\s*\)', content):
            print(f"✅ Pattern 5 MATCH - Letter {letter}) pattern")
            break
    else:
        print("❌ Pattern 5 FAILED - Letter) pattern")
    
    print("\n🔧 PROPOSED FIX:")
    print("Change Pattern 1 to handle leading spaces:")
    print("  OLD: re.match(r'^[ABCD]', content)")
    print("  NEW: re.match(r'^\s*[ABCD]', content)")
    
    # Test proposed fix
    if re.match(r'^\s*[ABCD]', content):
        print("✅ PROPOSED FIX WORKS!")
        # Find first non-space character
        for char in content:
            if char in 'ABCD':
                print(f"   Would return: {char}")
                break

if __name__ == "__main__":
    test_extraction()
