#!/bin/bash
# Formal V2 matrix: identical to the completed V0 and V1 benchmarks.
#SBATCH --job-name=life-v2-grid
#SBATCH --partition=cosc3500
#SBATCH --account=cosc3500
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%j.out

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

if [[ ! -x build/benchmark/life ]]; then
    echo "error: build/benchmark/life is missing; run 'make benchmark' on login0 first" >&2
    exit 1
fi
if ! git diff --quiet v2_contiguous_grid -- src tests; then
    echo "error: src/tests differ from the frozen v2_contiguous_grid tag" >&2
    exit 1
fi
if [[ ! -f results/v0_baseline/raw.csv ]]; then
    echo "error: V0 raw.csv is required for checksum equivalence checks" >&2
    exit 1
fi
if [[ ! -f results/v1_precomputed_wrap/raw.csv ]]; then
    echo "error: V1 raw.csv is required for checksum equivalence checks" >&2
    exit 1
fi

result_dir="results/v2_contiguous_grid"
raw_file="${result_dir}/raw-${SLURM_JOB_ID}.csv"
environment_file="${result_dir}/environment-${SLURM_JOB_ID}.txt"
mkdir -p "${result_dir}"

source_commit="$(git rev-list -n 1 v2_contiguous_grid)"
evidence_commit="$(git rev-parse HEAD)"
compute_hostname="$(hostname)"
compiler_version="$(g++ -dumpfullversion -dumpversion)"
compiler_flags="-std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -O3 -DNDEBUG"
generations=800
density=35
seed=12345
repetitions=5
sizes=(512 1024 2048)

{
    echo "benchmark_start=$(date --iso-8601=seconds)"
    echo "hostname=${compute_hostname}"
    echo "uname=$(uname -a)"
    echo "source_commit=${source_commit}"
    echo "source_tag=v2_contiguous_grid"
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
    /opt/slurm/bin/scontrol show job "${SLURM_JOB_ID}"
} > "${environment_file}"

header="timestamp,version,source_commit,tag,evidence_commit,grid_width,grid_height,generations,density,seed,run_number,elapsed_seconds,live_cells,checksum,hostname,job_id,compiler,compiler_version,compiler_flags"
echo "${header}" > "${raw_file}"
echo "=== V2 CONTIGUOUS-GRID FORMAL BENCHMARK ==="
echo "raw_file=${raw_file}"
echo "environment_file=${environment_file}"
echo "${header}"

for size in "${sizes[@]}"; do
    v0_correctness="$(awk -F',' -v target_size="${size}" \
        'NR > 1 && $6 == target_size {print $13 "," $14; exit}' \
        results/v0_baseline/raw.csv)"
    if [[ -z "${v0_correctness}" ]]; then
        echo "error: no V0 correctness row found for size ${size}" >&2
        exit 1
    fi
    IFS=',' read -r v0_live v0_checksum <<< "${v0_correctness}"
    v1_correctness="$(awk -F',' -v target_size="${size}" \
        'NR > 1 && $6 == target_size {print $13 "," $14; exit}' \
        results/v1_precomputed_wrap/raw.csv)"
    if [[ -z "${v1_correctness}" ]]; then
        echo "error: no V1 correctness row found for size ${size}" >&2
        exit 1
    fi
    IFS=',' read -r v1_live v1_checksum <<< "${v1_correctness}"
    if [[ "${v0_live}" != "${v1_live}" || "${v0_checksum}" != "${v1_checksum}" ]]; then
        echo "error: V0 and V1 correctness references differ for size ${size}" >&2
        exit 1
    fi

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

        if [[ "${version}" != "v2_contiguous_grid" ]]; then
            echo "error: executable reported unexpected version ${version}" >&2
            exit 1
        fi
        if [[ "${live_cells}" != "${v0_live}" || "${checksum}" != "${v0_checksum}" ]]; then
            echo "error: V2 differs from V0/V1 correctness output for size ${size}" >&2
            exit 1
        fi
        if [[ "${run_number}" -eq 1 ]]; then
            expected_live="${live_cells}"
            expected_checksum="${checksum}"
        elif [[ "${live_cells}" != "${expected_live}" || "${checksum}" != "${expected_checksum}" ]]; then
            echo "error: V2 correctness mismatch for size ${size}, run ${run_number}" >&2
            exit 1
        fi

        row="$(date --iso-8601=seconds),${version},${source_commit},v2_contiguous_grid,${evidence_commit},${width},${height},${actual_generations},${actual_density},${actual_seed},${run_number},${elapsed},${live_cells},${checksum},${compute_hostname},${SLURM_JOB_ID},g++,${compiler_version},${compiler_flags}"
        echo "${row}" | tee -a "${raw_file}"
    done
done

echo "benchmark_end=$(date --iso-8601=seconds)" >> "${environment_file}"
echo "=== V2 CONTIGUOUS-GRID BENCHMARK COMPLETE ==="
