"""New main entry point using separated modules."""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig, WorkflowStep


async def main():
    """Main function to run the Swiss market research with separated modules."""
    
    # Configuration
    config = WorkflowConfig(
        persona_count=10,  # Reduced for testing
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=3,  # Conservative limit based on benchmark results
        questions=[
            "What is your preferred political party in next Swiss election? A) SVP (Swiss People's Party) B) SP (Social Democratic Party) C) FDP (Free Democratic Party) D) Green Party",
            "What is your opinion on Switzerland's environmental policies? A) Need stricter regulations B) Current policies are adequate C) Need more business-friendly approach D) Focus on renewable energy",
            "How do you feel about Switzerland's relationship with the European Union? A) Join EU immediately B) Strengthen bilateral agreements C) Maintain current independence D) Reduce EU influence",
            "What do you think about Swiss banking secrecy policies? A) Maintain complete secrecy B) Limited transparency C) Full transparency D) Abolish banking secrecy",
            "What should be Switzerland's priority for economic development? A) Technology and innovation B) Traditional industries C) Service sector growth D) Sustainable development"
        ]
    )
    
    # Create orchestrator
    orchestrator = SwissMarketResearchOrchestrator(config)
    
    # Run full workflow
    await orchestrator.run_full_workflow()


if __name__ == "__main__":
    asyncio.run(main())
