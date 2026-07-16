"""
Sentinel-RAG: Mitigating Indirect Prompt Injection via Semantic Neutralization

A defense system that protects RAG pipelines from indirect prompt injection
attacks by detecting and neutralizing malicious commands in retrieved content.
"""

from .main import QueryResult, SentinelRAG, create_system

__version__ = "1.0.0"
__all__ = ["SentinelRAG", "QueryResult", "create_system"]
