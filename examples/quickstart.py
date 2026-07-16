"""
Minimal Sentinel-RAG example: detect and neutralize a prompt injection
without needing ChromaDB or a running LLM.

Run from the repository root:
    python examples/quickstart.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.sentinel import SentinelPipeline  # noqa: E402

SAMPLES_DIR = ROOT_DIR / "data" / "samples"


def main() -> None:
    pipeline = SentinelPipeline()

    clean_text = (SAMPLES_DIR / "sample_clean.txt").read_text(encoding="utf-8")
    attack_text = (SAMPLES_DIR / "sample_attack_naive.txt").read_text(encoding="utf-8")

    for label, text in [("clean", clean_text), ("attack", attack_text)]:
        result = pipeline.process_with_details([text])[0]
        print(f"\n--- {label} ---")
        print(f"Threat detected: {result.was_threat} ({result.threat_level.value})")
        if result.was_neutralized:
            print(f"Neutralized preview: {result.processed_text[:200]}...")

    print(f"\n{pipeline.summary()}")


if __name__ == "__main__":
    main()
