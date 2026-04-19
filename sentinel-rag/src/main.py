"""
Sentinel-RAG Main System

The complete integrated system that combines:
- RAG pipeline (document retrieval)
- Sentinel layer (threat detection & neutralization)
- LLM generation (Ollama)

This is the main entry point for the entire system.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass 

from .rag import RAGPipeline, OllamaLLM, GenerationResult, RetrievalResult
from .sentinel import SentinelPipeline, ProcessedChunk


@dataclass
class QueryResult:
    """Complete result of a Sentinel-RAG query"""
    query: str
    response: str
    retrieval: RetrievalResult
    sentinel_results: List[ProcessedChunk]
    generation: GenerationResult
    threats_detected: int
    threats_neutralized: int
    sentinel_enabled: bool


class SentinelRAG:
    """
    The Complete Sentinel-RAG System
    
    Architecture:
    
    User Query
        │
        ▼
    ┌─────────────────┐
    │  RAG Retrieval  │  ◄── ChromaDB
    │  (get chunks)   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  SENTINEL LAYER │  ◄── DeBERTa Detection
    │  - Detect       │  ◄── Neutralization
    │  - Neutralize   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  LLM Generation │  ◄── Ollama (Llama-3)
    │  (safe context) │
    └────────┬────────┘
             │
             ▼
        Response
    """
    
    def __init__(
        self,
        # RAG settings
        persist_directory: str = "./data/embeddings",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 5,
        # Sentinel settings
        sentinel_model: str = "microsoft/deberta-v3-small",
        detection_threshold: float = 0.7,
        sentinel_enabled: bool = True,
        # LLM settings
        llm_model: str = "llama3:8b",
        llm_base_url: str = "http://localhost:11434",
        llm_temperature: float = 0.1,
        llm_max_tokens: int = 2048
    ):
        """
        Initialize the Sentinel-RAG system.
        
        Args:
            persist_directory: ChromaDB storage path
            embedding_model: Model for document embeddings
            chunk_size: Document chunk size
            chunk_overlap: Chunk overlap
            top_k: Number of results to retrieve
            sentinel_model: Model for threat detection
            detection_threshold: Confidence threshold
            sentinel_enabled: Whether Sentinel is active
            llm_model: Ollama model name
            llm_base_url: Ollama server URL
            llm_temperature: Generation temperature
            llm_max_tokens: Max tokens to generate
        """
        print("Initializing Sentinel-RAG System...")
        
        # Initialize RAG pipeline
        print("\n[1/3] Setting up RAG pipeline...")
        self.rag = RAGPipeline(
            persist_directory=persist_directory,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k
        )
        
        # Initialize Sentinel
        print("\n[2/3] Setting up Sentinel layer...")
        self.sentinel = SentinelPipeline(
            model_name=sentinel_model,
            detection_threshold=detection_threshold,
            enabled=sentinel_enabled
        )
        
        # Initialize LLM
        print("\n[3/3] Setting up LLM...")
        self.llm = OllamaLLM(
            model=llm_model,
            base_url=llm_base_url,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )
        
        print("\n✓ Sentinel-RAG System Ready!")
    
    def ingest(self, path: str) -> int:
        """
        Ingest documents into the system.
        
        Args:
            path: File or directory path
            
        Returns:
            Number of chunks ingested
        """
        from pathlib import Path
        p = Path(path)
        
        if p.is_file():
            return self.rag.ingest_file(str(p))
        elif p.is_dir():
            return self.rag.ingest_directory(str(p))
        else:
            raise ValueError(f"Path not found: {path}")
    
    def query(self, question: str, k: Optional[int] = None) -> QueryResult:
        """
        Query the system with Sentinel protection.
        
        This is the main interface for users.
        
        Args:
            question: User's question
            k: Number of chunks to retrieve
            
        Returns:
            QueryResult with response and security details
        """
        # Step 1: Retrieve relevant chunks
        retrieval = self.rag.retrieve(question, k=k)
        
        # Step 2: Run through Sentinel
        sentinel_results = self.sentinel.process_with_details(retrieval.chunks)
        safe_chunks = [r.processed_text for r in sentinel_results]
        
        # Count threats
        threats_detected = sum(1 for r in sentinel_results if r.was_threat)
        threats_neutralized = sum(1 for r in sentinel_results if r.was_neutralized)
        
        # Step 3: Build context from safe chunks
        context = "\n\n---\n\n".join(safe_chunks)
        
        # Step 4: Generate response
        generation = self.llm.generate(question, context)
        
        return QueryResult(
            query=question,
            response=generation.response,
            retrieval=retrieval,
            sentinel_results=sentinel_results,
            generation=generation,
            threats_detected=threats_detected,
            threats_neutralized=threats_neutralized,
            sentinel_enabled=self.sentinel.enabled
        )
    
    def query_unsafe(self, question: str, k: Optional[int] = None) -> QueryResult:
        """
        Query WITHOUT Sentinel protection.
        
        Used for comparison/evaluation to show the vulnerability.
        
        ⚠️ WARNING: This bypasses security!
        """
        # Temporarily disable Sentinel
        was_enabled = self.sentinel.enabled
        self.sentinel.disable()
        
        try:
            result = self.query(question, k=k)
        finally:
            # Restore state
            if was_enabled:
                self.sentinel.enable()
        
        return result
    
    def compare(self, question: str, k: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare protected vs unprotected responses.
        
        Useful for demonstrating the value of Sentinel.
        
        Returns:
            Dict with both responses and analysis
        """
        # Get unsafe response
        unsafe_result = self.query_unsafe(question, k=k)
        
        # Get safe response
        safe_result = self.query(question, k=k)
        
        return {
            "question": question,
            "unsafe_response": unsafe_result.response,
            "safe_response": safe_result.response,
            "threats_detected": safe_result.threats_detected,
            "threats_neutralized": safe_result.threats_neutralized,
            "chunks_retrieved": len(safe_result.retrieval.chunks),
            "analysis": self._analyze_difference(unsafe_result, safe_result)
        }
    
    def _analyze_difference(
        self,
        unsafe: QueryResult,
        safe: QueryResult
    ) -> str:
        """Analyze the difference between safe and unsafe responses"""
        if unsafe.response == safe.response:
            return "Responses are identical - no attack detected or neutralized."
        
        if safe.threats_neutralized > 0:
            return (
                f"Sentinel neutralized {safe.threats_neutralized} potential threat(s). "
                "Compare the responses to see how the attack was prevented."
            )
        
        return "Responses differ but no explicit threats were detected."
    
    def get_sentinel_summary(self) -> str:
        """Get Sentinel statistics"""
        return self.sentinel.summary()
    
    def enable_sentinel(self):
        """Enable Sentinel protection"""
        self.sentinel.enable()
    
    def disable_sentinel(self):
        """Disable Sentinel protection"""
        self.sentinel.disable()
    
    def health_check(self) -> Dict[str, bool]:
        """Check system health"""
        return {
            "rag_ready": True,  # ChromaDB is local
            "sentinel_ready": True,  # Model loaded
            "llm_ready": self.llm.health_check()
        }


# Convenience function
def create_system(**kwargs) -> SentinelRAG:
    """Factory function to create a Sentinel-RAG system"""
    return SentinelRAG(**kwargs)
