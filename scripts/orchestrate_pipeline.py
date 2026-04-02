"""
Batch pipeline orchestrator.

Run order:
1) bronze_layer.py
2) silver_layer.py
3) gold_layer.py
4) embedding_layer.py
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


def run_spark_job(job_name: str, script_path: Path) -> bool:
    print("\n" + "=" * 64)
    print(f"RUNNING: {job_name}")
    print("=" * 64)
    try:
        subprocess.run(["spark-submit", str(script_path)], check=True)
        print(f"OK: {job_name}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: {job_name} failed ({exc})")
        return False
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {job_name} could not start ({exc})")
        return False


def main() -> None:
    print("\n" + "=" * 64)
    print("AI-READY REVIEW PIPELINE - ORCHESTRATION")
    print("=" * 64)

    base = Path(__file__).parent
    jobs = [
        ("BRONZE LAYER", base / "bronze_layer.py"),
        ("SILVER LAYER", base / "silver_layer.py"),
        ("GOLD LAYER", base / "gold_layer.py"),
        ("EMBEDDING LAYER", base / "embedding_layer.py"),
    ]

    start = time.time()
    success = True

    for i, (name, script) in enumerate(jobs, start=1):
        print(f"\nStep {i}/{len(jobs)}")
        if not run_spark_job(name, script):
            success = False
            break
        time.sleep(1)

    elapsed = time.time() - start
    print("\n" + "=" * 64)
    if success:
        print("PIPELINE COMPLETED")
        print(f"Total time: {elapsed:.1f}s")
        print("Outputs:")
        print("- data/bronze")
        print("- data/silver")
        print("- data/gold/reviews")
        print("- data/gold/analytics/*")
        print("- data/embeddings")
    else:
        print("PIPELINE FAILED")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
