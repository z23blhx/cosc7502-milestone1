# Optimisation Log

## V0 - readable serial baseline

- **Change:** Initial serial implementation using a two-dimensional byte grid,
  a second output grid, simple nested neighbour loops, and modulo-based wrapping.
- **Hypothesis:** This design prioritises correctness and traceability. It is
  expected to be slower than later layouts because rows are separately allocated
  and wrapping performs repeated index/modulo work in the inner loop.
- **HPC concepts:** Baseline measurement, memory layout, spatial locality,
  instruction overhead, and reproducibility.
- **Correctness:** Six deterministic tests cover a still life, oscillator,
  glider, wrapping on both axes, and seeded random initialisation. Tests passed
  locally and on Rangpur. All five formal repetitions per size had identical
  live-cell counts and checksums.
- **Tag and source commit:** `v0_baseline` at
  `15e13cd499178bc80740b710912679aef8c2f037`.
- **UQ environment:** Rangpur `cosc3500` partition, compute node `a100-0`, one
  node/task/CPU, AMD EPYC 7542 virtualised node, GCC 8.5.0, benchmark flags
  `-O3 -DNDEBUG` plus the common C++17 warning flags.
- **Benchmark matrix:** Square sizes 512, 1024, and 2048; 800 generations;
  density 35%; seed 12345; five repetitions per size (Slurm Job 562436).
- **Benchmark result:** Median runtimes were 5.700869360 s (512),
  22.764008200 s (1024), and 90.852169800 s (2048). Coefficients of variation
  were below 0.1% for all sizes. See `results/v0_baseline/raw.csv`,
  `summary.csv`, and `environment.txt`.
- **Profiling:** gprof Job 562437 used `-O2 -g -pg` with a 2048 x 2048 grid for
  1000 generations. `Life::live_neighbours` accounted for 96.61% of sampled
  self time across 4,194,304,000 calls; `Life::step` accounted for 3.54%.
  See `results/v0_baseline/profile.txt`.
- **Measured bottleneck:** Neighbour calculation is the dominant hotspot.
- **Hypothesised cause:** The current hot loop repeatedly performs wrapped
  index/modulo calculations and two-dimensional row lookups. gprof does not
  isolate the cost of modulo because `-O2` may inline `wrap`, so this remains a
  hypothesis to test rather than a measured sub-component claim.
- **Speedup:** N/A (trusted reference version).
- **Interpretation:** This version provides a clear correctness oracle and the
  denominator for later speedup calculations.
- **Candidate V1:** Precompute previous/next wrapped indices for each coordinate
  and reuse them in neighbour calculation while retaining the two-dimensional
  grid and rule logic. This directly targets the 96.61% hotspot and isolates
  removal of repeated modulo/index work as one measurable change. Trade-offs
  are small lookup arrays and slightly more setup complexity. V1 must reproduce
  V0 checksums and use the identical formal matrix.
- **Decision:** Retained as `v0_baseline`.
