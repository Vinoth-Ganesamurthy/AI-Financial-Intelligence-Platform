"""Run frozen price and US enrichment benchmarks on the 2025 holdout."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "research/results/final_holdout"

EXPERIMENTS = [
    (
        "price",
        "research/experiments/06_price_baselines.py",
        "research/results/price_baselines",
    ),
    (
        "us",
        "research/experiments/10_us_macro_baselines.py",
        "research/results/us_macro_baselines",
    ),
]

INPUTS = [
    "data/processed/research/price_features.csv",
    "data/interim/research/sec_annual_features.csv",
    "data/interim/research/us_macro_features.csv",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(name, relative_source, old_output):
    source_path = ROOT / relative_source
    original = source_path.read_text(encoding="utf-8-sig")

    if original.count(f'OUTPUT = ROOT / "{old_output}"') != 1:
        raise ValueError(f"Unexpected output configuration: {name}")

    if '"train", "validation"' not in original:
        raise ValueError(f"Expected development split filter: {name}")

    if '"test_evaluated": False' not in original:
        raise ValueError(f"Expected unevaluated metadata: {name}")

    # All validation references become test references, including
    # dataframe names, split labels, and report filenames.
    code = original.replace("validation", "test")

    code = code.replace(
        f'OUTPUT = ROOT / "{old_output}"',
        f'OUTPUT = ROOT / "research/results/final_holdout/{name}"',
        1,
    )

    code = code.replace(
        '"test_evaluated": False',
        '"test_evaluated": True',
        1,
    )

    code = code.replace(
        "2025 test results have not been evaluated.",
        "2025 holdout results evaluated with frozen settings.",
    )
    code = code.replace(
        "2025 test predictions have not been evaluated.",
        "2025 holdout predictions evaluated with frozen settings.",
    )

    # Correct the old explanatory comment after switching splits.
    code = code.replace(
        "Test rows are excluded from every calculation below.",
        "Validation rows are excluded from the holdout evaluation.",
    )
    code = code.replace(
        "holdout predictions stay untouched.",
        "validation rows are excluded.",
    )

    compile(code, str(source_path), "exec")
    return source_path, original, code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the final holdout; without this flag, check syntax only.",
    )
    args = parser.parse_args()

    prepared = [
        (name, *prepare(name, source, old_output))
        for name, source, old_output in EXPERIMENTS
    ]

    print("Both frozen benchmark scripts passed preparation checks.")

    if not args.evaluate:
        print("Syntax check only; no datasets loaded or predictions evaluated.")
        return

    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError(
            "Final holdout output already exists. "
            "Preserve it and document any proposed rerun."
        )

    for relative_path in INPUTS:
        if not (ROOT / relative_path).exists():
            raise FileNotFoundError(relative_path)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    manifest = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "started",
        "training_period": "2021-2023",
        "evaluation_period": "2025",
        "validation_used_for_refitting": False,
        "protocol_sha256": sha256(
            ROOT / "research/FINAL_EVALUATION_PROTOCOL.md"
        ),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "input_hashes": {
            path: sha256(ROOT / path)
            for path in INPUTS
        },
        "experiments": {},
    }

    manifest_path = OUTPUT / "evaluation_manifest.json"

    def save_manifest():
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

    save_manifest()

    for name, source_path, original, code in prepared:
        generated_path = OUTPUT / f"{name}_executed.py"
        generated_path.write_text(code, encoding="utf-8")

        manifest["experiments"][name] = {
            "original_script": str(source_path.relative_to(ROOT)),
            "original_sha256": hashlib.sha256(
                original.encode("utf-8")
            ).hexdigest(),
            "executed_sha256": sha256(generated_path),
            "status": "started",
        }
        save_manifest()

        print(f"\nRunning frozen holdout experiment: {name}", flush=True)

        # Keep the original source location so its ROOT calculation
        # and source imports behave exactly as before.
        namespace = {
            "__name__": "__main__",
            "__file__": str(source_path),
        }

        try:
            exec(compile(code, str(source_path), "exec"), namespace)
        except Exception:
            manifest["status"] = "failed"
            manifest["experiments"][name]["status"] = "failed"
            save_manifest()
            raise

        manifest["experiments"][name]["status"] = "completed"
        save_manifest()

    manifest["status"] = "completed"
    manifest["completed_at_utc"] = datetime.now(
        timezone.utc
    ).isoformat()
    save_manifest()

    print("\nFinal holdout predictions saved.")
    print("Uncertainty analysis will use these saved predictions.")
    print(f"Results: {OUTPUT}")


if __name__ == "__main__":
    main()