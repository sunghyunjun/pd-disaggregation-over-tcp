#!/usr/bin/env python3
"""Write-up figures from safe data only (results/safe_runs.csv, safety 안전/주의).

Usage:
  uv run --with matplotlib python3 harness/make_figures.py [-o paper/figures]

Writes <name>.pdf and <name>.svg per figure plus figures.json (numbers behind
each figure). Values quoted from RESULTS.md tables (network and transfer
decomposition) are marked in figures.json under "quoted".
"""
import argparse, csv, json, os, statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

INK, INK2, GRID = "#0b0b0b", "#52514e", "#dcdcd6"
# Deuteranomaly-safe: two hue families (blue = replicas, orange = disaggregated), variants by
# lightness + marker + line style. Solid = two nodes, dashed / dash-dot = three nodes.
S1, S2, S3, S4, S5 = "#1d4f91", "#c8501e", "#e9a23b", "#6b3410", "#6aa8e0"
LS3 = (0, (6, 2.5))            # dashed, long enough to read in a legend
LS3B = (0, (7, 2, 1.5, 2))     # dash-dot
NEUTRAL = "#9a9a94"
GPU_H = 3.363  # g7e.2xlarge on-demand $/h, us-east-1 (RESULTS.md E5)

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.titlesize": 9.5,
    "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.axisbelow": True, "lines.linewidth": 2.2, "lines.markersize": 5.5,
    "legend.handlelength": 3.4, "legend.handletextpad": 0.6,
    "svg.fonttype": "none", "pdf.fonttype": 42, "legend.frameon": False,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})

META = {}


def load(path):
    rows = []
    for r in csv.DictReader(open(path)):
        if r["safety"] not in ("안전", "주의"):
            continue
        for k in ("attain_chat", "attain_doc", "ttft_p50_ms", "ttft_p99_ms", "tbt_p99_ms",
                  "goodput_chat_tok_s", "stall_req_frac"):
            try:
                r[k] = float(r[k])
            except (ValueError, KeyError):
                r[k] = float("nan")
        try:
            r["rate_f"] = float(r["rate"])
        except ValueError:
            r["rate_f"] = None
        rows.append(r)
    return rows


def pick(rows, stage=None, config=None, workload=None, network="N0", inlen=None):
    out = []
    for r in rows:
        if stage and r["stage"] not in (stage if isinstance(stage, tuple) else (stage,)):
            continue
        if config and r["config"] != config:
            continue
        if workload and r["workload"] != workload:
            continue
        if network and r["network"] != network:
            continue
        if inlen and r["input_len_median"] != str(inlen):
            continue
        out.append(r)
    return out


def by_rate(rs, key="attain_chat"):
    g = defaultdict(list)
    for r in rs:
        if r["rate_f"] is not None:
            g[r["rate_f"]].append(r)
    return {k: g[k] for k in sorted(g)}


def save(fig, out, name, meta):
    fig.savefig(os.path.join(out, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(out, name + ".svg"), bbox_inches="tight", transparent=True)
    plt.close(fig)
    META[name] = meta


def slo_line(ax, y=0.9):
    ax.axhline(y, color=INK2, lw=1, ls=(0, (4, 3)))


def range_series(ax, grouped, per_gpu, color, marker, label, ls="-", caution=()):
    xs, ys, lo, hi = [], [], [], []
    for rate, rs in grouped.items():
        a = [r["attain_chat"] for r in rs]
        xs.append(rate / per_gpu); ys.append(st.mean(a)); lo.append(min(a)); hi.append(max(a))
    ax.plot(xs, ys, color=color, marker=marker, ls=ls, label=label)
    ax.vlines(xs, lo, hi, color=color, lw=1.2)
    for x, y, rate in zip(xs, ys, grouped):
        if rate in caution:
            ax.plot([x], [y], marker=marker, mfc="white", mec=color, ms=7, ls="none")
    return [{"rate": r, "per_gpu": r / per_gpu, "n": len(v),
             "attain": [round(x["attain_chat"], 3) for x in v]} for r, v in grouped.items()]


def is_pd(cfg):
    c = cfg.lower()
    return any(t in c for t in ("p1", "1p1d", "1p2d", "2p1d", "pull", "push", "xfer", "d1"))


# ---------------------------------------------------------------- figures
def f01(rows, out):
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    pts = {"rep": [], "pd": []}
    for r in rows:
        if r["ttft_p99_ms"] >= 1000 or r["tbt_p99_ms"] != r["tbt_p99_ms"]:
            continue
        pts["pd" if is_pd(r["config"]) else "rep"].append((r["tbt_p99_ms"], r["attain_chat"], r["run_id"]))
    for k, c, m, lab in (("rep", S1, "o", "Replicas / single node"), ("pd", S2, "s", "Disaggregated")):
        ax.scatter([p[0] for p in pts[k]], [p[1] for p in pts[k]], s=16, color=c, marker=m,
                   label=lab, alpha=0.85, edgecolors="white", linewidths=0.4)
    ax.axvline(50, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.axhline(0.9, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.set_xscale("log"); ax.set_ylim(-0.03, 1.03)
    xlo = min(p[0] for k in pts for p in pts[k]) * 0.85
    ax.set_xlim(left=xlo)
    ax.fill_between([xlo, 50], -0.03, 0.9, color=GRID, alpha=0.55, lw=0, zorder=0)
    ax.text(xlo * 1.05, 0.02, "System p99 within the 50 ms budget,\nyet attainment below 0.9", ha="left",
            va="bottom", fontsize=7.3, color=INK2)
    ax.text(51, 1.0, "50 ms", fontsize=7, color=INK2, va="top")
    ax.text(260, 0.905, "0.9", fontsize=7, color=INK2, va="bottom", ha="right")
    ax.set_xlabel("System-wide inter-token latency p99 (ms, log)")
    ax.set_ylabel("Strict-SLO attainment (per request)")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.86))
    ax.set_title("System percentiles hide per-request stalls")
    bad = [p for p in pts["rep"] if p[0] < 50 and p[1] < 0.9]
    save(fig, out, "fig01_request_vs_system", {
        "n_runs": len(pts["rep"]) + len(pts["pd"]), "filter": "safe runs with TTFT p99 < 1 s",
        "replica_runs_p99_under_50_but_attain_below_0.9": len(bad),
        "pd_runs_p99_under_50_but_attain_below_0.9": len([p for p in pts["pd"] if p[0] < 50 and p[1] < 0.9])})


def f02(rows, out):
    pts = [("1", "p1_tcfix_1gbit"), ("2", "p1_tcfix_2gbit"), ("3", "p1_tcfix_3gbit"),
           ("5", "p1_tcfix_5gbit"), ("no limit", "p1_best")]
    data = []
    for lab, cfg in pts:
        r = [x for x in pick(rows, "D", cfg, "random", inlen=4096) if x["rate"] == "0.5"][0]
        data.append((lab, r["ttft_p50_ms"], r["attain_chat"]))
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.4, 2.7))
    xs = range(len(data))
    a.plot(xs, [d[1] for d in data], color=S2, marker="s")
    a.axhline(1000, color=INK2, lw=1, ls=(0, (4, 3)))
    a.text(4.1, 1040, "TTFT budget 1 s", fontsize=7.5, color=INK2, ha="right")
    a.set_ylabel("TTFT p50 (ms)"); a.set_title("(a) First token")
    b.bar(xs, [d[2] for d in data], color=S2, width=0.55)
    for x, d in zip(xs, data):
        b.text(x, d[2] + 0.02, f"{d[2]:.2f}", ha="center", fontsize=7.3)
    slo_line(b); b.set_ylim(0, 1.12); b.set_ylabel("Strict-SLO attainment"); b.set_title("(b) Attainment")
    for ax in (a, b):
        ax.set_xticks(list(xs)); ax.set_xticklabels([d[0] for d in data])
        ax.set_xlabel("Sender rate limit (Gbps)")
    fig.suptitle("1P1D, 26B NVFP4, two g7 nodes, 4K input at 0.5 req/s (tuned transfer)", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig02_bandwidth_sweep", {"points": [{"limit_gbps": d[0], "ttft_p50": round(d[1]),
                                                           "attain": d[2]} for d in data]})


def f03(rows, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.3})
    flows = [1, 2, 4, 8]; gb = [9.54, 19.06, 38.11, 49.72]
    a.plot(flows, gb, color=S1, marker="o")
    a.axhline(50, color=INK2, lw=1, ls=(0, (4, 3)))
    a.text(1, 51.5, "instance 50 Gbps", fontsize=7.5, color=INK2)
    a.set_xticks(flows); a.set_ylim(0, 58)
    a.set_xlabel("Parallel TCP flows (iperf, placement group)"); a.set_ylabel("Gbps"); a.set_title("(a) Bandwidth vs TCP flows")
    cats = ["No placement\ngroup", "Placement\ngroup"]
    cap = [4.97, 9.54]; eff = [6.55, 13.96]
    x = [0, 1]; w = 0.34
    b.bar([i - w / 2 for i in x], cap, w, color=S1, label="One TCP flow limit (iperf)")
    b.bar([i + w / 2 for i in x], eff, w, color=S2, label="Measured KV cache transfer rate")
    for i in x:
        b.text(i + w / 2, eff[i] + 0.4, f"{eff[i] / cap[i]:.2f}×", ha="center", fontsize=7.5, color=INK)
    knobs = [13.86, 14.43, 13.99, 13.58]
    b.scatter([1 + w / 2 + 0.2] * 4, knobs, s=12, color=INK2, zorder=3, label="KV cache transfer rate, 4 other UCX/NIXL settings")
    b.set_xticks(x); b.set_xticklabels(cats); b.set_ylim(0, 17); b.set_ylabel("Gbps")
    b.set_title("(b) Flow cap vs KV transfer"); h, l = b.get_legend_handles_labels(); o = [l.index(x) for x in ("One TCP flow limit (iperf)", "Measured KV cache transfer rate", "KV cache transfer rate, 4 other UCX/NIXL settings")]
    b.legend([h[i] for i in o], [l[i] for i in o], loc="upper left", bbox_to_anchor=(-0.02, -0.25), fontsize=7.5)
    fig.tight_layout()
    save(fig, out, "fig03_network", {"quoted": "RESULTS.md E4-0, E4-2", "iperf_pg": dict(zip(flows, gb)),
                                     "cap": cap, "effective": eff, "knobs": knobs})


def f04(rows, out):
    items = [  # label, single, transfer, residual, predicted
        ("26B FP8 · 4K · 0.5 req/s\nno placement group", 158, 324, 0, None),
        ("26B FP8 · 4K · 0.5 req/s\nplacement group", 158, 165, 28, None),
        ("26B NVFP4 · 4K · 1 req/s\nplacement group", 130, 84, 53, 235),
        ("31B NVFP4 · 4K · 0.25 req/s\nplacement group", 483, 283, 87, 820),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ys = list(range(len(items)))[::-1]
    for y, (lab, s, t, r, p) in zip(ys, items):
        ax.barh(y, s, color=NEUTRAL, height=0.55)
        ax.barh(y, t, left=s, color=S2, height=0.55)
        ax.barh(y, r, left=s + t, color="#f4b79c", height=0.55)
        ax.text(s + t + r + 12, y, f"{s + t + r} ms", va="center", fontsize=7.5, color=INK)
        if p:
            ax.plot([p, p], [y - 0.34, y + 0.34], color=INK, lw=1.6)
    ax.set_yticks(ys); ax.set_yticklabels([i[0] for i in items])
    ax.set_xlabel("TTFT p50 (ms)"); ax.set_xlim(0, 1000); ax.grid(axis="y", visible=False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=NEUTRAL), plt.Rectangle((0, 0), 1, 1, color=S2),
                       plt.Rectangle((0, 0), 1, 1, color="#f4b79c"), Line2D([0], [0], color=INK, lw=1.6)],
              labels=["Single-node TTFT", "KV transfer", "Residual", "Predicted before run"],
              loc="upper left", bbox_to_anchor=(0, -0.22), ncol=4, fontsize=7.5)
    ax.set_title("Disaggregation adds TTFT almost entirely through KV transfer")
    save(fig, out, "fig04_ttft_decomposition", {"quoted": "RESULTS.md E4-1, E5 formula check",
                                                "items": items})


def f05(rows, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.4, 2.7), sharey=True)
    L = [4096, 16384, 32000]; meta = {}
    for cfg, c, m, lab in (("B2", S1, "o", "Replicas (2)"), ("P1", S2, "s", "1P1D")):
        rs = [[x for x in pick(rows, "B", cfg, "random", inlen=l) if x["rate"] == "0.5"][0] for l in L]
        a.plot(range(3), [r["attain_chat"] for r in rs], color=c, marker=m, label=lab)
        b.plot(range(3), [r["attain_doc"] for r in rs], color=c, marker=m, label=lab)
        meta[cfg] = [(l, r["attain_chat"], r["attain_doc"]) for l, r in zip(L, rs)]
    for ax, t in ((a, "(a) Strict SLO (1 s / 50 ms)"), (b, "(b) Relaxed SLO (3 s / 250 ms)")):
        ax.set_xticks(range(3)); ax.set_xticklabels(["4K", "16K", "32K"]); ax.set_xlabel("Input length")
        slo_line(ax); ax.set_title(t); ax.set_ylim(-0.03, 1.05)
    a.set_ylabel("SLO attainment"); a.legend(loc="upper right")
    fig.suptitle("26B NVFP4, two g7 nodes, 0.5 req/s (default transfer settings, before tuning)", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig05_input_length", meta)


def f06(rows, out):
    groups = [
        ("g7 · PRO 4500\n26B NVFP4\n(before tuning)", ("B", "B2", "4096", "1"), ("B", "P1", "4096", "1")),
        ("g6e · L40S\n26B FP8", ("E3", "B2", "4096", "1"), ("E3", "P1tuned", "4096", "1")),
        ("g7e · PRO 6000\n26B FP8", ("E2", "B2", "4096", "1"), ("E2", "P1tuned", "4096", "1")),
        ("g7e · PRO 6000\n26B NVFP4\n+ placement group", ("E7", "26_B2", "4096", "1"), ("E7", "26_1P1D", "4096", "1")),
    ]

    def one(stage, cfg, inl, rate):
        rs = [x for x in pick(rows, stage, cfg, "random", inlen=inl) if x["rate"] == rate]
        return st.mean([x["attain_chat"] for x in rs])
    fig, ax = plt.subplots(figsize=(6.2, 2.7)); w = 0.34; meta = []
    for i, (lab, rep, pd) in enumerate(groups):
        a, b = one(*rep), one(*pd)
        ax.bar(i - w / 2, a, w, color=S1, label="Replicas (2)" if i == 0 else None)
        ax.bar(i + w / 2, b, w, color=S2, label="1P1D" if i == 0 else None)
        for x, v in ((i - w / 2, a), (i + w / 2, b)):
            ax.text(x, v + 0.02, f"{v:.2f}", ha="center", fontsize=7.5)
        meta.append({"group": lab.replace("\n", " "), "replicas": a, "pd": b})
    slo_line(ax); ax.set_ylim(0, 1.12); ax.set_xticks(range(4))
    ax.set_xticklabels([g[0] for g in groups]); ax.set_ylabel("Strict-SLO attainment")
    ax.set_title("4K input at 1 req/s: replicas hold only with a fast GPU and light weights", fontsize=9)
    ax.legend(loc="upper left")
    save(fig, out, "fig06_gpu_speed_4k", meta)


def f07(rows, out):
    fig, ax = plt.subplots(figsize=(6.2, 2.9)); meta = {}
    series = [("E1", "l40s_26b_fp8_kvmatch", S2, "^", "L40S (g6e), KV 226k"),
              ("E1", "pro6000_26b_fp8_kvmax", S5, "D", "PRO 6000 (g7e), KV max"),
              ("E1", "pro6000_26b_fp8_kvmatch", S1, "o", "PRO 6000 (g7e), KV matched, first day"),
              ("E7", "26F_single_kvmatch", S1, "o", "PRO 6000 (g7e), KV matched, 3 repeats two days later")]
    for stg, cfg, c, m, lab in series:
        g = by_rate(pick(rows, stg, cfg, "sharegpt"))
        meta[cfg] = range_series(ax, g, 1, c, m, lab, LS3 if cfg.startswith("pro6000_26b_fp8_kvmatch") else "-")
    slo_line(ax); ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel("ShareGPT request rate, one GPU (req/s)"); ax.set_ylabel("Strict-SLO attainment")
    ax.set_title("Single node, 26B FP8: supported load 1 vs 16 req/s at equal KV")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=7.5)
    save(fig, out, "fig07_gpu_kv", meta)


def f08(rows, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True); meta = {}
    cfgs = [("26_B2", 2, S1, "o", "-", "Replicas (2)"), ("26_B3", 3, S5, "o", LS3, "Replicas (3)"),
            ("26_1P1D", 2, S2, "s", "-", "1P1D"), ("26_1P2D", 3, S3, "^", LS3, "1P2D"),
            ("26_2P1D", 3, S4, "D", LS3B, "2P1D")]
    for cfg, n, c, m, ls, lab in cfgs:
        g = by_rate(pick(rows, ("E5", "E7"), cfg, "random", inlen=4096))
        meta["4k_" + cfg] = range_series(a, g, n, c, m, lab, ls)
        gc = by_rate(pick(rows, ("E5", "E7"), cfg, "sharegpt"))
        caution = {r for r, v in gc.items() if any(x["safety"] == "주의" for x in v)}
        meta["chat_" + cfg] = range_series(b, gc, n, c, m, lab, ls, caution)
    a.set_title("(a) 4K input"); b.set_title("(b) ShareGPT chat")
    a.set_xlabel("Request rate per GPU (req/s)"); b.set_xlabel("Request rate per GPU (req/s)")
    a.set_ylabel("Strict-SLO attainment")
    for ax in (a, b):
        slo_line(ax); ax.set_ylim(-0.03, 1.05)
    b.text(0.98, 0.04, "hollow marker: client-limited, not used for verdicts", transform=b.transAxes, ha="right", fontsize=7, color=INK2)
    a.legend(loc="lower left", fontsize=7.5)
    fig.suptitle("26B NVFP4, g7e in a placement group. Vertical bars: min–max over repeated runs", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig08_scaling_26b", meta)


def f09(rows, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True); meta = {}
    for cfg, n, c, m, ls, lab in (("31_B2", 2, S1, "o", "-", "Replicas (2)"), ("31_1P1D", 2, S2, "s", "-", "1P1D")):
        meta["chat_" + cfg] = range_series(a, by_rate(pick(rows, ("E5", "E7"), cfg, "sharegpt")), n, c, m, lab, ls)
    for cfg, n, c, m, ls, lab in (("31_B2", 2, S1, "o", "-", "Replicas (2)"), ("31_B3", 3, S5, "o", LS3, "Replicas (3)"),
                                  ("31_1P1D", 2, S2, "s", "-", "1P1D"), ("31_1P2D", 3, S3, "^", LS3, "1P2D"),
                                  ("31_2P1D", 3, S4, "D", LS3B, "2P1D")):
        g = by_rate(pick(rows, ("E5", "E7"), cfg, "random", inlen=4096))
        if g:
            meta["4k_" + cfg] = range_series(b, g, n, c, m, lab, ls)
    a.set_title("(a) ShareGPT chat"); b.set_title("(b) 4K input")
    a.set_xlabel("Request rate per GPU (req/s)"); b.set_xlabel("Request rate per GPU (req/s)")
    a.set_ylabel("Strict-SLO attainment")
    for ax in (a, b):
        slo_line(ax); ax.set_ylim(-0.03, 1.05)
    a.legend(loc="lower left"); b.legend(loc="upper right", fontsize=7.5)
    fig.suptitle("31B NVFP4, g7e in a placement group. Vertical bars: min–max over repeated runs", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig09_scaling_31b", meta)


def f10(rows, out):
    prec = [("NVFP4", "26"), ("FP8", "26F"), ("BF16", "26H")]
    points = [("4K input, 1 req/s", "random", "1"), ("4K input, 2 req/s", "random", "2"), ("ShareGPT, 16 req/s", "sharegpt", "16")]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.8), sharey=True); w = 0.34; meta = []
    for ax, (t, wl, rate) in zip(axes, points):
        for i, (pl, pre) in enumerate(prec):
            vals = []
            for suf, c, off in (("_B2", S1, -0.19), ("_1P1D", S2, 0.19)):
                rs = [x for x in pick(rows, "E7", pre + suf, wl) if x["rate"] == rate]
                v = st.mean([x["attain_chat"] for x in rs]); vals.append(v)
                ax.bar(i + off, v, w, color=c)
                ax.text(i + off, v + 0.02, f"{v:.2f}", ha="center", fontsize=6.3)
            meta.append({"point": t, "precision": pl, "replicas": vals[0], "pd": vals[1]})
        slo_line(ax); ax.set_title(t); ax.set_xticks(range(3)); ax.set_xticklabels([p[0] for p in prec])
        ax.set_ylim(0, 1.13)
    axes[0].set_ylabel("Strict-SLO attainment")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=S1), plt.Rectangle((0, 0), 1, 1, color=S2)],
               labels=["Replicas (2)", "1P1D"], loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    fig.suptitle("26B on the same two g7e nodes (placement group), weight precision varied, measured the same day", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig10_quantization", meta)


def f11(rows, out):
    cfgs = [("26_B2", "Rep ×2", S1), ("26_1P1D", "1P1D", S2), ("26_B3", "Rep ×3", S5),
            ("26_1P2D", "1P2D", S3), ("26_2P1D", "2P1D", S4), ("31_B2", "Rep ×2", S1),
            ("31_1P1D", "1P1D", S2)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.8, 2.8)); meta = []
    for i, (cfg, lab, c) in enumerate(cfgs):
        rs = pick(rows, "E7", cfg, "azure_conv")
        t = [x["ttft_p50_ms"] for x in rs]; at = [x["attain_chat"] for x in rs]
        a.bar(i, st.mean(t), color=c, width=0.6)
        b.bar(i, st.mean(at), color=c, width=0.6)
        b.vlines(i, min(at), max(at), color=INK, lw=1)
        meta.append({"config": cfg, "req_s": round(st.mean(float(x["req_per_s"]) for x in rs), 2),
                     "ttft_p50": [round(v) for v in t], "attain": at})
    rates = [m["req_s"] for m in meta]
    for ax in (a, b):
        ax.set_xticks(range(len(cfgs)))
        ax.set_xticklabels([f"{c[1]}\n{r:.1f}/s" for c, r in zip(cfgs, rates)], fontsize=6.6)
        ax.axvline(4.5, color=INK2, lw=0.9, ls=(0, (2, 2)))
        ax.text(2.0, -0.30, "26B NVFP4", transform=ax.get_xaxis_transform(), ha="center", fontsize=7.3, color=INK)
        ax.text(5.5, -0.30, "31B NVFP4", transform=ax.get_xaxis_transform(), ha="center", fontsize=7.3, color=INK)
    a.set_ylabel("TTFT p50 (ms)"); a.set_title("(a) First token")
    b.set_ylabel("Strict-SLO attainment"); b.set_ylim(0, 1.08); slo_line(b); b.set_title("(b) Attainment")
    fig.suptitle("Azure conversation trace, 600 requests (input median 996, output 217 tokens); x labels give the replayed rate", x=0.01,
                 ha="left", fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig11_trace", meta)


def supported(rows, stages, cfg, wl, inlen=None):
    g = by_rate(pick(rows, stages, cfg, wl, inlen=inlen))
    best = None
    for rate, rs in g.items():
        if any(x["safety"] == "주의" for x in rs):
            continue
        if min(x["attain_chat"] for x in rs) >= 0.9:
            best = (rate, rs)
    return best


def f12(rows, out):
    groups = [("26B · 4K\n2 nodes", ("26_B2", 2), ("26_1P1D", 2), "random", 4096),
              ("26B · 4K\n3 nodes", ("26_B3", 3), ("26_1P2D", 3), "random", 4096),
              ("26B · chat\n2 nodes", ("26_B2", 2), ("26_1P1D", 2), "sharegpt", None),
              ("31B · chat\n2 nodes", ("31_B2", 2), ("31_1P1D", 2), "sharegpt", None),
              ("31B · 4K\n2 nodes", ("31_B2", 2), ("31_1P1D", 2), "random", 4096)]
    fig, ax = plt.subplots(figsize=(6.4, 2.9)); w = 0.36; meta = []
    for i, (lab, rep, pd, wl, inl) in enumerate(groups):
        row = {"group": lab.replace("\n", " ")}
        for (cfg, n), c, off, key in ((rep, S1, -w / 2, "replicas"), (pd, S2, w / 2, "pd")):
            s = supported(rows, ("E5", "E7"), cfg, wl, inl)
            if s is None:
                ax.text(i + off, 0.12, "none", rotation=90, ha="center", va="bottom", fontsize=7, color=INK2)
                row[key] = None; continue
            rate, rs = s
            cost = GPU_H * n / (st.mean(x["goodput_chat_tok_s"] for x in rs) * 3600) * 1e6
            ax.bar(i + off, cost, w, color=c)
            ax.text(i + off, cost * 1.08, f"${cost:.2f}\n{rate:g} req/s", ha="center", fontsize=6.8)
            row[key] = {"config": cfg, "rate": rate, "cost_per_1M": round(cost, 3), "n": len(rs)}
        meta.append(row)
    ax.set_yscale("log"); ax.set_ylim(0.1, 20); ax.set_xlim(-0.6, len(groups) - 0.4)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([g[0] for g in groups], fontsize=7.5)
    ax.set_ylabel("$ per 1M SLO-meeting tokens (log)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=S1), plt.Rectangle((0, 0), 1, 1, color=S2)],
              labels=["Replicas", "Disaggregated"], loc="upper left")
    ax.set_title("Cost at the highest rate where every repeat meets the chat SLO")
    save(fig, out, "fig12_cost", meta)


def f13(rows, out):
    e7 = defaultdict(list)
    for r in pick(rows, "E7"):
        if r["workload"] in ("random", "sharegpt"):
            e7[(r["config"], r["workload"], r["rate"])].append(r)
    keys = [k for k, v in e7.items() if len(v) >= 3]
    keys.sort(key=lambda k: st.mean(x["attain_chat"] for x in e7[k]))
    e5 = {(r["config"], r["workload"], r["rate"]): r["attain_chat"] for r in pick(rows, "E5")}
    fig, ax = plt.subplots(figsize=(6.2, 3.6)); meta = []
    ax.axvspan(0.85, 0.95, color=GRID, alpha=0.6, lw=0)
    for y, k in enumerate(keys):
        vals = [x["attain_chat"] for x in e7[k]]
        ax.hlines(y, min(vals), max(vals), color=S1, lw=1.2)
        ax.scatter(vals, [y] * len(vals), s=18, color=S1, zorder=3, edgecolors="white", linewidths=0.4)
        if k in e5:
            ax.scatter([e5[k]], [y], s=26, marker="D", facecolors="white", edgecolors=S2, zorder=4, linewidths=1.2)
        meta.append({"point": k, "e7": vals, "e5": e5.get(k)})
    wl = {"random": "4K", "sharegpt": "chat"}
    def nice(c):
        m = {"26": "26B NVFP4", "26F": "26B FP8", "26H": "26B BF16", "31": "31B NVFP4"}
        mod, _, cf = c.partition("_")
        cf = {"B2": "replicas (2)", "B3": "replicas (3)", "single_kvmatch": "single node, KV matched"}.get(cf, cf)
        return f"{m.get(mod, mod)} {cf}"
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([f"{nice(k[0])} · {wl[k[1]]} · {k[2]} req/s" for k in keys], fontsize=7)
    ax.axvline(0.9, color=INK2, lw=1, ls=(0, (4, 3))); ax.set_xlim(0.3, 1.02)
    ax.set_xlabel("Strict-SLO attainment"); ax.grid(axis="y", visible=False)
    ax.legend(handles=[Line2D([0], [0], marker="o", color=S1, lw=0), Line2D([0], [0], marker="D", mfc="white", mec=S2, lw=0)],
              labels=["Repeat (seed varied)", "Single run, previous day"], loc="lower right")
    ax.set_title("Repeats only disagree near the 0.9 threshold (shaded 0.85–0.95)")
    save(fig, out, "fig13_repeatability", meta)


def f14(rows, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.2, 2.6)); meta = []
    for cfg, c, off, lab in (("31_pull", S2, -0.18, "Pull (read)"), ("31_push", S3, 0.18, "Push (write)")):
        g = by_rate(pick(rows, "E6", cfg, "random", inlen=4096))
        rates = [r for r in g if r in (0.25, 0.5)]
        for j, r in enumerate(rates):
            x = g[r][0]
            a.bar(j + off, x["ttft_p50_ms"], 0.34, color=c, label=lab if j == 0 else None)
            b.bar(j + off, x["attain_chat"], 0.34, color=c)
            meta.append({"config": cfg, "rate": r, "ttft_p50": round(x["ttft_p50_ms"]), "attain": x["attain_chat"]})
    for ax in (a, b):
        ax.set_xticks([0, 1]); ax.set_xticklabels(["0.25 req/s", "0.5 req/s"])
    a.set_ylabel("TTFT p50 (ms)"); a.set_title("(a) First token")
    fig.legend(*a.get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    b.set_ylabel("Strict-SLO attainment"); b.set_ylim(0, 1.05); slo_line(b); b.set_title("(b) Attainment")
    fig.suptitle("31B NVFP4 1P1D, 4K input: push trims the median, not the SLO", x=0.01, ha="left",
                 fontsize=8, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "fig14_push_vs_pull", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/safe_runs.csv")
    ap.add_argument("-o", "--out", default="paper/figures")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = load(a.csv)
    for f in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13, f14):
        f(rows, a.out)
    json.dump(META, open(os.path.join(a.out, "figures.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(f"wrote {len(META)} figures to {a.out}")


if __name__ == "__main__":
    main()
