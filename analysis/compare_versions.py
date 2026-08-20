#!/usr/bin/env python3
"""Validate comparable benchmark summaries and write V0/V1 speedups."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_FIELDS = [
    "grid_width",
    "grid_height",
    "generations",
    "density",
    "seed",
    "repetitions",
    "v0_median_seconds",
    "v1_median_seconds",
    "speedup",
    "runtime_reduction_percent",
    "v0_cv_percent",
    "v1_cv_percent",
    "live_cells",
    "checksum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("v0_summary", type=Path)
    parser.add_argument("v1_summary", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def load(path: Path) -> dict[tuple[str, ...], dict[str, str]]:
    key_fields = ("grid_width", "grid_height", "generations", "density", "seed")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no data rows")
    keyed = {tuple(row[field] for field in key_fields): row for row in rows}
    if len(keyed) != len(rows):
        raise ValueError(f"{path} contains duplicate configurations")
    return keyed


def main() -> None:
    args = parse_args()
    v0 = load(args.v0_summary)
    v1 = load(args.v1_summary)
    if set(v0) != set(v1):
        raise ValueError("V0 and V1 configuration matrices differ")

    output_rows: list[dict[str, str]] = []
    for key in sorted(v0, key=lambda values: int(values[0])):
        baseline = v0[key]
        optimised = v1[key]
        if baseline["repetitions"] != optimised["repetitions"]:
            raise ValueError(f"repetition counts differ for {key}")
        if (baseline["live_cells"], baseline["checksum"]) != (
            optimised["live_cells"],
            optimised["checksum"],
        ):
            raise ValueError(f"correctness outputs differ for {key}")

        v0_median = float(baseline["median_seconds"])
        v1_median = float(optimised["median_seconds"])
        output_rows.append(
            {
                "grid_width": key[0],
                "grid_height": key[1],
                "generations": key[2],
                "density": key[3],
                "seed": key[4],
                "repetitions": baseline["repetitions"],
                "v0_median_seconds": f"{v0_median:.9f}",
                "v1_median_seconds": f"{v1_median:.9f}",
                "speedup": f"{v0_median / v1_median:.6f}",
                "runtime_reduction_percent": f"{(1.0 - v1_median / v0_median) * 100.0:.6f}",
                "v0_cv_percent": baseline["cv_percent"],
                "v1_cv_percent": optimised["cv_percent"],
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
    print("matrix_equivalence=PASS")
    print("checksum_equivalence=PASS")


if __name__ == "__main__":
    main()
