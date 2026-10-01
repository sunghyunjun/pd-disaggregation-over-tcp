#!/usr/bin/env python3
"""Where does chunked prefill run out? A step-time model calibrated on measured runs (paper v4, Section 6).

Model (one replica, low load, homogeneous prompts of length L):
  step time of a prefill chunk of c tokens that starts at prompt position p, batched with ongoing decodes:
      t(c, p) = d + e + a*c + b*c*(p + c/2)        (d: decode share of the step, e: fixed cost of a step that
                                                     carries a prefill chunk, a: per-token cost,
                                                     b: attention over the prefix and inside the chunk)
  a co-scheduled request's longest gap  = max over the chunks of one prompt of t(c_k, p_k)
  replica TTFT                          = o + sum_k t(c_k, p_k)          (no queueing)
  disaggregated TTFT (Eq. 2 of the paper) = o + sum_k t(c_P, p_k) + V(L)/(m*C_flow) + r
Calibration: e, a and b by least squares on measured longest gaps only (p90 of the per-request longest gap at the
lowest rate where at least 10% of requests overlapped a prefill); d = measured median inter-token latency; o from
one TTFT point. All other TTFTs are out-of-sample checks.

Usage: python3 harness/boundary_model.py [--json paper/figures_v4/boundary.json]
"""
import argparse, json, math, os, sys, statistics as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slo_sensitivity as ss  # noqa: E402

KIB, MIB = 1024, 1024 * 1024
GBPS_PER_MIBS = 0.008388608   # Gbps per MiB/s


def runs(C, stage, cfg, rate, L, wl="random"):
    return [r for rid, r in sorted(C.items()) if r["stage"] == stage and r["config"] == cfg and r["workload"] == wl
            and float(r["rate"]) == rate and r["safety"] == "안전" and int(r["input_len_median"]) == L]


def q(x, p):
    x = sorted(x)
    return x[min(len(x) - 1, int(p * len(x)))]


def longest_gap_ms(rs):
    mg = [m * 1000 for r in rs for m in r["maxitl"] if m is not None]
    return q(mg, 0.9)


def ttft_ms(rs):
    return st.median([t * 1000 for r in rs for t in r["ttft"]])


def chunks(L, c):
    out, p = [], 0
    while p < L:
        k = min(c, L - p); out.append((k, p)); p += k
    return out


def step(par, c, p):
    return par["d"] + par["e"] + par["a"] * c + par["b"] * c * (p + c / 2)


def gap(par, L, c):
    return max(step(par, k, p) for k, p in chunks(L, c))


def prefill(par, L, c):
    return sum(step(par, k, p) for k, p in chunks(L, c))


def fit_eab(points, d):
    """least squares for e, a, b from (L, c, measured longest gap); the longest chunk is re-chosen each iteration"""
    import numpy as np
    e, a, b = 0.0, 0.02, 1e-6
    for _ in range(50):
        X, y = [], []
        for L, c, g in points:
            k, p = max(chunks(L, c), key=lambda kp: a * kp[0] + b * kp[0] * (kp[1] + kp[0] / 2))
            X.append([1.0, k, k * (p + k / 2)]); y.append(g - d)
        e, a, b = np.linalg.lstsq(np.array(X), np.array(y), rcond=None)[0]
    return float(e), float(a), float(b)


def kv_mib(L, bg_kib, bw_kib, W=1024):
    return (bg_kib * L + bw_kib * min(L, W)) * KIB / MIB


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=None)
    a_ = ap.parse_args()
    C = ss.load_cache("results/safe_runs.csv")
    out = {}

    # ---------------- 26B FP8 on g7e (BF16 KV): calibrated at 4K (three chunks) and 16K (chunk 2,560)
    pts = [  # (L, c, stage, config, total rate)
        (4096, 2560, "E7", "26F_B2", 1.0), (4096, 1024, "E8", "26F_B2_c1024", 1.0),
        (4096, 512, "E9", "26F_B2_c512", 1.0), (16384, 2560, "E2", "B2", 0.25)]
    meas = []
    for L, c, stg, cfg, rate in pts:
        rs = runs(C, stg, cfg, rate, L)
        meas.append({"L": L, "c": c, "src": f"{stg} {cfg} rate {rate:g}", "gap_ms": round(longest_gap_ms(rs), 1),
                     "ttft_ms": round(ttft_ms(rs)), "runs": len(rs)})
    d = 7.0   # decode-only step at these loads: measured ITL p50 5.9-8.1 ms for 26B FP8 replicas (E2, E7)
    e, a, b = fit_eab([(m["L"], m["c"], m["gap_ms"]) for m in meas], d)
    par = {"d": d, "e": e, "a": a, "b": b}
    o = meas[0]["ttft_ms"] - prefill(par, 4096, 2560)          # overhead from one point (4K, chunk 2,560)
    par["o"] = o
    for m in meas:
        m["gap_model_ms"] = round(gap(par, m["L"], m["c"]), 1)
        m["ttft_model_ms"] = round(o + prefill(par, m["L"], m["c"]))
    # disaggregated checks (Eq. 2): BF16 KV of the FP8 checkpoint is twice that of NVFP4 (b_g 20, b_w 200 KiB/token)
    pd = []
    for L, stg, cfg, rate, cflow, mm, note in [
            (4096, "E7", "26F_1P1D", 1.0, 9.54, 1.5, "placement group"),
            (4096, "E2", "P1tuned", 0.5, 4.97, 1.5, "no placement group"),
            (16384, "E2", "P1tuned", 0.25, 4.97, 1.5, "no placement group")]:
        rs = runs(C, stg, cfg, rate, L)
        V = kv_mib(L, 20, 200)
        xfer = V * 8.388608 / (mm * cflow)      # ms: MiB * Mbit/MiB / Gbps
        model = o + prefill(par, L, 2560) + xfer + 28
        pd.append({"L": L, "src": f"{stg} {cfg} rate {rate:g} ({note})", "ttft_ms": round(ttft_ms(rs)),
                   "ttft_model_ms": round(model), "kv_mib": round(V), "xfer_ms": round(xfer)})
    out["fp8_g7e"] = {"params": {k: (float(f"{v:.4g}") if isinstance(v, float) else v) for k, v in par.items()},
                      "replicas": meas, "disaggregated": pd}

    # print
    print(f"26B FP8 on g7e: d={d} ms  e={e:.2f} ms  a={a*1000:.3f} us/token  b={b*1e6:.3f} ns/token^2  o={o:.0f} ms")
    print(" replicas: L     c   gap meas/model    TTFT meas/model   (" + "gap fitted; TTFT out of sample except 4K/2560)")
    for m in meas:
        print(f"   {m['L']:6d} {m['c']:5d}   {m['gap_ms']:6.1f}/{m['gap_model_ms']:6.1f}     {m['ttft_ms']:5d}/{m['ttft_model_ms']:5d}   {m['src']}")
    print(" disaggregated (out of sample):")
    for p in pd:
        print(f"   {p['L']:6d}  TTFT meas/model {p['ttft_ms']:5d}/{p['ttft_model_ms']:5d}  (KV {p['kv_mib']} MiB, transfer {p['xfer_ms']} ms)  {p['src']}")
    # ---------------- extrapolation check on a second GPU: 26B NVFP4 on g7 (session B, chunk 2,560 only)
    # fit e+a*c and b on 4K and 16K longest gaps, then predict the 32K gap and TTFTs (out of sample)
    g7 = []
    for L, rate in ((4096, 0.25), (16384, 0.25), (32000, 0.25)):
        rs = runs(C, "B", "B2", rate, L)
        g7.append({"L": L, "gap_ms": round(longest_gap_ms(rs), 1), "ttft_ms": round(ttft_ms(rs)), "runs": len(rs)})
    d7 = 12.0   # measured ITL p50 10.4-14.8 ms for these runs
    pts7 = [(m["L"], 2560, m["gap_ms"]) for m in g7[:2]]
    # two points, two unknowns (k0 = e + a*2560 lumped, b): solve with a fixed per-token share taken from g7e ratio
    import numpy as np
    X = []; y = []
    for L, c, g in pts7:
        k, p = max(chunks(L, c), key=lambda kp: kp[0] * (kp[1] + kp[0] / 2))
        X.append([1.0, k * (p + k / 2)]); y.append(g - d7)
    k0, b7 = np.linalg.solve(np.array(X), np.array(y))
    def step7(c, p):
        return d7 + k0 * c / 2560 + b7 * c * (p + c / 2)
    o7 = g7[0]["ttft_ms"] - sum(step7(k, p) for k, p in chunks(4096, 2560))
    for m in g7:
        m["gap_model_ms"] = round(max(step7(k, p) for k, p in chunks(m["L"], 2560)), 1)
        m["ttft_model_ms"] = round(o7 + sum(step7(k, p) for k, p in chunks(m["L"], 2560)))
    out["nvfp4_g7_check"] = {"fit_on": "4K and 16K gaps", "d": d7, "k0": round(float(k0), 2), "b": float(b7), "o": round(o7), "points": g7}
    print("26B NVFP4 on g7 (fit on 4K and 16K gaps; 32K gap and all TTFTs out of sample, 2,560-token chunk):")
    for m in g7:
        print(f"   {m['L']:6d}  gap meas/model {m['gap_ms']:6.1f}/{m['gap_model_ms']:6.1f}   TTFT meas/model {m['ttft_ms']:5d}/{m['ttft_model_ms']:5d}")

    # ---------------- feasibility map (26B FP8 on g7e parameters; low load, no queueing)
    def replica_best(L, G):
        """largest chunk whose longest step fits the gap limit, and the TTFT it gives"""
        best = None
        for c in range(128, 8193, 16):
            if gap(par, L, c) <= G:
                best = c
        if best is None:
            return None, math.inf
        return best, o + prefill(par, L, best)
    R_PD, CFLOW, CP = 28.0, 9.54, 8192
    kvs = {"hybrid": lambda L: kv_mib(L, 20, 200), "all_global": lambda L: L * 220 * KIB / MIB}
    def pd_ttft(L, kv, m):
        return o + prefill(par, L, CP) + kvs[kv](L) * 8.388608 / (m * CFLOW) + R_PD
    Ls = [int(round(2 ** (11 + i / 8))) for i in range(0, 41)]          # 2K .. 64K
    Ts = [round(0.25 * 2 ** (i / 6), 3) for i in range(0, 32)]           # 0.25 s .. ~9 s
    grid = {}
    for G in (50, 30):
        rep = {L: replica_best(L, G) for L in Ls}
        for kv in kvs:
            for m in (1.0, 1.5):
                key = f"G{G}_{kv}_m{m:g}"
                cells = []
                for T in Ts:
                    row = []
                    for L in Ls:
                        r_ok = rep[L][1] <= T * 1000
                        p_ok = pd_ttft(L, kv, m) <= T * 1000 and par["d"] <= G
                        row.append("R" if r_ok else ("P" if p_ok else "N"))
                    cells.append(row)
                first = next(((L, Ts[i]) for j, L in enumerate(Ls) for i in range(len(Ts)) if cells[i][j] == "P"), None)
                grid[key] = {"cells": cells, "first_pd_only": first,
                             "replica_chunk": {L: rep[L][0] for L in Ls}, "replica_ttft_ms": {L: (round(rep[L][1]) if rep[L][1] < math.inf else None) for L in Ls},
                             "pd_ttft_ms": {L: round(pd_ttft(L, kv, m)) for L in Ls}}
    out["map"] = {"L": Ls, "T": Ts, "grid": grid, "assumptions": {
        "load": "low load, no queueing; decodes per step small", "pd_prefill_chunk": CP, "C_flow_gbps": CFLOW,
        "residual_ms": R_PD, "chunks": "128..8192 in steps of 16", "calibrated_range": "4K-16K (26B FP8, g7e)"}}
    print("\nfeasibility (26B FP8 on g7e, low load):")
    for G in (50, 30):
        print(f" gap limit {G} ms:")
        for L in (4096, 8192, 16384, 24576, 32768, 49152, 65536):
            c, tr = replica_best(L, G)
            print(f"   L={L:6d}  replica best chunk {c}  TTFT {tr/1000:6.2f} s | PD TTFT hybrid m=1 {pd_ttft(L,'hybrid',1)/1000:5.2f} s, m=1.5 {pd_ttft(L,'hybrid',1.5)/1000:5.2f} s | all-global m=1 {pd_ttft(L,'all_global',1)/1000:6.2f} s")
        for kv in kvs:
            print(f"   first PD-only cell ({kv}, m=1): {grid[f'G{G}_{kv}_m1']['first_pd_only']}")

    # ---------------- sensitivity of the boundary (first input length with a disaggregation-only cell, T <= ~9 s)
    def first_pd_only(G, kv="hybrid", m=1.0, bscale=1.0, xfer_scale=1.0):
        p2 = dict(par); p2["b"] = par["b"] * bscale
        def gap2(L, c):
            return max(step(p2, k, pp) for k, pp in chunks(L, c))
        for L in Ls:
            best = None
            for c in range(128, 8193, 16):
                if gap2(L, c) <= G:
                    best = c
            tr = (o + prefill(p2, L, best)) if best else math.inf
            tp = o + prefill(p2, L, CP) + xfer_scale * kvs[kv](L) * 8.388608 / (m * CFLOW) + R_PD
            for T in Ts:
                if tp <= T * 1000 < tr:
                    return L, T
        return None
    sens = {}
    for G in (50, 30):
        for name, kw in [("base", {}), ("b x0.85 (32K gap over-estimate on g7)", {"bscale": 0.85}),
                         ("m = 1.5 (low-load transfer rate)", {"m": 1.5}), ("fast link (transfer x0.05)", {"xfer_scale": 0.05}),
                         ("all-global KV", {"kv": "all_global"})]:
            sens[f"G{G} {name}"] = first_pd_only(G, **kw)
    out["sensitivity_first_pd_only"] = {k: v for k, v in sens.items()}
    print("\nsensitivity: first (input length, TTFT limit s) where only disaggregation meets both limits")
    for k, v in sens.items():
        print(f"   {k:45s} {v}")

    # ---------------- curves for the figure (finer grid)
    Lf = [int(round(2 ** (11 + i / 16))) for i in range(0, 81)]   # 2K .. 64K
    curves = {"L": Lf}
    for G in (50, 30):
        rb = [replica_best(L, G) for L in Lf]
        curves[f"G{G}"] = {"replica_chunk": [c for c, _ in rb],
                           "replica_ttft_s": [(t / 1000 if t < math.inf else None) for _, t in rb]}
    curves["pd_hybrid_m1_s"] = [pd_ttft(L, "hybrid", 1.0) / 1000 for L in Lf]
    curves["pd_all_global_m1_s"] = [pd_ttft(L, "all_global", 1.0) / 1000 for L in Lf]
    curves["pd_fast_link_s"] = [(o + prefill(par, L, CP) + 0.05 * kvs["hybrid"](L) * 8.388608 / CFLOW + R_PD) / 1000 for L in Lf]
    out["curves"] = curves

    if a_.json:
        os.makedirs(os.path.dirname(a_.json), exist_ok=True)
        json.dump(out, open(a_.json, "w"), indent=1)


if __name__ == "__main__":
    main()
