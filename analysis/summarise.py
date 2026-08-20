#!/usr/bin/env python3
"""Validate Game of Life benchmark rows and write per-configuration statistics."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


REQUIRED_FIELDS = {
    "version",
    "source_commit",
    "tag",
    "grid_width",
    "grid_height",
    "generations",
    "density",
    "seed",
    "run_number",
    "elapsed_seconds",
    "live_cells",
    "checksum",
    "hostname",
    "job_id",
}

SUMMARY_FIELDS = [
    "version",
    "source_commit",
    "tag",
    "grid_width",
    "grid_height",
    "generations",
    "density",
    "seed",
    "repetitions",
    "mean_seconds",
    "median_seconds",
    "min_seconds",
    "max_seconds",
    "sample_stddev_seconds",
    "cv_percent",
    "live_cells",
    "checksum",
    "hostname",
    "job_id",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="raw benchmark CSV")
    parser.add_argument("output", type=Path, help="summary CSV to create")
    parser.add_argument("--expected-repetitions", type=int, default=5)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing required fields: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("input contains no benchmark rows")
    return rows


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input)
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)

    key_fields = (
        "version",
        "source_commit",
        "tag",
        "grid_width",
        "grid_height",
        "generations",
        "density",
        "seed",
        "hostname",
        "job_id",
    )
    for row in rows:
        if int(row["grid_width"]) != int(row["grid_height"]):
            raise ValueError("formal matrix contains a non-square grid")
        if float(row["elapsed_seconds"]) <= 0:
            raise ValueError("elapsed_seconds must be positive")
        groups[tuple(row[field] for field in key_fields)].append(row)

    summaries: list[dict[str, str | int]] = []
    for key, group in groups.items():
        if len(group) != args.expected_repetitions:
            raise ValueError(
                f"configuration {key} has {len(group)} rows; "
                f"expected {args.expected_repetitions}"
            )
        run_numbers = sorted(int(row["run_number"]) for row in group)
        if run_numbers != list(range(1, args.expected_repetitions + 1)):
            raise ValueError(f"invalid or duplicate run numbers for configuration {key}")
        live_counts = {row["live_cells"] for row in group}
        checksums = {row["checksum"] for row in group}
        if len(live_counts) != 1 or len(checksums) != 1:
            raise ValueError(f"correctness indicators differ for configuration {key}")

        times = [float(row["elapsed_seconds"]) for row in group]
        mean = statistics.fmean(times)
        stddev = statistics.stdev(times)
        first = group[0]
        summaries.append(
            {
                "version": first["version"],
                "source_commit": first["source_commit"],
                "tag": first["tag"],
                "grid_width": first["grid_width"],
                "grid_height": first["grid_height"],
                "generations": first["generations"],
                "density": first["density"],
                "seed": first["seed"],
                "repetitions": len(group),
                "mean_seconds": f"{mean:.9f}",
                "median_seconds": f"{statistics.median(times):.9f}",
                "min_seconds": f"{min(times):.9f}",
                "max_seconds": f"{max(times):.9f}",
                "sample_stddev_seconds": f"{stddev:.9f}",
                "cv_percent": f"{(stddev / mean) * 100.0:.6f}",
                "live_cells": next(iter(live_counts)),
                "checksum": next(iter(checksums)),
                "hostname": first["hostname"],
                "job_id": first["job_id"],
            }
        )

    summaries.sort(key=lambda row: int(str(row["grid_width"])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summaries)

    print(f"validated_rows={len(rows)}")
    print(f"validated_configurations={len(summaries)}")
    print("checksum_consistency=PASS")


if __name__ == "__main__":
    main()
