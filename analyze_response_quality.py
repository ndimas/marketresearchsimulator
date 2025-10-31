#!/usr/bin/env python3
"""Analyze response quality from RTX 5090 VLLM test."""

import json

def analyze_response_quality():
    """Analyze if non-empty responses are valid political party choices."""
    with open('responses_q1.json', 'r') as f:
        responses = json.load(f)
    
    valid_responses = []
    invalid_responses = []
    empty_responses = []
    
    valid_letters = {'A', 'B', 'C', 'D'}
    
    for response in responses:
        answer = response['answer'].strip()
        
        if not answer:
            empty_responses.append(response)
            continue
            
        # Check for valid single letter
        if answer in valid_letters:
            valid_responses.append((response, "SINGLE_LETTER"))
            continue
            
        # Check for valid JSON format
        if answer.startswith("{'answer':") and answer.endswith("'}"):
            try:
                parsed = json.loads(answer)
                if isinstance(parsed, dict) and parsed.get('answer') in valid_letters:
                    valid_responses.append((response, "VALID_JSON"))
                    continue
            except:
                pass
        
        # Check for Answer: X format
        if answer.startswith("Answer:") and len(answer) > 8:
            letter = answer.split("Answer:")[1].strip().split()[0]
            if letter in valid_letters:
                valid_responses.append((response, "ANSWER_FORMAT"))
                continue
        
        # Check for {answer: X} format
        if answer.startswith("{answer:") and len(answer) < 15:
            letter = answer.split("{answer:")[1].strip().rstrip('}')
            if letter in valid_letters:
                valid_responses.append((response, "SIMPLE_JSON"))
                continue
        
        # If none of the above, it's invalid
        invalid_responses.append((response, "INVALID"))
    
    print(f"📊 RESPONSE QUALITY ANALYSIS")
    print(f"=" * 50)
    print(f"Total responses: {len(responses)}")
    print(f"Empty responses: {len(empty_responses)} ({len(empty_responses)/len(responses)*100:.1f}%)")
    print(f"Valid responses: {len(valid_responses)} ({len(valid_responses)/len(responses)*100:.1f}%)")
    print(f"Invalid responses: {len(invalid_responses)} ({len(invalid_responses)/len(responses)*100:.1f}%)")
    
    print(f"\n✅ VALID RESPONSE TYPES:")
    valid_types = {}
    for _, valid_type in valid_responses:
        valid_types[valid_type] = valid_types.get(valid_type, 0) + 1
    
    for valid_type, count in sorted(valid_types.items()):
        print(f"  {valid_type}: {count}")
    
    print(f"\n❌ INVALID RESPONSE EXAMPLES:")
    for response, invalid_type in invalid_responses[:5]:  # Show first 5 invalid
        print(f"  Persona {response['persona_id']}: '{response['answer'][:100]}{'...' if len(response['answer']) > 100 else ''}' ({invalid_type})")
    
    print(f"\n✅ VALID RESPONSE EXAMPLES:")
    for response, valid_type in valid_responses[:5]:  # Show first 5 valid
        print(f"  Persona {response['persona_id']}: '{response['answer']}' ({valid_type})")
    
    # Overall quality assessment
    total_valid = len(valid_responses)
    quality_score = total_valid / len(responses) if responses else 0
    
    print(f"\n🎯 QUALITY ASSESSMENT:")
    print(f"  Response Quality Score: {quality_score*100:.1f}%")
    if quality_score >= 0.8:
        print(f"  🟢 EXCELLENT: High-quality responses")
    elif quality_score >= 0.6:
        print(f"  🟡 GOOD: Moderate quality responses")
    elif quality_score >= 0.4:
        print(f"  🟠 FAIR: Low quality responses")
    else:
        print(f"  🔴 POOR: Very low quality responses")
    
    return {
        'total': len(responses),
        'valid': total_valid,
        'quality_score': quality_score,
        'valid_types': valid_types
    }

if __name__ == "__main__":
    analyze_response_quality()
