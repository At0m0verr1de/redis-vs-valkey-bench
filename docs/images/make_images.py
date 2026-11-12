"""Original images for the Redis vs Valkey Medium article, drawn from the benchmark results."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

SURF = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
VKGO = "#2a78d6"   # valkey-go (series 1)
GORED = "#eb6834"  # go-redis  (series 2)
OUT = "/home/claude/images/"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK, "figure.facecolor": SURF, "axes.facecolor": SURF,
    "savefig.facecolor": SURF,
})


def fmt_k(v):
    return f"{v/1e6:.2f}M" if v >= 1e6 else f"{v/1e3:,.0f}k"


def hbar(fname, title, sub, rows, unit_fmt, xlabel, legend=True):
    """rows: (label, value, client)"""
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=200)
    labels = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]
    cols = [VKGO if r[2] == "valkeygo" else GORED for r in rows][::-1]
    bars = ax.barh(labels, vals, color=cols, height=0.62, edgecolor=SURF, linewidth=2)
    top = max(vals)
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + top * 0.012, b.get_y() + b.get_height() / 2, unit_fmt(v),
                va="center", ha="left", fontsize=10.5, color=INK)
    ax.set_xlim(0, top * 1.18)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: unit_fmt(x) if x else "0"))
    ax.set_xlabel(xlabel, fontsize=9.5)
    fig.text(0.02, 0.95, title, fontsize=13.5, weight="bold", va="top")
    fig.text(0.02, 0.875, sub, fontsize=9.5, color=INK2, va="top")
    if legend:
        h = [Line2D([0], [0], color=VKGO, lw=8), Line2D([0], [0], color=GORED, lw=8)]
        fig.legend(h, ["valkey-go client", "go-redis client"], loc="lower center",
                   bbox_to_anchor=(0.6, 0.0), frameon=False, fontsize=9, ncol=2)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.25)
    fig.savefig(OUT + fname)
    plt.close(fig)


# --- Fig 2: Finding 1, io-threads 4
hbar("fig2_throughput_io4.png",
     "With 4 I/O threads, Redis 8.8 pulled ahead",
     "Max throughput · io-threads 4 · 100-byte values · 400 workers · median of 3 runs",
     [("Redis + go-redis", 208121, "goredis"), ("Valkey + go-redis", 181780, "goredis"),
      ("Redis + valkey-go", 1026118, "valkeygo"), ("Valkey + valkey-go", 742625, "valkeygo")],
     fmt_k, "operations per second")

# --- Fig 3: Finding 2, io-threads 1
hbar("fig3_client_vs_server.png",
     "Swapping the client mattered far more than the server",
     "Max throughput · io-threads 1 · 100-byte values · 400 workers · median of 3 runs",
     [("Redis + go-redis", 70687, "goredis"), ("Valkey + go-redis", 79627, "goredis"),
      ("Redis + valkey-go", 722654, "valkeygo"), ("Valkey + valkey-go", 699968, "valkeygo")],
     fmt_k, "operations per second")


def dumbbell(fname, title, sub, rows, a_lab, b_lab, xlabel, clients=True):
    """rows: (label, a, b, client) ; a=hollow, b=filled"""
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=200)
    n = len(rows)
    top = max(max(r[1], r[2]) for r in rows)
    for i, (lab, a, b, cl) in enumerate(rows[::-1]):
        c = VKGO if cl == "valkeygo" else GORED
        ax.plot([a, b], [i, i], color=c, lw=2, solid_capstyle="round", zorder=1)
        ax.scatter([a], [i], s=70, facecolor=SURF, edgecolor=c, linewidth=2, zorder=2)
        ax.scatter([b], [i], s=70, color=c, edgecolor=SURF, linewidth=2, zorder=3)
        ax.text(max(a, b) + top * 0.03, i, f"{a/1000:.1f} → {b/1000:.1f} ms", va="center",
                fontsize=10, color=INK)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlim(0, top * 1.38)
    ax.set_ylim(-0.6, n - 0.4)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1000:g} ms"))
    ax.set_xlabel(xlabel, fontsize=9.5)
    fig.text(0.02, 0.95, title, fontsize=13.5, weight="bold", va="top")
    fig.text(0.02, 0.875, sub, fontsize=9.5, color=INK2, va="top")
    h = [Line2D([0], [0], marker="o", color="none", markerfacecolor=SURF, markeredgecolor=INK2, markersize=8, markeredgewidth=2),
         Line2D([0], [0], marker="o", color="none", markerfacecolor=INK2, markersize=8),
         Line2D([0], [0], color=VKGO, lw=4), Line2D([0], [0], color=GORED, lw=4)]
    labs = [a_lab, b_lab, "valkey-go", "go-redis"]
    if not clients:
        h, labs = h[:2], labs[:2]
    fig.legend(h, labs, loc="lower center",
               bbox_to_anchor=(0.6, 0.0), frameon=False, fontsize=8.5, ncol=4)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.25)
    fig.savefig(OUT + fname)
    plt.close(fig)


# --- Fig 4: Finding 3, P99.9 no delay -> +50us
dumbbell("fig4_tail_network_delay.png",
         "Add network delay, and go-redis's slowest requests explode",
         "P99.9 latency at 33,988 req/s · io-threads 1 · 100-byte values · median of 5 runs",
         [("Redis + go-redis", 4843, 11639, "goredis"), ("Valkey + go-redis", 3835, 7995, "goredis"),
          ("Redis + valkey-go", 2285, 2673, "valkeygo"), ("Valkey + valkey-go", 2000, 2075, "valkeygo")],
         "no added delay", "+50 µs round trip", "P99.9 latency (lower is better)")

# --- Fig 5: Finding 4, io-threads trap
dumbbell("fig5_iothreads_trap.png",
         "More I/O threads made Redis's slowest requests worse",
         "P99.9 latency at 33,988 req/s · valkey-go client · 100-byte values · median of 5 runs",
         [("Redis, no delay", 2285, 5387, "valkeygo"), ("Valkey, no delay", 2000, 2177, "valkeygo"),
          ("Redis, +50 µs RTT", 2673, 10519, "valkeygo"), ("Valkey, +50 µs RTT", 2075, 1887, "valkeygo")],
         "io-threads 1", "io-threads 4", "P99.9 latency (lower is better)", clients=False)

# --- Fig 6: memory
fig, ax = plt.subplots(figsize=(7, 3.4), dpi=200)
sizes = ["32-byte values", "100-byte values", "1 KB values"]
redis_b = [85, 158, 1326]
valkey_b = [80, 145, 1329]
diff = [(v - r) / r * 100 for r, v in zip(redis_b, valkey_b)]
bars = ax.barh(sizes[::-1], diff[::-1], color=VKGO, height=0.55, edgecolor=SURF, linewidth=2)
for b, d, r, v in zip(bars, diff[::-1], redis_b[::-1], valkey_b[::-1]):
    ax.text(1.0, b.get_y() + b.get_height() / 2,
            f"{d:+.1f}%".replace("-", "−") + f"   {r:,} → {v:,} bytes/key", va="center",
            ha="left", fontsize=10, color=INK)
ax.axvline(0, color=INK2, lw=1)
ax.axvline(-20, color=GORED, lw=1.5, ls=(0, (4, 3)))
ax.text(-19.6, 2.5, "advertised: up to −20%", color=INK2, fontsize=9, va="center")
ax.set_xlim(-24, 21)
ax.set_xticks([-20, -15, -10, -5, 0])
ax.xaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=9)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: (f"{x:+.0f}%".replace("-", "−") if x else "0") if x <= 0 else ""))
ax.set_xlabel("Valkey 9.1 memory per key vs Redis 8.8", fontsize=9.5)
ax.set_ylim(-0.6, 2.75)
fig.text(0.02, 0.95, "Valkey saves memory on small keys, but nowhere near 20%", fontsize=13.5, weight="bold", va="top")
fig.text(0.02, 0.87, "1 million keys · used memory per key · identical in all 5 runs", fontsize=9.5, color=INK2, va="top")
fig.subplots_adjust(left=0.2, right=0.97, top=0.78, bottom=0.17)
fig.savefig(OUT + "fig6_memory.png")
plt.close(fig)


# --- Fig 1: setup diagram
fig, ax = plt.subplots(figsize=(7, 3.4), dpi=200)
ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")
def box(x, y, w, h, head, lines, edge):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2",
                                facecolor="#ffffff", edgecolor=edge, linewidth=1.6))
    ax.text(x + 2, y + h - 3.2, head, fontsize=9, color=INK2, va="top")
    for i, (t, bold) in enumerate(lines):
        ax.text(x + 2, y + h - 10 - i * 5.6, t, fontsize=10.5, va="top", weight="bold" if bold else "normal")
box(3, 13, 36, 28, "SOCKET 1 · 16 CORES", [("Go load generator", True), ("go-redis v9.23.0", False), ("or valkey-go v1.0.79", False)], INK2)
box(61, 13, 36, 28, "SOCKET 0 · 8 CORES", [("Cache server", True), ("Redis 8.8.4", False), ("or Valkey 9.1.3", False)], INK2)
ax.add_patch(FancyArrowPatch((40.5, 30), (59.5, 30), arrowstyle="-|>", mutation_scale=14, color=VKGO, lw=1.8))
ax.add_patch(FancyArrowPatch((59.5, 23), (40.5, 23), arrowstyle="-|>", mutation_scale=14, color=VKGO, lw=1.8))
ax.text(50, 34, "commands", ha="center", fontsize=9, color=INK2)
ax.text(50, 18.5, "replies", ha="center", fontsize=9, color=INK2)
ax.text(50, 26.5, "RESP", ha="center", fontsize=9.5, weight="bold", color=VKGO)
ax.text(50, 6, "Separate containers and network namespaces · optional +50 µs round trip to mimic a same-zone hop",
        ha="center", fontsize=8.5, color=INK2)
ax.text(3, 48.5, "Client and server on separate sockets of one machine", fontsize=12.5, weight="bold", va="top")
fig.savefig(OUT + "fig1_setup.png")
plt.close(fig)


# --- Cover
fig = plt.figure(figsize=(7, 3.94), dpi=200)  # 1400 x 788
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off")
ax.add_patch(plt.Rectangle((0, 0), 100, 56, color="#14213a"))
ax.text(6, 47, "Redis vs Valkey", fontsize=26, weight="bold", color="#f0efec", va="top")
ax.text(6, 37.5, "Everyone argues about the server.", fontsize=13, color="#c3c2b7", va="top")
ax.text(6, 26.5, "Swap the server", fontsize=11, color="#c3c2b7", va="center")
ax.add_patch(FancyBboxPatch((32, 24.2), 9, 4.6, boxstyle="round,pad=0,rounding_size=1", color="#d95926"))
ax.text(43, 26.5, "up to 1.3×", fontsize=13, weight="bold", color="#f0efec", va="center")
ax.text(6, 14.5, "Swap the client", fontsize=11, color="#c3c2b7", va="center")
ax.add_patch(FancyBboxPatch((32, 12.2), 60, 4.6, boxstyle="round,pad=0,rounding_size=1", color="#3987e5"))
ax.text(90, 14.5, "up to 10×", fontsize=13, weight="bold", color="#f0efec", va="center", ha="right")
ax.text(6, 4.5, "461 benchmark runs · Redis 8.8 · Valkey 9.1 · go-redis · valkey-go", fontsize=9, color="#c3c2b7")
fig.savefig(OUT + "cover.png")
plt.close(fig)
print("done")
