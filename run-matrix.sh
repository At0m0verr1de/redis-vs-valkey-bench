#!/usr/bin/env bash
# Single-host variant: runs every combination with the server and the client in
# separate containers on separate NUMA nodes, standing in for two VMs.
# Run from the kit directory.
#
#   ./run-matrix.sh A                   # find max throughput (closed loop)
#   RATE=150000 ./run-matrix.sh B       # tail latency at a fixed rate
#   ./run-matrix.sh mem                 # memory per key
#   DELAY_US=25 RESULTS=results-lan ./run-matrix.sh A   # with netem on both sides
#
# For phase B, set RATE to about 60% of the LOWEST throughput you saw in phase A
# (python3 analyze.py results prints it), so every setup is tested at the same
# load and none of them is pushed past its limit.
set -euo pipefail

PHASE="${1:?usage: run-matrix.sh A|B|mem}"
REPS="${REPS:-3}"
DURATION="${DURATION:-30s}"
WARMUP="${WARMUP:-5s}"
KEYS="${KEYS:-1000000}"
IO_LIST="${IO_LIST:-1 4}"
ENGINES="${ENGINES:-redis valkey}"
CLIENTS="${CLIENTS:-goredis valkeygo}"
SIZES="${SIZES:-100 1024}"
RESULTS="${RESULTS:-results}"
# Client: 16 physical cores on NUMA node 1, so it is never the bottleneck.
CLIENT_CPUS="${CLIENT_CPUS:-24-39}"
CLIENT_MEMS="${CLIENT_MEMS:-1}"
CLIENT_IMAGE="${CLIENT_IMAGE:-nicolaka/netshoot:latest}"
NET="${NET:-rvnet}"
SUBNET="${SUBNET:-172.28.0.0/24}"
SERVER_IP="${SERVER_IP:-172.28.0.10}"
DELAY_US="${DELAY_US:-0}"
export NET SERVER_IP DELAY_US
ADDR="$SERVER_IP:6379"
OUT="$RESULTS/$PHASE"
mkdir -p "$OUT"

[ -x bench/rvbench ] || { echo "build bench/rvbench first (CGO_ENABLED=0)" >&2; exit 1; }

docker network inspect "$NET" >/dev/null 2>&1 || docker network create --subnet "$SUBNET" "$NET" >/dev/null

# Long-lived client container; every run is a docker exec inside it.
docker rm -f rvclient >/dev/null 2>&1 || true
docker run -d --name rvclient --network "$NET" \
  --cpuset-cpus "$CLIENT_CPUS" --cpuset-mems "$CLIENT_MEMS" \
  --cap-add NET_ADMIN --ulimit nofile=100000:100000 \
  -v "$PWD":/rvbench -w /rvbench \
  "$CLIENT_IMAGE" sleep infinity >/dev/null
if [ "$DELAY_US" -gt 0 ]; then
  docker exec rvclient tc qdisc add dev eth0 root netem delay "${DELAY_US}us" limit 100000
fi

# taskset, not cgroups, does the pinning (rootless Docker here ignores
# --cpuset-cpus); Go sizes GOMAXPROCS from the affinity mask.
RV="docker exec rvclient taskset -c $CLIENT_CPUS /rvbench/bench/rvbench"

start() { ./start-server.sh "$1" "$2"; }

# With MAX_LOAD set, wait (up to 10 min) for the shared host's 1-minute load
# to drop below it before each run, so neighbours' bursts don't land in results.
wait_quiet() {
  [ -n "${MAX_LOAD:-}" ] || return 0
  for _ in $(seq 1 60); do
    awk -v m="$MAX_LOAD" '{ exit !($1 < m) }' /proc/loadavg && return 0
    sleep 10
  done
  echo "  (load still >= $MAX_LOAD after 10 min: $(cut -d' ' -f1 /proc/loadavg); running anyway)"
}

bench() { # engine io client size workers rate rep
  local f="$OUT/${1}_io${2}_${3}_v${4}_w${5}_r${6}_rep${7}.json"
  wait_quiet
  echo "  -> $(basename "$f")"
  $RV -mode bench -addr "$ADDR" -client "$3" \
    -value-size "$4" -workers "$5" -rate "$6" -keys "$KEYS" \
    -duration "$DURATION" -warmup "$WARMUP" -seed "$((100 + $7))" \
    -engine "$1" -io-threads "$2" -phase "$PHASE" -rep "$7" -out "$f"
  sleep 3
}

case "$PHASE" in
  A)
    for e in $ENGINES; do for io in $IO_LIST; do
      start "$e" "$io"
      for s in $SIZES; do
        $RV -mode load -addr "$ADDR" -keys "$KEYS" -value-size "$s"
        for rep in $(seq 1 "$REPS"); do
          for c in $CLIENTS; do
            for w in ${WORKERS_A:-50 400}; do bench "$e" "$io" "$c" "$s" "$w" 0 "$rep"; done
          done
        done
      done
    done; done
    ;;
  B)
    RATE="${RATE:?set RATE (ops/sec) from phase A results}"
    for e in $ENGINES; do for io in $IO_LIST; do
      start "$e" "$io"
      for s in $SIZES; do
        $RV -mode load -addr "$ADDR" -keys "$KEYS" -value-size "$s"
        for rep in $(seq 1 "$REPS"); do
          for c in $CLIENTS; do bench "$e" "$io" "$c" "$s" "${WORKERS_B:-400}" "$RATE" "$rep"; done
        done
      done
    done; done
    ;;
  mem)
    for e in $ENGINES; do
      start "$e" 1
      for s in ${MEM_SIZES:-32 100 1024}; do
        for rep in $(seq 1 "$REPS"); do
          f="$OUT/${e}_v${s}_rep${rep}.json"
          echo "  -> $(basename "$f")"
          $RV -mode mem -addr "$ADDR" -keys "$KEYS" -value-size "$s" \
            -engine "$e" -phase mem -rep "$rep" -out "$f"
        done
      done
    done
    ;;
  *) echo "phase must be A, B or mem" >&2; exit 1 ;;
esac
echo "done: results in $OUT"
