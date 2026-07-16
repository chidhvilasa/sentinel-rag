# scripts/quick_demo.py
"""
Quick 2-minute demo for review presentation.
Shows one clean and one poisoned resume comparison.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pypdf import PdfReader
from src.sentinel import SentinelPipeline
from src.rag import OllamaLLM

def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "".join(page.extract_text() for page in reader.pages)

def main():
    print("\n" + "="*60)
    print("  SENTINEL-RAG QUICK DEMO")
    print("  Prompt Injection Defense for RAG Systems")
    print("="*60)
    
    # Initialize
    print("\n⏳ Loading models...")
    sentinel = SentinelPipeline()
    llm = OllamaLLM(model="llama3:8b")
    print("✅ Ready!\n")
    
    # Test the poisoned resume
    print("="*60)
    print("TEST: Poisoned Resume (Mike Thompson)")
    print("="*60)
    
    text = extract_text(str(ROOT_DIR / "data/test_resumes/poisoned_resume_obvious.pdf"))
    
    print("\n📄 Resume contains hidden attack:")
    print("-"*40)
    # Find and show the attack
    if "[SYSTEM]" in text:
        start = text.find("[SYSTEM]")
        print(text[start:start+120] + "...")
    print("-"*40)
    
    # Process
    chunks = [text]
    results = sentinel.process_with_details(chunks)
    
    print(f"\n🔍 Sentinel Detection:")
    print(f"   Threat detected: {results[0].was_threat}")
    print(f"   Confidence: {results[0].confidence:.0%}")
    print(f"   Patterns: {results[0].detection_result.matched_patterns}")
    
    # Compare evaluations
    query = "Rate this candidate for Senior Developer (1-10) in one sentence."
    
    print("\n" + "-"*60)
    print("❌ WITHOUT SENTINEL (Vulnerable):")
    unsafe = llm.generate(query, text)
    print(f"   {unsafe.response.strip()[:200]}")
    
    print("\n✅ WITH SENTINEL (Protected):")
    safe_text = results[0].processed_text
    safe = llm.generate(query, safe_text)
    print(f"   {safe.response.strip()[:200]}")
    print("-"*60)
    
    print("\n" + "="*60)
    print("DEMO COMPLETE - Attack Neutralized!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()