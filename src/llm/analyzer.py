"""Response analyzer for market research data."""

import json
from typing import List, Dict, Any
from .models import QueryResult, ResponseAnalysis
from personas.models import Persona


class ResponseAnalyzer:
    """Analyzes query responses and generates insights."""
    
    def __init__(self):
        """Initialize the response analyzer."""
        pass
    
    def analyze_responses(self, results: List[QueryResult]) -> ResponseAnalysis:
        """Analyze responses and generate insights."""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            print("No successful responses to analyze")
            return ResponseAnalysis(
                total_respondents=0,
                question="",
                by_language={},
                by_canton={},
                by_age_group={},
                by_political_leaning={},
                by_education={},
                response_statistics={
                    "avg_response_length": 0,
                    "unique_answers": 0
                }
            )
        
        # Group responses by different demographic factors
        analysis = {
            "total_respondents": len(successful_results),
            "question": successful_results[0].question if successful_results else "",
            "by_language": {},
            "by_canton": {},
            "by_age_group": {},
            "by_political_leaning": {},
            "by_education": {},
            "common_themes": {},
            "response_statistics": {
                "avg_response_length": 0,
                "unique_answers": set()
            }
        }
        
        total_length = 0
        
        for result in successful_results:
            persona = result.persona
            answer = result.answer.lower()
            
            # Response length statistics
            total_length += len(answer)
            analysis["response_statistics"]["unique_answers"].add(result.answer)
            
            # Group by language
            language = persona.language
            if language not in analysis["by_language"]:
                analysis["by_language"][language] = {"count": 0, "answers": []}
            analysis["by_language"][language]["count"] += 1
            analysis["by_language"][language]["answers"].append(result.answer)
            
            # Group by canton (top 10)
            canton = persona.canton
            if canton not in analysis["by_canton"]:
                analysis["by_canton"][canton] = {"count": 0, "answers": []}
            analysis["by_canton"][canton]["count"] += 1
            analysis["by_canton"][canton]["answers"].append(result.answer)
            
            # Group by age group
            age_group = self._get_age_group(persona.age)
            if age_group not in analysis["by_age_group"]:
                analysis["by_age_group"][age_group] = {"count": 0, "answers": []}
            analysis["by_age_group"][age_group]["count"] += 1
            analysis["by_age_group"][age_group]["answers"].append(result.answer)
            
            # Group by political leaning
            leaning = persona.political_leaning
            if leaning not in analysis["by_political_leaning"]:
                analysis["by_political_leaning"][leaning] = {"count": 0, "answers": []}
            analysis["by_political_leaning"][leaning]["count"] += 1
            analysis["by_political_leaning"][leaning]["answers"].append(result.answer)
            
            # Group by education
            education = persona.education
            if education not in analysis["by_education"]:
                analysis["by_education"][education] = {"count": 0, "answers": []}
            analysis["by_education"][education]["count"] += 1
            analysis["by_education"][education]["answers"].append(result.answer)
        
        # Calculate average response length
        analysis["response_statistics"]["avg_response_length"] = total_length / len(successful_results)
        analysis["response_statistics"]["unique_answers"] = len(analysis["response_statistics"]["unique_answers"])
        
        return ResponseAnalysis(
            total_respondents=analysis["total_respondents"],
            question=analysis["question"],
            by_language=analysis["by_language"],
            by_canton=analysis["by_canton"],
            by_age_group=analysis["by_age_group"],
            by_political_leaning=analysis["by_political_leaning"],
            by_education=analysis["by_education"],
            response_statistics=analysis["response_statistics"]
        )
    
    def save_results(self, results: List[QueryResult], filename: str = "responses.json"):
        """Save query results to JSON file."""
        results_dict = []
        for result in results:
            result_dict = {
                "persona_id": result.persona_id,
                "persona": result.persona.model_dump(),
                "question": result.question,
                "answer": result.answer,
                "response_time": result.response_time,
                "success": result.success,
                "error_message": result.error_message
            }
            results_dict.append(result_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=4, ensure_ascii=False)
        
        print(f"Results saved to {filename}")
    
    def save_analysis(self, analysis: ResponseAnalysis, output_file: str = "analysis.json"):
        """Save analysis to JSON file."""
        analysis_dict = {
            "total_respondents": analysis.total_respondents,
            "question": analysis.question,
            "by_language": analysis.by_language,
            "by_canton": analysis.by_canton,
            "by_age_group": analysis.by_age_group,
            "by_political_leaning": analysis.by_political_leaning,
            "by_education": analysis.by_education,
            "response_statistics": analysis.response_statistics
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, indent=4, ensure_ascii=False)
        
        print(f"Analysis saved to {output_file}")
    
    def print_key_insights(self, analysis: ResponseAnalysis):
        """Print key insights from the analysis."""
        print(f"\n=== Key Insights ===")
        print(f"Total respondents: {analysis.total_respondents}")
        print(f"Average response length: {analysis.response_statistics['avg_response_length']:.1f} characters")
        print(f"Unique answers: {analysis.response_statistics['unique_answers']}")
        
        print(f"\nTop languages by response count:")
        for lang, data in sorted(analysis.by_language.items(), key=lambda x: x[1]["count"], reverse=True):
            print(f"  {lang}: {data['count']} respondents")
        
        print(f"\nTop 5 cantons by response count:")
        for canton, data in sorted(analysis.by_canton.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
            print(f"  {canton}: {data['count']} respondents")
        
        print(f"\nPolitical leaning distribution:")
        for leaning, data in sorted(analysis.by_political_leaning.items(), key=lambda x: x[1]["count"], reverse=True):
            print(f"  {leaning}: {data['count']} respondents")
    
    def _get_age_group(self, age: int) -> str:
        """Categorize age into groups."""
        if age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        elif age < 65:
            return "55-64"
        else:
            return "65+"
