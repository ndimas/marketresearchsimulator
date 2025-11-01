"""Swiss Market Research Toolkit - A modular toolkit for persona-based market research."""

from .personas import Persona, SwissPersonaGenerator
from .llm import LLMClient, MarketResearchQuery, ResponseAnalyzer, QueryResult
from .deployment import RunPodDeployer, DeploymentConfig
from .orchestration import SwissMarketResearchOrchestrator, WorkflowConfig, WorkflowStep
from .concurrency import ConcurrencyManager, get_concurrency_manager, set_max_concurrent

__version__ = "1.0.0"
__all__ = [
    # Core models
    'Persona',
    'QueryResult',
    'DeploymentConfig',
    'MarketResearchQuery',
    'WorkflowConfig',
    'WorkflowStep',
    
    # Main classes
    'SwissPersonaGenerator',
    'LLMClient',
    'ResponseAnalyzer',
    'RunPodDeployer',
    'SwissMarketResearchOrchestrator',
]
