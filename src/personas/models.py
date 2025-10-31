"""Persona data models."""

from typing import Optional
from pydantic import BaseModel


class Persona(BaseModel):
    """Represents a Swiss persona for market research."""
    
    id: int
    age: int
    gender: str
    canton: str
    language: str
    occupation: str
    education: str
    political_leaning: str
    description: str
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Add any custom encoders if needed
        }
