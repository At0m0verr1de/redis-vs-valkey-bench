# Summary: Redis 8.8.4 vs Valkey 9.1.3, go-redis v9.23.0 vs valkey-go v1.0.79

Single host standing in for two VMs: server on 8 pinned cores of one socket,
client on 16 pinned cores of the other, separate network namespaces. Two network
variants: **no delay**, and **lan** (+25 µs netem per side, about +50 µs RTT).
Details and limitations are in `README.md`; full tables are in `report-*.md`.

"Clear" means the min–max ranges across repetitions don't overlap. This host is
shared, so single reps occasionally stall (one P99.9 hit 2.19 s); that makes the
rule strict for tail percentiles, and many large median gaps still count as
within noise.

## Verdicts

| # | Claim | Verdict |
|---|---|---|
| H1 | Redis and Valkey perform about the same | **Partly.** Within about 14% at io-threads 1; Redis 8 pulls ahead at io-threads 4 (13–33% more throughput). Tail differences between servers mostly within noise. |
| H2 | io-threads 4 helps | **Yes for throughput, mixed for latency.** +128–203% throughput with go-redis. With valkey-go: +32–45% on Redis, no gain on Valkey. Lower p50; tails don't consistently improve and get worse for Redis + valkey-go. |
| H3 | Client swap moves the tail more than server swap | **Supported at P99/P99.9, not provable at P99.99.** |
| H4 | Valkey uses less memory per small key (claim: up to 20%) | **Partly.** 5.9% less at 32 B, 8.2% at 100 B, none at 1 KB. Real but well under 20%. |

## H1 + H2: maximum throughput (phase A, 400 workers, no delay)

Median ops/s over 3 reps:

| Setup | io1, 100 B | io1, 1 KB | io4, 100 B | io4, 1 KB |
|---|---|---|---|---|
| redis + go-redis | 70,687 | 69,430 | 208,121 | 203,566 |
| valkey + go-redis | 79,627 | 71,980 | 181,780 | 168,987 |
| redis + valkey-go | 722,654 | 584,737 | 1,026,118 | 770,321 |
| valkey + valkey-go | 699,968 | 547,581 | 742,625 | 535,721 |

- **io-threads 1:** the servers are within about 14% of each other: Valkey is +12.6%
  (+13.6% vs redisnomod) with go-redis at 100 B (clear) and −2% to −6% with valkey-go.
- **io-threads 4:** Redis is ahead: Valkey is 13–17% lower with go-redis and 28–33%
  lower with valkey-go (clear except one cell).
- **io-threads 1→4:** go-redis gains +194% on Redis and +128–135% on Valkey.
  valkey-go gains +32–42% on Redis and +6% / −2% on Valkey. A pipelining client
  already keeps Valkey's single thread busy; threads add little.
- **lan variant** (2 reps) shows the same order with smaller gaps, e.g. io4
  valkey-go 724,636 (Redis) vs 665,221 (Valkey).
- **Client effect dwarfs both:** valkey-go is 3.2–10× go-redis on the same server
  (e.g. 70,687 vs 722,654 on Redis io1 100 B), mainly because it pipelines
  concurrent commands over 5 connections while go-redis needs one round trip per
  command on a 160-connection pool.
- **Redis modules don't matter here:** `redisnomod` is within about 3% of `redis`
  in every cell.

## H3: tail latency at a fixed rate (phase B)

Every setup was driven at **33,988 ops/s**, open loop: 60% of the slowest setup's
maximum (lan valkey + go-redis io1, 56,647 ops/s). 5 reps each, 0 errors in all 240
runs, and no run started above host load 30.

How much each swap moves the median, over all io-threads × value-size cells:

| Variant | Metric | Server swap (16 comparisons) | Client swap (12 comparisons) |
|---|---|---|---|
| no delay | P99 | 4.7%, 9 clear | 16.5%, 10 clear |
| no delay | P99.9 | 27.1%, 0 clear | 44.8%, 3 clear |
| no delay | P99.99 | 33.1%, 0 clear | 34.6%, 1 clear |
| lan | P99 | 7.0%, 4 clear | 23.3%, 7 clear |
| lan | P99.9 | 49.1%, 5 clear | 59.0%, 5 clear |
| lan | P99.99 | 51.4%, 1 clear | 58.3%, 0 clear |

(Median absolute % change between the two setups' medians; "clear" = ranges don't overlap.)

- At P99 and P99.9 the client swap is larger and clears the noise bar more often.
  At P99.99 both are dominated by host noise.
- **valkey + valkey-go had the lowest median P99.9 in all 8 cells** (2 variants × io1/io4
  × 100 B/1 KB): 1.8–2.7 ms. Most pairwise gaps are within noise, but the ordering
  never changed.
- go-redis tails grow most under added RTT: lan io1 P99.9 was 7.0–25.6 ms with
  go-redis vs 1.8–21.6 ms with valkey-go (−74% to −77% where clear).

Example cell, io-threads 1, 100 B, median P99.9:

| Setup | no delay | lan |
|---|---|---|
| redis + go-redis | 4,843 µs | 11,639 µs |
| valkey + go-redis | 3,835 µs | 7,995 µs |
| redis + valkey-go | 2,285 µs | 2,673 µs |
| valkey + valkey-go | 2,000 µs | 2,075 µs |

### Side findings

- **Median latency (p50) separates the servers clearly** (tight ranges):
  - no delay, io4: Redis about 190 µs, Valkey about 345 µs with go-redis (160 vs 274 µs with valkey-go)
  - no delay, io1 with valkey-go: Redis about 250 µs, Valkey about 310 µs
  - lan: the gap reverses and shrinks, with Valkey 16–42 µs lower, except io1 with go-redis (equal)

  The reversal isn't explained; treat sub-100 µs p50 gaps as specific to this setup.
- **Redis io-threads 4 + valkey-go worsens tails:** no-delay P99.9 went from 2,285 to
  5,387 µs (+136%, clear) on redis and +177% on redisnomod at 100 B; lan +294%.
  Valkey + valkey-go was flat (+8.8%, within noise). One plausible cause, not
  verified: Redis 8 assigns each connection to one io thread, and valkey-go uses
  only 5 connections, so its traffic landed 2/2/1 on the three worker threads
  (`io_thread_N` counters in the raw results).
- **P99 has a floor of about 1.3 ms** on this host for every setup, which is
  background noise from the shared machine, not the servers.

## H4: memory per key (1M keys, `used_memory` delta, 5 reps, identical every rep)

| Value | Redis | Redis, no modules | Valkey | Valkey vs Redis |
|---|---|---|---|---|
| 32 B | 85 B | 85 B | 80 B | **−5.9%** |
| 100 B | 158 B | 158 B | 145 B | **−8.2%** |
| 1 KB | 1,326 B | 1,326 B | 1,329 B | +0.2% |

The saving is per-key overhead, so it fades as values grow. Loaded modules don't
change it.

## How much to trust this

- **Solid:** memory (deterministic), throughput order and io-threads gains
  (tight ranges), p50 differences, 0 errors.
- **Directional:** P99.9 rankings. They're consistent across cells, but most
  pairwise gaps fail the strict noise rule on a shared host.
- **Weak:** P99.99/max; anything about io-threads' interaction with real NICs (none here).
- **Re-runs:** host-load spikes (up to 440 on 96 vCPUs) hit some phase-A reps. All
  reps of the affected groups were re-run behind a load gate; see `README.md`.
  Seven groups kept a rep that started at load 30–141, but its reps agree (e.g.
  73.9k / 74.0k / 73.2k); the widest is lan redis + go-redis io4 100 B (132k vs 159k).
- To publish firm numbers, repeat on two dedicated VMs with the original SSH flow.
