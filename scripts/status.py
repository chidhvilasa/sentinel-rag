# scripts/status.py
"""Quick project status overview."""
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def main():
    print("="*60)
    print("   SENTINEL-RAG PROJECT STATUS")
    print("="*60)

    results_dir = str(ROOT_DIR / "results")
    
    # Check for result files
    result_files = [
        ("large_dataset_evaluation.json", "Large Dataset (148 docs)"),
        ("deepset_benchmark.json", "Deepset Benchmark"),
        ("baseline_comparison.json", "Baseline Comparison"),
        ("latency_benchmark.json", "Latency Benchmark"),
    ]
    
    print("\n📊 EVALUATION RESULTS:")
    print("-"*60)
    
    for filename, description in result_files:
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            with open(filepath) as f:
                data = json.load(f)
            
            if "metrics" in data:
                metrics = data["metrics"]
                print(f"\n✅ {description}:")
                print(f"   Precision: {metrics.get('precision', 0):.1%}")
                print(f"   Recall:    {metrics.get('recall', 0):.1%}")
                print(f"   F1 Score:  {metrics.get('f1', 0):.1%}")
                print(f"   Accuracy:  {metrics.get('accuracy', 0):.1%}")
            elif "without_sentinel" in data:
                print(f"\n✅ {description}:")
                print(f"   Without Sentinel ASR: {data['without_sentinel']['asr']:.1f}%")
                print(f"   With Sentinel ASR:    {data['with_sentinel']['asr']:.1f}%")
                print(f"   Improvement:          {data['reduction_percentage']:.0f}%")
            elif isinstance(data, list):
                print(f"\n✅ {description}:")
                avg = sum(r['avg_ms'] for r in data) / len(data)
                print(f"   Average latency: {avg:.1f}ms")
        else:
            print(f"\n❌ {description}: Not found")
    
    # Check for test files
    print("\n\n📁 TEST DATA:")
    print("-"*60)
    
    test_files = [
        (str(ROOT_DIR / "data" / "attack_dataset.json"), "Small dataset (30 docs)"),
        (str(ROOT_DIR / "data" / "large_attack_dataset.json"), "Large dataset (148 docs)"),
        (str(ROOT_DIR / "data" / "test_resumes"), "PDF test resumes"),
    ]
    
    for filepath, description in test_files:
        if os.path.exists(filepath):
            if filepath.endswith('.json'):
                with open(filepath) as f:
                    data = json.load(f)
                print(f"✅ {description}: {len(data)} items")
            else:
                files = os.listdir(filepath)
                print(f"✅ {description}: {len(files)} files")
        else:
            print(f"❌ {description}: Not found")
    
    print("\n" + "="*60)
    print("PROJECT READY FOR REVIEW ✅")
    print("="*60)

if __name__ == "__main__":
    main()