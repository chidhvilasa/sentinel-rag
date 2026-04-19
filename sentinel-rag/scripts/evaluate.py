# scripts/evaluate.py
"""
Evaluate Sentinel-RAG against the attack dataset.
Measures Attack Success Rate (ASR) with and without protection.
"""
import sys
import json
sys.path.insert(0, '..')

from src.sentinel import SentinelPipeline

def load_dataset(path: str) -> list:
    """Load the attack dataset."""
    with open(path, 'r') as f:
        return json.load(f)

def evaluate_detection(dataset: list, pipeline: SentinelPipeline) -> dict:
    """Evaluate detection accuracy."""
    results = {
        "total": len(dataset),
        "true_positives": 0,   # Attack detected as attack
        "false_positives": 0,  # Clean detected as attack
        "true_negatives": 0,   # Clean detected as clean
        "false_negatives": 0,  # Attack detected as clean
        "by_attack_type": {}
    }
    
    for doc in dataset:
        content = doc["content"]
        label = doc["label"]  # 1 = attack, 0 = clean
        attack_type = doc["attack_type"]
        
        # Process through Sentinel
        processed = pipeline.process_with_details([content])
        detected = processed[0].was_threat
        
        # Track by attack type
        if attack_type not in results["by_attack_type"]:
            results["by_attack_type"][attack_type] = {"detected": 0, "total": 0}
        results["by_attack_type"][attack_type]["total"] += 1
        
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
    
    # Attack Success Rate (lower is better for defense)
    # ASR = attacks that were NOT detected / total attacks
    total_attacks = tp + fn
    results["attack_success_rate"] = fn / total_attacks if total_attacks > 0 else 0
    
    return results

def main():
    print("="*60)
    print("SENTINEL-RAG EVALUATION")
    print("="*60)
    
    # Load dataset
    print("\n[1] Loading dataset...")
    dataset = load_dataset("../data/attack_dataset.json")
    print(f"Loaded {len(dataset)} documents")
    
    attacks = [d for d in dataset if d["label"] == 1]
    clean = [d for d in dataset if d["label"] == 0]
    print(f"  - Attacks: {len(attacks)}")
    print(f"  - Clean: {len(clean)}")
    
    # Initialize Sentinel
    print("\n[2] Initializing Sentinel...")
    pipeline = SentinelPipeline()
    
    # Evaluate
    print("\n[3] Evaluating detection...")
    results = evaluate_detection(dataset, pipeline)
    
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
    print(f"    (Lower is better - this is % of attacks that bypassed detection)")
    
    print(f"\nDetection by Attack Type:")
    for attack_type, stats in results["by_attack_type"].items():
        if attack_type != "none":
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {attack_type}: {stats['detected']}/{stats['total']} detected ({rate:.0%})")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()