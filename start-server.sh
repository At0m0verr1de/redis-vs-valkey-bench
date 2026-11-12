#!/usr/bin/env bash
# Single-host variant: starts Redis or Valkey in a container on a private bridge
# network, pinned to its own cores and NUMA node, standing in for the server VM.
# Usage: ./start-server.sh redis|valkey IO_THREADS
#
# Override images to pin exact versions, e.g.
#   REDIS_IMAGE=redis:8.8.1 VALKEY_IMAGE=valkey/valkey:9.1.3 ./start-server.sh valkey 4
# DELAY_US>0 adds that much netem delay to every packet the server sends.
set -euo pipefail

ENGINE="${1:?usage: start-server.sh redis|valkey IO_THREADS}"
IOT="${2:?usage: start-server.sh redis|valkey IO_THREADS}"
REDIS_IMAGE="${REDIS_IMAGE:-redis:8.8}"
VALKEY_IMAGE="${VALKEY_IMAGE:-valkey/valkey:9.1}"
TC_IMAGE="${TC_IMAGE:-nicolaka/netshoot:latest}"
# Pin the server to the same cores for every run. Default: 8 physical cores on
# NUMA node 0 that share one L3; keep their SMT siblings (48-55) idle.
CPUS="${CPUS:-0-7}"
MEMS="${MEMS:-0}"
NET="${NET:-rvnet}"
SERVER_IP="${SERVER_IP:-172.28.0.10}"
PORT="${PORT:-6379}"
DELAY_US="${DELAY_US:-0}"

EXTRA=()
case "$ENGINE" in
  redis)  IMAGE="$REDIS_IMAGE";  BIN="redis-server" ;;
  # The Redis image's entrypoint loads every module in this dir; an empty tmpfs
  # over it gives the same image with no modules, to compare like for like.
  redisnomod) IMAGE="$REDIS_IMAGE"; BIN="redis-server"; EXTRA=(--tmpfs /usr/local/lib/redis/modules) ;;
  valkey) IMAGE="$VALKEY_IMAGE"; BIN="valkey-server" ;;
  *) echo "engine must be redis, redisnomod or valkey" >&2; exit 1 ;;
esac

docker rm -f cache >/dev/null 2>&1 || true

# Same settings for both engines:
#  - no persistence (pure cache; removes fork/disk noise)
#  - no maxmemory (no eviction during the run)
#  - only io-threads varies
# No published port: clients connect to the container IP directly, so
# docker-proxy and DNAT stay out of the path.
# --cpuset-* are kept for hosts where Docker has cgroups; see the taskset below.
docker run -d --name cache \
  --network "$NET" --ip "$SERVER_IP" \
  --cpuset-cpus "$CPUS" --cpuset-mems "$MEMS" \
  --ulimit nofile=100000:100000 \
  "${EXTRA[@]}" \
  "$IMAGE" "$BIN" \
    --port "$PORT" \
    --bind 0.0.0.0 \
    --protected-mode no \
    --save "" \
    --appendonly no \
    --io-threads "$IOT" >/dev/null

if [ "$DELAY_US" -gt 0 ]; then
  # Sidecar shares the server's network namespace and sets netem on its eth0.
  docker run --rm --network container:cache --cap-add NET_ADMIN "$TC_IMAGE" \
    tc qdisc add dev eth0 root netem delay "${DELAY_US}us" limit 100000
fi

# Wait until it answers PING
up=0
for _ in $(seq 1 30); do
  if docker exec cache "${BIN/server/cli}" -p "$PORT" PING 2>/dev/null | grep -q PONG; then
    up=1
    break
  fi
  sleep 1
done
if [ "$up" -ne 1 ]; then
  echo "server did not come up" >&2
  docker logs cache >&2
  exit 1
fi

# Rootless Docker here has no cgroups, so --cpuset-cpus is silently ignored.
# Pin with CPU affinity instead: every existing thread now, and threads the
# server spawns later (e.g. Valkey's on-demand io threads) inherit the mask.
docker run --rm --pid container:cache --cap-add SYS_NICE "$TC_IMAGE" \
  taskset -a -pc "$CPUS" 1 >/dev/null
echo "$ENGINE ($IMAGE) up with io-threads=$IOT on cpus $CPUS, delay ${DELAY_US}us"
