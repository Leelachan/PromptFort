
"""Configuration and model-agnostic setup."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024

    def __post_init__(self):
        if self.api_key is None:
            env_var = f"{self.provider.upper()}_API_KEY"
            self.api_key = os.getenv(env_var)


PRESETS = {
    # Local Ollama model — no hosted API key required
    "ollama": ModelConfig(
        provider="openai",
        model="llama3.2:1b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0.2,
        max_tokens=1024,
    ),

    # Hosted model presets retained for future use
    "gpt-4": ModelConfig("openai", "gpt-4"),
    "gpt-3.5": ModelConfig("openai", "gpt-3.5-turbo"),
    "claude-3-opus": ModelConfig(
        "anthropic", "claude-3-opus-20240229"
    ),
    "claude-3-sonnet": ModelConfig(
        "anthropic", "claude-3-sonnet-20240229"
    ),
}
