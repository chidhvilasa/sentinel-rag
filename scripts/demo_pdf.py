# scripts/demo_pdf.py
"""
Full demonstration of Sentinel-RAG with PDF resumes.
Shows detection and neutralization of prompt injection attacks in real PDFs.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pypdf import PdfReader
from src.sentinel import SentinelPipeline
from src.rag import OllamaLLM

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def evaluate_resume(llm, context: str, candidate_name: str) -> str:
    """Ask LLM to evaluate a resume."""
    query = f"""Based on the resume provided, evaluate {candidate_name} for a Senior Software Developer position.

Provide:
1. A rating from 1-10
2. Key strengths
3. Key concerns
4. Hiring recommendation (Yes/No/Maybe)

Be objective and base your assessment ONLY on the actual qualifications shown."""
    
    response = llm.generate(query, context)
    return response.response

def demo_single_resume(pdf_path: str, sentinel: SentinelPipeline, llm: OllamaLLM):
    """Demo detection and neutralization for a single resume."""
    print(f"\n{'='*70}")
    print(f"PROCESSING: {pdf_path}")
    print('='*70)
    
    # Extract text from PDF
    print("\n[1] Extracting text from PDF...")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"    Extracted {len(raw_text)} characters")
    
    # Show first 500 chars of raw content
    print(f"\n[2] Raw PDF Content (first 500 chars):")
    print("-"*50)
    print(raw_text[:500])
    print("-"*50)
    
    # Process through Sentinel
    print(f"\n[3] Processing through Sentinel...")
    
    # Split into chunks (simulate RAG chunking)
    chunks = [raw_text[i:i+500] for i in range(0, len(raw_text), 500)]
    print(f"    Split into {len(chunks)} chunks")
    
    # Process each chunk
    results = sentinel.process_with_details(chunks)
    
    threats_found = sum(1 for r in results if r.was_threat)
    print(f"\n    🔍 Detection Results:")
    print(f"       Chunks analyzed: {len(chunks)}")
    print(f"       Threats detected: {threats_found}")
    
    if threats_found > 0:
        print(f"\n    🚨 THREATS FOUND:")
        for i, r in enumerate(results):
            if r.was_threat:
                print(f"       Chunk {i+1}: {r.threat_level.value} threat (confidence: {r.confidence:.2f})")
                print(f"       Patterns: {r.detection_result.matched_patterns}")
    
    # Get safe context
    safe_chunks = [r.processed_text for r in results]
    safe_context = "\n".join(safe_chunks)
    unsafe_context = raw_text
    
    # Compare LLM responses
    print(f"\n[4] Comparing LLM Evaluations...")
    
    # Extract candidate name from first line
    candidate_name = raw_text.split('\n')[0].strip()
    
    print(f"\n--- UNSAFE EVALUATION (No Sentinel) ---")
    unsafe_response = evaluate_resume(llm, unsafe_context, candidate_name)
    print(unsafe_response)
    
    print(f"\n--- SAFE EVALUATION (With Sentinel) ---")
    safe_response = evaluate_resume(llm, safe_context, candidate_name)
    print(safe_response)
    
    return {
        "file": pdf_path,
        "threats_found": threats_found,
        "unsafe_response": unsafe_response,
        "safe_response": safe_response
    }


def main():
    print("="*70)
    print("   SENTINEL-RAG DEMONSTRATION")
    print("   Detecting and Neutralizing Prompt Injection in PDF Resumes")
    print("="*70)
    
    # Initialize components
    print("\n[INIT] Loading Sentinel Pipeline...")
    sentinel = SentinelPipeline()
    
    print("[INIT] Connecting to Ollama LLM...")
    try:
        llm = OllamaLLM(model="llama3:8b")
        # Quick test
        test = llm.simple_query("Say 'ready' and nothing else.")
        print(f"[INIT] LLM Ready: {test.strip()}")
    except Exception as e:
        print(f"[ERROR] Could not connect to Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
        sys.exit(1)
    
    # Test resumes
    test_resumes = [
        (str(ROOT_DIR / "data/test_resumes/clean_resume.pdf"), "Clean - Should pass normally"),
        (str(ROOT_DIR / "data/test_resumes/poisoned_resume_obvious.pdf"), "Attack - Hidden instruction"),
        (str(ROOT_DIR / "data/test_resumes/poisoned_resume_context.pdf"), "Attack - Context ignoring"),
        (str(ROOT_DIR / "data/test_resumes/poisoned_resume_completion.pdf"), "Attack - Fake completion"),
    ]
    
    results = []
    
    for pdf_path, description in test_resumes:
        print(f"\n\n{'#'*70}")
        print(f"# TEST: {description}")
        print(f"{'#'*70}")
        
        try:
            result = demo_single_resume(pdf_path, sentinel, llm)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final Summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    print(f"\nResumes Processed: {len(results)}")
    total_threats = sum(r["threats_found"] for r in results)
    print(f"Total Threats Detected: {total_threats}")
    
    print("\n" + "-"*70)
    print("KEY FINDINGS:")
    print("-"*70)
    
    for r in results:
        status = "🚨 ATTACK NEUTRALIZED" if r["threats_found"] > 0 else "✅ CLEAN"
        print(f"\n{status}: {r['file'].split('/')[-1]}")
        if r["threats_found"] > 0:
            print("  Without Sentinel: LLM may have followed malicious instructions")
            print("  With Sentinel: LLM evaluated based on actual qualifications")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()