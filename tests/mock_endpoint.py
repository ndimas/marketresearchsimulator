"""Mock LLM endpoint for testing separated modules."""

import json
import asyncio
import aiohttp
from aiohttp import web
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from personas import Persona


class MockLLMEndpoint:
    """Mock LLM endpoint for testing the deployment without actual GPU."""
    
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        self.site = None
        
    def setup_routes(self):
        """Setup mock API routes."""
        
        async def health_check(request):
            return web.json_response({"status": "healthy"})
        
        async def chat_completions(request):
            data = await request.json()
            
            # Mock response based on persona in the prompt
            user_message = data.get('messages', [{}])[-1].get('content', '')
            
            # Extract persona info from the prompt
            persona_response = self.generate_mock_response(user_message)
            
            return web.json_response({
                "choices": [{
                    "message": {
                        "content": f'{{"answer": "{persona_response}"}}'
                    }
                }]
            })
        
        self.app.router.add_get('/health', health_check)
        self.app.router.add_post('/v1/chat/completions', chat_completions)
    
    def generate_mock_response(self, user_message: str) -> str:
        """Generate mock responses based on persona characteristics."""
        
        # Mock Swiss political party responses
        if "political party" in user_message.lower():
            responses = [
                "SVP", "SP", "FDP", "The Center", "Greens", "GLP"
            ]
            import random
            return random.choice(responses)
        
        # Mock environmental policy responses
        if "environmental" in user_message.lower():
            responses = [
                "Strongly support green policies",
                "Need balanced approach",
                "Economic growth first",
                "Climate action urgent"
            ]
            import random
            return random.choice(responses)
        
        # Mock EU relationship responses
        if "european union" in user_message.lower():
            responses = [
                "Maintain independence",
                "Closer ties needed",
                "Bilateral agreements best",
                "Join the EU"
            ]
            import random
