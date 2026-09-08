#!/usr/bin/env bash
# Sequential Linux validation; never resumes an inconclusive research search.
set -euo pipefail
if [[ ${1:-} == --help ]]; then
  printf '%s\n' 'Usage: bash research/unit-step/tracks/check_uniform_checkpoint.sh [STATE_DIR]' \
    'Default: .checkpoint-uniform-certificate-validation (relative to repository root).' \
    'Pins all checks and subprocesses to one available CPU; requires taskset and setsid.' \
    'Validators resume identity/checksum-checked rows; bounded regressions rerun.' \
    'SIGINT/SIGTERM forward to the active process group so validators can checkpoint.' \
    'Logs and regenerated validation summaries stay in STATE_DIR, not proof artifacts.' \
    'Use a fresh directory after incompatible code changes. This does not prove either minimum.'
  exit 0
fi
[[ $# -le 1 ]] || { printf 'Expected at most one state directory\n' >&2; exit 2; }
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
command -v taskset >/dev/null
command -v setsid >/dev/null
allowed=$(awk '/Cpus_allowed_list/ {print $2}' /proc/self/status)
cpu=${allowed%%[,-]*}
taskset -pc "$cpu" "$$" >/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
state=${1:-.checkpoint-uniform-certificate-validation}
mkdir -p "$state"
state=$(cd "$state" && pwd)
log=$state/run.log
track=research/unit-step/tracks
step=0
total=21
child=''
started=$SECONDS
event() { printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$log"; }
stop() {
  trap - INT TERM
  if [[ -n $child ]]; then
    kill -TERM -- "-$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
  fi
  event "INTERRUPTED step=$step/$total elapsed=$((SECONDS-started))s state=$state"
  exit 130
}
trap stop INT TERM
run() {
  step=$((step+1))
  event "START step=$step/$total elapsed=$((SECONDS-started))s command=$*"
  setsid "$@" >> "$log" 2>&1 & child=$!
  if wait "$child"; then
    child=''
    event "PASS step=$step/$total elapsed=$((SECONDS-started))s"
  else
    status=$?
    child=''
    event "FAIL step=$step/$total exit=$status elapsed=$((SECONDS-started))s log=$log"
    exit "$status"
  fi
}
event "CONFIG head=$(git rev-parse HEAD) runner_sha=$(sha256sum "$track/check_uniform_checkpoint.sh" | cut -d' ' -f1) cpu=$cpu native_threads=1 state=$state"
run node "$track/check_shallit_ratio_automaton.mjs" --state-dir "$state/ratio" --output "$state/ratio.json"
run cmp "$state/ratio.json" "$track/checks/shallit-ratio-validation.json"
run node "$track/check_shallit_interval.mjs"
run node "$track/verify_shallit_midpoint.mjs" --state-dir "$state/midpoint" --output "$state/midpoint.json"
run cmp "$state/midpoint.json" "$track/checks/shallit-midpoint-validation.json"
run node "$track/verify_shallit_interval_extension.mjs" --seconds 600 --state-dir "$state/extension" --output "$state/extension.json"
run cmp "$state/extension.json" "$track/checks/shallit-extension-100-validation.json"
run node "$track/verify_shallit_centered_returns.mjs" --state-dir "$state/centered" --output "$state/centered.json"
run cmp "$state/centered.json" "$track/checks/shallit-centered-validation.json"
run node "$track/test_shallit_ratio_cli.mjs"
run node "$track/test_shallit_interval_cli.mjs"
run node "$track/test_shallit_extension.mjs"
run node "$track/test_shallit_centered.mjs"
run node "$track/four_return_blocks.mjs" --state-dir "$state/four-return"
run node "$track/test_four_return_blocks_cli.mjs"
run node "$track/check_contradiction_obstructions.mjs"
run node research/unit-step/explorations/descent-algebra-check.mjs
run node research/unit-step/check.mjs
run node research/unit-step/joint_minimum_examples.mjs
run node design/unit-step-explainer/test.mjs
run git diff --check
event "COMPLETE steps=$step/$total elapsed=$((SECONDS-started))s; no new minimum bound"
