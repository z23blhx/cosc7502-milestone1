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

## V1 - precomputed wrapped indices

- **Controlled change:** Added four constructor-initialised lookup arrays for
  previous/next x and y coordinates. The existing nested neighbour loop reuses
  these indices. The two-dimensional byte grid, two-buffer update, rule logic,
  traversal, interface, benchmark matrix, and compiler flags remain unchanged.
- **Hypothesis:** Removing repeated wrapped-coordinate calculations from the V0
  neighbour hotspot will reduce inner-loop instruction overhead. This does not
  predict a cache or memory-bandwidth improvement.
- **Tag and source commit:** `v1_precomputed_wrap` at
  `b6f45e2596b0babb0565697c7250c3ab039f4511`.
- **Correctness:** Six tests passed locally and on Rangpur. Five additional
  deterministic V0/V1 comparisons passed locally. All 15 formal V1 rows match
  the corresponding V0 live-cell count and checksum.
- **Formal benchmark:** Slurm Job 562440 ran on `a100-0` with the identical V0
  matrix and resources: 512/1024/2048 square grids, 800 generations, density
  35%, seed 12345, five repetitions, one node/task/CPU, GCC 8.5.0, and
  `-O3 -DNDEBUG` plus the common warning flags.
- **Results:** Median V1 runtimes were 1.276579850 s, 5.069925500 s, and
  20.354371500 s. The respective V0-to-V1 speedups were 4.465737x, 4.490008x,
  and 4.463521x; runtime reductions were 77.607278%, 77.728327%, and
  77.596164%. V1 CVs were 0.279608%, 0.126138%, and 0.093286%.
- **Profiling:** gprof Job 562441 used the matching V0 diagnostic workload and
  `-O2 -g -pg` flags. `Life::live_neighbours` fell from 96.61% of V0 sampled
  self time to 75.02% in V1, while `Life::step` rose from 3.54% to 22.94%.
  The profile-build wall time fell from 207.768831 s to 92.7033395 s. These
  profile figures diagnose hotspot movement; formal speedup uses the `-O3` data.
- **Interpretation:** The 4.46-4.49x improvement is consistent across problem
  sizes and far exceeds run-to-run variation. This supports the experiment's
  combined precomputed-index hypothesis while preserving observable results.
  It does not isolate one machine instruction or attribute the entire gain to
  modulo alone.
- **Decision:** Retained as `v1_precomputed_wrap`.
- **Candidate V2 only:** Replace separately allocated two-dimensional rows with
  one contiguous one-dimensional byte buffer while keeping V1's precomputed
  indices and all other logic fixed. This targets row-indirection and locality
  in the remaining neighbour/step hotspot. Validate with the same checksums and
  formal matrix before retention. V2 is not implemented in this milestone step.

## V2 - contiguous row-major grid

- **Controlled change:** Replaced both `vector<vector<uint8_t>>` grids with
  single `vector<uint8_t>` buffers using `y * width + x` row-major indexing.
  V1's four wrapped-index arrays, nested neighbour loops, rule, double buffer,
  cell type, traversal, interface, benchmark matrix, and flags were retained.
- **Hypothesis:** One contiguous allocation may reduce row indirection and make
  sequential access more locality/compiler friendly. Cache improvement is not
  assumed without measurement.
- **Tag and source commit:** `v2_contiguous_grid` at
  `eb599a441f759ace2fd3a693e51baf73dc568321`.
- **Correctness:** Six tests passed locally and on Rangpur. Five deterministic
  V0/V1/V2 comparisons passed. All 15 formal V2 rows match V0 and V1 live-cell
  counts and checksums.
- **UQ environment and matrix:** Slurm Job 562443 ran on `a100-0`, partition and
  account `cosc3500`, QOS `normal`, one node/task/CPU, GCC 8.5.0, and the same
  `-O3 -DNDEBUG` flags. Sizes were 512/1024/2048, with 800 generations,
  density 35%, seed 12345, and five repetitions.
- **Medians:** 1.063583010 s, 4.206093940 s, and 16.924774400 s for 512, 1024,
  and 2048 respectively.
- **Speedup vs V0:** 5.360061x, 5.412149x, and 5.367999x, corresponding to
  runtime reductions of 81.343494%, 81.523052%, and 81.371084%.
- **Incremental speedup vs V1:** 1.200263x, 1.205376x, and 1.202638x,
  corresponding to reductions of 16.684960%, 17.038348%, and 16.849437%.
- **Variability:** V2 CVs were 0.421498%, 0.035717%, and 0.053105%.
- **Profiling:** gprof Job 562444 used the matching `-O2 -g -pg` diagnostic
  workload. `Life::live_neighbours` represented 82.38% and 31.09 sampled self
  seconds; `Life::step` represented 14.42% and 5.44 s. Both absolute sampled
  self times fell from V1's 40.96 s and 12.52 s. Profile-build wall time fell
  from 92.7033395 s in V1 to 72.447904 s in V2. Formal speedup uses `-O3` data.
- **Interpretation:** The roughly 1.20x incremental improvement is consistent
  across sizes and larger than run-to-run variation. It is consistent with the
  controlled contiguous-storage hypothesis, but does not independently prove a
  cache mechanism.
- **Decision:** Retained as `v2_contiguous_grid`.
- **Candidate V3 only:** Explicitly sum the eight neighbour cells instead of
  executing the current nested `dx`/`dy` loops and center-skip branch, while
  retaining V2 storage, precomputed indices, rule, and all other controls. V2
  profiling still attributes 82.38% of sampled self time to 4,194,304,000
  `live_neighbours` calls, so removing loop/index/branch overhead directly
  targets measured remaining work. V3 is not implemented here.
