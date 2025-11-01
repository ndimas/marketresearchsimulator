"""Configuration management for market research simulator."""

import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import unified concurrency management
from .concurrency import get_concurrency_manager, set_max_concurrent


@dataclass
class ModelConfig:
    """Model configuration."""
    model_id: str
    endpoint_url: str
    model_name: Optional[str] = None
    max_tokens: int = 100
    temperature: float = 0.3
    top_p: float = 0.9
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.model_name is None:
            # Extract model name from model_id if not provided
            self.model_name = self.model_id.split('/')[-1] if '/' in self.model_id else self.model_id
        
        # Clean endpoint URL
        self.endpoint_url = self.endpoint_url.rstrip('/')


@dataclass
class ConcurrencyConfig:
    """Concurrency configuration with unified management."""
    max_concurrent: int = 100
    request_delay: float = 0.02  # Minimal delay between requests
    max_retries: int = 2
    timeout_total: int = 60
    timeout_connect: int = 10
    
    def __post_init__(self):
        """Initialize concurrency manager after config creation."""
        # Set global MAX_CONCURRENT when config is created
        set_max_concurrent(self.max_concurrent)
        
        # Initialize the global concurrency manager
        self.manager = get_concurrency_manager(self.max_concurrent)


@dataclass
class TestConfig:
    """Test configuration."""
    persona_count: int = 100
    personas_file: str = "personas.json"
    results_prefix: str = "results/market_research_results"
    
    # Default questions for Swiss market research
    questions: List[str] = None
    
    def __post_init__(self):
        """Set default questions if not provided."""
        if self.questions is None:
            self.questions = [
                "What is your preferred political party in next Swiss election? A) SVP B) SP C) FDP D) Green Party",
                "What should be Switzerland's top priority? A) Economic Growth B) Climate Action C) Social Welfare D) National Security",
                "Which EU policy should Switzerland adopt? A) Free Movement B) Trade Agreement C) Climate Standards D) Digital Integration",
                "What tax system do you prefer? A) Progressive B) Flat C) Consumption D) Wealth Tax",
                "How should Switzerland handle immigration? A) Open Borders B) Skilled Only C) Quota System D) Strict Limits"
            ]


@dataclass
class AppConfig:
    """Main application configuration."""
    model: ModelConfig
    concurrency: ConcurrencyConfig
    test: TestConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        # Model configuration
        model_config = ModelConfig(
            model_id=os.getenv('LLM_MODEL_ID', 'TheBloke/Mistral-7B-Instruct-v0.1-AWQ'),
            endpoint_url=os.getenv('LLM_ENDPOINT_URL', 'https://kx02ilhnbvqcrw-8000.proxy.runpod.net'),
            model_name=os.getenv('LLM_MODEL_NAME'),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '100')),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.3')),
            top_p=float(os.getenv('LLM_TOP_P', '0.9'))
        )
        
        # Concurrency configuration
        max_concurrent = int(os.getenv('MAX_CONCURRENT', '100'))
        concurrency_config = ConcurrencyConfig(
            max_concurrent=max_concurrent,
            request_delay=float(os.getenv('REQUEST_DELAY', '0.02')),
            max_retries=int(os.getenv('MAX_RETRIES', '2')),
            timeout_total=int(os.getenv('TIMEOUT_TOTAL', '60')),
            timeout_connect=int(os.getenv('TIMEOUT_CONNECT', '10'))
        )
        
        # Test configuration
        test_config = TestConfig(
            persona_count=int(os.getenv('PERSONA_COUNT', '100')),
            personas_file=os.getenv('PERSONAS_FILE', 'personas.json'),
            results_prefix=os.getenv('RESULTS_PREFIX', 'market_research_results')
        )
        
        return cls(
            model=model_config,
            concurrency=concurrency_config,
            test=test_config
        )
    
    @classmethod
    def create_demo(cls) -> 'AppConfig':
        """Create configuration for demo/testing."""
        return cls(
            model=ModelConfig(
                model_id="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
                endpoint_url="https://kx02ilhnbvqcrw-8000.proxy.runpod.net"
            ),
            concurrency=ConcurrencyConfig(
                max_concurrent=100
            ),
            test=TestConfig(
                persona_count=100
            )
        )
    
    def print_config(self):
        """Print current configuration."""
        print("🔧 CONFIGURATION")
        print("=" * 50)
        print(f"📝 Model: {self.model.model_name}")
        print(f"🔗 Endpoint: {self.model.endpoint_url}")
        print(f"⚡ Max Concurrent: {self.concurrency.max_concurrent}")
        print(f"👥 Persona Count: {self.test.persona_count}")
        print(f"📄 Personas File: {self.test.personas_file}")
        print(f"❓ Questions: {len(self.test.questions)}")
        
        # Print concurrency manager metrics
        if hasattr(self.concurrency, 'manager'):
            self.concurrency.manager.print_summary()
        
        print("=" * 50)
    
    def get_concurrency_manager(self):
        """Get the unified concurrency manager."""
        return self.concurrency.manager
