#!/usr/bin/env python3
"""Attainment at the points that decide the comparisons, with 95% intervals from a hierarchical bootstrap
(resample the repeated runs with replacement, then resample 20 time blocks within each run) (report Appendix F).
Written for the second mock review (R2-4, meta-reviewer item A11); the third review (A13-16) added the 30 ms
decision points and the points behind the threefold claim. Usage: python3 analysis/decisive_ci.py [--tex] [--rebuild]
A request meets the SLO when its first token arrives within T and its longest gap is within B (a request whose output
is one token passes the gap condition). Reads the cache results/per_request.json.gz and uses safe runs only.
"""
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slo_sensitivity as ss  # noqa: E402

# The cache is rebuilt automatically when it no longer matches safe_runs.csv; --rebuild always rebuilds it.
C = ss.load_cache("results/safe_runs.csv", rebuild="--rebuild" in sys.argv)
POINTS = [  # (label, workload, [(stages, config)], total rate, per-GPU, T, B_ms)
    ("26B NVFP4 4K, replicas chunk 2,560", "random", [(("E5", "E7"), "26_B2"), (("E8",), "26_B2_c2560")], 2, 1, 1.0, 50),
    ("26B NVFP4 4K, replicas chunk 2,560", "random", [(("E5", "E7"), "26_B2"), (("E8",), "26_B2_c2560")], 4, 2, 1.0, 50),
    ("26B NVFP4 4K, 1P1D aiohttp", "random", [(("E8",), "26_1P1D_aio")], 6, 3, 1.0, 50),
    ("26B NVFP4 4K, replicas chunk 1,024", "random", [(("E9",), "26_B2_c1024")], 8, 4, 1.0, 50),
    ("26B NVFP4 4K, replicas chunk 1,024", "random", [(("E9",), "26_B2_c1024")], 10, 5, 1.0, 50),
    ("26B NVFP4 4K, replicas chunk 512", "random", [(("E9",), "26_B2_c512")], 8, 4, 1.0, 50),
    ("26B NVFP4 4K, 1P1D aiohttp", "random", [(("E8",), "26_1P1D_aio")], 8, 4, 1.0, 50),
    ("26B NVFP4 4K, 1P1D test proxy", "random", [(("E5", "E7"), "26_1P1D"), (("E8",), "26_1P1D_toyi")], 8, 4, 1.0, 50),
    ("26B NVFP4 4K, 1P1D aiohttp, prefill chunk 8,192, UCX segment sizes only", "random", [(("E9",), "26_1P1D_aio_p8192")], 8, 4, 1.0, 50),
    ("26B NVFP4 4K, replicas chunk 512", "random", [(("E9",), "26_B2_c512")], 4, 2, 1.0, 30),
    ("26B NVFP4 4K, replicas chunk 512", "random", [(("E9",), "26_B2_c512")], 6, 3, 1.0, 30),
    ("26B NVFP4 4K, 1P1D test proxy", "random", [(("E5", "E7"), "26_1P1D")], 4, 2, 1.0, 30),
    ("26B NVFP4 4K, 1P1D test proxy", "random", [(("E5", "E7"), "26_1P1D")], 6, 3, 1.0, 30),
    ("26B NVFP4 4K, 1P1D aiohttp", "random", [(("E8",), "26_1P1D_aio")], 6, 3, 1.0, 30),
    ("26B FP8 4K, replicas chunk 512", "random", [(("E9",), "26F_B2_c512")], 2, 1, 1.0, 30),
    ("26B FP8 4K, 1P1D test proxy", "random", [(("E7",), "26F_1P1D")], 2, 1, 1.0, 30),
    ("31B chat, replicas chunk 256", "sharegpt", [(("E9",), "31_B2_c256")], 16, 8, 1.0, 50),
    ("31B chat, 1P1D aiohttp", "sharegpt", [(("E8", "E9"), "31_1P1D_aio")], 8, 4, 1.0, 50),
    ("31B chat, 1P1D test proxy", "sharegpt", [(("E5", "E7"), "31_1P1D")], 8, 4, 1.0, 50),
    ("31B chat, 1P1D aiohttp", "sharegpt", [(("E9",), "31_1P1D_aio")], 12, 6, 1.0, 50),
]

def oks(r, T, B):
    return [(not e) and t <= T and (m is None or m * 1000 <= B) for t, m, e in zip(r["ttft"], r["maxitl"], r["err"])]


def hboot(runs, n=2000, blocks=20, seed=0):
    rnd = random.Random(seed)
    per = []
    for o in runs:
        k = max(1, len(o) // blocks)
        per.append([o[i:i + k] for i in range(0, len(o), k)])
    vals = []
    for _ in range(n):
        tot = ok = 0
        for _ in range(len(runs)):
            bl = rnd.choice(per)
            for _ in range(len(bl)):
                b = rnd.choice(bl); tot += len(b); ok += sum(b)
        vals.append(ok / tot)
    vals.sort()
    return vals[int(.025 * n)], vals[int(.975 * n)]


rows = []
for lab, wl, srcs, rate, pg, T, B in POINTS:
    runs = []
    for stages, cfg in srcs:
        for rid, r in sorted(C.items()):
            if r["stage"] in stages and r["config"] == cfg and r["workload"] == wl and float(r["rate"]) == rate and r["safety"] == "안전":
                runs.append(oks(r, T, B))
    if not runs:
        continue
    each = [sum(o) / len(o) for o in runs]
    lo, hi = hboot(runs)
    st = sorted({r["stage"] for rid, r in C.items() for stages, cfg in srcs
                 if r["stage"] in stages and r["config"] == cfg and r["workload"] == wl and float(r["rate"]) == rate and r["safety"] == "안전"})
    rows.append((f"{lab} ({', '.join(st)})", pg, B, len(runs), each, lo, hi))

if "--tex" in sys.argv:
    for lab, pg, B, n, each, lo, hi in rows:
        print(f"{lab} & {pg:g} & {B} & {n} & {', '.join(f'{x:.3f}' for x in each)} & {lo:.3f}--{hi:.3f} \\\\")
else:
    for lab, pg, B, n, each, lo, hi in rows:
        print(f"{lab:44s} {pg:>3g}/GPU B={B:>2} runs={n} each={[round(x, 3) for x in each]} 95%=[{lo:.3f}, {hi:.3f}]")
