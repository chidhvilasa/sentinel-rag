# scripts/analyze_deepset_failures.py
"""
Analyze which attacks from deepset we're missing.
"""
import sys
sys.path.insert(0, '..')

from datasets import load_dataset
from src.sentinel import SentinelPipeline

def main():
    print("="*60)
    print("ANALYZING MISSED ATTACKS FROM DEEPSET")
    print("="*60)
    
    # Load dataset
    dataset = load_dataset("deepset/prompt-injections")
    test_data = dataset["test"]
    
    # Initialize Sentinel
    pipeline = SentinelPipeline()
    
    # Find missed attacks
    missed = []
    detected = []
    
    for item in test_data:
        text = item["text"]
        label = item["label"]
        
        if label == 1:  # Only check actual injections
            processed = pipeline.process_with_details([text])
            was_detected = processed[0].was_threat
            
            if not was_detected:
                missed.append(text)
            else:
                detected.append(text)
    
    print(f"\nTotal injections in test set: {len(missed) + len(detected)}")
    print(f"Detected: {len(detected)}")
    print(f"Missed: {len(missed)}")
    
    print("\n" + "="*60)
    print("SAMPLE MISSED ATTACKS (first 15):")
    print("="*60)
    
    for i, attack in enumerate(missed[:15], 1):
        print(f"\n--- Missed Attack {i} ---")
        print(attack[:300] + "..." if len(attack) > 300 else attack)
    
    # Analyze patterns in missed attacks
    print("\n" + "="*60)
    print("COMMON PATTERNS IN MISSED ATTACKS:")
    print("="*60)
    
    keywords = {}
    for attack in missed:
        attack_lower = attack.lower()
        # Check for common keywords
        check_words = ['ignore', 'forget', 'disregard', 'pretend', 'act as', 
                       'you are', 'new instructions', 'instead', 'override',
                       'system', 'admin', 'prompt', 'reveal', 'show me']
        for word in check_words:
            if word in attack_lower:
                keywords[word] = keywords.get(word, 0) + 1
    
    print("\nKeyword frequency in missed attacks:")
    for word, count in sorted(keywords.items(), key=lambda x: -x[1]):
        print(f"  '{word}': {count}")

if __name__ == "__main__":
    main()