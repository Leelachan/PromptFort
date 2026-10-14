"""Model-agnostic interface for sending prompts to any LLM."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import time

import openai
import anthropic

from .config import ModelConfig


class TargetInterface(ABC):
    @abstractmethod
    async def generate(
        self, 
        system_prompt: str, 
        user_input: str,
        conversation_history: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class OpenAITarget(TargetInterface):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    @property
    def name(self) -> str:
        return f"openai-{self.config.model}"
    
    async def generate(
        self, 
        system_prompt: str, 
        user_input: str,
        conversation_history: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        
        return {
            "text": response.choices[0].message.content,
            "raw": response,
            "metadata": {
                "model": response.model,
                "usage": response.usage.dict() if response.usage else {},
                "finish_reason": response.choices[0].finish_reason,
            }
        }


class AnthropicTarget(TargetInterface):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
    
    @property
    def name(self) -> str:
        return f"anthropic-{self.config.model}"
    
    async def generate(
        self, 
        system_prompt: str, 
        user_input: str,
        conversation_history: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        response = await self.client.messages.create(
            model=self.config.model,
            system=system_prompt,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
        )
        
        return {
            "text": response.content[0].text if response.content else "",
            "raw": response,
            "metadata": {
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "stop_reason": response.stop_reason,
            }
        }


class RateLimitedTarget(TargetInterface):
    def __init__(self, target: TargetInterface, max_rpm: int = 60, max_retries: int = 3):
        self.target = target
        self.max_rpm = max_rpm
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_rpm)
        self._last_request_time = 0
        self._min_interval = 60.0 / max_rpm
    
    @property
    def name(self) -> str:
        return self.target.name
    
    async def generate(self, *args, **kwargs) -> Dict[str, Any]:
        async with self._semaphore:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            
            for attempt in range(self.max_retries):
                try:
                    result = await self.target.generate(*args, **kwargs)
                    self._last_request_time = time.time()
                    return result
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
            
            raise RuntimeError("Max retries exceeded")


def create_target(config: ModelConfig, rate_limit: bool = True) -> TargetInterface:
    if config.provider == "openai":
        target = OpenAITarget(config)
    elif config.provider == "anthropic":
        target = AnthropicTarget(config)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
    
    if rate_limit:
        target = RateLimitedTarget(target)
    
    return target