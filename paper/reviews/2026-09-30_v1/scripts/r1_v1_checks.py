#!/usr/bin/env python3
"""R1 round-2 checks (read-only). Run: python3 r1_v1_checks.py
1) replica proxy cap: TTFT>1s failures vs client in-flight count; server running/waiting (prom.txt)
2) D-server ITL histogram (>50 ms) per 1P1D run, pre/post diff
3) socket busy-time rate and rwnd_limited share per connection (ss)
"""
import json, glob, os, re, statistics as st
R = "results/E8"

print("== 1) replica runs: TTFT failures vs in-flight (rr_proxy uses aiohttp default connector, limit=100)")
for d in sorted(glob.glob(R + "/2026-*_B2_*")):
    b = json.load(open(d + "/bench.json"))
    rows = list(zip(b["start_times"], b["ttfts"], b["latencies"]))
    infl = lambda x: sum(1 for s, t, l in rows if s < x < s + l)
    fails = [s for s, t, l in rows if t > 1.0]
    fi = [infl(s) for s in fails]
    mx = 0; wmax = 0
    for line in open(d + "/prom.txt"):
        m = re.search(r"vllm:num_requests_running\{[^}]*\}\s+([0-9.]+)", line)
        w = re.search(r"vllm:num_requests_waiting\{[^}]*\}\s+([0-9.]+)", line)
        if m: mx = max(mx, float(m.group(1)))
        if w: wmax = max(wmax, float(w.group(1)))
    tt = sorted(b["ttfts"])
    print(f"{os.path.basename(d)[18:]:42s} n={len(rows):5d} maxC={b.get('max_concurrent_requests')!s:>4} "
          f"ttft>1s={len(fails):4d} min_inflight_at_fail={min(fi) if fi else '-':>4} "
          f"ttft p50/p90={tt[len(tt)//2]*1e3:.0f}/{tt[int(.9*(len(tt)-1))]*1e3:.0f}ms server(one node) max_running={mx:.0f} max_waiting={wmax:.0f}")

print("\n== 2) decode-server ITL histogram diff (metrics_E8)")
def h(f):
    d = {}
    for l in open(f):
        m = re.match(r'vllm:inter_token_latency_seconds_bucket\{[^}]*le="([^"]+)"[^}]*\}\s+([0-9.e+]+)', l)
        if m: d[m.group(1)] = float(m.group(2))
    return d
for pre in sorted(glob.glob(R + "/metrics_E8/*_pre_50.txt")):
    a, b = h(pre), h(pre.replace("_pre_", "_post_"))
    diff = {k: b[k] - a.get(k, 0) for k in b}
    tot = diff["+Inf"]
    print(f"{os.path.basename(pre)[:-11]:34s} tokens={tot:8.0f} <=25ms={diff['0.025']/tot:.3f} >50ms={tot-diff['0.05']:.0f}")

print("\n== 3) ss on prefill node: per-connection rate while busy, rwnd_limited share")
for f in sorted(glob.glob(R + "/ss/*_P.txt")):
    first, last, key = {}, {}, None
    for line in open(f, errors="replace"):
        if line.startswith("# "): continue
        m = re.match(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)", line.strip())
        if m:
            lp, rp = int(m.group(2)), int(m.group(4))
            key = None if lp in (22, 5201, 5600) or rp in (22, 5201, 5600) else (lp, rp); continue
        if key:
            g = lambda p: int(re.search(p, line).group(1)) if re.search(p, line) else 0
            v = (g(r"busy:(\d+)ms"), g(r"rwnd_limited:(\d+)ms"), g(r"bytes_acked:(\d+)"))
            first.setdefault(key, v); last[key] = v
    out = []
    for k in last:
        dbusy, drw, dby = [last[k][i] - first[k][i] for i in range(3)]
        if dby > 5e6:
            out.append(f"{dby*8/max(dbusy,1)/1e6:.1f}Gbps/{100*drw/max(dbusy,1):.0f}%")
    print(f"{os.path.basename(f):42s} " + "  ".join(out))
