import pytest
from unittest.mock import patch, MagicMock
from src.rag_pipeline import RAGPipeline, NO_CONTEXT_MESSAGE

@patch('src.rag_pipeline.load_model')
@patch('src.rag_pipeline.retrieve_relevant_chunks')
@patch('src.rag_pipeline.generate_answer')
@patch('src.reranker.rerank_chunks')
def test_pipeline_answer(mock_rerank, mock_generate, mock_retrieve, mock_load, sample_chunks):
    mock_load.return_value = MagicMock()
    mock_retrieve.return_value = sample_chunks
    mock_rerank.side_effect = lambda q, chunks, top_n=5: chunks[:top_n]
    mock_generate.return_value = "Diabetes is a chronic condition."
    
    with patch('src.config.Settings.require_pinecone'):
        pipeline = RAGPipeline()
        result = pipeline.answer("What is diabetes?")
    
    assert result['answer'] == "Diabetes is a chronic condition."
    assert len(result['sources']) == 2
    assert result['sources'][0]['score'] == 0.9

@patch('src.rag_pipeline.load_model')
@patch('src.rag_pipeline.retrieve_relevant_chunks')
def test_pipeline_fallback(mock_retrieve, mock_load):
    mock_load.return_value = MagicMock()
    mock_retrieve.return_value = []
    
    with patch('src.config.Settings.require_pinecone'):
        pipeline = RAGPipeline()
        result = pipeline.answer("What is something unknown?")
    
    assert result['answer'] == NO_CONTEXT_MESSAGE
    assert len(result['sources']) == 0
    assert result['grounded'] is False

@patch('src.rag_pipeline.load_model')
def test_pipeline_empty_question(mock_load):
    mock_load.return_value = MagicMock()
    with patch('src.config.Settings.require_pinecone'):
        pipeline = RAGPipeline()
        with pytest.raises(ValueError):
            pipeline.answer("")
