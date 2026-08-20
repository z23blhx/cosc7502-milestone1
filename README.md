# COSC7502 Milestone 1 - Serial Conway's Game of Life

This project implements a readable serial V0 baseline of Conway's Game of Life,
matching the supplied NetLogo model:

- synchronous two-buffer updates;
- an eight-cell Moore neighbourhood;
- toroidal wrapping in both axes;
- configurable dimensions, generations, density, and seed;
- deterministic live-cell count and final-state checksum.

## Build and test

On Windows with MinGW:

```powershell
mingw32-make test
```

On Rangpur/Linux (later phases):

```bash
make test
```

The debug build is used by the correctness tests. A benchmark build with
explicit `-O3 -DNDEBUG` flags is available, but no formal performance results
are claimed in Phase 1:

```powershell
mingw32-make clean
mingw32-make benchmark
```

The configurations use separate output directories, so a debug executable
cannot accidentally be mistaken for the benchmark executable.

## Run

```powershell
.\build\debug\life.exe --size 101 --generations 1000 --density 35 --seed 12345
```

After `mingw32-make benchmark`, use `.\build\benchmark\life.exe` with the same
arguments.

For machine-readable output, add `--csv`. Run `--help` for all options.

Only generation updates are timed. Random initialisation, result checks, and
console output are outside the timed region.

## Correctness tests

`tests/test_life.cpp` covers:

1. block still life;
2. blinker oscillator;
3. glider motion;
4. wrapping across the left/right boundary;
5. wrapping across the top/bottom boundary;
6. deterministic random setup.

The V0 implementation intentionally favours clarity. It uses a two-dimensional
`vector<vector<uint8_t>>` and modulo-based wrapping in the hot loop. Potential
optimisations must remain separate, checksum-equivalent experiments in later
phases.
