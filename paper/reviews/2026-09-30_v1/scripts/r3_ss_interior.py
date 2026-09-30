#!/usr/bin/env python3
"""R3 round-2: aggregate and per-connection rate in interior intervals of bursts (interval whose neighbours are also active),
split by how many connections were active; and max single-interval aggregate."""
import sys, importlib.util, statistics as st, collections
d = "<scratch>/reviews_v1/"
spec = importlib.util.spec_from_file_location("b", d + "r3_ss_bursts.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
for path in sys.argv[1:]:
    S = b.parse(path); keys = sorted({k for _, s in S for k in s})
    rows = []
    for (t0, s0), (t1, s1) in zip(S, S[1:]):
        dd = {k: max(0, (s1[k]["bytes_acked"] + s1[k]["bytes_received"]) - (s0[k]["bytes_acked"] + s0[k]["bytes_received"])) if k in s0 and k in s1 else 0 for k in keys}
        rows.append((t1 - t0, dd))
    act = lambda r: any(v > 64 * 1024 for v in r[1].values())
    byn = collections.defaultdict(list); percon = collections.defaultdict(list); allagg = []
    for i in range(1, len(rows) - 1):
        dt, dd = rows[i]
        if not act(rows[i]): continue
        agg = sum(dd.values()) * 8 / dt / 1e9; allagg.append(agg)
        if act(rows[i - 1]) and act(rows[i + 1]):
            # a connection counts as fully active if it moved data in prev, this, and next interval
            full = [k for k in keys if rows[i - 1][1][k] > 64*1024 and dd[k] > 64*1024 and rows[i + 1][1][k] > 64*1024]
            n = len([k for k in keys if dd[k] > 64 * 1024])
            byn[n].append(agg)
            for k in full: percon[n].append(dd[k] * 8 / dt / 1e9)
    print(f"{path.split('/')[-1]}: max interval aggregate {max(allagg):.1f} Gbps; p95 {sorted(allagg)[int(.95*len(allagg))]:.1f}")
    for n in sorted(byn):
        pc = percon.get(n, [])
        print(f"   interior intervals with {n} active: count {len(byn[n])}, aggregate median {st.median(byn[n]):.1f} max {max(byn[n]):.1f} Gbps"
              + (f"; per-connection (active through prev/next) median {st.median(pc):.1f} max {max(pc):.1f} (n={len(pc)})" if pc else ""))
