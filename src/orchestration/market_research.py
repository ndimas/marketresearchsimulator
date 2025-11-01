"""Swiss market research orchestrator."""

import asyncio
import json
import os
from typing import List, Optional
from dotenv import load_dotenv

from .workflow import WorkflowConfig, WorkflowStep
from ..personas import SwissPersonaGenerator, Persona
from ..llm import LLMClient, MarketResearchQuery, ResponseAnalyzer
from ..deployment import RunPodDeployer, DeploymentConfig


class SwissMarketResearchOrchestrator:
    """Orchestrates the complete Swiss market research workflow."""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the orchestrator with configuration."""
        load_dotenv()  # Load environment variables
        
        self.config = config or WorkflowConfig()
        self.persona_generator = SwissPersonaGenerator()
        self.deployer = RunPodDeployer()
        self.analyzer = ResponseAnalyzer()
        
        # Initialize LLM client lazily when needed
        self._llm_client: Optional[LLMClient] = None
        
    def get_llm_client(self) -> LLMClient:
        """Get or create LLM client."""
        if self._llm_client is None:
            endpoint_url, model_id = self._get_endpoint_info()
            
            llm_config = MarketResearchQuery(
                endpoint_url=endpoint_url,
                model_id=model_id,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                max_concurrent=self.config.max_concurrent
            )
            
            self._llm_client = LLMClient(llm_config)
        
        return self._llm_client
    
    def _get_endpoint_info(self) -> tuple[str, str]:
        """Get endpoint URL and model ID from configuration or endpoint_info.json."""
        if self.config.endpoint_url and self.config.model_name:
            return self.config.endpoint_url, self.config.model_name
        
        # Try to load from endpoint_info.json
        if os.path.exists("endpoint_info.json"):
            with open("endpoint_info.json", "r") as f:
                endpoint_info = json.load(f)
                return endpoint_info["endpoint_url"], endpoint_info["model_id"]
        
        # Fallback to environment variables or defaults
        endpoint_url = os.getenv("LLM_ENDPOINT_URL", "http://localhost:8000")
        model_id = os.getenv("LLM_MODEL_ID", "meta-llama/Meta-Llama-3.1-8B-Instruct")
        
        return endpoint_url, model_id
    
    def generate_personas(self) -> List[Persona]:
        """Generate personas for market research."""
        print(f"🎭 Generating {self.config.persona_count} Swiss personas...")
        
        personas = self.persona_generator.generate_personas(self.config.persona_count)
        self.persona_generator.save_personas(personas, self.config.personas_file)
        
        return personas
    
    def load_personas(self) -> List[Persona]:
        """Load personas from file."""
        if not os.path.exists(self.config.personas_file):
            raise FileNotFoundError(f"Personas file not found: {self.config.personas_file}")
        
        print(f"📁 Loading personas from {self.config.personas_file}...")
        return self.persona_generator.load_personas(self.config.personas_file)
    
    def create_deployment(self) -> None:
        """Create deployment files for the model."""
        print(f"🚀 Creating deployment files for {self.config.model_id}...")
        
        deployment_config = DeploymentConfig(
            model_id=self.config.model_id,
            gpu_type=self.config.gpu_type,
            vram_gb=self.config.vram_gb
        )
        
        self.deployer.create_deployment_files(deployment_config, self.config.deployment_dir)
        
        print(f"\n📝 Deployment files created in {self.config.deployment_dir}/")
        print("Next steps:")
        print("1. Set your RUNPOD_API_KEY environment variable")
        print(f"2. Run: cd {self.config.deployment_dir} && ./deploy.sh")
        print(f"3. Test: cd {self.config.deployment_dir} && ./test.sh")
    
    async def query_personas(self, personas: List[Persona], questions: List[str]) -> List[List]:
        """Query personas with research questions."""
        client = self.get_llm_client()
        all_results = []
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*50}")
            print(f"❓ Question {i}: {question}")
            print(f"{'='*50}")
            
            # Query all personas
            results = await client.query_all_personas(personas, question)
            all_results.append(results)
            
            # Print summary
            client.print_summary(results)
            
            # Wait between questions to avoid overwhelming the service
            if i < len(questions):
                print("⏳ Waiting 10 seconds before next question...")
                await asyncio.sleep(10)
        
        return all_results
    
    def analyze_and_save_results(self, all_results: List[List], questions: List[str]) -> None:
        """Analyze and save query results."""
        print(f"\n{'='*50}")
        print("📊 Analyzing and saving results...")
        print(f"{'='*50}")
        
        for i, (results, question) in enumerate(zip(all_results, questions), 1):
            # Save raw results
            results_file = f"{self.config.results_prefix}_q{i}.json"
            self.analyzer.save_results(results, results_file)
            
            # Analyze responses
            analysis = self.analyzer.analyze_responses(results)
            
            # Save analysis
            analysis_file = f"{self.config.analysis_prefix}_q{i}.json"
            self.analyzer.save_analysis(analysis, analysis_file)
            
            # Print key insights
            self.analyzer.print_key_insights(analysis)
    
    async def run_full_workflow(self, steps: Optional[List[WorkflowStep]] = None) -> None:
        """Run the complete market research workflow."""
        if steps is None:
            steps = [
                WorkflowStep.GENERATE_PERSONAS,
                WorkflowStep.QUERY_PERSONAS,
                WorkflowStep.ANALYZE_RESPONSES
            ]
        
        personas: List[Persona] = []
        
        # Step 1: Generate or load personas
        if WorkflowStep.GENERATE_PERSONAS in steps:
            personas = self.generate_personas()
        else:
            personas = self.load_personas()
        
        # Step 2: Deploy model (if requested)
        if WorkflowStep.DEPLOY_MODEL in steps:
            self.create_deployment()
            return  # Stop here to let user deploy first
        
        # Step 3: Query personas
        if WorkflowStep.QUERY_PERSONAS in steps:
            all_results = await self.query_personas(personas, self.config.questions)
        else:
            # Load existing results if skipping querying
            all_results = []
            for i in range(len(self.config.questions)):
                results_file = f"{self.config.results_prefix}_q{i+1}.json"
                if os.path.exists(results_file):
                    with open(results_file, 'r', encoding='utf-8') as f:
                        results_data = json.load(f)
                        # Convert back to QueryResult objects
                        from llm.models import QueryResult
                        results = [
                            QueryResult(
                                persona_id=r['persona_id'],
                                persona=Persona(**r['persona']),
                                question=r['question'],
                                answer=r['answer'],
                                response_time=r['response_time'],
                                success=r['success'],
                                error_message=r.get('error_message')
                            )
                            for r in results_data
                        ]
                        all_results.append(results)
        
        # Step 4: Analyze and save results
        if WorkflowStep.ANALYZE_RESPONSES in steps and all_results:
            self.analyze_and_save_results(all_results, self.config.questions)
        
        print(f"\n{'='*50}")
        print("🎉 Market research completed!")
        print("Check the following files for detailed results:")
        for i in range(len(self.config.questions)):
            print(f"- {self.config.results_prefix}_q{i+1}.json: Raw responses for question {i+1}")
            print(f"- {self.config.analysis_prefix}_q{i+1}.json: Detailed analysis of question {i+1}")
        print(f"{'='*50}")
    
    async def run_deployment_only(self) -> None:
        """Run only the deployment step."""
        await self.run_full_workflow([WorkflowStep.DEPLOY_MODEL])
    
    async def run_querying_only(self) -> None:
        """Run only the querying step (assumes personas and endpoint exist)."""
        await self.run_full_workflow([
            WorkflowStep.QUERY_PERSONAS,
            WorkflowStep.ANALYZE_RESPONSES
        ])


# Convenience functions for backward compatibility
async def main():
    """Main function to run the Swiss market research."""
    orchestrator = SwissMarketResearchOrchestrator()
    await orchestrator.run_full_workflow()


async def deploy_only():
    """Deploy model only."""
    orchestrator = SwissMarketResearchOrchestrator()
    await orchestrator.run_deployment_only()


async def query_only():
    """Query personas only."""
    orchestrator = SwissMarketResearchOrchestrator()
    await orchestrator.run_querying_only()


if __name__ == "__main__":
    asyncio.run(main())
