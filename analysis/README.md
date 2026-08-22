# Benchmark plots

`plot_results.py` reads the saved V0–V3 benchmark summaries, verifies that the
workloads and final simulation results are comparable, calculates speedups, and
generates 300 DPI presentation figures in `analysis/plots/`.

The script also creates the profiling figure only when all four saved gprof
records have matching workload and build settings. It uses absolute sampled
self time rather than hotspot percentages.

## Regenerate

From the repository root, run:

```sh
python analysis/plot_results.py
```

The source benchmark and profiling data was collected on UQ Rangpur. This
script reads the preserved evidence and does not run any new benchmarks or
modify the result CSV files.

## Figure guide

| Figure | Question answered | Form |
| --- | --- | --- |
| `runtime_vs_grid_size.png` | How does median runtime scale across V0–V3? | Multi-series line with marker and line-style distinctions |
| `speedup_vs_version.png` | What cumulative speedup does each version achieve at 2048 × 2048? | Zero-based bar chart with direct labels |
| `incremental_speedup.png` | How much does each individual optimisation stage add? | Zero-based bar chart with a 1× reference line |
| `live_neighbours_profile.png` | How did absolute neighbour-count self time change? | Zero-based bar chart using comparable gprof records |
