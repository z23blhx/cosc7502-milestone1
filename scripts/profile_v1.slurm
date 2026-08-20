#!/bin/bash
# V1 gprof diagnostic, matching the V0 profile workload and build flags.
#SBATCH --job-name=life-v1-profile
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

if [[ ! -x build/profile/life ]]; then
    echo "error: build/profile/life is missing; run 'make profile' on login0 first" >&2
    exit 1
fi
if ! git diff --quiet v1_precomputed_wrap -- src tests; then
    echo "error: src/tests differ from the frozen v1_precomputed_wrap tag" >&2
    exit 1
fi

result_dir="results/v1_precomputed_wrap"
work_dir="work/profile-v1-${SLURM_JOB_ID}"
profile_file="${result_dir}/profile-${SLURM_JOB_ID}.txt"
mkdir -p "${result_dir}" "${work_dir}"

source_commit="$(git rev-list -n 1 v1_precomputed_wrap)"
evidence_commit="$(git rev-parse HEAD)"
executable="${SLURM_SUBMIT_DIR}/build/profile/life"

cd "${work_dir}"
run_output="$("${executable}" --size 2048 --generations 1000 --density 35 --seed 12345 --csv)"
gprof "${executable}" gmon.out > gprof-report.txt

{
    echo "V1 PRECOMPUTED-WRAP GPROF PROFILE"
    echo "profile_date=$(date --iso-8601=seconds)"
    echo "hostname=$(hostname)"
    echo "job_id=${SLURM_JOB_ID}"
    echo "source_commit=${source_commit}"
    echo "source_tag=v1_precomputed_wrap"
    echo "evidence_commit=${evidence_commit}"
    echo "profile_flags=-std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -O2 -g -pg"
    echo "profile_workload=2048x2048,1000 generations,density 35,seed 12345"
    echo
    echo "PROGRAM OUTPUT"
    echo "${run_output}"
    echo
    echo "GPROF REPORT"
    cat gprof-report.txt
} > "${SLURM_SUBMIT_DIR}/${profile_file}"

echo "profile_file=${profile_file}"
echo "${run_output}"
echo "=== V1 PRECOMPUTED-WRAP PROFILE COMPLETE ==="
