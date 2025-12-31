"""AI provider abstraction supporting OpenAI and Anthropic.

Provides a unified interface for different AI providers with
automatic provider selection and fallback.
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response from the AI model.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Chat with the AI model using conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Generated response text
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
            logger.info(f"OpenAI provider initialized with model {model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response using OpenAI."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, max_tokens, temperature)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Chat with OpenAI model."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name to use
        """
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = model
            logger.info(f"Anthropic provider initialized with model {model}")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response using Anthropic."""
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Chat with Anthropic model."""
        try:
            # Extract system message if present
            system_prompt = None
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    user_messages.append(msg)

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class AIProviderFactory:
    """Factory for creating AI provider instances."""

    @staticmethod
    def create(
        provider_name: str,
        api_key: str,
        model: Optional[str] = None
    ) -> AIProvider:
        """Create an AI provider instance.

        Args:
            provider_name: Name of provider (openai, anthropic)
            api_key: API key for the provider
            model: Optional model name override

        Returns:
            AI provider instance

        Raises:
            ValueError: If provider name is unknown
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4o-mini"
            )
        elif provider_name == "anthropic":
            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022"
            )
        else:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Supported: openai, anthropic"
            )


def get_ai_provider(config: Any) -> AIProvider:
    """Get AI provider from configuration.

    Args:
        config: Config object with provider settings

    Returns:
        Initialized AI provider

    Raises:
        ValueError: If no valid API key is found
    """
    provider_name = config.ai_provider

    if provider_name == "openai":
        api_key = config.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
    elif provider_name == "anthropic":
        api_key = config.anthropic_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    return AIProviderFactory.create(provider_name, api_key)
