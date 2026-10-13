import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock settings, pinecone, and model loading early so importing app does not hit external APIs/HF
with patch('src.config.Settings.require_pinecone'), \
     patch('src.rag_pipeline.RAGPipeline') as mock_rag_class, \
     patch('src.vector_store.get_client') as mock_vc_client:
    mock_pipeline = MagicMock()
    mock_pipeline.llm_model_name = "google/flan-t5-base"
    mock_rag_class.return_value = mock_pipeline
    mock_vc_client.return_value.list_indexes.return_value = []
    from app import app
    from src.rag_pipeline import RAGPipeline

@pytest.fixture
def mock_pinecone_client():
    with patch('src.vector_store.Pinecone') as mock:
        yield mock

@pytest.fixture
def mock_llm():
    with patch('src.llm.generate_answer') as mock:
        mock.return_value = "This is a mocked answer."
        yield mock

@pytest.fixture
def sample_chunks():
    return [
        {"id": "1", "score": 0.9, "text": "Diabetes is a chronic condition.", "source": "page_1", "page": 1},
        {"id": "2", "score": 0.8, "text": "Insulin regulates blood sugar.", "source": "page_2", "page": 2}
    ]

@pytest.fixture
def app_client():
    app.config['TESTING'] = True
    
    with patch('app.rag_pipeline.answer') as mock_answer:
        mock_answer.return_value = {
            "answer": "Diabetes is a chronic condition.",
            "sources": [{"excerpt": "Diabetes is a chronic condition.", "source": "page_1", "score": 0.9, "page": 1}],
            "grounded": True,
            "emergency": False
        }
        with app.test_client() as client:
            yield client
