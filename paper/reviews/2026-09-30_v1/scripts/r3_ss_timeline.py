#!/usr/bin/env python3
"""R3 round-2: print per-interval per-connection MiB for the first N single-transfer bursts (P side)."""
import sys, importlib.util, io, contextlib
d = "<scratch>/reviews_v1/"
spec = importlib.util.spec_from_file_location("b", d + "r3_ss_bursts.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
path, N = sys.argv[1], int(sys.argv[2])
S = b.parse(path)
keys = sorted({k for _, s in S for k in s})
rows = []
for (t0, s0), (t1, s1) in zip(S, S[1:]):
    dd = {k: max(0, (s1[k]["bytes_acked"] + s1[k]["bytes_received"]) - (s0[k]["bytes_acked"] + s0[k]["bytes_received"])) if k in s0 and k in s1 else 0 for k in keys}
    rows.append((t0 - S[0][0], t1 - t0, dd))
shown, i = 0, 0
print("cols:", [k[1] if k[0] < 50000 or True else k for k in keys])
while i < len(rows) and shown < N:
    if any(v > 64 * 1024 for v in rows[i][2].values()):
        j = i
        while j < len(rows) and any(v > 64 * 1024 for v in rows[j][2].values()): j += 1
        tot = sum(sum(r[2].values()) for r in rows[i:j]) / 2**20
        print(f"-- burst t+{rows[i][0]:.2f}s total {tot:.0f} MiB")
        for r in rows[max(i-1,0):j+1]:
            print(f"   t+{r[0]:7.2f} dt={r[1]*1000:5.0f}ms  " + "  ".join(f"{r[2][k]/2**20:6.1f}" for k in keys) + f"   agg {sum(r[2].values())*8/r[1]/1e9:5.1f} Gbps")
        shown += 1; i = j
    else:
        i += 1
