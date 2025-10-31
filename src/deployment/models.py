"""Deployment data models."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DeploymentConfig:
    """Configuration for model deployment."""
    model_id: str
    gpu_type: str = "RTX 4090"
    vram_gb: int = 24
    name: str = ""
    min_workers: int = 0
    max_workers: int = 5
    gpu_count: int = 1
    container_disk_gb: int = 50
    volume_gb: int = 20
    volume_mount_path: str = "/workspace"
    ports: str = "8000/http"
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.name:
            self.name = f"swiss-llm-{self.model_id.split('/')[-1]}"


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    config: Dict[str, Any]
    dockerfile: str
    deploy_script: str
    test_script: str
    optimizations: str
