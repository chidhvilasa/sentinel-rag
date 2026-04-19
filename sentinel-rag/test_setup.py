# test_setup.py
print("Testing imports...")

try:
    from src.sentinel import SentinelDetector, SentinelNeutralizer
    print("✓ Sentinel modules imported")
except Exception as e:
    print(f"✗ Sentinel import failed: {e}")

try:
    from src.rag import RAGPipeline, OllamaLLM
    print("✓ RAG modules imported")
except Exception as e:
    print(f"✗ RAG import failed: {e}")

try:
    import chromadb
    print("✓ ChromaDB available")
except Exception as e:
    print(f"✗ ChromaDB failed: {e}")

try:
    import torch
    print(f"✓ PyTorch available (CUDA: {torch.cuda.is_available()})")
except Exception as e:
    print(f"✗ PyTorch failed: {e}")

print("\nSetup test complete!")