#!/usr/bin/env python3
"""Test script to verify the fixes work."""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestration import SwissMarketResearchOrchestrator, WorkflowConfig


async def test():
    """Test the fixed system with a small dataset."""
    config = WorkflowConfig(
        persona_count=3,  # Small test
        model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net",
        model_name="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
        max_concurrent=2,
        questions=["What is your opinion on Switzerland?"]  # Just one question
    )
    
    orchestrator = SwissMarketResearchOrchestrator(config)
    await orchestrator.run_full_workflow()


if __name__ == "__main__":
    asyncio.run(test())
