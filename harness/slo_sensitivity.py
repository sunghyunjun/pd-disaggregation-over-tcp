#!/usr/bin/env python3
"""Re-read per-request timings of safe runs and reinterpret them without a fixed SLO.

Usage:
  uv run --with matplotlib python3 harness/slo_sensitivity.py [-o paper/figures]

Steps:
  1. Cache per-request arrays (ttft, max ITL, e2e, output length, error) of every safe/caution run in
     results/per_request.json.gz, so later analyses do not reparse ~2 GB of bench JSON.
  2. SLO sensitivity: for a grid of TTFT budgets x per-request max-ITL budgets, compute each config's
     SLO goodput capacity = max over rates of (SLO-meeting output tok/s per GPU), using the minimum over
     repeats at each rate. Compare disaggregated vs replicas as a ratio (fig15, sensitivity.json).
  3. SLO-free frontier: output tok/s per GPU vs request-level p90 TTFT and p90 of per-request max ITL
     (fig16).
"""
import argparse, csv, glob, gzip, json, math, os
from collections import defaultdict

CACHE = "results/per_request.json.gz"
T_GRID = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]           # seconds
B_GRID = [30, 40, 50, 75, 100, 150, 200, 300]                  # ms, per-request max ITL


def build_cache(safe_csv):
    safe = [r for r in csv.DictReader(open(safe_csv)) if r["safety"] in ("안전", "주의")]
    where = {}
    for p in glob.glob("results/*/*/bench.json"):
        where[os.path.basename(os.path.dirname(p))] = p
    out = {}
    for r in safe:
        p = where.get(r["run_id"])
        if not p:
            continue
        b = json.load(open(p))
        itls = b["itls"]
        out[r["run_id"]] = {
            "stage": r["stage"], "config": r["config"], "workload": r["workload"], "rate": r["rate"],
            "network": r["network"], "input_len_median": r["input_len_median"], "safety": r["safety"],
            "duration": b["duration"],
            "ttft": [round(x, 5) for x in b["ttfts"]],
            "maxitl": [round(max(l), 5) if l else None for l in itls],
            "e2e": [round(x, 4) for x in b["latencies"]],
            "outlen": b["output_lens"],
            "err": [1 if e else 0 for e in b.get("errors", [""] * len(itls))],
        }
    with gzip.open(CACHE, "wt") as f:
        json.dump(out, f)
    return out


def load_cache(safe_csv, rebuild=False):
    if rebuild or not os.path.exists(CACHE):
        return build_cache(safe_csv)
    return json.load(gzip.open(CACHE, "rt"))


def goodput(run, T, B):
    tok = 0
    for t, m, ol, e in zip(run["ttft"], run["maxitl"], run["outlen"], run["err"]):
        if not e and m is not None and t <= T and m * 1000 <= B:
            tok += ol
    return tok / run["duration"]


def attain(run, T, B):
    ok = sum(1 for t, m, e in zip(run["ttft"], run["maxitl"], run["err"])
             if not e and m is not None and t <= T and m * 1000 <= B)
    return ok / len(run["ttft"])


def q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; lo = int(k); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


# comparison groups: (key, title, [(label, stages, config, workload, inlen, gpus)])
GROUPS = [
    ("26b_4k", "26B NVFP4 · 4K\ng7e, placement group",
     [("Replicas (2)", ("E5", "E7"), "26_B2", "random", "4096", 2),
      ("Replicas (3)", ("E5", "E7"), "26_B3", "random", "4096", 3),
      ("1P1D", ("E5", "E7"), "26_1P1D", "random", "4096", 2),
      ("1P2D", ("E5", "E7"), "26_1P2D", "random", "4096", 3),
      ("2P1D", ("E5", "E7"), "26_2P1D", "random", "4096", 3)]),
    ("26b_chat", "26B NVFP4 · ShareGPT\ng7e, placement group",
     [("Replicas (2)", ("E5", "E7"), "26_B2", "sharegpt", None, 2),
      ("Replicas (3)", ("E5", "E7"), "26_B3", "sharegpt", None, 3),
      ("1P1D", ("E5", "E7"), "26_1P1D", "sharegpt", None, 2),
      ("1P2D", ("E5", "E7"), "26_1P2D", "sharegpt", None, 3),
      ("2P1D", ("E5", "E7"), "26_2P1D", "sharegpt", None, 3)]),
    ("31b_chat", "31B NVFP4 · ShareGPT\ng7e, placement group",
     [("Replicas (2)", ("E5", "E7"), "31_B2", "sharegpt", None, 2),
      ("1P1D", ("E5", "E7"), "31_1P1D", "sharegpt", None, 2)]),
    ("31b_4k", "31B NVFP4 · 4K\ng7e, placement group",
     [("Replicas (2)", ("E5",), "31_B2", "random", "4096", 2),
      ("Replicas (3)", ("E5",), "31_B3", "random", "4096", 3),
      ("1P1D", ("E5", "E6", "E7"), "31_1P1D", "random", "4096", 2),
      ("1P2D", ("E5",), "31_1P2D", "random", "4096", 3),
      ("2P1D", ("E5", "E7"), "31_2P1D", "random", "4096", 3)]),
    ("26f_chat_e2", "26B FP8 · ShareGPT\ng7e",
     [("Replicas (2)", ("E2",), "B2", "sharegpt", None, 2),
      ("1P1D", ("E2",), "P1tuned", "sharegpt", None, 2)]),
    ("26f_4k_e2", "26B FP8 · 4K\ng7e",
     [("Replicas (2)", ("E2",), "B2", "random", "4096", 2),
      ("1P1D", ("E2",), "P1tuned", "random", "4096", 2)]),
    ("26f_16k_e2", "26B FP8 · 16K\ng7e",
     [("Replicas (2)", ("E2",), "B2", "random", "16384", 2),
      ("1P1D", ("E2",), "P1tuned", "random", "16384", 2)]),
    ("26n_4k_g7", "26B NVFP4 · 4K\ng7",
     [("Replicas (2)", ("B",), "B2", "random", "4096", 2),
      ("1P1D", ("B",), "P1", "random", "4096", 2)]),
    ("26n_16k_g7", "26B NVFP4 · 16K\ng7",
     [("Replicas (2)", ("B",), "B2", "random", "16384", 2),
      ("1P1D", ("B",), "P1", "random", "16384", 2)]),
]


def runs_for(cache, stages, config, workload, inlen, safe_only=True):
    by = defaultdict(list)
    for rid, r in cache.items():
        if r["stage"] in stages and r["config"] == config and r["workload"] == workload and r["network"] == "N0":
            if inlen and r["input_len_median"] != inlen:
                continue
            if safe_only and r["safety"] != "안전":
                continue
            by[float(r["rate"])].append(r)
    return dict(sorted(by.items()))


def capacity(by_rate, gpus, T, B):
    """SLO goodput per GPU at the highest rate where every repeat reaches 0.9 attainment.
    Returns (value, censored): censored means that rate is the highest one measured, so the
    true capacity may be higher (a lower bound)."""
    best, best_rate = 0.0, None
    for rate, rs in by_rate.items():
        if min(attain(r, T, B) for r in rs) >= 0.9:
            g = min(goodput(r, T, B) for r in rs) / gpus
            if g > best:
                best, best_rate = g, rate
    return best, (best_rate is not None and best_rate == max(by_rate))


def supported(by_rate, gpus, T, B):
    s = 0.0
    for rate, rs in by_rate.items():
        if min(attain(r, T, B) for r in rs) >= 0.9:
            s = rate / gpus
    return s


def sensitivity(cache):
    res = {}
    for key, title, members in GROUPS:
        g = {"title": title, "members": {}}
        for lab, stages, cfg, wl, inl, n in members:
            br = runs_for(cache, stages, cfg, wl, inl)
            if not br:
                continue
            g["members"][lab] = {
                "rates": list(br), "gpus": n,
                "capacity": [[round(capacity(br, n, T, B)[0], 1) for B in B_GRID] for T in T_GRID],
                "censored": [[capacity(br, n, T, B)[1] for B in B_GRID] for T in T_GRID],
                "supported_per_gpu": [[supported(br, n, T, B) for B in B_GRID] for T in T_GRID],
            }
        res[key] = g
    return res


def best_of(g, pd):
    """per cell: (best capacity among configs of this kind, whether that best is censored)"""
    labs = [l for l in g["members"] if (l.startswith("Replicas") != pd)]
    out = []
    for i in range(len(T_GRID)):
        row = []
        for j in range(len(B_GRID)):
            c = [(g["members"][l]["capacity"][i][j], g["members"][l]["censored"][i][j]) for l in labs]
            v = max(x[0] for x in c)
            row.append((v, any(x[1] for x in c if x[0] == v and v > 0)))
        out.append(row)
    return out


def cell(rep, pd):
    """-> (log2 ratio for colour or nan, label, kind)"""
    (a, ca), (b, cb) = rep, pd
    if a <= 0 and b <= 0:
        return float("nan"), "–", "none"
    if a <= 0:
        return 4.0, "D", "pd_only"
    if b <= 0:
        return -4.0, "R", "rep_only"
    r = b / a
    if ca and cb:
        return float("nan"), "?", "both_censored"
    txt = f"{r:.1f}" if r < 9.95 else f"{r:.0f}"
    if ca:
        return math.log2(r), "≤" + txt, "upper"
    if cb:
        return math.log2(r), "≥" + txt, "lower"
    return math.log2(r), txt, "exact"


# ---------------------------------------------------------------- figures
def figures(res, cache, out):
    import matplotlib
    import matplotlib.ticker
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    import make_figures as mf  # shared style
    INK, INK2 = mf.INK, mf.INK2

    cmap = LinearSegmentedColormap.from_list("div", ["#1d4f91", "#8fb3dd", "#ebe9e4", "#eeb08c", "#c8501e"])
    keys = ["26n_4k_g7", "26f_4k_e2", "26b_4k", "26n_16k_g7", "26f_chat_e2", "26b_chat", "31b_chat", "31b_4k", "26f_16k_e2"]
    fig, axes = plt.subplots(3, 3, figsize=(7.2, 7.9), sharex=True, sharey=True)
    summary = {}
    for ax, key in zip(axes.flat, keys):
        g = res[key]; rep, pd = best_of(g, False), best_of(g, True)
        C = [[cell(rep[i][j], pd[i][j]) for j in range(len(B_GRID))] for i in range(len(T_GRID))]
        Mc = [[max(-4, min(4, c[0])) if c[0] == c[0] else float("nan") for c in r] for r in C]
        ax.imshow(Mc, origin="lower", aspect="auto", cmap=cmap, norm=TwoSlopeNorm(0, -4, 4))
        for i in range(len(T_GRID)):
            for j in range(len(B_GRID)):
                v, lab, kind = C[i][j]
                col = "white" if (v == v and abs(v) > 2.2) else (INK2 if kind in ("none", "both_censored") else INK)
                ax.text(j, i, lab, ha="center", va="center", fontsize=5.4, color=col,
                        style="italic" if kind in ("upper", "lower") else "normal")
        j50, i1 = B_GRID.index(50), T_GRID.index(1.0)
        M = [[c[0] for c in r] for r in C]
        ax.add_patch(plt.Rectangle((j50 - .5, i1 - .5), 1, 1, fill=False, ec=INK, lw=1.4))
        ax.set_title(g["title"], fontsize=7.6, loc="left")
        ax.grid(False)
        summary[key] = {"title": g["title"], "cells": [[c[1] for c in r] for r in C],
                        "at_1s_50ms": C[i1][j50][1]}
    for ax in axes[-1]:
        ax.set_xticks(range(len(B_GRID))); ax.set_xticklabels(B_GRID, fontsize=6.5)
        ax.set_xlabel("max ITL budget (ms)", fontsize=7.5)
    for ax in axes[:, 0]:
        ax.set_yticks(range(len(T_GRID))); ax.set_yticklabels([f"{t:g}" for t in T_GRID], fontsize=6.5)
        ax.set_ylabel("TTFT budget (s)", fontsize=7.5)
    fig.suptitle("SLO goodput per GPU at the highest rate where every repeat reaches 0.9, disaggregated ÷ replicas\n"
                 "(best config of each kind). Orange: disaggregation wins. ≥/≤: one side still passing at its highest "
                 "measured rate. ?: both. D or R: only that side reaches 0.9. Box: 1 s / 50 ms.",
                 x=0.01, ha="left", fontsize=7.4, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(os.path.join(out, "fig15_slo_sensitivity.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(out, "fig15_slo_sensitivity.svg"), bbox_inches="tight", transparent=True)
    plt.close(fig)

    # frontier: tok/s per GPU vs p90 TTFT and p90 of per-request max ITL
    colors = {"Replicas (2)": mf.S1, "Replicas (3)": mf.S5, "1P1D": mf.S2, "1P2D": mf.S3, "2P1D": mf.S4}
    styles = {"Replicas (3)": mf.LS3, "1P2D": mf.LS3, "2P1D": mf.LS3B}
    marks = {"Replicas (2)": "o", "Replicas (3)": "o", "1P1D": "s", "1P2D": "^", "2P1D": "D"}
    fkeys = ["26b_4k", "26b_chat", "31b_chat", "31b_4k"]
    fig, axes = plt.subplots(2, 4, figsize=(8.4, 4.6))
    front = {}
    for col, key in enumerate(fkeys):
        g = [x for x in GROUPS if x[0] == key][0]
        for lab, stages, cfg, wl, inl, n in g[2]:
            br = runs_for(cache, stages, cfg, wl, inl, safe_only=False)
            if not br:
                continue
            pts = []
            for rate, rs in br.items():
                tt = [t for r in rs for t in r["ttft"]]
                mi = [m for r in rs for m in r["maxitl"] if m is not None]
                tput = sum(sum(r["outlen"]) / r["duration"] for r in rs) / len(rs) / n
                caution = any(r["safety"] == "주의" for r in rs)
                pts.append((tput, q(tt, .9) * 1000, q(mi, .9) * 1000, caution, rate))
            front[f"{key}:{lab}"] = [{"rate": p[4], "tok_s_per_gpu": round(p[0]), "ttft_p90_ms": round(p[1]),
                                      "maxitl_p90_ms": round(p[2]), "caution": p[3]} for p in pts]
            for row, idx in ((0, 1), (1, 2)):
                ax = axes[row][col]
                ax.plot([p[0] for p in pts], [p[idx] for p in pts], color=colors[lab], marker=marks[lab],
                        ls=styles.get(lab, "-"), lw=1.6, ms=4, label=lab)
                for p in pts:
                    if p[3]:
                        ax.plot([p[0]], [p[idx]], marker=marks[lab], mfc="white", mec=colors[lab], ms=6, ls="none")
        axes[0][col].set_title(g[1].split("\n")[0], fontsize=7.8, loc="left")
        for row in (0, 1):
            axes[row][col].set_yscale("log")
            axes[row][col].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            axes[row][col].yaxis.set_minor_formatter(matplotlib.ticker.FuncFormatter(
                lambda v, _: f"{v:g}" if str(f"{v:g}")[0] in "25" else ""))
            axes[row][col].tick_params(labelsize=6.5, which="both")
        axes[0][col].axhline(1000, color=INK2, lw=0.8, ls=(0, (4, 3)))
        axes[1][col].axhline(50, color=INK2, lw=0.8, ls=(0, (4, 3)))
        axes[1][col].set_xlabel("output tok/s per GPU", fontsize=7.2)
    axes[0][0].set_ylabel("TTFT p90 (ms, log)", fontsize=7.5)
    axes[1][0].set_ylabel("per-request max ITL p90\n(ms, log)", fontsize=7.5)
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("Latency and throughput without an SLO, g7e in a placement group (lower-right is better). "
                 "Dashed: 1 s and 50 ms. Hollow: client-limited.", x=0.01, ha="left", fontsize=8, color=INK2, y=1.0)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(os.path.join(out, "fig16_frontier.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(out, "fig16_frontier.svg"), bbox_inches="tight", transparent=True)
    plt.close(fig)
    return summary, front


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/safe_runs.csv")
    ap.add_argument("-o", "--out", default="paper/figures")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    cache = load_cache(a.csv, a.rebuild)
    res = sensitivity(cache)
    summary, front = figures(res, cache, a.out)
    json.dump({"T_grid_s": T_GRID, "B_grid_ms": B_GRID, "groups": res, "ratio": summary, "frontier": front},
              open(os.path.join(a.out, "sensitivity.json"), "w"), ensure_ascii=False, indent=1)
    for k, v in summary.items():
        print(f"{k:14} at 1s/50ms: {v['at_1s_50ms']}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
