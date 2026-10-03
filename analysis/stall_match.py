#!/usr/bin/env python3
"""Round E8 (step B2): match the "global stalls" seen by the client against the proxy instrumentation
(harness/proxy_trace.py) (report Appendix B.1).
Usage: stall_match.py PROXY_TRACE.jsonl RUN_DIR [RUN_DIR ...]
- Global stall: a moment at which a token gap above 50 ms occurred in 15 or more requests within 5 ms (the same
  definition as the mock reviewer's r2_global.py)
- Proxy pause: a generation-2 GC (>5 ms) or an event-loop lag (>20 ms) within +-100 ms of that moment
- start_times in bench.json and t in the proxy trace are both perf_counter (CLOCK_MONOTONIC) on the same machine,
  so they compare directly
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
