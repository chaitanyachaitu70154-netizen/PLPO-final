"""
Base AI Provider Interface for Phase 3.
Enables pluggable, modular LLM backends (Gemini, OpenAI, Anthropic, or local offline simulator).
Never exposes API keys in UI or source code.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseAIProvider(ABC):
    """Abstract base class defining standardized AI interface."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API credentials and dependencies are available."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name (e.g. 'Google Gemini API')."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return active model identifier (e.g. 'gemini-1.5-flash')."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """Generate unstructured textual response with optional system instruction."""
        pass

    @abstractmethod
    def generate_structured_json(
        self,
        prompt: str,
        schema_class: Type[T],
        system_instruction: Optional[str] = None
    ) -> T:
        """
        Generate structured output validated against a Pydantic schema.
        Guarantees schema compliance and handles malformed output recovery.
        """
        pass
