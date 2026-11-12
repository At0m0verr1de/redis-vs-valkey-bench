#!/usr/bin/env python3
"""Summarise rvbench results and produce Medium-ready ASCII charts.

Usage:  python3 analyze.py [results_dir]      (default: results)

Writes:
  results/summary_A.csv, summary_B.csv, summary_mem.csv
  results/report.md   tables, effect sizes, and ASCII charts to paste into Medium code blocks

Only the standard library is used.
"""
import csv
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else "results"
PCTS = ["p50", "p90", "p99", "p99.9", "p99.99", "max"]


def load(phase):
    runs = []
    for f in sorted(glob.glob(os.path.join(ROOT, phase, "*.json"))):
        with open(f) as fh:
            runs.append(json.load(fh))
    return runs


def bench_key(r):
    c = r["config"]
    return (c["engine"], c["io_threads"], c["client"], c["value_size"], c["workers"], c["rate"])


def summarise_bench(runs):
    groups = defaultdict(list)
    for r in runs:
        groups[bench_key(r)].append(r)
    rows = []
    for k, rs in sorted(groups.items()):
        engine, io, client, size, workers, rate = k
        row = dict(engine=engine, io_threads=io, client=client, value_size=size,
                   workers=workers, rate=rate, reps=len(rs),
                   errors=sum(r["errors"] for r in rs))
        rps = [r["achieved_rps"] for r in rs]
        row["rps_median"] = round(statistics.median(rps))
        row["rps_min"], row["rps_max"] = round(min(rps)), round(max(rps))
        for p in PCTS:
            vals = [r["latency_us"][p] for r in rs]
            row[f"{p}_median"] = statistics.median(vals)
            row[f"{p}_min"], row[f"{p}_max"] = min(vals), max(vals)
        versions = {r["server"].get("valkey_version") or r["server"].get("redis_version") for r in rs}
        row["server_version"] = ",".join(sorted(v for v in versions if v))
        # The host is shared; the 1-minute load at run start flags noisy reps.
        row["load1_max"] = max(float(r.get("loadavg_start", "0").split()[0]) for r in rs)
        rows.append(row)
    return rows


def summarise_mem(runs):
    groups = defaultdict(list)
    for r in runs:
        groups[(r["config"]["engine"], r["config"]["value_size"])].append(r)
    rows = []
    for (engine, size), rs in sorted(groups.items()):
        bpk = [r["memory"]["bytes_per_key"] for r in rs]
        rows.append(dict(engine=engine, value_size=size, reps=len(rs),
                         bytes_per_key_median=statistics.median(bpk),
                         bytes_per_key_min=min(bpk), bytes_per_key_max=max(bpk),
                         module_count=rs[0]["server"].get("module_count", "")))
    return rows


def write_csv(rows, name):
    if not rows:
        return
    path = os.path.join(ROOT, name)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def bars(items, unit="", width=36):
    """items: list of (label, value). Returns an ASCII bar chart string."""
    if not items:
        return ""
    lw = max(len(l) for l, _ in items)
    top = max(v for _, v in items) or 1
    lines = []
    for label, v in items:
        n = max(1, round(width * v / top))
        lines.append(f"{label.ljust(lw)}  {'█' * n} {fmt(v)}{unit}")
    return "\n".join(lines)


def fmt(v):
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.1f}"
    return f"{int(v):,}"


def pct(a, b):
    """% change going from a to b (negative = b is lower)."""
    return (b - a) / a * 100 if a else float("nan")


def overlaps(r1, r2, metric):
    return not (r1[f"{metric}_max"] < r2[f"{metric}_min"] or r2[f"{metric}_max"] < r1[f"{metric}_min"])


def label(r):
    return f"{r['engine']}+{r['client']}"


def find(rows, **kw):
    return next((r for r in rows if all(r[k] == v for k, v in kw.items())), None)


def report(A, B, M):
    out = ["# rvbench report", ""]
    out.append("Medians across repetitions. A difference is marked *within noise* when the "
               "min–max ranges of the two setups overlap.\n")

    if A:
        out.append("## Phase A — maximum throughput (closed loop)\n")
        for (io, size, w) in sorted({(r["io_threads"], r["value_size"], r["workers"]) for r in A}):
            sel = [r for r in A if (r["io_threads"], r["value_size"], r["workers"]) == (io, size, w)]
            out.append(f"### io-threads={io}, value={size}B, workers={w}\n")
            out.append("```\n" + bars([(label(r), r["rps_median"]) for r in sel], " ops/s") + "\n```\n")
        busiest = [r for r in A if r["workers"] == max(x["workers"] for x in A)]
        low = min(busiest, key=lambda r: r["rps_median"])
        out.append(f"**Suggested RATE for phase B:** {int(low['rps_median'] * 0.6):,} ops/s "
                   f"(60% of the lowest max throughput, {label(low)} io={low['io_threads']} "
                   f"v={low['value_size']}B).\n")

        ios = sorted({r["io_threads"] for r in A})
        if len(ios) > 1:
            out.append(f"### io-threads effect on max throughput (workers={busiest[0]['workers']})\n")
            for r1 in [r for r in busiest if r["io_threads"] == ios[0]]:
                r2 = find(busiest, engine=r1["engine"], client=r1["client"],
                          value_size=r1["value_size"], io_threads=ios[-1])
                if r2:
                    note = " *within noise*" if overlaps(r1, r2, "rps") else ""
                    out.append(f"- {label(r1)} v={r1['value_size']}B: io {ios[0]}→{ios[-1]} "
                               f"{pct(r1['rps_median'], r2['rps_median']):+.1f}%{note}")
            out.append("")

            out.append("### Server effect on max throughput\n")
            for r1 in [r for r in busiest if r["engine"] != "valkey"]:
                r2 = find(busiest, engine="valkey", client=r1["client"],
                          value_size=r1["value_size"], io_threads=r1["io_threads"])
                if r2:
                    note = " *within noise*" if overlaps(r1, r2, "rps") else ""
                    out.append(f"- {r1['engine']}→valkey, {r1['client']}, io={r1['io_threads']}, "
                               f"v={r1['value_size']}B: {pct(r1['rps_median'], r2['rps_median']):+.1f}%{note}")
            out.append("")

    if B:
        out.append("## Phase B — tail latency at a fixed rate (open loop)\n")
        for (io, size) in sorted({(r["io_threads"], r["value_size"]) for r in B}):
            sel = [r for r in B if (r["io_threads"], r["value_size"]) == (io, size)]
            out.append(f"### io-threads={io}, value={size}B, rate={sel[0]['rate']:,} ops/s\n")
            out.append("| setup | p50 | p99 | p99.9 | p99.99 | errors |\n|---|---|---|---|---|---|")
            for r in sel:
                out.append(f"| {label(r)} | {r['p50_median']}µs | {r['p99_median']}µs | "
                           f"{r['p99.9_median']}µs | {r['p99.99_median']}µs | {r['errors']} |")
            out.append("\nP99.9 latency (lower is better):\n")
            out.append("```\n" + bars([(label(r), r["p99.9_median"]) for r in sel], " µs") + "\n```\n")

            # The key test: does swapping the server or swapping the client move the tail more?
            out.append("**Server effect vs client effect (P99.9 and P99.99):**\n")
            for metric in ("p99.9", "p99.99"):
                m = f"{metric}_median"
                for base in ("redis", "redisnomod"):
                    for client in ("goredis", "valkeygo"):
                        a, b = find(sel, engine=base, client=client), find(sel, engine="valkey", client=client)
                        if a and b:
                            note = " *within noise*" if overlaps(a, b, metric) else ""
                            out.append(f"- Server swap {base}→valkey with {client}: {metric} "
                                       f"{pct(a[m], b[m]):+.1f}%{note}")
                for engine in ("redis", "redisnomod", "valkey"):
                    a, b = find(sel, engine=engine, client="goredis"), find(sel, engine=engine, client="valkeygo")
                    if a and b:
                        note = " *within noise*" if overlaps(a, b, metric) else ""
                        out.append(f"- Client swap goredis→valkeygo on {engine}: {metric} "
                                   f"{pct(a[m], b[m]):+.1f}%{note}")
            out.append("")

        # io-threads effect
        ios = sorted({r["io_threads"] for r in B})
        if len(ios) > 1:
            out.append("### io-threads effect on P99.9\n")
            for r1 in [r for r in B if r["io_threads"] == ios[0]]:
                r2 = find(B, engine=r1["engine"], client=r1["client"], value_size=r1["value_size"],
                          io_threads=ios[-1])
                if r2:
                    note = " *within noise*" if overlaps(r1, r2, "p99.9") else ""
                    out.append(f"- {label(r1)} v={r1['value_size']}B: io {ios[0]}→{ios[-1]} "
                               f"{pct(r1['p99.9_median'], r2['p99.9_median']):+.1f}%{note}")
            out.append("")

    if M:
        out.append("## Memory per key\n")
        for size in sorted({r["value_size"] for r in M}):
            sel = [r for r in M if r["value_size"] == size]
            out.append(f"### value={size}B\n")
            out.append("```\n" + bars([(r["engine"], r["bytes_per_key_median"]) for r in sel],
                                      " bytes/key") + "\n```")
            b = find(sel, engine="valkey")
            for base in ("redis", "redisnomod"):
                a = find(sel, engine=base)
                if a and b:
                    note = " *within noise*" if overlaps(a, b, "bytes_per_key") else ""
                    out.append(f"Valkey vs {base}: "
                               f"{pct(a['bytes_per_key_median'], b['bytes_per_key_median']):+.1f}%{note} "
                               f"({base} modules loaded: {a['module_count']}, Valkey: {b['module_count']})\n")

    if A or B:
        loads = [r["load1_max"] for r in A + B]
        out.append(f"Host 1-minute load at run start ranged up to {max(loads):.1f} "
                   f"on 96 vCPUs (shared host).\n")

    errs = sum(r["errors"] for r in A + B)
    if errs:
        out.append(f"> ⚠️ {errs:,} request errors recorded. Check them before trusting the numbers.\n")
    return "\n".join(out)


def main():
    A = summarise_bench(load("A"))
    B = summarise_bench(load("B"))
    M = summarise_mem(load("mem"))
    if not (A or B or M):
        sys.exit(f"no results found under {ROOT}/A, {ROOT}/B or {ROOT}/mem")
    write_csv(A, "summary_A.csv")
    write_csv(B, "summary_B.csv")
    write_csv(M, "summary_mem.csv")
    text = report(A, B, M)
    with open(os.path.join(ROOT, "report.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
