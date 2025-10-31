"""Workflow configuration and management."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class WorkflowStep(Enum):
    """Workflow steps for market research."""
    GENERATE_PERSONAS = "generate_personas"
    DEPLOY_MODEL = "deploy_model"
    QUERY_PERSONAS = "query_personas"
    ANALYZE_RESPONSES = "analyze_responses"
    SAVE_RESULTS = "save_results"


@dataclass
class WorkflowConfig:
    """Configuration for market research workflow."""
    # Persona generation
    persona_count: int = 100
    personas_file: str = "personas.json"
    
    # Model deployment
    model_id: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    gpu_type: str = "RTX 4090"
    vram_gb: int = 24
    deployment_dir: str = "deployment"
    
    # LLM querying
    endpoint_url: Optional[str] = None  # Loaded from endpoint_info.json if not provided
    model_name: Optional[str] = None   # Loaded from endpoint_info.json if not provided
    max_concurrent: int = 50
    max_tokens: int = 150
    temperature: float = 0.8
    
    # Research questions
    questions: List[str] = None
    
    # Output files
    results_prefix: str = "responses"
    analysis_prefix: str = "analysis"
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.questions is None:
            self.questions = [
                "What is your preferred political party in the next Swiss election?",
                "What is your opinion on Switzerland's environmental policies?",
                "How do you feel about Switzerland's relationship with the European Union?",
                "What do you think about Swiss banking secrecy policies?",
                "What should be Switzerland's priority for economic development?"
            ]
