from unittest.mock import patch, MagicMock
import pytest
from src.retriever import retrieve_relevant_chunks, format_context

def test_retrieve_relevant_chunks(sample_chunks):
    with patch('src.retriever.get_embedding_model') as mock_embedder_factory, \
         patch('src.retriever.search_documents') as mock_search:
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384
        mock_embedder_factory.return_value = mock_embedder
        mock_search.return_value = sample_chunks
        
        results = retrieve_relevant_chunks("What is diabetes?", top_k=2)
        
        assert len(results) == 2
        assert results[0]['score'] == 0.9
        assert results[0]['page'] == 1

def test_retrieve_empty_results():
    with patch('src.retriever.get_embedding_model') as mock_embedder_factory, \
         patch('src.retriever.search_documents') as mock_search:
        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1] * 384
        mock_embedder_factory.return_value = mock_embedder
        mock_search.return_value = []
        
        results = retrieve_relevant_chunks("What is a rare disease?", top_k=2)
        assert len(results) == 0

def test_retrieve_empty_question():
    results = retrieve_relevant_chunks("")
    assert results == []

def test_format_context(sample_chunks):
    ctx = format_context(sample_chunks)
    assert "[Page 1] Diabetes is a chronic condition." in ctx
    assert "[Page 2] Insulin regulates blood sugar." in ctx
