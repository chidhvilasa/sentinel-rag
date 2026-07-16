"""
RAG Module - Retrieval-Augmented Generation Pipeline

This module provides the core RAG functionality:
- Document loading and chunking
- Vector storage with ChromaDB
- Retrieval pipeline
- LLM interface via Ollama
"""

from .pipeline import (
    DocumentLoader,
    VectorStore,
    RAGPipeline,
    RetrievalResult
)

from .llm import (
    OllamaLLM,
    GenerationResult
)

__all__ = [
    "DocumentLoader",
    "VectorStore", 
    "RAGPipeline",
    "RetrievalResult",
    "OllamaLLM",
    "GenerationResult"
]
