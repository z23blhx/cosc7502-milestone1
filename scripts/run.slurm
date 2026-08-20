#!/bin/bash
# Exploratory V0 timing only. This is not the final benchmark matrix.
#SBATCH --job-name=life-v0-explore
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
#SBATCH --output=slurm/v0-explore-%j.out

# No memory directive is used. On 2026-08-20, every cosc3500 node reported
# MEMORY=1 MB to Slurm despite substantially larger FREE_MEM values. A 1 GiB
# request therefore remained pending with reason PartitionConfig (job 562428).

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

if [[ ! -x build/benchmark/life ]]; then
    echo "error: build/benchmark/life is missing; run 'make benchmark' on login0 first" >&2
    exit 1
fi

echo "=== V0 EXPLORATORY ENVIRONMENT ==="
date --iso-8601=seconds
hostname
uname -a
echo "git_commit=$(git rev-parse HEAD)"
echo "git_tag=$(git describe --tags --exact-match HEAD 2>/dev/null || echo untagged)"
echo "compiler_flags=-std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -O3 -DNDEBUG"
echo "slurm_memory_request=none (cluster nodes report MEMORY=1 MB)"
echo "slurm_account=cosc3500"
g++ --version
lscpu
scontrol show job "${SLURM_JOB_ID}"

echo "=== V0 EXPLORATORY RESULTS ==="
echo "version,width,height,generations,density,seed,elapsed_seconds,live_cells,checksum"

generations="${GENERATIONS:-100}"
density="${DENSITY:-35}"
seed="${SEED:-12345}"
sizes=(101 256 512 1024 2048 4096)

for size in "${sizes[@]}"; do
    build/benchmark/life \
        --size "${size}" \
        --generations "${generations}" \
        --density "${density}" \
        --seed "${seed}" \
        --csv | tail -n 1
done

echo "=== V0 EXPLORATORY COMPLETE ==="
date --iso-8601=seconds
