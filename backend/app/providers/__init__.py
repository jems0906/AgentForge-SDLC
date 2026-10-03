import os

from app.providers.mock_provider import MockProvider
from app.providers.remote import RemoteProvider


def get_provider(name: str):
    if name == "mock":
        return MockProvider()
    keys = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
    if name not in keys:
        raise ValueError(f"Unknown provider: {name}")
    api_key = os.getenv(keys[name])
    if not api_key:
        raise ValueError(f"Provider '{name}' is not configured; set {keys[name]} on the API service.")
    return RemoteProvider(name, api_key)
