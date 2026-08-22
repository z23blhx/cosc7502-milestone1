#!/usr/bin/env python3
"""Validate the saved UQ Rangpur evidence and generate presentation plots."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
PLOTS_DIR = ROOT / "analysis" / "plots"
EXPECTED_SIZES = (512, 1024, 2048)


@dataclass(frozen=True)
class Version:
    key: str
    label: str
    result_dir: str
    color: str
    marker: str
    line_style: str


VERSIONS = (
    Version("V0", "V0 Baseline", "v0_baseline", "#59636E", "o", "-"),
    Version("V1", "V1 Precomputed Wrap", "v1_precomputed_wrap", "#2F6B9A", "s", "--"),
    Version("V2", "V2 Contiguous Grid", "v2_contiguous_grid", "#D58A24", "^", "-."),
    Version("V3", "V3 Explicit Neighbours", "v3_explicit_neighbours", "#76874A", "D", ":"),
)


def load_summary(version: Version) -> dict[int, dict[str, str]]:
    path = ROOT / "results" / version.result_dir / "summary.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"no rows found in {path}")
    by_size: dict[int, dict[str, str]] = {}
    for row in rows:
        width = int(row["grid_width"])
        if width in by_size:
            raise ValueError(f"duplicate {width} row in {path}")
        by_size[width] = row
    return by_size


def validate_benchmarks(
    summaries: dict[str, dict[int, dict[str, str]]],
) -> None:
    expected_sizes = set(EXPECTED_SIZES)
    reference = summaries[VERSIONS[0].key]
    comparable_fields = ("grid_width", "grid_height", "generations", "density", "seed", "repetitions")
    correctness_fields = ("live_cells", "checksum")

    for version in VERSIONS:
        rows = summaries[version.key]
        if set(rows) != expected_sizes:
            raise ValueError(
                f"{version.key} grid sizes are {sorted(rows)}, expected {list(EXPECTED_SIZES)}"
            )
        for size in EXPECTED_SIZES:
            row = rows[size]
            if int(row["grid_width"]) != size or int(row["grid_height"]) != size:
                raise ValueError(f"{version.key} does not contain a square {size} x {size} row")
            for field in comparable_fields + correctness_fields:
                if row[field] != reference[size][field]:
                    raise ValueError(
                        f"{field} mismatch at {size}: {version.key}={row[field]}, "
                        f"V0={reference[size][field]}"
                    )


def median(summaries: dict[str, dict[int, dict[str, str]]], key: str, size: int) -> float:
    return float(summaries[key][size]["median_seconds"])


def load_profile(version: Version) -> dict[str, object]:
    path = ROOT / "results" / version.result_dir / "profile.txt"
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line and not line.startswith("version,"):
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()

    program_row: dict[str, str] | None = None
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        if line.startswith("version,width,height,generations,density,seed,"):
            program_row = dict(zip(line.split(","), lines[index + 1].split(",")))
            break
    if program_row is None:
        raise ValueError(f"program output was not found in {path}")

    hotspot = re.search(
        r"^\s*(?P<percent>\d+(?:\.\d+)?)\s+"
        r"\d+(?:\.\d+)?\s+(?P<seconds>\d+(?:\.\d+)?)\s+"
        r"\d+.*Life::live_neighbours\(",
        text,
        flags=re.MULTILINE,
    )
    if hotspot is None:
        raise ValueError(f"Life::live_neighbours self time was not found in {path}")

    return {
        "path": path,
        "metadata": metadata,
        "program": program_row,
        "self_percent": float(hotspot.group("percent")),
        "self_seconds": float(hotspot.group("seconds")),
    }


def validate_profiles(profiles: dict[str, dict[str, object]]) -> None:
    reference = profiles[VERSIONS[0].key]
    ref_metadata = reference["metadata"]
    ref_program = reference["program"]
    assert isinstance(ref_metadata, dict)
    assert isinstance(ref_program, dict)

    for version in VERSIONS:
        profile = profiles[version.key]
        metadata = profile["metadata"]
        program = profile["program"]
        assert isinstance(metadata, dict)
        assert isinstance(program, dict)
        for field in ("hostname", "profile_flags", "profile_workload"):
            if metadata.get(field) != ref_metadata.get(field):
                raise ValueError(
                    f"profile {field} mismatch for {version.key}: "
                    f"{metadata.get(field)!r} != {ref_metadata.get(field)!r}"
                )
        for field in ("width", "height", "generations", "density", "seed", "live_cells", "checksum"):
            if program.get(field) != ref_program.get(field):
                raise ValueError(
                    f"profile {field} mismatch for {version.key}: "
                    f"{program.get(field)!r} != {ref_program.get(field)!r}"
                )


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#39424C",
            "axes.labelcolor": "#252B33",
            "axes.titlecolor": "#1F252C",
            "axes.titlesize": 18,
            "axes.titleweight": "semibold",
            "axes.labelsize": 13,
            "xtick.color": "#39424C",
            "ytick.color": "#39424C",
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "font.family": "DejaVu Sans",
            "legend.fontsize": 10.5,
        }
    )


def finish_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_subtitle(ax: plt.Axes, text: str) -> None:
    ax.text(0.0, 1.01, text, transform=ax.transAxes, fontsize=10.5, color="#59636E", va="bottom")


def add_bar_labels(ax: plt.Axes, bars: Iterable[matplotlib.patches.Patch], values: Iterable[float]) -> None:
    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.2f}×",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="semibold",
            color="#252B33",
        )


def plot_runtime(summaries: dict[str, dict[int, dict[str, str]]]) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    x = list(range(len(EXPECTED_SIZES)))
    for version in VERSIONS:
        values = [median(summaries, version.key, size) for size in EXPECTED_SIZES]
        ax.plot(
            x,
            values,
            label=version.label,
            color=version.color,
            marker=version.marker,
            linestyle=version.line_style,
            linewidth=2.4,
            markersize=7,
            markeredgecolor="white",
            markeredgewidth=0.8,
        )
    ax.set_title("Game of Life Runtime on UQ Rangpur", loc="left", pad=26)
    add_subtitle(ax, "Median of 5 runs; 800 generations, density 35%, seed 12345")
    ax.set_xlabel("Grid Size (N × N)")
    ax.set_ylabel("Median Runtime (seconds)")
    ax.set_xticks(x, [f"{size} × {size}" for size in EXPECTED_SIZES])
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color="#DCE1E6", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False)
    path = PLOTS_DIR / "runtime_vs_grid_size.png"
    finish_figure(fig, path)
    return path


def plot_cumulative_speedup(
    summaries: dict[str, dict[int, dict[str, str]]], cumulative: dict[str, float]
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [version.key for version in VERSIONS]
    values = [cumulative[version.key] for version in VERSIONS]
    bars = ax.bar(
        labels,
        values,
        color=[version.color for version in VERSIONS],
        edgecolor="#39424C",
        linewidth=0.8,
        width=0.62,
    )
    add_bar_labels(ax, bars, values)
    ax.set_title("Cumulative Serial Optimisation Speedup\n2048 × 2048 Grid", loc="left", pad=14)
    add_subtitle(ax, "Median runtime relative to V0; higher is better")
    ax.set_xlabel("Version")
    ax.set_ylabel("Speedup Relative to V0")
    ax.set_ylim(0, max(values) * 1.22)
    ax.grid(axis="y", color="#DCE1E6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    path = PLOTS_DIR / "speedup_vs_version.png"
    finish_figure(fig, path)
    return path


def plot_incremental_speedup(incremental: dict[str, float]) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = list(incremental)
    values = list(incremental.values())
    bars = ax.bar(
        labels,
        values,
        color=["#2F6B9A", "#77A4C4", "#B6CEDF"],
        edgecolor="#2A536F",
        linewidth=0.8,
        width=0.58,
    )
    add_bar_labels(ax, bars, values)
    ax.axhline(1.0, color="#59636E", linewidth=1.0, linestyle="--")
    ax.set_title("Incremental Speedup by Optimisation Stage", loc="left", pad=26)
    add_subtitle(ax, "2048 × 2048 median runtime; previous version ÷ new version")
    ax.set_xlabel("Optimisation Stage")
    ax.set_ylabel("Incremental Speedup")
    ax.set_ylim(0, max(values) * 1.2)
    ax.grid(axis="y", color="#DCE1E6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    path = PLOTS_DIR / "incremental_speedup.png"
    finish_figure(fig, path)
    return path


def plot_profile(profiles: dict[str, dict[str, object]]) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [version.key for version in VERSIONS]
    values = [float(profiles[version.key]["self_seconds"]) for version in VERSIONS]
    bars = ax.bar(
        labels,
        values,
        color=[version.color for version in VERSIONS],
        edgecolor="#39424C",
        linewidth=0.8,
        width=0.62,
    )
    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.2f} s",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="semibold",
            color="#252B33",
        )
    ax.set_title("Life::live_neighbours Sampled Self Time", loc="left", pad=26)
    add_subtitle(ax, "gprof; 2048 × 2048, 1000 generations, -O2 -g -pg")
    ax.set_xlabel("Version")
    ax.set_ylabel("Absolute Sampled Self Time (seconds)")
    ax.set_ylim(0, max(values) * 1.16)
    ax.grid(axis="y", color="#DCE1E6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    path = PLOTS_DIR / "live_neighbours_profile.png"
    finish_figure(fig, path)
    return path


def main() -> None:
    configure_style()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    summaries = {version.key: load_summary(version) for version in VERSIONS}
    validate_benchmarks(summaries)

    size = 2048
    medians = {version.key: median(summaries, version.key, size) for version in VERSIONS}
    cumulative = {key: medians["V0"] / value for key, value in medians.items()}
    incremental = {
        "V0 → V1": medians["V0"] / medians["V1"],
        "V1 → V2": medians["V1"] / medians["V2"],
        "V2 → V3": medians["V2"] / medians["V3"],
    }

    generated = [
        plot_runtime(summaries),
        plot_cumulative_speedup(summaries, cumulative),
        plot_incremental_speedup(incremental),
    ]

    profile_note = ""
    try:
        profiles = {version.key: load_profile(version) for version in VERSIONS}
        validate_profiles(profiles)
        generated.append(plot_profile(profiles))
    except (FileNotFoundError, ValueError) as error:
        profile_note = f"Profiling plot skipped: {error}"

    print("Benchmark validation: PASS")
    print("Correctness equivalence: PASS")
    print("\n2048x2048 medians:")
    for version in VERSIONS:
        print(f"{version.key}: {medians[version.key]:.9f} s")
    print("\nCumulative speedup:")
    for version in VERSIONS[1:]:
        print(f"{version.key}: {cumulative[version.key]:.6f}x")
    print("\nIncremental speedup:")
    for stage, speedup in incremental.items():
        print(f"{stage}: {speedup:.6f}x")
    if profile_note:
        print(f"\n{profile_note}")
    else:
        print("\nProfiling comparability: PASS")
    print("\nGenerated:")
    for path in generated:
        print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
