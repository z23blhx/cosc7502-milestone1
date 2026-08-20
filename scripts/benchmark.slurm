#!/bin/bash
# Formal V0 matrix selected from exploratory job 562431.
#SBATCH --job-name=life-v0-benchmark
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:20:00
#SBATCH --output=slurm-%j.out

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

if [[ ! -x build/benchmark/life ]]; then
    echo "error: build/benchmark/life is missing; run 'make benchmark' on login0 first" >&2
    exit 1
fi
if ! git diff --quiet v0_baseline -- src tests; then
    echo "error: src/tests differ from the frozen v0_baseline tag" >&2
    exit 1
fi

result_dir="results/v0_baseline"
raw_file="${result_dir}/raw-${SLURM_JOB_ID}.csv"
environment_file="${result_dir}/environment-${SLURM_JOB_ID}.txt"
mkdir -p "${result_dir}"

source_commit="$(git rev-list -n 1 v0_baseline)"
evidence_commit="$(git rev-parse HEAD)"
compute_hostname="$(hostname)"
compiler_version="$(g++ -dumpfullversion -dumpversion)"
compiler_flags="-std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -O3 -DNDEBUG"
generations=1000
density=35
seed=12345
repetitions=5
sizes=(512 1024 2048)

{
    echo "benchmark_start=$(date --iso-8601=seconds)"
    echo "hostname=${compute_hostname}"
    echo "uname=$(uname -a)"
    echo "source_commit=${source_commit}"
    echo "source_tag=v0_baseline"
    echo "evidence_commit=${evidence_commit}"
    echo "compiler=/usr/bin/g++"
    echo "compiler_version=${compiler_version}"
    echo "compiler_flags=${compiler_flags}"
    echo "executable_sha256=$(sha256sum build/benchmark/life | awk '{print $1}')"
    echo "matrix_sizes=512,1024,2048"
    echo "generations=${generations}"
    echo "density=${density}"
    echo "seed=${seed}"
    echo "repetitions=${repetitions}"
    echo "slurm_partition=cosc3500"
    echo "slurm_account=cosc3500"
    echo "slurm_qos=${SLURM_JOB_QOS:-normal}"
    echo "slurm_nodes=${SLURM_JOB_NUM_NODES}"
    echo "slurm_cpus_per_task=${SLURM_CPUS_PER_TASK}"
    echo "slurm_memory_request=none"
    echo
    g++ --version
    echo
    lscpu
    echo
    scontrol show job "${SLURM_JOB_ID}"
} > "${environment_file}"

header="timestamp,version,source_commit,tag,evidence_commit,grid_width,grid_height,generations,density,seed,run_number,elapsed_seconds,live_cells,checksum,hostname,job_id,compiler,compiler_version,compiler_flags"
echo "${header}" > "${raw_file}"
echo "=== V0 FORMAL BENCHMARK ==="
echo "raw_file=${raw_file}"
echo "environment_file=${environment_file}"
echo "${header}"

for size in "${sizes[@]}"; do
    expected_live=""
    expected_checksum=""
    for ((run_number = 1; run_number <= repetitions; ++run_number)); do
        result="$(build/benchmark/life \
            --size "${size}" \
            --generations "${generations}" \
            --density "${density}" \
            --seed "${seed}" \
            --csv | tail -n 1)"

        IFS=',' read -r version width height actual_generations actual_density actual_seed \
            elapsed live_cells checksum <<< "${result}"

        if [[ "${run_number}" -eq 1 ]]; then
            expected_live="${live_cells}"
            expected_checksum="${checksum}"
        elif [[ "${live_cells}" != "${expected_live}" || "${checksum}" != "${expected_checksum}" ]]; then
            echo "error: correctness mismatch for size ${size}, run ${run_number}" >&2
            exit 1
        fi

        row="$(date --iso-8601=seconds),${version},${source_commit},v0_baseline,${evidence_commit},${width},${height},${actual_generations},${actual_density},${actual_seed},${run_number},${elapsed},${live_cells},${checksum},${compute_hostname},${SLURM_JOB_ID},g++,${compiler_version},${compiler_flags}"
        echo "${row}" | tee -a "${raw_file}"
    done
done

echo "benchmark_end=$(date --iso-8601=seconds)" >> "${environment_file}"
echo "=== V0 FORMAL BENCHMARK COMPLETE ==="
