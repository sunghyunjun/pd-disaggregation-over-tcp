#!/usr/bin/env python3
"""판정을 가르는 지점의 달성률과 95% 구간(계층 부트스트랩: 반복 런을 복원 추출한 뒤 각 런 안에서 시간 블록 20개를 복원 추출).
2차 모의 심사(R2-4, 종합 심사자 A11) 대응. 3차 심사(A13-16)에서 30 ms 결정점과 3배의 근거 점을 더했다. 사용: python3 harness/decisive_ci.py [--tex] [--rebuild]
판정 기준: 요청별 첫 토큰 ≤ T, 요청 내 최대 간격 ≤ B(출력 1토큰 요청은 간격 조건 통과). 캐시 results/per_request.json.gz(안전 런만).
"""
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slo_sensitivity as ss  # noqa: E402

# 캐시가 safe_runs.csv와 어긋나면 자동으로 다시 만든다. --rebuild면 항상 다시 만든다.
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
