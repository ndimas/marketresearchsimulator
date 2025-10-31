"""LLM client data models."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from personas.models import Persona


@dataclass
class QueryResult:
    """Result of a persona query."""
    persona_id: int
    persona: Persona
    question: str
    answer: str
    response_time: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class MarketResearchQuery:
    """Configuration for market research queries."""
    endpoint_url: str
    model_id: str
    system_prompt: str = "RESPOND ONLY WITH: {'answer': 'X'} WHERE X IS A, B, C, OR D. NO EXPLANATIONS. NO OTHER TEXT."
    max_tokens: int = 150
    temperature: float = 0.8
    top_p: float = 0.9
    max_concurrent: int = 50


@dataclass
class ResponseAnalysis:
    """Analysis of query responses."""
    total_respondents: int
    question: str
    by_language: Dict[str, Dict[str, Any]]
    by_canton: Dict[str, Dict[str, Any]]
    by_age_group: Dict[str, Dict[str, Any]]
    by_political_leaning: Dict[str, Dict[str, Any]]
    by_education: Dict[str, Dict[str, Any]]
    response_statistics: Dict[str, Any]
