# rvbench results: Redis 8.8 vs Valkey 9.1, go-redis vs valkey-go

> **Paths in this repo:** this file was written for the results bundle. Here, `kit/` is the repo root, `results/` and `results-lan/` are `raw/nodelay/` and `raw/lan/` in this folder, and `report-*.md`, `csv/` and `run-all.log` sit next to this file. `export.sh` is not included.


Results bundle from running the rvbench kit on one large host that stands in for
the two-VM setup the kit was designed for. `SUMMARY.md` has the findings; this
file explains how they were produced and how far to trust them.

## What was tested

| # | Claim | Evidence |
|---|-------|----------|
| H1 | Redis and Valkey perform about the same when configured identically | Phase A throughput + phase B tail latency, server swapped, client fixed |
| H2 | `io-threads 4` beats `io-threads 1` on a multi-core box | Same runs, io-threads 1 vs 4 |
| H3 | Swapping the Go client moves P99.9/P99.99 more than swapping the server | Phase B "server effect vs client effect" lines |
| H4 | Valkey uses less memory per small key | `mem` phase, bytes/key at 32 B, 100 B, 1 KB |

A difference counts only if the min–max ranges across repetitions don't overlap;
the reports mark overlapping ones *within noise*.

## Versions

| Component | Version |
|---|---|
| Redis | 8.8.4 (`redis:8.8` image, jemalloc 5.3.0) |
| Valkey | 9.1.3 (`valkey/valkey:9.1` image, jemalloc 5.3.0) |
| go-redis | v9.23.0 |
| valkey-go | v1.0.79 |
| hdrhistogram-go | v1.4.0 |
| Go | 1.27.3 |
| Kernel | 6.12.105+ |

## Hardware and layout

One KVM guest: AMD EPYC 7B13, 96 vCPUs = 2 sockets × 24 cores × 2 SMT, two
NUMA nodes (node 0: CPUs 0-23,48-71; node 1: 24-47,72-95), 6 L3 slices.
Docker 28.5 (rootless).

| | Server | Client |
|---|---|---|
| Runs in | container `cache` | container `rvclient`, `docker exec` per run |
| CPUs | 0-7: 8 physical cores on node 0, one L3 slice | 24-39: 16 physical cores on node 1 |
| SMT siblings | 48-55 left unused | |
| Network | private Docker bridge, fixed IP, no published port | same bridge |

Separate sockets give separate cores, L3 and memory controllers; separate
containers give separate network namespaces, so traffic crosses a veth pair and
a bridge instead of loopback. Connecting to the container IP directly keeps
docker-proxy and DNAT out of the path.

Two network variants:

- `results/` (**no delay**): bridge only.
- `results-lan/` (**lan**): `tc netem delay 25us` on both containers' eth0, about
  +50 µs round trip, standing in for a same-AZ hop.

## Matrix

| Phase | Engines | Other axes | Reps |
|---|---|---|---|
| mem | redis, redisnomod, valkey | 1M keys at 32 B, 100 B, 1 KB | 5 |
| A (no delay) | redis, redisnomod, valkey | io 1/4 × goredis/valkeygo × 100 B/1 KB × 50/400 workers, closed loop | 3 |
| A (lan) | redis, valkey | same, 400 workers only | 2 |
| B (no delay) | redis, redisnomod, valkey | io 1/4 × goredis/valkeygo × 100 B/1 KB, 400 workers, open loop | 5 |
| B (lan) | redis, redisnomod, valkey | same as B | 5 |

Each bench run: 5 s warmup, 30 s measured, 1M-key uniform keyspace, 80% GET /
20% SET. Phase B uses one fixed rate for every setup in both variants: 60% of
the lowest 400-worker phase-A median across both variants (logged as `RATE=` in
`run-all.log`). Phase B is open loop: latency is measured from each request's
scheduled send time, which corrects for coordinated omission.

`redisnomod` is the same Redis image with an empty tmpfs over
`/usr/local/lib/redis/modules`. The image's entrypoint otherwise loads
redisearch, rejson, redisbloom and redistimeseries. With it, Redis loads only its
built-in `vectorset`, the counterpart of Valkey 9's built-in `lua`.

Both clients use library defaults (`-pool 0`, `-multiplex 0`); valkey-go client-side
caching is off. go-redis uses a connection pool (10 × GOMAXPROCS = 160 here);
valkey-go pipelines concurrent commands over a few connections. That design
difference drives the client effect.

## Changes from the original kit

- **CPU pinning via `taskset`, not `--cpuset-cpus`.** Rootless Docker on this host
  has no cgroups and silently ignores cpuset flags. The server is pinned by a
  sidecar running `taskset -a -pc` on its PID 1 (threads spawned later inherit
  the mask); the client is launched under `taskset -c`. Go then sizes
  GOMAXPROCS to 16 (recorded as `gomaxprocs` in every result).
- **Single host instead of SSH to a server VM** (`start-server.sh`, `run-matrix.sh`).
- **`io_threads_active` fix.** The original read it from `INFO server`, where it
  doesn't exist. Results now carry `server_end`: the `io_*` fields from
  `INFO stats`/`threads` read after the run, showing whether io threads did work.
- **`redisnomod` engine** added (above).
- **Host load recorded** (`loadavg_start`/`loadavg_end`) per run; the report
  prints the maximum.
- **`analyze.py`**: io-threads and server effect on max throughput; redisnomod
  comparisons; noise flag on memory.
- **`rate.py`, `run-all.sh`** added to pick the common phase-B rate and run everything.
- **Load gate and re-runs** (`MAX_LOAD` in `run-matrix.sh`, `rerun-noisy.sh`). Two bursts
  from other tenants hit phase A (16:20–16:44 UTC, 1-minute load up to 440; 17:13–17:23,
  up to 229). Affected reps were off by up to 8× (e.g. 78k vs 627k/672k ops/s). Every
  rep of the affected groups was re-run after the main pass, each waiting for load
  below 30: no-delay `redisnomod` io4 (all), no-delay `valkey` io1 100 B, lan `redis`
  io4 1 KB. The phase-B rate was unaffected (it came from a group whose two reps agree).
  `run-all.log` records both passes; the result files hold the re-run values.

## Limitations

- **Shared host.** Other tenants ran during the study (1-minute load usually ~9–22
  on 96 vCPUs, with the two spikes above) and can be scheduled on our cores;
  taskset only keeps *our* processes apart. Every result records the load at start
  and end, and each summary row has `load1_max`. Expect about 1–2 ms of background tail noise; P99.99 and max are the
  least reliable figures.
- **No NIC.** There are no hardware interrupts or cloud NIC packet limits. This
  weakens H2 most, since io threads partly exist to absorb network work.
- **netem is an approximation** of a real hop: a fixed delay with no jitter, applied
  per packet. go-redis sends one request per packet and valkey-go batches, so
  netem may affect them differently from a real network.
- **No memory binding.** Without cgroups, memory isn't pinned to a node; Linux's
  default first-touch policy keeps it mostly local to each pinned process.
- **One machine, one day.** Run-to-run noise is measured; machine-to-machine
  variation is not.

## Files

| Path | Contents |
|---|---|
| `SUMMARY.md` | Findings per hypothesis |
| `report-nodelay.md`, `report-lan.md` | Generated reports with tables and ASCII charts |
| `csv/` | `summary_A.csv`, `summary_B.csv`, `summary_mem.csv` per variant |
| `raw/` | Every per-run JSON result (config, server info, latency percentiles, load) |
| `run-all.log` | Full run log with timestamps and the chosen RATE |
| `kit/` | The exact scripts and load generator used, including `rerun-noisy.sh` |

## Reproducing

On a host with Docker and Go 1.24+:

```bash
cd kit/bench && CGO_ENABLED=0 GO111MODULE=on go build -o rvbench . && cd ..
for i in redis:8.8 valkey/valkey:9.1 nicolaka/netshoot; do docker pull "$i"; done
./run-all.sh        # ~4.5 h; adjust CPUS / CLIENT_CPUS to your NUMA layout
```

On real two-VM hardware, use the original kit's SSH flow instead.
