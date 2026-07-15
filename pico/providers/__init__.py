"""Model provider adapters."""

<<<<<<< HEAD
from .clients import DeepSeekModelClient, FakeModelClient, OllamaModelClient, OpenAICompatibleModelClient

__all__ = [
    "DeepSeekModelClient",
=======
from .clients import AnthropicCompatibleModelClient, FakeModelClient, OllamaModelClient, OpenAICompatibleModelClient

__all__ = [
    "AnthropicCompatibleModelClient",
>>>>>>> origin/main
    "FakeModelClient",
    "OllamaModelClient",
    "OpenAICompatibleModelClient",
]
