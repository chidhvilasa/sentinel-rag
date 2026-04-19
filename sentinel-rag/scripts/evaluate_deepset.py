# scripts/evaluate_deepset.py
"""
Evaluate Sentinel against the standard deepset/prompt-injections benchmark.
This is a public benchmark used by many prompt injection detection papers.
"""
import sys
sys.path.insert(0, '..')

from datasets import load_dataset
from src.sentinel import SentinelPipeline

def main():
    print("="*60)
    print("SENTINEL EVALUATION - DEEPSET BENCHMARK")
    print("Public benchmark: deepset/prompt-injections (662 samples)")
    print("="*60)
    
    # Load the dataset from HuggingFace
    print("\n[1] Loading deepset/prompt-injections from HuggingFace...")
    try:
        dataset = load_dataset("deepset/prompt-injections")
        train_data = dataset["train"]
        test_data = dataset["test"]
        print(f"    Train samples: {len(train_data)}")
        print(f"    Test samples: {len(test_data)}")
    except Exception as e:
        print(f"    Error loading dataset: {e}")
        print("    Installing datasets library...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "datasets", "-q"])
        from datasets import load_dataset
        dataset = load_dataset("deepset/prompt-injections")
        train_data = dataset["train"]
        test_data = dataset["test"]
    
    # Initialize Sentinel
    print("\n[2] Initializing Sentinel...")
    pipeline = SentinelPipeline()
    
    # Evaluate on test set
    print("\n[3] Evaluating on test set...")
    
    results = {
        "total": 0,
        "true_positives": 0,
        "false_positives": 0,
        "true_negatives": 0,
        "false_negatives": 0,
    }
    
    for i, item in enumerate(test_data):
        text = item["text"]
        label = item["label"]  # 1 = injection, 0 = legitimate
        
        # Process through Sentinel
        processed = pipeline.process_with_details([text])
        detected = processed[0].was_threat
        
        results["total"] += 1
        
        if label == 1:  # Actual injection
            if detected:
                results["true_positives"] += 1
            else:
                results["false_negatives"] += 1
        else:  # Legitimate
            if detected:
                results["false_positives"] += 1
            else:
                results["true_negatives"] += 1
        
        if (i + 1) % 20 == 0:
            print(f"    Processed {i+1}/{len(test_data)}...")
    
    # Calculate metrics
    tp = results["true_positives"]
    fp = results["false_positives"]
    tn = results["true_negatives"]
    fn = results["false_negatives"]
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / results["total"] if results["total"] > 0 else 0
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS ON DEEPSET BENCHMARK")
    print("="*60)
    
    print(f"\nConfusion Matrix:")
    print(f"  True Positives (injections detected):  {tp}")
    print(f"  False Positives (legit flagged):       {fp}")
    print(f"  True Negatives (legit passed):         {tn}")
    print(f"  False Negatives (injections missed):   {fn}")
    
    print(f"\nMetrics:")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall:    {recall:.2%}")
    print(f"  F1 Score:  {f1:.2%}")
    print(f"  Accuracy:  {accuracy:.2%}")
    
    # Compare with reported results
    print(f"\n" + "-"*60)
    print("COMPARISON WITH PUBLISHED RESULTS:")
    print("-"*60)
    print(f"  deepset/deberta-v3-base-injection: 99.1% accuracy (reported)")
    print(f"  Sentinel-RAG (our system):         {accuracy:.1%} accuracy")
    
    # Save results
    import json
    results_data = {
        "dataset": "deepset/prompt-injections",
        "test_samples": len(test_data),
        "confusion_matrix": {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy
        }
    }
    
    with open("../results/deepset_benchmark.json", "w") as f:
        json.dump(results_data, f, indent=2)
    print(f"\nResults saved to ../results/deepset_benchmark.json")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()