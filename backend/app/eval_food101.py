#!/usr/bin/env python
"""
Evaluate your VLM models on Food-101 and print results to terminal.

Usage example:
    python eval_food101.py \
        --models "qwen3-vl:8b,llava-v1.6-vl:13b,acpm-vl:7b" \
        --num_samples 100
"""

import argparse
import re
import time
from typing import Dict

from datasets import load_dataset
from PIL import Image

# Adjust this import to match your project layout
# (this assumes you're running from the repo root)
from vlm import classify


def normalize_label(s: str) -> str:
    """Lowercase, remove punctuation, collapse spaces."""
    s = (s or "").lower()
    s = s.replace("_", " ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        type=str,
        required=True,
        help="Comma-separated list of Ollama/OpenAI model names (e.g. 'qwen3-vl:8b,llava-v1.6-vl:13b')",
    )
    
    parser.add_argument(
        "--backend",
        type=str,
        default="ollama",
        help="Backend for classify() (default: ollama)",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=50,
        help="Number of Food-101 test images to evaluate (default: 50)",
    )
    args = parser.parse_args()

   
    if not args.models:
        args.models = "qwen3-vl:8b,llava:7b-v1.6,minicpm-v:8b"
    
    if not args.num_samples:
        args.num_samples = 5


    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        raise SystemExit("No models provided via --models")

    print(f"Using backend={args.backend}, models={models}")
    print(f"Loading Food-101 test split (first {args.num_samples} samples)...")

    # Load first N images from the Food-101 test split
    ds = load_dataset("food101", split=f"validation[:{args.num_samples}]")

    label_names = ds.features["label"].names  # integer -> class name (e.g. 'spaghetti_bolognese')

    # Stats per model
    stats: Dict[str, Dict[str, float]] = {}
    for m in models:
        stats[m] = {
            "total": 0,
            "correct": 0,
            "lat_sum": 0.0,
            "lat_count": 0,
        }

    # Main evaluation loop
    for idx, sample in enumerate(ds):
        img: Image.Image = sample["image"]  # already a PIL Image
        gt_idx: int = sample["label"]
        gt_name_raw: str = label_names[gt_idx]           # e.g. 'spaghetti_bolognese'
        gt_name_norm: str = normalize_label(gt_name_raw) # e.g. 'spaghetti bolognese'

        print(f"\n=== Sample {idx+1}/{len(ds)} | GT: {gt_name_raw} ===")

        for model_name in models:
            s = stats[model_name]
            s["total"] += 1

            try:
                t0 = time.time()
                pred_label, portion_g, conf, trace = classify(
                    img,
                    backend=args.backend,
                    model=model_name,
                )
                dt = time.time() - t0

                pred_norm = normalize_label(str(pred_label))
                correct = int(
                    pred_norm == gt_name_norm
                    or gt_name_norm in pred_norm
                    or pred_norm in gt_name_norm
                )

                s["correct"] += correct
                s["lat_sum"] += dt
                s["lat_count"] += 1

                print(
                    f"[{model_name}] "
                    f"pred='{pred_label}' (norm='{pred_norm}') | "
                    f"gt='{gt_name_norm}' | "
                    f"correct={bool(correct)} | "
                    f"latency={dt:.3f}s"
                )

            except Exception as e:
                # Count as a failure (incorrect, no latency)
                print(f"[{model_name}] ERROR: {e}")

    # Summary
    print("\n===== SUMMARY =====")
    print(f"{'Model':30s} {'Accuracy':>10s} {'Avg Latency (s)':>16s}")
    print("-" * 60)

    for model_name in models:
        s = stats[model_name]
        total = s["total"] or 1  # avoid div by 0
        acc = s["correct"] / total
        avg_lat = (s["lat_sum"] / s["lat_count"]) if s["lat_count"] else float("nan")

        print(f"{model_name:30s} {acc:10.3f} {avg_lat:16.3f}")


if __name__ == "__main__":
    main()
