#!/usr/bin/env python3
"""Market Research Simulator - Clean, configurable version with proven extraction logic."""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import AppConfig
from src.client import MarketResearchClient, ClientResult
from src.personas.generator import SwissPersonaGenerator
from src.concurrency import get_concurrency_manager


class MarketResearchSimulator:
    """Main simulator class for Swiss market research."""
    
    def __init__(self, config: AppConfig):
        """Initialize the simulator with configuration."""
        self.config = config
        self.client = MarketResearchClient(config)
        self.persona_generator = SwissPersonaGenerator()
        
    def load_personas(self) -> List[Any]:
        """Load personas from file or generate if needed."""
        personas = self.persona_generator.load_personas(self.config.test.personas_file)
        
        if not personas or len(personas) < self.config.test.persona_count:
            print(f"📝 Generating {self.config.test.persona_count} personas...")
            personas = self.persona_generator.generate_personas(self.config.test.persona_count)
            self.persona_generator.save_personas(personas, self.config.test.personas_file)
            print(f"💾 Saved {len(personas)} personas to {self.config.test.personas_file}")
        else:
            print(f"📄 Loaded {len(personas)} personas from {self.config.test.personas_file}")
        
        return personas[:self.config.test.persona_count]
    
    async def run_single_question(self, personas: List[Any], question: str, question_idx: int) -> Dict[str, Any]:
        """Run a single question against all personas."""
        print(f"\n{'='*80}")
        print(f"📝 QUESTION {question_idx}")
        print(f"❓ {question}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # Query all personas
        results = await self.client.query_all_personas(personas, question)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🏁 QUESTION {question_idx} COMPLETED!")
        print(f"⏱️ Duration: {duration:.2f}s")
        
        # Print detailed summary
        self.client.print_summary(results)
        
        # Calculate metrics
        query_results = [r.query_result for r in results]
        successful = [r for r in query_results if r.success]
        failed = [r for r in query_results if not r.success]
        
        success_rate = len(successful) / len(query_results) * 100
        throughput = len(query_results) / duration
        
        # Quality metrics
        valid_letters = {'A', 'B', 'C', 'D'}
        valid_choices = [r for r in successful if r.answer in valid_letters]
        quality_rate = len(valid_choices) / len(query_results) * 100
        
        # Political alignment metrics
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
        
        left_accuracy = left_correct / left_total * 100 if left_total > 0 else 0
        right_accuracy = right_correct / right_total * 100 if right_total > 0 else 0
        
        # Prepare results for saving
        results_data = []
        for result in results:
            results_data.append({
                "persona_id": result.query_result.persona_id,
                "persona": result.query_result.persona.__dict__,
                "question": result.query_result.question,
                "answer": result.query_result.answer,
                "response_time": result.query_result.response_time,
                "success": result.query_result.success,
                "error_message": result.query_result.error_message,
                "extraction_method": result.extraction_method,
                "raw_content": result.raw_content,
                "processing_time": result.processing_time
            })
        
        # Save results
        filename = f'{self.config.test.results_prefix}_q{question_idx}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to {filename}")
        
        # Return metrics
        return {
            'question_idx': question_idx,
            'question': question,
            'duration': duration,
            'success_rate': success_rate,
            'quality_rate': quality_rate,
            'throughput': throughput,
            'left_accuracy': left_accuracy,
            'right_accuracy': right_accuracy,
            'total_queries': len(query_results),
            'successful_queries': len(successful),
            'failed_queries': len(failed)
        }
    
    async def run_full_survey(self) -> Dict[str, Any]:
        """Run the complete survey with all questions."""
        print("🚀 SWISS MARKET RESEARCH SIMULATOR")
        print("=" * 80)
        print("🎯 Objective: Test LLM endpoint with Swiss voter personas")
        print("🔧 Features: Configurable model, endpoint, and concurrency")
        print("📊 Purpose: Measure political alignment and response quality")
        print("=" * 80)
        
        # Print configuration
        self.config.print_config()
        
        # Print unified concurrency summary
        concurrency_manager = self.config.get_concurrency_manager()
        concurrency_manager.print_summary()
        
        # Load personas
        personas = self.load_personas()
        
        print(f"\n📋 SURVEY CONFIGURATION:")
        print(f"   👥 Personas: {len(personas)}")
        print(f"   📝 Questions: {len(self.config.test.questions)}")
        print(f"   🔗 Endpoint: {self.config.model.endpoint_url}")
        print(f"   ⚡ Max Concurrent: {self.config.concurrency.max_concurrent}")
        
        all_results = {}
        survey_start_time = time.time()
        
        # Process each question
        for q_idx, question in enumerate(self.config.test.questions, 1):
            question_result = await self.run_single_question(personas, question, q_idx)
            all_results[f'q{q_idx}'] = question_result
            
            # Brief pause between questions
            if q_idx < len(self.config.test.questions):
                print(f"⏸️ Brief pause before next question...")
                await asyncio.sleep(2)
        
        total_survey_time = time.time() - survey_start_time
        
        # Calculate overall statistics
        print(f"\n{'🏆'*20}")
        print(f"🏆 SURVEY COMPLETED!")
        print(f"{'🏆'*20}")
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"⏱️ Total Duration: {total_survey_time:.2f}s")
        print(f"👥 Total Personas Processed: {len(personas) * len(self.config.test.questions)}")
        print(f"📝 Questions Processed: {len(self.config.test.questions)}")
        
        # Calculate averages
        avg_success = sum(r['success_rate'] for r in all_results.values()) / len(all_results)
        avg_quality = sum(r['quality_rate'] for r in all_results.values()) / len(all_results)
        avg_throughput = sum(r['throughput'] for r in all_results.values()) / len(all_results)
        avg_left_accuracy = sum(r['left_accuracy'] for r in all_results.values()) / len(all_results)
        avg_right_accuracy = sum(r['right_accuracy'] for r in all_results.values()) / len(all_results)
        
        print(f"\n📈 AVERAGE PERFORMANCE:")
        print(f"✅ Success Rate: {avg_success:.1f}%")
        print(f"🎯 Quality Rate: {avg_quality:.1f}%")
        print(f"🔥 Throughput: {avg_throughput:.1f} personas/second")
        print(f"🏛️ Political Alignment - Left: {avg_left_accuracy:.1f}%")
        print(f"🏛️ Political Alignment - Right: {avg_right_accuracy:.1f}%")
        
        # Performance assessment
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if avg_quality >= 95 and avg_left_accuracy >= 80 and avg_right_accuracy >= 80:
            print(f"🟢 EXCELLENT: Perfect performance with correct political alignment!")
        elif avg_quality >= 90 and avg_left_accuracy >= 70 and avg_right_accuracy >= 70:
            print(f"🟡 VERY GOOD: Strong performance with good political alignment")
        elif avg_quality >= 80 and avg_left_accuracy >= 60 and avg_right_accuracy >= 60:
            print(f"🟠 GOOD: Solid performance with moderate political alignment")
        else:
            print(f"🔴 NEEDS IMPROVEMENT: Political alignment or quality issues detected")
        
        print(f"\n📁 FILES CREATED:")
        for q_idx in range(1, len(self.config.test.questions) + 1):
            print(f"   - {self.config.test.results_prefix}_q{q_idx}.json")
        
        # Save summary
        summary_data = {
            'survey_config': {
                'persona_count': len(personas),
                'questions_count': len(self.config.test.questions),
                'model_id': self.config.model.model_id,
                'endpoint_url': self.config.model.endpoint_url,
                'max_concurrent': self.config.concurrency.max_concurrent
            },
            'overall_metrics': {
                'total_duration': total_survey_time,
                'avg_success_rate': avg_success,
                'avg_quality_rate': avg_quality,
                'avg_throughput': avg_throughput,
                'avg_left_accuracy': avg_left_accuracy,
                'avg_right_accuracy': avg_right_accuracy
            },
            'question_results': all_results
        }
        
        summary_filename = f'{self.config.test.results_prefix}_summary.json'
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Summary saved to {summary_filename}")
        
        return summary_data


async def main():
    """Main entry point."""
    # Load configuration from environment or use demo config
    try:
        config = AppConfig.from_env()
    except Exception as e:
        print(f"⚠️ Could not load config from environment: {e}")
        print("🔄 Using demo configuration...")
        config = AppConfig.create_demo()
    
    # Create and run simulator
    simulator = MarketResearchSimulator(config)
    results = await simulator.run_full_survey()
    
    print(f"\n🎉 Simulation completed successfully!")
    return results


if __name__ == "__main__":
    asyncio.run(main())
