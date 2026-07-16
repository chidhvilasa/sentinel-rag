"""
RAG Module - Retrieval-Augmented Generation Pipeline

This module provides the core RAG functionality:
- Document loading and chunking
- Vector storage with ChromaDB
- Retrieval pipeline
- LLM interface via Ollama
"""

from .llm import GenerationResult, OllamaLLM
from .pipeline import DocumentLoader, RAGPipeline, RetrievalResult, VectorStore

__all__ = [
    "DocumentLoader",
    "VectorStore",
    "RAGPipeline",
    "RetrievalResult",
    "OllamaLLM",
    "GenerationResult",
]
