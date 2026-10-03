#!/usr/bin/env python3
"""세션 E8(B2): 클라이언트가 본 '전역 정지'를 프록시 계측(proxy_trace.py)과 맞춘다.
사용: stall_match.py PROXY_TRACE.jsonl RUN_DIR [RUN_DIR ...]
- 전역 정지: 50 ms 넘는 토큰 간격이 5 ms 안에 15개 이상 요청에서 동시에 난 순간(심사자 r2_global.py와 같은 정의)
- 프록시 정지: 같은 시각 ±100 ms 안의 2세대 GC(>5 ms) 또는 이벤트 루프 지연(>20 ms)
- bench.json의 start_times와 프록시의 t는 같은 머신의 perf_counter(CLOCK_MONOTONIC)라 그대로 비교된다
"""
import json, os, sys

tr = [json.loads(l) for l in open(sys.argv[1])]
gc2 = [x for x in tr if x["k"] == "gc" and x.get("gen") == 2]
lag = [x for x in tr if x["k"] == "lag"]
for d in sys.argv[2:]:
    if not os.path.exists(d + "/bench.json"):
        continue
    b = json.load(open(d + "/bench.json"))
    st, T, I = b["start_times"], b["ttfts"], b["itls"]
    E = b.get("errors") or [""] * len(T)
    t0, t1 = min(st), max(st) + 60
    ev = []
    for i, (s, t, l) in enumerate(zip(st, T, I)):
        tt = s + t
        for g in l:
            tt += g
            if g > 0.05:
                ev.append((tt, i, g))
    ev.sort()
    cl = []
    for e in ev:
        if cl and e[0] - cl[-1][-1][0] < 0.005:
            cl[-1].append(e)
        else:
            cl.append([e])
    glob = [c for c in cl if len({x[1] for x in c}) >= 15]
    glob_req = {x[1] for c in glob for x in c}
    other_req = {x[1] for c in cl if c not in glob for x in c}
    n = len(T)
    ok = [(not e) and t <= 1 and (not l or max(l) <= 0.05) for t, l, e in zip(T, I, E)]
    ok_wo = [o or ((not e) and t <= 1 and bool(l) and i in glob_req and i not in other_req)
             for i, (o, t, l, e) in enumerate(zip(ok, T, I, E))]
    gin = [x for x in gc2 if t0 <= x["t"] <= t1]
    lin = [x for x in lag if t0 <= x["t"] <= t1]
    pauses = gin + lin
    matched = sum(any(abs(c[0][0] - p["t"]) < 0.1 for p in pauses) for c in glob)
    print(f"{os.path.basename(d)}: att={sum(ok)/n:.3f} att_without_global={sum(ok_wo)/n:.3f} "
          f"global_events={len(glob)} matched_to_proxy_pause={matched} "
          f"gen2_gc_ms={[round(x['ms']) for x in gin]} loop_lag_ms={[round(x['ms']) for x in lin]}")
