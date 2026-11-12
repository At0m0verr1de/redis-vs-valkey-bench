#!/usr/bin/env bash
# Runs the whole single-host study in order; log goes to run-all.log.
#   results/      no added delay (server and client on separate NUMA nodes)
#   results-lan/  +25us netem on each side (~+50us RTT)
set -euo pipefail
cd "$(dirname "$0")"
exec >>run-all.log 2>&1

log() { echo "[$(date -u +%FT%TZ)] $*"; }
ALL="redis redisnomod valkey"

log "start; host: $(uname -r), $(nproc) cpus"
log "phase mem"
REPS=5 ENGINES="$ALL" ./run-matrix.sh mem
log "phase A (no delay)"
REPS=3 ENGINES="$ALL" ./run-matrix.sh A
log "phase A (lan, capacity check for RATE)"
REPS=2 WORKERS_A=400 DELAY_US=25 RESULTS=results-lan ./run-matrix.sh A

python3 -I analyze.py results >/dev/null
python3 -I analyze.py results-lan >/dev/null
RATE="$(python3 -I rate.py results/summary_A.csv results-lan/summary_A.csv)"
log "RATE=$RATE (60% of lowest workers=400 max across both)"

log "phase B (no delay)"
REPS=5 RATE="$RATE" ENGINES="$ALL" ./run-matrix.sh B
log "phase B (lan)"
REPS=5 RATE="$RATE" DELAY_US=25 ENGINES="$ALL" RESULTS=results-lan ./run-matrix.sh B

python3 -I analyze.py results >/dev/null
python3 -I analyze.py results-lan >/dev/null
docker rm -f cache rvclient >/dev/null
log "all done"
