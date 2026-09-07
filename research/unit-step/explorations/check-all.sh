#!/usr/bin/env bash
# Sequential bounded validation. Checkpointed checkers reuse completed work;
# the tiny algebra/indexing checks safely rerun. Logs are not proof artifacts.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
track=research/unit-step/explorations
run=".checkpoint-s-star-validation/$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$run" .checkpoint-return-blocks
completed=0
total=13
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$run/progress.log"; }
trap 'log "interrupted completed=$completed/$total; rerun this script to resume validated calculation checkpoints"; exit 130' INT TERM
trap 'rc=$?; if ((rc != 0)); then log "error exit=$rc completed=$completed/$total logs=$run"; fi' EXIT
log "start completed=0/$total parallel_jobs=1 native_threads=1 ETA=30-60s logs=$run resume=validated-checker-units"
sha256sum "$track"/*.mjs "$track"/*.cpp "$track/check-all.sh" > "$run/code.sha256"
check() {
  local name=$1; shift
  log "running=$name completed=$completed/$total"
  "$@" > "$run/$name.tmp" 2>&1
  mv "$run/$name.tmp" "$run/$name.log"
  completed=$((completed+1))
  log "pass=$name completed=$completed/$total"
}
node_one() { node --single-threaded --v8-pool-size=1 "$@"; }
check gaussian node_one "$track/gaussian-tags-check.mjs"
check selectors node_one "$track/return-blocks-check.mjs"
check gap-js node_one --max-old-space-size=256 "$track/return-blocks-gap-check.mjs" 16 512
src="$track/return-blocks-gap-verify.cpp"
log 'compiling independent C++ validator (one compiler job)'
g++ -O2 -std=c++17 -Wall -Wextra -pedantic \
  -DSOURCE_SHA=\"$(sha256sum "$src" | cut -d' ' -f1)\" "$src" -o "$run/gap-verify"
check gap-cpp "$run/gap-verify" 16 512
check universal-five node_one "$track/universal-five-check.mjs" .checkpoint-s-star-validation/universal-five
check arithmetic node_one "$track/new-arithmetic-check.mjs"
check words node_one "$track/new-words-check.mjs"
check geometry node_one "$track/check_three_d_geometry.mjs"
check descent-algebra node_one "$track/descent-algebra-check.mjs"
check descent-automata node_one "$track/descent-automata-check.mjs"
check descent-adversary node_one --max-old-space-size=128 "$track/descent-adversary-check.mjs"
check descent-block-selectors node_one "$track/descent-adversary-block-selector.mjs"
check descent-five-menu-independent node_one "$track/descent-five-menu-verify.mjs"
log "complete outcome=all-$total-checkers-pass; restricted research evidence, not an exact-minimum theorem"
