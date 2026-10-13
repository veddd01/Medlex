import pytest
from src.config import load_settings, ConfigError
import os
from unittest.mock import patch

def test_settings_defaults():
    settings = load_settings()
    assert settings.llm_provider in ["local", "openai", "gemini", "ollama"]
    assert settings.chunk_size == 500
    assert settings.chunk_overlap == 50

@patch.dict(os.environ, {'PINECONE_API_KEY': '', 'PINECONE_ENVIRONMENT': ''}, clear=False)
def test_require_pinecone_missing():
    settings = load_settings()
    with pytest.raises(ConfigError):
        settings.require_pinecone()

@patch.dict(os.environ, {'PINECONE_API_KEY': 'fake-key', 'PINECONE_ENVIRONMENT': 'us-east-1'}, clear=False)
def test_require_pinecone_valid():
    settings = load_settings()
    # Should not raise
    settings.require_pinecone()
