#!/usr/bin/env python3
"""Validate V0/V1/V2 summaries and write controlled speedup comparisons."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


KEY_FIELDS = ("grid_width", "grid_height", "generations", "density", "seed")
OUTPUT_FIELDS = [
    "grid_width",
    "grid_height",
    "generations",
    "density",
    "seed",
    "repetitions",
    "v0_median_seconds",
    "v1_median_seconds",
    "v2_median_seconds",
    "v1_speedup_vs_v0",
    "v2_speedup_vs_v0",
    "v2_incremental_speedup_vs_v1",
    "v1_runtime_reduction_vs_v0_percent",
    "v2_runtime_reduction_vs_v0_percent",
    "v2_runtime_reduction_vs_v1_percent",
    "v0_cv_percent",
    "v1_cv_percent",
    "v2_cv_percent",
    "live_cells",
    "checksum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("v0_summary", type=Path)
    parser.add_argument("v1_summary", type=Path)
    parser.add_argument("v2_summary", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def load(path: Path) -> dict[tuple[str, ...], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no data rows")
    keyed = {tuple(row[field] for field in KEY_FIELDS): row for row in rows}
    if len(keyed) != len(rows):
        raise ValueError(f"{path} contains duplicate configurations")
    return keyed


def main() -> None:
    args = parse_args()
    versions = [load(args.v0_summary), load(args.v1_summary), load(args.v2_summary)]
    if not (set(versions[0]) == set(versions[1]) == set(versions[2])):
        raise ValueError("V0, V1, and V2 configuration matrices differ")

    output_rows: list[dict[str, str]] = []
    for key in sorted(versions[0], key=lambda values: int(values[0])):
        baseline, precomputed, contiguous = (version[key] for version in versions)
        repetitions = {row["repetitions"] for row in (baseline, precomputed, contiguous)}
        correctness = {
            (row["live_cells"], row["checksum"])
            for row in (baseline, precomputed, contiguous)
        }
        if len(repetitions) != 1:
            raise ValueError(f"repetition counts differ for {key}")
        if len(correctness) != 1:
            raise ValueError(f"correctness outputs differ for {key}")

        v0 = float(baseline["median_seconds"])
        v1 = float(precomputed["median_seconds"])
        v2 = float(contiguous["median_seconds"])
        output_rows.append(
            {
                "grid_width": key[0],
                "grid_height": key[1],
                "generations": key[2],
                "density": key[3],
                "seed": key[4],
                "repetitions": baseline["repetitions"],
                "v0_median_seconds": f"{v0:.9f}",
                "v1_median_seconds": f"{v1:.9f}",
                "v2_median_seconds": f"{v2:.9f}",
                "v1_speedup_vs_v0": f"{v0 / v1:.6f}",
                "v2_speedup_vs_v0": f"{v0 / v2:.6f}",
                "v2_incremental_speedup_vs_v1": f"{v1 / v2:.6f}",
                "v1_runtime_reduction_vs_v0_percent": f"{(1.0 - v1 / v0) * 100.0:.6f}",
                "v2_runtime_reduction_vs_v0_percent": f"{(1.0 - v2 / v0) * 100.0:.6f}",
                "v2_runtime_reduction_vs_v1_percent": f"{(1.0 - v2 / v1) * 100.0:.6f}",
                "v0_cv_percent": baseline["cv_percent"],
                "v1_cv_percent": precomputed["cv_percent"],
                "v2_cv_percent": contiguous["cv_percent"],
                "live_cells": baseline["live_cells"],
                "checksum": baseline["checksum"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"validated_configurations={len(output_rows)}")
    print("three_version_matrix_equivalence=PASS")
    print("three_version_checksum_equivalence=PASS")


if __name__ == "__main__":
    main()
