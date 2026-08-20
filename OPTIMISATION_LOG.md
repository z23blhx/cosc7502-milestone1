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
  glider, wrapping on both axes, and seeded random initialisation.
- **Benchmark result:** Not measured in Phase 1. Formal results must be collected
  on a Rangpur compute node in a later phase.
- **Speedup:** N/A (trusted reference version).
- **Interpretation:** This version provides a clear correctness oracle and the
  denominator for later speedup calculations.
- **Decision:** Retained as `v0_baseline`.
