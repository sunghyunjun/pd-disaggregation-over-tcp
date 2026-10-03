#!/usr/bin/env python3
"""Where does chunked prefill run out? A step-time model calibrated on measured runs (paper Section 6).

Model (one replica, low load, homogeneous prompts of length L):
  step time of a prefill chunk of c tokens that starts at prompt position p, batched with ongoing decodes:
      t(c, p) = d + e + a*c + b*c*(p + c/2)        (d: decode share of the step, e: fixed cost of a step that
                                                     carries a prefill chunk, a: per-token cost,
                                                     b: attention over the prefix and inside the chunk)
  a co-scheduled request's longest gap  = max over the chunks of one prompt of t(c_k, p_k)
  replica TTFT                          = o + sum_k t(c_k, p_k) = o + n (d + e) + a L + b L^2 / 2    (no queueing)
  1P1D TTFT (paper Eq. 2)               = o + prefill at 8,192-token chunks + V(L) / (m * C_flow) + residual
  1P1D gap                              = the decode node's longest gap, a line through measured p90 at 4K and 16K
Calibration (26B FP8 on g7e): e, a, b by least squares on the measured longest gaps (p90 of the per-request
longest gap) of four runs: E7 26F_B2 (4K, chunk 2,560), E8 26F_B2_c1024 (4K), E9 26F_B2_c512 (4K), E2 B2 (16K,
chunk 2,560); d = mean measured median inter-token latency of those runs; o from the 4K, 2,560-token TTFT.
The crossover length is the shortest input beyond which 1P1D's TTFT stays below the replicas' (scanned in 64-token
steps); 1P1D's advantage ends where the decode node's longest gap reaches the gap limit.

Usage: uv run --with numpy python3 analysis/boundary_model.py [--json paper/figures/boundary.json]
"""
import argparse, csv, json, math, os, sys, statistics as st

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slo_sensitivity as ss  # noqa: E402

KIB, MIB = 1024, 1024 * 1024
MBIT_PER_MIB = 8.388608          # MiB -> Mbit, so MiB * MBIT_PER_MIB / Gbps = ms
C_FLOW = 9.54                    # Gbps, one TCP flow in a cluster placement group (iperf, Section 3.1)
M_MAP, M_BAND = 1.5, (1.0, 1.8)  # low-load transfer rate / per-flow cap; band: rate at decision loads, four-way split
RESIDUAL = 28.0                  # ms, 1P1D TTFT residual measured for 26B FP8 (Figure 4, first row)
CP = 8192                        # prefill-node chunk for 1P1D
FAST_GBPS = 95.4                 # ten times one TCP flow
CHUNKS = np.arange(128, 8193, 16)  # replica chunk sizes considered
SCAN = range(2048, 65537, 64)    # input lengths scanned


def runs(C, stage, cfg, rate, L, wl="random"):
    return [(rid, r) for rid, r in sorted(C.items()) if r["stage"] == stage and r["config"] == cfg and r["workload"] == wl
            and float(r["rate"]) == rate and r["safety"] == "안전" and int(r["input_len_median"]) == L]


def q(x, p):
    x = sorted(x)
    return x[min(len(x) - 1, int(p * len(x)))]


def longest_gap_ms(rs):
    return q([m * 1000 for _, r in rs for m in r["maxitl"] if m is not None], 0.9)


def ttft_ms(rs):
    return st.median([t * 1000 for _, r in rs for t in r["ttft"]])


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


def gap_vec(par, L, c):
    """gap() for an array of chunk sizes: the longest step is the last full chunk or the last (partial) chunk"""
    D = par["d"] + par["e"]
    n = np.ceil(L / c)
    r = L - (n - 1) * c
    full = np.where(n >= 2, D + par["a"] * c + par["b"] * c * (np.maximum(n - 2, 0) * c + c / 2), -np.inf)
    last = D + par["a"] * r + par["b"] * r * ((n - 1) * c + r / 2)
    return np.maximum(full, last)


def fit_eab(points, d):
    """least squares for e, a, b from (L, c, measured longest gap); the longest chunk is re-chosen each iteration"""
    e, a, b = 0.0, 0.02, 1e-6
    for _ in range(50):
        X, y = [], []
        for L, c, g in points:
            k, p = max(chunks(L, c), key=lambda kp: a * kp[0] + b * kp[0] * (kp[1] + kp[0] / 2))
            X.append([1.0, k, k * (p + k / 2)]); y.append(g - d)
        e, a, b = np.linalg.lstsq(np.array(X), np.array(y), rcond=None)[0]
    return float(e), float(a), float(b)


def make_par(points, d, ttft_4k_2560):
    e, a, b = fit_eab(points, d)
    par = {"d": d, "e": e, "a": a, "b": b}
    par["o"] = ttft_4k_2560 - prefill(par, 4096, 2560)
    return par


def kv_mib(L, kv="hybrid"):
    if kv == "hybrid":                  # FP8 checkpoint, BF16 KV: b_g 20, b_w 200 KiB/token, W 1,024
        return (20 * L + 200 * min(L, 1024)) * KIB / MIB
    if kv == "sliding_keep_all":        # sliding-window layers keep every token: 220 KiB/token
        return L * 220 * KIB / MIB
    if kv == "global_shape":            # global-layer shape in every layer: 120 KiB/token
        return L * 120 * KIB / MIB
    raise ValueError(kv)


class Model:
    def __init__(self, par, dgap, d_small=None):
        self.p, self.dgap, self.d_small = par, dgap, d_small

    def _cost(self, c):
        D = self.p["d"] + self.p["e"]
        return self.d_small if (self.d_small is not None and c <= 512) else D

    def replica(self, L, G):
        """largest chunk whose longest step fits G, and the TTFT it gives (None, inf if no chunk fits)"""
        D = self.p["d"] + self.p["e"]
        cost = np.where(CHUNKS <= 512, self.d_small, D) if self.d_small is not None else D
        ok = CHUNKS[gap_vec(self.p, L, CHUNKS) - D + cost <= G]
        if ok.size == 0:
            return None, math.inf
        best = int(ok.max())
        return best, self.p["o"] + math.ceil(L / best) * self._cost(best) + self.p["a"] * L + self.p["b"] * L * L / 2

    def pd(self, L, m=M_MAP, kv="hybrid", gbps=None, residual=RESIDUAL):
        xfer = kv_mib(L, kv) * MBIT_PER_MIB / (gbps if gbps else m * C_FLOW)
        return self.p["o"] + prefill(self.p, L, CP) + xfer + residual

    def crossover(self, G, rep_scale=1.0, pd_scale=1.0, **kw):
        """shortest L beyond which 1P1D's TTFT stays below the replicas' (to the end of the scan)"""
        start = None
        for L in SCAN:
            win = self.pd(L, **kw) * pd_scale < self.replica(L, G)[1] * rep_scale
            if not win:
                start = None
            elif start is None:
                start = L
        if start is None:
            return None
        c, tr = self.replica(start, G)
        return {"L": start, "pd_ttft_s": round(self.pd(start, **kw) / 1000, 3),
                "replica_ttft_s": (round(tr / 1000, 3) if tr < math.inf else None), "replica_chunk": c}

    def end(self, G):
        """input length where the decode node's longest gap reaches G (1P1D's advantage ends)"""
        return next((L for L in SCAN if self.dgap(L) > G), None)

    def longest(self, G, T, side, **kw):
        if side == "replicas":
            ok = [L for L in SCAN if self.replica(L, G)[1] <= T * 1000]
        else:
            ok = [L for L in SCAN if self.pd(L, **kw) <= T * 1000 and self.dgap(L) <= G]
        return max(ok, default=None)

    def capacity(self, L, G):
        """per-GPU prefill capacity at zero queueing (req/s/GPU): replicas 1/prefill time, 1P1D 1/(2 x P-node prefill)"""
        _, tr = self.replica(L, G)
        rep = 1000 / (tr - self.p["o"]) if tr < math.inf else 0.0
        return round(rep, 3), round(1000 / (2 * prefill(self.p, L, CP)), 3)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", default=None)
    args = ap.parse_args()
    C = ss.load_cache("results/safe_runs.csv")
    rows = {r["run_id"]: r for r in csv.DictReader(open("results/safe_runs.csv"))}
    itl = lambda rs: st.mean(float(rows[rid]["itl_p50_ms"]) for rid, _ in rs)
    out = {}

    # ---------------- calibration: 26B FP8 on g7e
    cal = [(4096, 2560, "E7", "26F_B2", 1.0), (4096, 1024, "E8", "26F_B2_c1024", 1.0),
           (4096, 512, "E9", "26F_B2_c512", 1.0), (16384, 2560, "E2", "B2", 0.25)]
    meas, itls = [], []
    for L, c, stg, cfg, rate in cal:
        rs = runs(C, stg, cfg, rate, L)
        itls.append(itl(rs))
        meas.append({"L": L, "c": c, "src": f"{stg} {cfg} rate {rate:g}", "gap_ms": round(longest_gap_ms(rs), 1),
                     "ttft_ms": round(ttft_ms(rs)), "runs": len(rs)})
    d = round(st.mean(itls), 2)
    par = make_par([(m["L"], m["c"], m["gap_ms"]) for m in meas], d, meas[0]["ttft_ms"])
    for m in meas:
        m["gap_model_ms"] = round(gap(par, m["L"], m["c"]), 1)
        m["ttft_model_ms"] = round(par["o"] + prefill(par, m["L"], m["c"]))
    pdchk = []  # 1P1D checks: the runs' prefill chunk (2,560), the measured per-flow cap of each setting, m = 1.5
    for L, stg, cfg, rate, cflow, note in [(4096, "E7", "26F_1P1D", 1.0, 9.54, "placement group"),
                                           (4096, "E2", "P1tuned", 0.5, 4.97, "no placement group"),
                                           (16384, "E2", "P1tuned", 0.25, 4.97, "no placement group")]:
        rs = runs(C, stg, cfg, rate, L)
        model = par["o"] + prefill(par, L, 2560) + kv_mib(L) * MBIT_PER_MIB / (M_MAP * cflow) + RESIDUAL
        pdchk.append({"L": L, "src": f"{stg} {cfg} rate {rate:g} ({note})", "ttft_ms": round(ttft_ms(rs)),
                      "ttft_model_ms": round(model)})
    g4 = longest_gap_ms(runs(C, "E2", "P1tuned", 0.5, 4096))
    g16 = longest_gap_ms(runs(C, "E2", "P1tuned", 0.25, 16384))
    dgap = lambda L: g4 + (g16 - g4) * (L - 4096) / (16384 - 4096)
    M = Model(par, dgap)
    out["fp8_g7e"] = {"params": {k: float(f"{v:.4g}") for k, v in par.items()}, "replicas": meas, "disaggregated": pdchk,
                      "decode_gap_p90_ms": {"4K": round(g4, 1), "16K": round(g16, 1)}}

    # ---------------- second GPU: 26B NVFP4 on g7 (session B, chunk 2,560), two parameters solved on 4K and 16K gaps
    g7, g7ids = [], []
    for L in (4096, 16384, 32000):
        rs = runs(C, "B", "B2", 0.25, L)
        g7.append({"L": L, "gap_ms": round(longest_gap_ms(rs), 1), "ttft_ms": round(ttft_ms(rs))}); g7ids += rs
    d7 = round(itl(g7ids), 2)
    k0, b7 = 90.0, 4e-6
    for _ in range(50):
        X, y = [], []
        for m in g7[:2]:
            k, p = max(chunks(m["L"], 2560), key=lambda kp: k0 * kp[0] / 2560 + b7 * kp[0] * (kp[1] + kp[0] / 2))
            X.append([k / 2560, k * (p + k / 2)]); y.append(m["gap_ms"] - d7)
        k0, b7 = (float(v) for v in np.linalg.solve(np.array(X), np.array(y)))
    st7 = lambda c, p: d7 + k0 * c / 2560 + b7 * c * (p + c / 2)
    o7 = g7[0]["ttft_ms"] - sum(st7(k, p) for k, p in chunks(4096, 2560))
    for m in g7:
        m["gap_model_ms"] = round(max(st7(k, p) for k, p in chunks(m["L"], 2560)), 1)
        m["ttft_model_ms"] = round(o7 + sum(st7(k, p) for k, p in chunks(m["L"], 2560)))
    pg = {L: longest_gap_ms(runs(C, "B", "P1", 0.25, L)) for L in (4096, 16384, 32000)}
    pred32 = pg[4096] + (pg[16384] - pg[4096]) * (32000 - 4096) / (16384 - 4096)
    out["nvfp4_g7_check"] = {"d": d7, "k0": round(k0, 2), "b": float(f"{b7:.4g}"), "o": round(o7), "points": g7,
                             "decode_gap_p90_ms": {str(k): round(v, 1) for k, v in pg.items()},
                             "decode_gap_32K_from_line_ms": round(pred32, 1)}

    # ---------------- crossover, end of advantage, longest input, capacity
    res = {}
    for G in (50, 30):
        r = {f"m{m:g}": M.crossover(G, m=m) for m in (1.0, M_MAP, 1.8)}
        r["end_L"] = M.end(G)
        r["longest_input"] = {f"T{T:g}": {"replicas": M.longest(G, T, "replicas"), "1P1D_m1.5": M.longest(G, T, "pd")}
                              for T in (1.0, 1.5, 2.0, 3.0)}
        r["capacity_req_s_per_gpu_rep_pd"] = {str(L): M.capacity(L, G) for L in (8192, 16384, 24576, 32768)}
        r["ttft_s_at"] = {str(L): {"replicas": round(M.replica(L, G)[1] / 1000, 3) if M.replica(L, G)[1] < math.inf else None,
                                   "chunk": M.replica(L, G)[0], "1P1D_m1.5": round(M.pd(L) / 1000, 3)}
                          for L in (4096, 16384, 20480, 32768)}
        res[f"G{G}"] = r
    sens = {}
    for G in (50, 30):
        s = {}
        for i, drop in enumerate(meas):
            pts = [(m["L"], m["c"], m["gap_ms"]) for j, m in enumerate(meas) if j != i]
            Mi = Model(make_par(pts, d, meas[0]["ttft_ms"]), dgap)
            s[f"drop {drop['L']}/{drop['c']}"] = {f"m{m:g}": (Mi.crossover(G, m=m) or {}).get("L") for m in (1.0, M_MAP)}
        s["16K error corrected"] = {f"m{m:g}": (M.crossover(G, m=m, rep_scale=meas[3]["ttft_ms"] / meas[3]["ttft_model_ms"],
                                                             pd_scale=pdchk[2]["ttft_ms"] / pdchk[2]["ttft_model_ms"]) or {}).get("L")
                                    for m in (1.0, M_MAP)}
        p9 = dict(par); p9["b"] = par["b"] * 0.9; p9["o"] = meas[0]["ttft_ms"] - prefill(p9, 4096, 2560)
        s["b x0.9"] = {f"m{m:g}": (Model(p9, dgap).crossover(G, m=m) or {}).get("L") for m in (1.0, M_MAP)}
        s["residual 87 ms"] = {f"m{m:g}": (M.crossover(G, m=m, residual=87.0) or {}).get("L") for m in (1.0, M_MAP)}
        s["step cost 12 ms for chunks <= 512"] = {f"m{m:g}": (Model(par, dgap, d_small=12.0).crossover(G, m=m) or {}).get("L")
                                                  for m in (1.0, M_MAP)}
        s["fast link 95 Gbps"] = (M.crossover(G, gbps=FAST_GBPS) or {}).get("L")
        s["KV 220 KiB/token, m1.5"] = (M.crossover(G, kv="sliding_keep_all") or {}).get("L")
        s["KV 120 KiB/token, m1.5"] = (M.crossover(G, kv="global_shape") or {}).get("L")
        sens[f"G{G}"] = s
    nine_src = [(4096, 2560, "E7", "26F_B2", 1.0), (4096, 2560, "E7", "26F_B2", 2.0), (4096, 2560, "E2", "B2", 1.0),
                (4096, 1024, "E8", "26F_B2_c1024", 1.0), (4096, 1024, "E8", "26F_B2_c1024", 2.0),
                (4096, 512, "E9", "26F_B2_c512", 1.0), (4096, 512, "E9", "26F_B2_c512", 2.0),
                (16384, 2560, "E2", "B2", 0.25), (16384, 2560, "E2", "B2", 0.5)]
    nine = [(L, c, round(longest_gap_ms(runs(C, stg, cfg, rate, L)), 1)) for L, c, stg, cfg, rate in nine_src]
    par9 = make_par(nine, d, meas[0]["ttft_ms"])
    X, y = [], []
    for L, c, g in nine:
        k, p = max(chunks(L, c), key=lambda kp: par9["a"] * kp[0] + par9["b"] * kp[0] * (kp[1] + kp[0] / 2))
        X.append([1.0, k, k * (p + k / 2)]); y.append(g - d)
    X, y = np.array(X), np.array(y)
    beta = np.array([par9["e"], par9["a"], par9["b"]]); rsd = y - X @ beta
    cov = (rsd @ rsd / (len(y) - 3)) * np.linalg.inv(X.T @ X)
    rng = np.random.default_rng(0)
    joint = {}
    draws = rng.multivariate_normal(beta, cov, 400)
    for G in (50, 30):
        xs = []
        for s_ in draws:
            pp = {"d": d, "e": s_[0], "a": s_[1], "b": s_[2]}; pp["o"] = meas[0]["ttft_ms"] - prefill(pp, 4096, 2560)
            cr = Model(pp, dgap).crossover(G, m=M_MAP)
            xs.append(cr["L"] if cr else SCAN[-1])
        joint[f"G{G}"] = {"point": (Model(par9, dgap).crossover(G, m=M_MAP) or {}).get("L"),
                          "p2.5_p50_p97.5": [int(v) for v in np.percentile(xs, [2.5, 50, 97.5])]}
    out["nine_points"] = nine
    out["crossover"] = {"map_m": M_MAP, "results": res, "sensitivity": sens, "joint_fit_m1.5": joint}

    # ---------------- curves for Figure 7
    Lf = list(range(2048, 49153, 256))
    curves = {"L": Lf}
    for G in (50, 30):
        rb = [M.replica(L, G) for L in Lf]
        curves[f"G{G}"] = {"replica_chunk": [c for c, _ in rb],
                           "replica_ttft_s": [(t / 1000 if t < math.inf else None) for _, t in rb], "end_L": M.end(G),
                           "crossover_m1.5": M.crossover(G, m=M_MAP)}
    for m in (1.0, M_MAP, 1.8):
        curves[f"pd_m{m:g}_s"] = [M.pd(L, m=m) / 1000 for L in Lf]
    curves["pd_fast_s"] = [M.pd(L, gbps=FAST_GBPS) / 1000 for L in Lf]
    curves["pd_kv220_s"] = [M.pd(L, kv="sliding_keep_all") / 1000 for L in Lf]
    curves["decode_gap_ms"] = [dgap(L) for L in Lf]
    out["curves"] = curves

    # ---------------- print
    print(f"26B FP8 on g7e: d={par['d']} ms  e={par['e']:.2f} ms  a={par['a']*1000:.2f} us/token  b={par['b']*1e6:.3f} ns/token^2  o={par['o']:.0f} ms")
    for m in meas:
        print(f"   replicas {m['L']:6d} chunk {m['c']:5d}: gap {m['gap_ms']}/{m['gap_model_ms']}  TTFT {m['ttft_ms']}/{m['ttft_model_ms']}   {m['src']}")
    for p in pdchk:
        print(f"   1P1D     {p['L']:6d}: TTFT {p['ttft_ms']}/{p['ttft_model_ms']}   {p['src']}")
    print(f"   1P1D decode-node longest gap p90: 4K {g4:.1f}, 16K {g16:.1f} ms")
    print(f"26B NVFP4 on g7 (k0={k0:.1f}, b={b7*1e6:.3f} ns, d={d7}, o={o7:.0f}):")
    for m in g7:
        print(f"   {m['L']:6d}: gap {m['gap_ms']}/{m['gap_model_ms']} ({m['gap_model_ms']/m['gap_ms']-1:+.1%})  "
              f"TTFT {m['ttft_ms']}/{m['ttft_model_ms']} ({m['ttft_model_ms']/m['ttft_ms']-1:+.1%})")
    print(f"   decode-node p90: {', '.join(f'{k}: {v:.1f}' for k, v in pg.items())}; line through 4K, 16K predicts 32K {pred32:.1f}")
    print("nine points:", nine)
    print(json.dumps(out["crossover"], indent=1))
    if args.json:
        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        json.dump(out, open(args.json, "w"), indent=1)


if __name__ == "__main__":
    main()
