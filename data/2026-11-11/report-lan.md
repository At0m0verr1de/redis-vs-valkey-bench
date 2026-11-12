# rvbench report

Medians across repetitions. A difference is marked *within noise* when the min–max ranges of the two setups overlap.

## Phase A — maximum throughput (closed loop)

### io-threads=1, value=100B, workers=400

```
redis+goredis    ████ 62,446 ops/s
redis+valkeygo   ████████████████████████████████████ 567,833 ops/s
valkey+goredis   ████ 56,647 ops/s
valkey+valkeygo  ██████████████████████████████████ 532,048 ops/s
```

### io-threads=1, value=1024B, workers=400

```
redis+goredis    █████ 60,473 ops/s
redis+valkeygo   ████████████████████████████████████ 451,655 ops/s
valkey+goredis   █████ 57,083 ops/s
valkey+valkeygo  ███████████████████████████████████ 444,451 ops/s
```

### io-threads=4, value=100B, workers=400

```
redis+goredis    ███████ 145,862 ops/s
redis+valkeygo   ████████████████████████████████████ 724,636 ops/s
valkey+goredis   ██████ 127,138 ops/s
valkey+valkeygo  █████████████████████████████████ 665,221 ops/s
```

### io-threads=4, value=1024B, workers=400

```
redis+goredis    ████████ 157,506 ops/s
redis+valkeygo   ████████████████████████████████████ 678,442 ops/s
valkey+goredis   ███████ 122,752 ops/s
valkey+valkeygo  █████████████████████████ 473,421 ops/s
```

**Suggested RATE for phase B:** 33,988 ops/s (60% of the lowest max throughput, valkey+goredis io=1 v=100B).

### io-threads effect on max throughput (workers=400)

- redis+goredis v=100B: io 1→4 +133.6%
- redis+goredis v=1024B: io 1→4 +160.5%
- redis+valkeygo v=100B: io 1→4 +27.6%
- redis+valkeygo v=1024B: io 1→4 +50.2%
- valkey+goredis v=100B: io 1→4 +124.4%
- valkey+goredis v=1024B: io 1→4 +115.0%
- valkey+valkeygo v=100B: io 1→4 +25.0%
- valkey+valkeygo v=1024B: io 1→4 +6.5% *within noise*

### Server effect on max throughput

- redis→valkey, goredis, io=1, v=100B: -9.3%
- redis→valkey, goredis, io=1, v=1024B: -5.6%
- redis→valkey, valkeygo, io=1, v=100B: -6.3%
- redis→valkey, valkeygo, io=1, v=1024B: -1.6% *within noise*
- redis→valkey, goredis, io=4, v=100B: -12.8% *within noise*
- redis→valkey, goredis, io=4, v=1024B: -22.1%
- redis→valkey, valkeygo, io=4, v=100B: -8.2% *within noise*
- redis→valkey, valkeygo, io=4, v=1024B: -30.2%

## Phase B — tail latency at a fixed rate (open loop)

### io-threads=1, value=100B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 246µs | 2169µs | 11639µs | 18527µs | 0 |
| redis+valkeygo | 225µs | 1331µs | 2673µs | 6611µs | 0 |
| redisnomod+goredis | 246µs | 2457µs | 10919µs | 14463µs | 0 |
| redisnomod+valkeygo | 224µs | 1351µs | 4009µs | 12031µs | 0 |
| valkey+goredis | 245µs | 1878µs | 7995µs | 15407µs | 0 |
| valkey+valkeygo | 209µs | 1340µs | 2075µs | 4447µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ████████████████████████████████████ 11,639 µs
redis+valkeygo       ████████ 2,673 µs
redisnomod+goredis   ██████████████████████████████████ 10,919 µs
redisnomod+valkeygo  ████████████ 4,009 µs
valkey+goredis       █████████████████████████ 7,995 µs
valkey+valkeygo      ██████ 2,075 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -31.3% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -22.4% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 -26.8% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -48.2%
- Client swap goredis→valkeygo on redis: p99.9 -77.0%
- Client swap goredis→valkeygo on redisnomod: p99.9 -63.3% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -74.0%
- Server swap redis→valkey with goredis: p99.99 -16.8% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -32.7% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 +6.5% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -63.0% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 -64.3% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -16.8% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -71.1% *within noise*

### io-threads=1, value=1024B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 253µs | 3383µs | 17327µs | 23423µs | 0 |
| redis+valkeygo | 236µs | 1376µs | 3039µs | 11335µs | 0 |
| redisnomod+goredis | 251µs | 6019µs | 25567µs | 38143µs | 0 |
| redisnomod+valkeygo | 239µs | 2467µs | 21551µs | 29743µs | 0 |
| valkey+goredis | 250µs | 1965µs | 7019µs | 11999µs | 0 |
| valkey+valkeygo | 218µs | 1361µs | 1788µs | 3545µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ████████████████████████ 17,327 µs
redis+valkeygo       ████ 3,039 µs
redisnomod+goredis   ████████████████████████████████████ 25,567 µs
redisnomod+valkeygo  ██████████████████████████████ 21,551 µs
valkey+goredis       ██████████ 7,019 µs
valkey+valkeygo      ███ 1,788 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -59.5% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -41.2%
- Server swap redisnomod→valkey with goredis: p99.9 -72.5% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -91.7%
- Client swap goredis→valkeygo on redis: p99.9 -82.5% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.9 -15.7% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -74.5%
- Server swap redis→valkey with goredis: p99.99 -48.8% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -68.7% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 -68.5% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -88.1% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 -51.6% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -22.0% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -70.5% *within noise*

### io-threads=4, value=100B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 245µs | 1434µs | 5099µs | 13903µs | 0 |
| redis+valkeygo | 235µs | 1388µs | 10519µs | 32431µs | 0 |
| redisnomod+goredis | 240µs | 1469µs | 8335µs | 20223µs | 0 |
| redisnomod+valkeygo | 233µs | 1349µs | 5667µs | 10951µs | 0 |
| valkey+goredis | 203µs | 1572µs | 4171µs | 13127µs | 0 |
| valkey+valkeygo | 211µs | 1291µs | 1887µs | 4435µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        █████████████████ 5,099 µs
redis+valkeygo       ████████████████████████████████████ 10,519 µs
redisnomod+goredis   █████████████████████████████ 8,335 µs
redisnomod+valkeygo  ███████████████████ 5,667 µs
valkey+goredis       ██████████████ 4,171 µs
valkey+valkeygo      ██████ 1,887 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -18.2% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -82.1%
- Server swap redisnomod→valkey with goredis: p99.9 -50.0% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -66.7%
- Client swap goredis→valkeygo on redis: p99.9 +106.3%
- Client swap goredis→valkeygo on redisnomod: p99.9 -32.0% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -54.8%
- Server swap redis→valkey with goredis: p99.99 -5.6% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -86.3%
- Server swap redisnomod→valkey with goredis: p99.99 -35.1% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -59.5% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 +133.3% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -45.8% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -66.2% *within noise*

### io-threads=4, value=1024B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 243µs | 1484µs | 6935µs | 13471µs | 0 |
| redis+valkeygo | 237µs | 1559µs | 5879µs | 10647µs | 0 |
| redisnomod+goredis | 248µs | 1477µs | 4259µs | 9071µs | 0 |
| redisnomod+valkeygo | 234µs | 1324µs | 6331µs | 14311µs | 0 |
| valkey+goredis | 202µs | 1558µs | 4679µs | 13975µs | 0 |
| valkey+valkeygo | 205µs | 1329µs | 2547µs | 5763µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ████████████████████████████████████ 6,935 µs
redis+valkeygo       ███████████████████████████████ 5,879 µs
redisnomod+goredis   ██████████████████████ 4,259 µs
redisnomod+valkeygo  █████████████████████████████████ 6,331 µs
valkey+goredis       ████████████████████████ 4,679 µs
valkey+valkeygo      █████████████ 2,547 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -32.5% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -56.7% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 +9.9% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -59.8% *within noise*
- Client swap goredis→valkeygo on redis: p99.9 -15.2% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.9 +48.6% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -45.6% *within noise*
- Server swap redis→valkey with goredis: p99.99 +3.7% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -45.9% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 +54.1% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -59.7% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 -21.0% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 +57.8% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -58.8% *within noise*

### io-threads effect on P99.9

- redis+goredis v=100B: io 1→4 -56.2% *within noise*
- redis+goredis v=1024B: io 1→4 -60.0% *within noise*
- redis+valkeygo v=100B: io 1→4 +293.5%
- redis+valkeygo v=1024B: io 1→4 +93.5% *within noise*
- redisnomod+goredis v=100B: io 1→4 -23.7% *within noise*
- redisnomod+goredis v=1024B: io 1→4 -83.3%
- redisnomod+valkeygo v=100B: io 1→4 +41.4% *within noise*
- redisnomod+valkeygo v=1024B: io 1→4 -70.6% *within noise*
- valkey+goredis v=100B: io 1→4 -47.8% *within noise*
- valkey+goredis v=1024B: io 1→4 -33.3% *within noise*
- valkey+valkeygo v=100B: io 1→4 -9.1% *within noise*
- valkey+valkeygo v=1024B: io 1→4 +42.4% *within noise*

Host 1-minute load at run start ranged up to 140.7 on 96 vCPUs (shared host).
