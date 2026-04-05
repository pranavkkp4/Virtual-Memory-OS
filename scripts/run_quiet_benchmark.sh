#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
RESULTS_DIR="${RESULTS_DIR:-results}"
BENCHMARK_ARGS=("$@")
if [ "${#BENCHMARK_ARGS[@]}" -eq 0 ]; then
  BENCHMARK_ARGS=("--experiment" "all")
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
METADATA_DIR="${REPO_ROOT}/${RESULTS_DIR}/metadata"
mkdir -p "${METADATA_DIR}"

timestamp="$(date +%Y%m%d_%H%M%S_%3N)"
run_id="${timestamp}_$$"
metadata_path="${METADATA_DIR}/run_environment_${run_id}.json"
output_path="${METADATA_DIR}/run_output_${run_id}.log"

python_version="$(${PYTHON_BIN} --version 2>&1 | tr -d '\n')"
git_commit="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || true)"
hostname="$(hostname 2>/dev/null || true)"
os_name="$(uname -s 2>/dev/null || true)"
cpu_model="$(grep -m 1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | xargs || true)"
ram_gb="$(awk '/MemTotal/ {printf "%.2f", $2 / 1024 / 1024}' /proc/meminfo 2>/dev/null || true)"

benchmark_args_json="$(python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "${BENCHMARK_ARGS[@]}")"
command_json="$(python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "${PYTHON_BIN}" "experiments/run_all_experiments.py" "${BENCHMARK_ARGS[@]}")"

cat > "${metadata_path}" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "mode": "quiet",
  "repo_root": "${REPO_ROOT}",
  "results_dir": "${REPO_ROOT}/${RESULTS_DIR}",
  "host": {
    "hostname": "${hostname}",
    "os": "${os_name}",
    "cpu": "${cpu_model}",
    "memory_gb": "${ram_gb}"
  },
  "python_executable": "${PYTHON_BIN}",
  "python_version": "${python_version}",
  "git_commit": "${git_commit}",
  "process_priority": "below_normal",
  "benchmark_args": ${benchmark_args_json},
  "command": ${command_json}
}
EOF

if command -v nice >/dev/null 2>&1; then
  if command -v ionice >/dev/null 2>&1; then
    ionice -c2 -n7 nice -n 10 "${PYTHON_BIN}" "${REPO_ROOT}/experiments/run_all_experiments.py" "${BENCHMARK_ARGS[@]}" >"${output_path}" 2>&1
  else
    nice -n 10 "${PYTHON_BIN}" "${REPO_ROOT}/experiments/run_all_experiments.py" "${BENCHMARK_ARGS[@]}" >"${output_path}" 2>&1
  fi
else
  "${PYTHON_BIN}" "${REPO_ROOT}/experiments/run_all_experiments.py" "${BENCHMARK_ARGS[@]}" >"${output_path}" 2>&1
fi

echo "Quiet benchmark complete."
echo "Metadata: ${metadata_path}"
echo "Log: ${output_path}"
