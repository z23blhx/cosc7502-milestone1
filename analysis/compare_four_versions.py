#!/usr/bin/env python3
"""Validate V0-V3 summaries and write controlled V3 comparisons."""

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
    "v3_median_seconds",
    "v3_speedup_vs_v0",
    "v3_speedup_vs_v1",
    "v3_incremental_speedup_vs_v2",
    "v3_runtime_reduction_vs_v0_percent",
    "v3_runtime_reduction_vs_v1_percent",
    "v3_runtime_reduction_vs_v2_percent",
    "v0_cv_percent",
    "v1_cv_percent",
    "v2_cv_percent",
    "v3_cv_percent",
    "live_cells",
    "checksum",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("v0_summary", type=Path)
    parser.add_argument("v1_summary", type=Path)
    parser.add_argument("v2_summary", type=Path)
    parser.add_argument("v3_summary", type=Path)
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
    versions = [
        load(args.v0_summary),
        load(args.v1_summary),
        load(args.v2_summary),
        load(args.v3_summary),
    ]
    if not all(set(version) == set(versions[0]) for version in versions[1:]):
        raise ValueError("V0, V1, V2, and V3 configuration matrices differ")

    output_rows: list[dict[str, str]] = []
    for key in sorted(versions[0], key=lambda values: int(values[0])):
        rows = [version[key] for version in versions]
        if len({row["repetitions"] for row in rows}) != 1:
            raise ValueError(f"repetition counts differ for {key}")
        if len({(row["live_cells"], row["checksum"]) for row in rows}) != 1:
            raise ValueError(f"correctness outputs differ for {key}")

        v0, v1, v2, v3 = (float(row["median_seconds"]) for row in rows)
        output_rows.append(
            {
                "grid_width": key[0],
                "grid_height": key[1],
                "generations": key[2],
                "density": key[3],
                "seed": key[4],
                "repetitions": rows[0]["repetitions"],
                "v0_median_seconds": f"{v0:.9f}",
                "v1_median_seconds": f"{v1:.9f}",
                "v2_median_seconds": f"{v2:.9f}",
                "v3_median_seconds": f"{v3:.9f}",
                "v3_speedup_vs_v0": f"{v0 / v3:.6f}",
                "v3_speedup_vs_v1": f"{v1 / v3:.6f}",
                "v3_incremental_speedup_vs_v2": f"{v2 / v3:.6f}",
                "v3_runtime_reduction_vs_v0_percent": f"{(1.0 - v3 / v0) * 100.0:.6f}",
                "v3_runtime_reduction_vs_v1_percent": f"{(1.0 - v3 / v1) * 100.0:.6f}",
                "v3_runtime_reduction_vs_v2_percent": f"{(1.0 - v3 / v2) * 100.0:.6f}",
                "v0_cv_percent": rows[0]["cv_percent"],
                "v1_cv_percent": rows[1]["cv_percent"],
                "v2_cv_percent": rows[2]["cv_percent"],
                "v3_cv_percent": rows[3]["cv_percent"],
                "live_cells": rows[0]["live_cells"],
                "checksum": rows[0]["checksum"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"validated_configurations={len(output_rows)}")
    print("four_version_matrix_equivalence=PASS")
    print("four_version_checksum_equivalence=PASS")


if __name__ == "__main__":
    main()
