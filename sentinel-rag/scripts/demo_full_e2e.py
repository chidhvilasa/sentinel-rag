# scripts/demo_full_e2e.py
"""
FULL END-TO-END DEMONSTRATION

Complete flow: PDF → ChromaDB → Retrieval → Sentinel → LLM

This demonstrates the real-world usage of Sentinel-RAG where:
1. Resumes are ingested into a vector database
2. User queries retrieve relevant chunks
3. Sentinel detects and neutralizes any attacks in retrieved chunks
4. LLM generates safe responses based on actual content
"""
import sys
import os
import shutil
sys.path.insert(0, '..')

from src.rag import RAGPipeline, OllamaLLM
from src.sentinel import SentinelPipeline


def clear_embeddings():
    """Clear existing embeddings for fresh demo."""
    embed_dir = "../data/embeddings"
    if os.path.exists(embed_dir):
        shutil.rmtree(embed_dir)
        print("✓ Cleared existing embeddings")


def main():
    print("="*70)
    print("   SENTINEL-RAG: FULL END-TO-END DEMONSTRATION")
    print("   PDF → ChromaDB → Retrieval → Sentinel → LLM")
    print("="*70)
    
    # Clear previous data
    print("\n[SETUP] Preparing environment...")
    clear_embeddings()
    
    # Initialize components
    print("\n[INIT] Loading RAG Pipeline...")
    rag = RAGPipeline(
        persist_directory="../data/embeddings",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=500,
        chunk_overlap=50,
        top_k=3
    )
    
    print("[INIT] Loading Sentinel Pipeline...")
    sentinel = SentinelPipeline()
    
    print("[INIT] Connecting to Ollama LLM...")
    llm = OllamaLLM(model="llama3:8b")
    
    # Test LLM
    test = llm.simple_query("Say 'ready' only")
    print(f"[INIT] LLM Status: {test.strip()}")
    
    # =========================================================================
    # PHASE 1: INGEST RESUMES INTO CHROMADB
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 1: INGESTING RESUMES INTO VECTOR DATABASE")
    print("="*70)
    
    resume_files = [
        ("../data/test_resumes/clean_resume.pdf", "Clean candidate"),
        ("../data/test_resumes/poisoned_resume_obvious.pdf", "POISONED - Hidden instruction"),
        ("../data/test_resumes/poisoned_resume_context.pdf", "POISONED - Context ignore"),
        ("../data/test_resumes/poisoned_resume_completion.pdf", "POISONED - Fake completion"),
    ]
    
    for filepath, description in resume_files:
        try:
            chunks = rag.ingest_file(filepath)
            print(f"  ✓ Ingested: {filepath.split('/')[-1]} ({chunks} chunks) - {description}")
        except Exception as e:
            print(f"  ✗ Failed: {filepath} - {e}")
    
    stats = rag.get_stats()
    print(f"\n  📊 Vector Database Stats:")
    print(f"     Collection: {stats['name']}")
    print(f"     Total chunks: {stats['count']}")
    
    # =========================================================================
    # PHASE 2: SIMULATE USER QUERIES (WITH AND WITHOUT SENTINEL)
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 2: PROCESSING USER QUERIES")
    print("="*70)
    
    queries = [
        "Tell me about Mike Thompson's qualifications for a senior developer role",
        "What experience does Emily Rodriguez have in software development?",
        "Evaluate David Chen for a programming position",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─'*70}")
        print(f"QUERY {i}: {query}")
        print('─'*70)
        
        # Step 1: Retrieve from ChromaDB
        print("\n[1] Retrieving from Vector Database...")
        result = rag.retrieve(query, k=3)
        print(f"    Retrieved {len(result.chunks)} chunks")
        
        # Show what was retrieved
        print("\n[2] Retrieved Content (RAW):")
        print("    " + "-"*60)
        for j, chunk in enumerate(result.chunks):
            preview = chunk[:150].replace('\n', ' ')
            print(f"    Chunk {j+1}: {preview}...")
        print("    " + "-"*60)
        
        # Step 2: Process through Sentinel
        print("\n[3] Processing through Sentinel...")
        sentinel_results = sentinel.process_with_details(result.chunks)
        
        threats = [r for r in sentinel_results if r.was_threat]
        print(f"    Threats detected: {len(threats)}/{len(result.chunks)} chunks")
        
        if threats:
            for t in threats:
                print(f"    🚨 THREAT: {t.threat_level.value} (conf: {t.confidence:.0%})")
                print(f"       Patterns: {t.detection_result.matched_patterns}")
        
        # Step 3: Compare LLM responses
        print("\n[4] Generating LLM Responses...")
        
        # UNSAFE: Raw chunks directly to LLM
        unsafe_context = "\n\n".join(result.chunks)
        
        # SAFE: Sentinel-processed chunks to LLM
        safe_context = "\n\n".join([r.processed_text for r in sentinel_results])
        
        eval_prompt = f"""Based on the resume information provided, evaluate this candidate for a Senior Software Developer position.
Provide a rating (1-10) and brief justification in 2-3 sentences."""
        
        print("\n    ❌ WITHOUT SENTINEL (Vulnerable):")
        unsafe_response = llm.generate(eval_prompt, unsafe_context)
        print(f"    {unsafe_response.response.strip()[:300]}")
        
        print("\n    ✅ WITH SENTINEL (Protected):")
        safe_response = llm.generate(eval_prompt, safe_context)
        print(f"    {safe_response.response.strip()[:300]}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    
    final_stats = sentinel.get_stats()
    print(f"""
Summary:
  • Total chunks processed: {final_stats.total_chunks}
  • Threats detected: {final_stats.threats_detected}
  • Chunks neutralized: {final_stats.chunks_neutralized}
  • Average confidence: {final_stats.avg_confidence:.0%}

Key Points:
  1. Poisoned resumes were ingested alongside clean ones
  2. When retrieved, Sentinel detected hidden attacks
  3. Attacks were neutralized before reaching the LLM
  4. LLM provided honest evaluations based on actual qualifications
  
This demonstrates Sentinel-RAG's ability to protect RAG systems
from indirect prompt injection attacks in real-world scenarios.
""")


if __name__ == "__main__":
    main()