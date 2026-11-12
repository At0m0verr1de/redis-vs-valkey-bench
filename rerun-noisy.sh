#!/usr/bin/env bash
# Waits for run-all.sh, re-runs the phase-A groups hit by the 16:20-16:44 and
# 17:13-17:23 UTC host-load spikes (load up to 440 / 229 on 96 vCPUs) with a
# load gate, then re-analyses.
set -euo pipefail
cd "$(dirname "$0")"

# Anchor on the interpreter so wrapper shells quoting the path don't match.
while pgrep -f "^bash .*rvbench/run-all.sh" >/dev/null; do
  sleep 60
done

exec >>run-all.log 2>&1
log() { echo "[$(date -u +%FT%TZ)] $*"; }
export MAX_LOAD=30

log "rerun: phase A redisnomod io4 (load spike)"
REPS=3 ENGINES=redisnomod IO_LIST=4 ./run-matrix.sh A
log "rerun: phase A valkey io1 100B (load spike)"
REPS=3 ENGINES=valkey IO_LIST=1 SIZES=100 ./run-matrix.sh A
log "rerun: phase A lan redis io4 1024B (load spike)"
REPS=2 WORKERS_A=400 DELAY_US=25 RESULTS=results-lan ENGINES=redis IO_LIST=4 SIZES=1024 ./run-matrix.sh A

python3 -I analyze.py results >/dev/null
python3 -I analyze.py results-lan >/dev/null
docker rm -f cache rvclient >/dev/null
log "reruns done"
