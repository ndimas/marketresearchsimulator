#!/usr/bin/env python3
"""Monitor and analyze the 100 persona test progress."""

import json
import os
import time
from collections import Counter

def monitor_progress():
    """Monitor the progress of the 100 persona test."""
    
    print("🔍 MONITORING 100 PERSONA TEST PROGRESS")
    print("=" * 50)
    
    # Check if personas file exists and has 100 personas
    if os.path.exists('personas.json'):
        with open('personas.json', 'r') as f:
            personas = json.load(f)
            print(f"✅ Generated {len(personas)} personas")
            
            # Demographic summary
            languages = Counter([p['language'] for p in personas])
            cantons = Counter([p['canton'] for p in personas])
            political_leanings = Counter([p['political_leaning'] for p in personas])
            
            print(f"Languages: {dict(languages)}")
            print(f"Top 5 Cantons: {dict(cantons.most_common(5))}")
            print(f"Political Leanings: {dict(political_leanings)}")
    
    # Monitor responses file
    response_file = 'responses_q1.json'
    if os.path.exists(response_file):
        # Get file modification time
        mod_time = os.path.getmtime(response_file)
        current_time = time.time()
        time_diff = current_time - mod_time
        
        print(f"\n📊 RESPONSE FILE STATUS:")
        print(f"Last modified: {time_diff:.0f} seconds ago")
        
        with open(response_file, 'r') as f:
            responses = json.load(f)
            print(f"Total responses: {len(responses)}")
            
            successful = [r for r in responses if r['success']]
            failed = [r for r in responses if not r['success']]
            
            print(f"Successful: {len(successful)}")
            print(f"Failed: {len(failed)}")
            
            if successful:
                response_times = [r['response_time'] for r in successful if r['response_time'] > 0]
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    print(f"Average response time: {avg_time:.2f}s")
                
                # Check answer formats
                answer_formats = Counter()
                for r in successful:
                    answer = r['answer'].strip()
                    if answer.startswith("{'answer': '") and answer.endswith("'}"):
                        answer_formats['JSON_single_quote'] += 1
                    elif answer.startswith("{'answer': \"") and answer.endswith("\"}"):
                        answer_formats['JSON_double_quote'] += 1
                    elif len(answer) == 1 and answer.isalpha():
                        answer_formats['single_letter'] += 1
                    else:
                        answer_formats['full_text'] += 1
                
                print(f"Answer formats: {dict(answer_formats)}")
                
                # Show sample responses
                print(f"\n📝 SAMPLE RESPONSES:")
                for i, r in enumerate(successful[:3]):
                    print(f"Persona {r['persona_id']}: {r['answer'][:100]}{'...' if len(r['answer']) > 100 else ''}")
            
            # Progress calculation
            progress = len(responses) / 100 * 100
            print(f"\n📈 PROGRESS: {progress:.1f}% ({len(responses)}/100)")
            
            if len(responses) < 100:
                remaining = 100 - len(responses)
                batches_remaining = (remaining + 2) // 3  # Ceiling division
                estimated_time = batches_remaining * 5  # 5 seconds per batch
                print(f"Estimated remaining time: ~{estimated_time} seconds")
            else:
                print("✅ COMPLETED!")

if __name__ == "__main__":
    monitor_progress()
