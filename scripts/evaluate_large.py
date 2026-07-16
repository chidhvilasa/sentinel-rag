# scripts/evaluate_large.py
"""
Evaluate Sentinel-RAG on the large dataset (148 documents).
"""
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.sentinel import SentinelPipeline

def load_dataset(path: str) -> list:
    with open(path, 'r') as f:
        return json.load(f)

def evaluate(dataset: list, pipeline: SentinelPipeline) -> dict:
    results = {
        "total": len(dataset),
        "true_positives": 0,
        "false_positives": 0,
        "true_negatives": 0,
        "false_negatives": 0,
        "by_attack_type": {}
    }
    
    for i, doc in enumerate(dataset):
        if (i + 1) % 20 == 0:
            print(f"  Processing {i+1}/{len(dataset)}...")
        
        content = doc["content"]
        label = doc["label"]
        attack_type = doc["attack_type"]
        
        # Initialize type tracking
        if attack_type not in results["by_attack_type"]:
            results["by_attack_type"][attack_type] = {"detected": 0, "total": 0}
        results["by_attack_type"][attack_type]["total"] += 1
        
        # Process through Sentinel
        processed = pipeline.process_with_details([content])
        detected = processed[0].was_threat
        
        if label == 1:  # Actual attack
            if detected:
                results["true_positives"] += 1
                results["by_attack_type"][attack_type]["detected"] += 1
            else:
                results["false_negatives"] += 1
        else:  # Clean document
            if detected:
                results["false_positives"] += 1
            else:
                results["true_negatives"] += 1
    
    # Calculate metrics
    tp = results["true_positives"]
    fp = results["false_positives"]
    tn = results["true_negatives"]
    fn = results["false_negatives"]
    
    results["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
    results["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
    results["f1"] = 2 * (results["precision"] * results["recall"]) / (results["precision"] + results["recall"]) if (results["precision"] + results["recall"]) > 0 else 0
    results["accuracy"] = (tp + tn) / results["total"] if results["total"] > 0 else 0
    
    total_attacks = tp + fn
    results["attack_success_rate"] = fn / total_attacks if total_attacks > 0 else 0
    
    return results

def main():
    print("="*60)
    print("SENTINEL-RAG EVALUATION - LARGE DATASET")
    print("="*60)
    
    print("\n[1] Loading large dataset...")
    dataset = load_dataset(str(ROOT_DIR / "data" / "large_attack_dataset.json"))
    
    attacks = [d for d in dataset if d["label"] == 1]
    clean = [d for d in dataset if d["label"] == 0]
    print(f"    Total: {len(dataset)}")
    print(f"    Attacks: {len(attacks)}")
    print(f"    Clean: {len(clean)}")
    
    print("\n[2] Initializing Sentinel...")
    pipeline = SentinelPipeline()
    
    print("\n[3] Evaluating (this may take a minute)...")
    results = evaluate(dataset, pipeline)
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    print(f"\nConfusion Matrix:")
    print(f"  True Positives (attacks detected):  {results['true_positives']}")
    print(f"  False Positives (clean flagged):    {results['false_positives']}")
    print(f"  True Negatives (clean passed):      {results['true_negatives']}")
    print(f"  False Negatives (attacks missed):   {results['false_negatives']}")
    
    print(f"\nMetrics:")
    print(f"  Precision: {results['precision']:.2%}")
    print(f"  Recall:    {results['recall']:.2%}")
    print(f"  F1 Score:  {results['f1']:.2%}")
    print(f"  Accuracy:  {results['accuracy']:.2%}")
    
    print(f"\n⚠️  Attack Success Rate (ASR): {results['attack_success_rate']:.2%}")
    
    print(f"\nDetection by Attack Type:")
    for attack_type, stats in sorted(results["by_attack_type"].items()):
        if attack_type != "none":
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {attack_type:20s}: {stats['detected']:2d}/{stats['total']:2d} detected ({rate:5.1%})")
    
    # Save results
    with open(ROOT_DIR / "results" / "large_dataset_evaluation.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {ROOT_DIR / 'results' / 'large_dataset_evaluation.json'}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()