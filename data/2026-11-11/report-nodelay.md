# rvbench report

Medians across repetitions. A difference is marked *within noise* when the min–max ranges of the two setups overlap.

## Phase A — maximum throughput (closed loop)

### io-threads=1, value=100B, workers=50

```
redis+goredis        ██████████ 72,604 ops/s
redis+valkeygo       ██████████████████████████████████ 256,988 ops/s
redisnomod+goredis   ██████████ 71,689 ops/s
redisnomod+valkeygo  ██████████████████████████████████ 255,115 ops/s
valkey+goredis       ██████████ 77,415 ops/s
valkey+valkeygo      ████████████████████████████████████ 270,776 ops/s
```

### io-threads=1, value=100B, workers=400

```
redis+goredis        ████ 70,687 ops/s
redis+valkeygo       ████████████████████████████████████ 722,654 ops/s
redisnomod+goredis   ███ 70,067 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 712,810 ops/s
valkey+goredis       ████ 79,627 ops/s
valkey+valkeygo      ███████████████████████████████████ 699,968 ops/s
```

### io-threads=1, value=1024B, workers=50

```
redis+goredis        ███████████ 69,721 ops/s
redis+valkeygo       ██████████████████████████████████ 219,721 ops/s
redisnomod+goredis   ███████████ 68,765 ops/s
redisnomod+valkeygo  ███████████████████████████████████ 221,006 ops/s
valkey+goredis       ████████████ 73,875 ops/s
valkey+valkeygo      ████████████████████████████████████ 230,226 ops/s
```

### io-threads=1, value=1024B, workers=400

```
redis+goredis        ████ 69,430 ops/s
redis+valkeygo       ████████████████████████████████████ 584,737 ops/s
redisnomod+goredis   ████ 67,629 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 585,829 ops/s
valkey+goredis       ████ 71,980 ops/s
valkey+valkeygo      ██████████████████████████████████ 547,581 ops/s
```

### io-threads=4, value=100B, workers=50

```
redis+goredis        █████████████████████ 197,410 ops/s
redis+valkeygo       ██████████████████████████████████ 315,663 ops/s
redisnomod+goredis   █████████████████████ 189,859 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 330,358 ops/s
valkey+goredis       ████████████████████ 186,211 ops/s
valkey+valkeygo      ████████████████████████████████████ 331,940 ops/s
```

### io-threads=4, value=100B, workers=400

```
redis+goredis        ███████ 208,121 ops/s
redis+valkeygo       ████████████████████████████████████ 1,026,118 ops/s
redisnomod+goredis   ███████ 209,753 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 1,032,749 ops/s
valkey+goredis       ██████ 181,780 ops/s
valkey+valkeygo      ██████████████████████████ 742,625 ops/s
```

### io-threads=4, value=1024B, workers=50

```
redis+goredis        ███████████████████████ 191,281 ops/s
redis+valkeygo       ███████████████████████████████████ 290,921 ops/s
redisnomod+goredis   ██████████████████████ 185,115 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 296,718 ops/s
valkey+goredis       █████████████████████ 175,099 ops/s
valkey+valkeygo      ██████████████████████████████████ 282,706 ops/s
```

### io-threads=4, value=1024B, workers=400

```
redis+goredis        █████████ 203,566 ops/s
redis+valkeygo       ███████████████████████████████████ 770,321 ops/s
redisnomod+goredis   █████████ 204,820 ops/s
redisnomod+valkeygo  ████████████████████████████████████ 793,181 ops/s
valkey+goredis       ████████ 168,987 ops/s
valkey+valkeygo      ████████████████████████ 535,721 ops/s
```

**Suggested RATE for phase B:** 40,577 ops/s (60% of the lowest max throughput, redisnomod+goredis io=1 v=1024B).

### io-threads effect on max throughput (workers=400)

- redis+goredis v=100B: io 1→4 +194.4%
- redis+goredis v=1024B: io 1→4 +193.2%
- redis+valkeygo v=100B: io 1→4 +42.0%
- redis+valkeygo v=1024B: io 1→4 +31.7%
- redisnomod+goredis v=100B: io 1→4 +199.4%
- redisnomod+goredis v=1024B: io 1→4 +202.9%
- redisnomod+valkeygo v=100B: io 1→4 +44.9%
- redisnomod+valkeygo v=1024B: io 1→4 +35.4%
- valkey+goredis v=100B: io 1→4 +128.3%
- valkey+goredis v=1024B: io 1→4 +134.8%
- valkey+valkeygo v=100B: io 1→4 +6.1%
- valkey+valkeygo v=1024B: io 1→4 -2.2%

### Server effect on max throughput

- redis→valkey, goredis, io=1, v=100B: +12.6%
- redis→valkey, goredis, io=1, v=1024B: +3.7% *within noise*
- redis→valkey, valkeygo, io=1, v=100B: -3.1%
- redis→valkey, valkeygo, io=1, v=1024B: -6.4%
- redis→valkey, goredis, io=4, v=100B: -12.7% *within noise*
- redis→valkey, goredis, io=4, v=1024B: -17.0%
- redis→valkey, valkeygo, io=4, v=100B: -27.6%
- redis→valkey, valkeygo, io=4, v=1024B: -30.5%
- redisnomod→valkey, goredis, io=1, v=100B: +13.6%
- redisnomod→valkey, goredis, io=1, v=1024B: +6.4% *within noise*
- redisnomod→valkey, valkeygo, io=1, v=100B: -1.8%
- redisnomod→valkey, valkeygo, io=1, v=1024B: -6.5% *within noise*
- redisnomod→valkey, goredis, io=4, v=100B: -13.3%
- redisnomod→valkey, goredis, io=4, v=1024B: -17.5%
- redisnomod→valkey, valkeygo, io=4, v=100B: -28.1%
- redisnomod→valkey, valkeygo, io=4, v=1024B: -32.5%

## Phase B — tail latency at a fixed rate (open loop)

### io-threads=1, value=100B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 455µs | 1874µs | 4843µs | 13711µs | 0 |
| redis+valkeygo | 257µs | 1371µs | 2285µs | 6151µs | 0 |
| redisnomod+goredis | 456µs | 1855µs | 4223µs | 7627µs | 0 |
| redisnomod+valkeygo | 248µs | 1376µs | 2361µs | 5551µs | 0 |
| valkey+goredis | 445µs | 1736µs | 3835µs | 11111µs | 0 |
| valkey+valkeygo | 315µs | 1335µs | 2000µs | 3805µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ████████████████████████████████████ 4,843 µs
redis+valkeygo       █████████████████ 2,285 µs
redisnomod+goredis   ███████████████████████████████ 4,223 µs
redisnomod+valkeygo  ██████████████████ 2,361 µs
valkey+goredis       █████████████████████████████ 3,835 µs
valkey+valkeygo      ███████████████ 2,000 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -20.8% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -12.5% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 -9.2% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -15.3% *within noise*
- Client swap goredis→valkeygo on redis: p99.9 -52.8%
- Client swap goredis→valkeygo on redisnomod: p99.9 -44.1%
- Client swap goredis→valkeygo on valkey: p99.9 -47.8% *within noise*
- Server swap redis→valkey with goredis: p99.99 -19.0% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -38.1% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 +45.7% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -31.5% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 -55.1% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -27.2%
- Client swap goredis→valkeygo on valkey: p99.99 -65.8% *within noise*

### io-threads=1, value=1024B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 458µs | 1911µs | 5911µs | 15447µs | 0 |
| redis+valkeygo | 248µs | 1420µs | 3307µs | 17487µs | 0 |
| redisnomod+goredis | 455µs | 1904µs | 4571µs | 8247µs | 0 |
| redisnomod+valkeygo | 247µs | 1397µs | 2367µs | 5027µs | 0 |
| valkey+goredis | 452µs | 1737µs | 3341µs | 10087µs | 0 |
| valkey+valkeygo | 301µs | 1370µs | 1821µs | 3907µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ████████████████████████████████████ 5,911 µs
redis+valkeygo       ████████████████████ 3,307 µs
redisnomod+goredis   ████████████████████████████ 4,571 µs
redisnomod+valkeygo  ██████████████ 2,367 µs
valkey+goredis       ████████████████████ 3,341 µs
valkey+valkeygo      ███████████ 1,821 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -43.5% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -44.9% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 -26.9% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -23.1% *within noise*
- Client swap goredis→valkeygo on redis: p99.9 -44.1% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.9 -48.2%
- Client swap goredis→valkeygo on valkey: p99.9 -45.5% *within noise*
- Server swap redis→valkey with goredis: p99.99 -34.7% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -77.7% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 +22.3% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -22.3% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 +13.2% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -39.0% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -61.3% *within noise*

### io-threads=4, value=100B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 193µs | 1524µs | 3329µs | 9287µs | 0 |
| redis+valkeygo | 160µs | 1373µs | 5387µs | 12023µs | 0 |
| redisnomod+goredis | 194µs | 1550µs | 4001µs | 8815µs | 0 |
| redisnomod+valkeygo | 160µs | 1678µs | 6531µs | 13471µs | 0 |
| valkey+goredis | 350µs | 1481µs | 2909µs | 7171µs | 0 |
| valkey+valkeygo | 274µs | 1342µs | 2177µs | 5011µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ██████████████████ 3,329 µs
redis+valkeygo       ██████████████████████████████ 5,387 µs
redisnomod+goredis   ██████████████████████ 4,001 µs
redisnomod+valkeygo  ████████████████████████████████████ 6,531 µs
valkey+goredis       ████████████████ 2,909 µs
valkey+valkeygo      ████████████ 2,177 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -12.6% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -59.6% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 -27.3% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -66.7% *within noise*
- Client swap goredis→valkeygo on redis: p99.9 +61.8% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.9 +63.2% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -25.2% *within noise*
- Server swap redis→valkey with goredis: p99.99 -22.8% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -58.3% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 -18.7% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -62.8% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 +29.5% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 +52.8% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -30.1% *within noise*

### io-threads=4, value=1024B, rate=33,988 ops/s

| setup | p50 | p99 | p99.9 | p99.99 | errors |
|---|---|---|---|---|---|
| redis+goredis | 195µs | 1573µs | 4675µs | 13919µs | 0 |
| redis+valkeygo | 162µs | 1385µs | 4567µs | 8383µs | 0 |
| redisnomod+goredis | 193µs | 1605µs | 8895µs | 14151µs | 0 |
| redisnomod+valkeygo | 164µs | 1472µs | 5383µs | 10639µs | 0 |
| valkey+goredis | 339µs | 1494µs | 3709µs | 7475µs | 0 |
| valkey+valkeygo | 251µs | 1376µs | 2735µs | 7435µs | 0 |

P99.9 latency (lower is better):

```
redis+goredis        ███████████████████ 4,675 µs
redis+valkeygo       ██████████████████ 4,567 µs
redisnomod+goredis   ████████████████████████████████████ 8,895 µs
redisnomod+valkeygo  ██████████████████████ 5,383 µs
valkey+goredis       ███████████████ 3,709 µs
valkey+valkeygo      ███████████ 2,735 µs
```

**Server effect vs client effect (P99.9 and P99.99):**

- Server swap redis→valkey with goredis: p99.9 -20.7% *within noise*
- Server swap redis→valkey with valkeygo: p99.9 -40.1% *within noise*
- Server swap redisnomod→valkey with goredis: p99.9 -58.3% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.9 -49.2% *within noise*
- Client swap goredis→valkeygo on redis: p99.9 -2.3% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.9 -39.5% *within noise*
- Client swap goredis→valkeygo on valkey: p99.9 -26.3% *within noise*
- Server swap redis→valkey with goredis: p99.99 -46.3% *within noise*
- Server swap redis→valkey with valkeygo: p99.99 -11.3% *within noise*
- Server swap redisnomod→valkey with goredis: p99.99 -47.2% *within noise*
- Server swap redisnomod→valkey with valkeygo: p99.99 -30.1% *within noise*
- Client swap goredis→valkeygo on redis: p99.99 -39.8% *within noise*
- Client swap goredis→valkeygo on redisnomod: p99.99 -24.8% *within noise*
- Client swap goredis→valkeygo on valkey: p99.99 -0.5% *within noise*

### io-threads effect on P99.9

- redis+goredis v=100B: io 1→4 -31.3% *within noise*
- redis+goredis v=1024B: io 1→4 -20.9% *within noise*
- redis+valkeygo v=100B: io 1→4 +135.8%
- redis+valkeygo v=1024B: io 1→4 +38.1% *within noise*
- redisnomod+goredis v=100B: io 1→4 -5.3% *within noise*
- redisnomod+goredis v=1024B: io 1→4 +94.6% *within noise*
- redisnomod+valkeygo v=100B: io 1→4 +176.6%
- redisnomod+valkeygo v=1024B: io 1→4 +127.4%
- valkey+goredis v=100B: io 1→4 -24.1% *within noise*
- valkey+goredis v=1024B: io 1→4 +11.0% *within noise*
- valkey+valkeygo v=100B: io 1→4 +8.8% *within noise*
- valkey+valkeygo v=1024B: io 1→4 +50.2% *within noise*

## Memory per key

### value=32B

```
redis       ████████████████████████████████████ 85 bytes/key
redisnomod  ████████████████████████████████████ 85 bytes/key
valkey      ██████████████████████████████████ 80 bytes/key
```
Valkey vs redis: -5.9% (redis modules loaded: 5, Valkey: 1)

Valkey vs redisnomod: -5.9% (redisnomod modules loaded: 1, Valkey: 1)

### value=100B

```
redis       ████████████████████████████████████ 158 bytes/key
redisnomod  ████████████████████████████████████ 158 bytes/key
valkey      █████████████████████████████████ 145 bytes/key
```
Valkey vs redis: -8.2% (redis modules loaded: 5, Valkey: 1)

Valkey vs redisnomod: -8.2% (redisnomod modules loaded: 1, Valkey: 1)

### value=1024B

```
redis       ████████████████████████████████████ 1,326 bytes/key
redisnomod  ████████████████████████████████████ 1,326 bytes/key
valkey      ████████████████████████████████████ 1,329 bytes/key
```
Valkey vs redis: +0.2% (redis modules loaded: 5, Valkey: 1)

Valkey vs redisnomod: +0.2% (redisnomod modules loaded: 1, Valkey: 1)

Host 1-minute load at run start ranged up to 36.6 on 96 vCPUs (shared host).
