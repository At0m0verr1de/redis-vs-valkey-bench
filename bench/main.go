// rvbench: a small, honest load generator for comparing
// Redis vs Valkey (server) and go-redis vs valkey-go (client).
//
// Modes:
//
//	-mode=load   populate keys key:0..N-1 with values of -value-size bytes
//	-mode=bench  run a GET/SET mix and record a latency histogram
//	-mode=mem    flush, load N keys, report memory used per key
//
// Latency is recorded in microseconds with HdrHistogram.
// With -rate > 0 the run is open-loop: each request has an intended send
// time on a fixed schedule, and latency is measured from that intended time.
// This corrects for "coordinated omission", where a closed-loop benchmark
// silently stops sending while the server is stalled and hides tail latency.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/HdrHistogram/hdrhistogram-go"
	"github.com/redis/go-redis/v9"
	"github.com/valkey-io/valkey-go"
)

// ---------- client abstraction ----------

type kv interface {
	Get(ctx context.Context, key string) error
	Set(ctx context.Context, key, val string) error
	Close()
}

type goRedisKV struct{ c *redis.Client }

func (g *goRedisKV) Get(ctx context.Context, k string) error {
	err := g.c.Get(ctx, k).Err()
	if err == redis.Nil {
		return nil
	}
	return err
}
func (g *goRedisKV) Set(ctx context.Context, k, v string) error {
	return g.c.Set(ctx, k, v, 0).Err()
}
func (g *goRedisKV) Close() { g.c.Close() }

type valkeyGoKV struct{ c valkey.Client }

func (v *valkeyGoKV) Get(ctx context.Context, k string) error {
	err := v.c.Do(ctx, v.c.B().Get().Key(k).Build()).Error()
	if valkey.IsValkeyNil(err) {
		return nil
	}
	return err
}
func (v *valkeyGoKV) Set(ctx context.Context, k, val string) error {
	return v.c.Do(ctx, v.c.B().Set().Key(k).Value(val).Build()).Error()
}
func (v *valkeyGoKV) Close() { v.c.Close() }

func newKV(kind, addr string, pool, multiplex int) (kv, error) {
	switch kind {
	case "goredis":
		opt := &redis.Options{Addr: addr}
		if pool > 0 {
			opt.PoolSize = pool // 0 keeps the library default (10 * GOMAXPROCS)
		}
		return &goRedisKV{redis.NewClient(opt)}, nil
	case "valkeygo":
		opt := valkey.ClientOption{
			InitAddress:       []string{addr},
			ForceSingleClient: true, // standalone server, skip cluster discovery
			DisableCache:      true, // no client-side caching: measure the server path
		}
		if multiplex > 0 {
			opt.PipelineMultiplex = multiplex // 0 keeps the library default
		}
		c, err := valkey.NewClient(opt)
		if err != nil {
			return nil, err
		}
		return &valkeyGoKV{c}, nil
	}
	return nil, fmt.Errorf("unknown client %q (use goredis or valkeygo)", kind)
}

// ---------- config & result ----------

type config struct {
	Mode      string  `json:"mode"`
	Addr      string  `json:"addr"`
	Client    string  `json:"client"`
	Workers   int     `json:"workers"`
	Rate      int     `json:"rate"` // total ops/sec target; 0 = closed loop
	Duration  string  `json:"duration"`
	Warmup    string  `json:"warmup"`
	Keys      int     `json:"keys"`
	ValueSize int     `json:"value_size"`
	ReadRatio float64 `json:"read_ratio"`
	Dist      string  `json:"dist"`
	Pool      int     `json:"pool"`
	Multiplex int     `json:"multiplex"`
	Seed      int64   `json:"seed"`
	// free-form labels so analyze.py can group runs
	Engine    string `json:"engine"`
	IOThreads int    `json:"io_threads"`
	Phase     string `json:"phase"`
	Rep       int    `json:"rep"`
}

type result struct {
	Config config            `json:"config"`
	Server map[string]string `json:"server"`
	// io_* INFO fields read after the run; io threads activate under load, so the
	// pre-run values in Server don't show whether they were used.
	ServerEnd   map[string]string `json:"server_end,omitempty"`
	StartedAt   string            `json:"started_at"`
	Ops         int64             `json:"ops"`
	Errors      int64             `json:"errors"`
	AchievedRPS float64           `json:"achieved_rps"`
	LatencyUS   map[string]int64  `json:"latency_us"`
	MeanUS      float64           `json:"mean_us"`
	Memory      map[string]int64  `json:"memory,omitempty"`
	GoMaxProcs  int               `json:"gomaxprocs"`
	// Host load at start and end of the run; the host is shared, so this flags noisy runs.
	LoadAvgStart string `json:"loadavg_start"`
	LoadAvgEnd   string `json:"loadavg_end"`
}

// ---------- helpers ----------

func randomValue(n int, seed int64) string {
	r := rand.New(rand.NewSource(seed))
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[r.Intn(len(letters))]
	}
	return string(b)
}

func key(i uint64) string { return "key:" + strconv.FormatUint(i, 10) }

func loadAvg() string {
	b, err := os.ReadFile("/proc/loadavg")
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

// adminClient is always go-redis: used for loading, INFO and FLUSHALL only,
// never for the measured traffic.
func adminClient(addr string) *redis.Client {
	return redis.NewClient(&redis.Options{Addr: addr, PoolSize: 4})
}

func parseInfo(raw string) map[string]string {
	m := map[string]string{}
	for _, line := range strings.Split(raw, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if k, v, ok := strings.Cut(line, ":"); ok {
			m[k] = v
		}
	}
	return m
}

func serverInfo(ctx context.Context, a *redis.Client) map[string]string {
	out := map[string]string{}
	// io_threads_active lives in "stats" (Valkey) or "threads" (Redis 8), not "server".
	info := parseInfo(a.Info(ctx, "server", "stats", "threads").Val())
	for _, k := range []string{"server_name", "valkey_version", "redis_version", "os", "arch_bits", "io_threads_active"} {
		if v, ok := info[k]; ok {
			out[k] = v
		}
	}
	if v, err := a.ConfigGet(ctx, "io-threads").Result(); err == nil {
		out["config_io_threads"] = v["io-threads"]
	}
	// Loaded modules can affect memory and speed; record them for fairness.
	if mods, err := a.Do(ctx, "MODULE", "LIST").Slice(); err == nil {
		out["module_count"] = strconv.Itoa(len(mods))
	}
	return out
}

func ioInfo(ctx context.Context, a *redis.Client) map[string]string {
	out := map[string]string{}
	for k, v := range parseInfo(a.Info(ctx, "stats", "threads").Val()) {
		if strings.HasPrefix(k, "io_") {
			out[k] = v
		}
	}
	return out
}

func loadKeys(ctx context.Context, a *redis.Client, n, size int, seed int64) error {
	val := randomValue(size, seed)
	const batch = 1000
	for i := 0; i < n; i += batch {
		p := a.Pipeline()
		for j := i; j < i+batch && j < n; j++ {
			p.Set(ctx, key(uint64(j)), val, 0)
		}
		if _, err := p.Exec(ctx); err != nil {
			return err
		}
	}
	return nil
}

func memStats(ctx context.Context, a *redis.Client) map[string]int64 {
	info := parseInfo(a.Info(ctx, "memory").Val())
	out := map[string]int64{}
	for _, k := range []string{"used_memory", "used_memory_rss", "used_memory_dataset"} {
		if v, err := strconv.ParseInt(info[k], 10, 64); err == nil {
			out[k] = v
		}
	}
	return out
}

// ---------- benchmark ----------

func runBench(ctx context.Context, cfg config, client kv) (*hdrhistogram.Histogram, int64, int64, time.Duration) {
	dur, _ := time.ParseDuration(cfg.Duration)
	warm, _ := time.ParseDuration(cfg.Warmup)
	val := randomValue(cfg.ValueSize, cfg.Seed+999)

	var interval time.Duration
	if cfg.Rate > 0 {
		interval = time.Duration(float64(time.Second) * float64(cfg.Workers) / float64(cfg.Rate))
	}

	start := time.Now()
	measureFrom := start.Add(warm)
	end := measureFrom.Add(dur)

	hists := make([]*hdrhistogram.Histogram, cfg.Workers)
	var ops, errs atomic.Int64
	var wg sync.WaitGroup

	for w := 0; w < cfg.Workers; w++ {
		hists[w] = hdrhistogram.New(1, 60_000_000, 3) // 1us .. 60s, 3 sig figs
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			r := rand.New(rand.NewSource(cfg.Seed + int64(id)))
			var zipf *rand.Zipf
			if cfg.Dist == "zipf" {
				zipf = rand.NewZipf(r, 1.1, 1, uint64(cfg.Keys-1))
			}
			// Stagger open-loop workers so they don't all fire at once.
			next := start
			if interval > 0 {
				next = start.Add(time.Duration(r.Int63n(int64(interval))))
			}
			h := hists[id]
			for {
				var intended time.Time
				if interval > 0 {
					intended = next
					if d := time.Until(intended); d > 0 {
						time.Sleep(d)
					}
					next = next.Add(interval)
				} else {
					intended = time.Now()
				}
				if intended.After(end) {
					return
				}

				var k uint64
				if zipf != nil {
					k = zipf.Uint64()
				} else {
					k = uint64(r.Intn(cfg.Keys))
				}

				var err error
				if r.Float64() < cfg.ReadRatio {
					err = client.Get(ctx, key(k))
				} else {
					err = client.Set(ctx, key(k), val)
				}
				done := time.Now()

				if intended.Before(measureFrom) {
					continue // warmup
				}
				if err != nil {
					errs.Add(1)
					continue
				}
				ops.Add(1)
				us := done.Sub(intended).Microseconds()
				if us < 1 {
					us = 1
				}
				_ = h.RecordValue(us)
			}
		}(w)
	}
	wg.Wait()

	total := hdrhistogram.New(1, 60_000_000, 3)
	for _, h := range hists {
		total.Merge(h)
	}
	return total, ops.Load(), errs.Load(), dur
}

func main() {
	var cfg config
	flag.StringVar(&cfg.Mode, "mode", "bench", "load | bench | mem")
	flag.StringVar(&cfg.Addr, "addr", "127.0.0.1:6379", "server host:port")
	flag.StringVar(&cfg.Client, "client", "goredis", "goredis | valkeygo")
	flag.IntVar(&cfg.Workers, "workers", 50, "concurrent goroutines")
	flag.IntVar(&cfg.Rate, "rate", 0, "target total ops/sec (open loop); 0 = closed loop")
	flag.StringVar(&cfg.Duration, "duration", "30s", "measured duration")
	flag.StringVar(&cfg.Warmup, "warmup", "5s", "warmup before measuring")
	flag.IntVar(&cfg.Keys, "keys", 1_000_000, "keyspace size")
	flag.IntVar(&cfg.ValueSize, "value-size", 100, "value size in bytes")
	flag.Float64Var(&cfg.ReadRatio, "read-ratio", 0.8, "fraction of GETs")
	flag.StringVar(&cfg.Dist, "dist", "uniform", "uniform | zipf")
	flag.IntVar(&cfg.Pool, "pool", 0, "go-redis PoolSize (0 = library default)")
	flag.IntVar(&cfg.Multiplex, "multiplex", 0, "valkey-go PipelineMultiplex (0 = library default)")
	flag.Int64Var(&cfg.Seed, "seed", 42, "random seed")
	flag.StringVar(&cfg.Engine, "engine", "", "label: redis | valkey")
	flag.IntVar(&cfg.IOThreads, "io-threads", 0, "label: server io-threads setting")
	flag.StringVar(&cfg.Phase, "phase", "", "label: A | B | mem")
	flag.IntVar(&cfg.Rep, "rep", 0, "label: repetition number")
	out := flag.String("out", "", "write JSON result to this file (default stdout)")
	flag.Parse()

	ctx := context.Background()
	admin := adminClient(cfg.Addr)
	defer admin.Close()
	if err := admin.Ping(ctx).Err(); err != nil {
		fmt.Fprintln(os.Stderr, "cannot reach server:", err)
		os.Exit(1)
	}

	res := result{
		Config:       cfg,
		Server:       serverInfo(ctx, admin),
		StartedAt:    time.Now().UTC().Format(time.RFC3339),
		GoMaxProcs:   runtime.GOMAXPROCS(0),
		LoadAvgStart: loadAvg(),
	}

	switch cfg.Mode {
	case "load":
		if err := loadKeys(ctx, admin, cfg.Keys, cfg.ValueSize, cfg.Seed); err != nil {
			fmt.Fprintln(os.Stderr, "load failed:", err)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr, "loaded %d keys of %d bytes\n", cfg.Keys, cfg.ValueSize)
		return

	case "mem":
		admin.FlushAll(ctx)
		time.Sleep(2 * time.Second)
		before := memStats(ctx, admin)
		if err := loadKeys(ctx, admin, cfg.Keys, cfg.ValueSize, cfg.Seed); err != nil {
			fmt.Fprintln(os.Stderr, "load failed:", err)
			os.Exit(1)
		}
		time.Sleep(2 * time.Second)
		after := memStats(ctx, admin)
		res.Memory = map[string]int64{
			"used_memory_before": before["used_memory"],
			"used_memory_after":  after["used_memory"],
			"used_memory_rss":    after["used_memory_rss"],
			"bytes_per_key":      (after["used_memory"] - before["used_memory"]) / int64(cfg.Keys),
		}

	case "bench":
		client, err := newKV(cfg.Client, cfg.Addr, cfg.Pool, cfg.Multiplex)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer client.Close()
		h, ops, errs, dur := runBench(ctx, cfg, client)
		res.ServerEnd = ioInfo(ctx, admin)
		res.Ops, res.Errors = ops, errs
		res.AchievedRPS = float64(ops) / dur.Seconds()
		res.MeanUS = h.Mean()
		res.LatencyUS = map[string]int64{
			"p50":    h.ValueAtQuantile(50),
			"p90":    h.ValueAtQuantile(90),
			"p99":    h.ValueAtQuantile(99),
			"p99.9":  h.ValueAtQuantile(99.9),
			"p99.99": h.ValueAtQuantile(99.99),
			"max":    h.Max(),
		}

	default:
		fmt.Fprintln(os.Stderr, "unknown -mode")
		os.Exit(2)
	}

	res.LoadAvgEnd = loadAvg()
	b, _ := json.MarshalIndent(res, "", "  ")
	if *out == "" {
		fmt.Println(string(b))
	} else if err := os.WriteFile(*out, b, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
