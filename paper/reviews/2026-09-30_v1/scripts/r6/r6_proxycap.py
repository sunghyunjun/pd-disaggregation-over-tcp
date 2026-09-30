#!/usr/bin/env python3
"""Chair check (read-only): which replica runs (rr_proxy, aiohttp default limit=100) reached >=100 in-flight
requests at the client, and how many of their strict-SLO failures arrived while >=100 were in flight.
Audited runs only (safe_runs.csv safety in {안전, 주의}). Run: python3 r6_proxycap.py"""
import csv, json, os, glob, bisect
ROOT = "<repo>"
safe = {r["run_id"]: r for r in csv.DictReader(open(ROOT + "/results/safe_runs.csv"))}
paths = {os.path.basename(os.path.dirname(p)): p for p in glob.glob(ROOT + "/results/*/*/bench.json")}
def inflight_at(starts, ends):
    # number in flight (started, not finished) at each start time, excluding itself
    se = sorted(ends)
    return [sum(1 for s2 in starts if s2 < s) - bisect.bisect_right(se, s) for s in starts]
rows = []
for rid, r in safe.items():
    if r["safety"] not in ("안전", "주의"): continue
    cfg = r["config"]
    if not ("B2" in cfg or "B3" in cfg): continue
    if r["rate"] in ("self", "inf"): continue
    if rid not in paths: continue
    b = json.load(open(paths[rid]))
    st, lat, tt, it = b["start_times"], b["latencies"], b["ttfts"], b["itls"]
    n = len(st)
    ends = [s + l for s, l in zip(st, lat)]
    order = sorted(range(n), key=lambda i: st[i])
    ss = [st[i] for i in order]; se = sorted(ends)
    infl = [i - bisect.bisect_right(se, s) for i, s in enumerate(ss)]  # in flight at arrival
    mx = max(infl)
    ttf = [order[k] for k in range(n) if tt[order[k]] and tt[order[k]] > 1.0]
    ttf_cap = sum(1 for k in range(n) if tt[order[k]] and tt[order[k]] > 1.0 and infl[k] >= 100)
    gapf = sum(1 for i in range(n) if it[i] and max(it[i]) > 0.05)
    frac100 = sum(1 for x in infl if x >= 100) / n
    rows.append((r["stage"], cfg, r["workload"], float(r["rate"]), r["chunk"], rid[:17], n, float(r["attain_chat"]), mx, frac100, len(ttf), ttf_cap, gapf, r["safety"]))
rows.sort()
print(f"{'stage':5s} {'config':14s} {'wl':9s} {'tot_r':>6s} {'chunk':>6s} {'n':>5s} {'att':>6s} {'maxInfl':>7s} {'arr@>=100':>9s} {'ttft>1s':>7s} {'..@>=100':>8s} {'gap>50':>6s}")
for x in rows:
    if x[8] >= 80:
        print(f"{x[0]:5s} {x[1]:14s} {x[2]:9s} {x[3]:6.1f} {x[4]:>6s} {x[6]:5d} {x[7]:6.3f} {x[8]:7d} {x[9]:9.3f} {x[10]:7d} {x[11]:8d} {x[12]:6d} {x[13]}")
print("\nreplica runs with max in-flight < 80 are not affected; count =", sum(1 for x in rows if x[8] < 80), "of", len(rows))
