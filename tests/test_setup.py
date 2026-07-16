"""Environment smoke tests: are the core dependencies importable?"""

import pytest


def test_sentinel_modules_importable():
    from src.sentinel import SentinelDetector, SentinelNeutralizer  # noqa: F401


def test_rag_modules_importable():
    from src.rag import OllamaLLM, RAGPipeline  # noqa: F401


def test_chromadb_importable():
    pytest.importorskip("chromadb")


def test_torch_importable():
    torch = pytest.importorskip("torch")
    # CUDA availability is informational only — CPU-only environments are supported.
    assert isinstance(torch.cuda.is_available(), bool)
