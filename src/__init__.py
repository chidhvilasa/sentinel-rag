"""
Sentinel-RAG: Mitigating Indirect Prompt Injection via Semantic Neutralization

A defense system that protects RAG pipelines from indirect prompt injection
attacks by detecting and neutralizing malicious commands in retrieved content.
"""

from .main import SentinelRAG, QueryResult, create_system

__version__ = "0.1.0"
__all__ = ["SentinelRAG", "QueryResult", "create_system"]
