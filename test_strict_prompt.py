#!/usr/bin/env python3
"""Test the ultra-strict prompt with small sample."""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


async def main():
    """Test ultra-strict prompt with 5 personas."""
    config = WorkflowConfig(
        persona_count=5,  # Small test
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=5,  # Test higher concurrency
        questions=[
            "What is your preferred political party in next Swiss election? A) SVP (Swiss People's Party) B) SP (Social Democratic Party) C) FDP (Free Democratic Party) D) Green Party"
        ]
    )
    
    orchestrator = SwissMarketResearchOrchestrator(config)
    await orchestrator.run_full_workflow()


if __name__ == "__main__":
    asyncio.run(main())
