"""Medical AI Chatbot — core RAG package.

Modules:
    config:        Environment/config loading and validation.
    data_loader:   PDF ingestion (PyPDFLoader).
    text_splitter: Chunking (RecursiveCharacterTextSplitter).
    embeddings:    Hugging Face embedding model factory.
    vector_store:  Pinecone index management (create/upsert/search).
    retriever:     Question -> relevant chunks.
    llm:           FLAN-T5 loading and answer generation.
    rag_pipeline:  End-to-end orchestration used by app.py.
"""
