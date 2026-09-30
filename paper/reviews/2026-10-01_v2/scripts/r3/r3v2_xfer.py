#!/usr/bin/env python3
"""R3 round-3: vLLM 'KV Transfer metrics' -> per-run volume, transfer time (transfer-weighted), Gbps, m (C_flow 9.54),
window-median Gbps, descriptor means, p90/avg spread. All windows with >=5 transfers (drops warm-up singletons).
Usage: r3v2_xfer.py LOG... (Gbps = MiB/s * 0.008388608)"""
import re, sys, statistics as st
pat = re.compile(r"Num successful transfers=(\d+), Avg xfer time \(ms\)=([\d.]+), P90 xfer time \(ms\)=([\d.]+).*Avg MB per transfer=([\d.]+), Throughput \(MB/s\)=([\d.]+), Avg number of descriptors=([\d.]+)")
C = 9.54
for p in sys.argv[1:]:
    W = [tuple(map(float, m.groups())) for l in open(p) if (m := pat.search(l))]
    W = [w for w in W if w[0] >= 5]
    if not W: continue
    n = sum(w[0] for w in W); mb = sum(w[0] * w[3] for w in W) / n; t = sum(w[0] * w[1] for w in W) / n
    d = sum(w[0] * w[5] for w in W) / n; g = [w[4] * 0.008388608 for w in W]
    spread = st.median(w[2] for w in W) / st.median(w[1] for w in W)
    print(f"{p.split('results/')[-1]:58s} xfers {int(n):5d} MiB {mb:6.1f} t_wtd {t:6.1f} ms  Gbps_wtd {mb*8.388608/t:5.2f} m_wtd {mb*8.388608/t/C:4.2f} | "
          f"win-median {st.median(g):5.2f} m {st.median(g)/C:4.2f} | desc_wtd {d:5.0f} [{min(w[5] for w in W):.0f},{max(w[5] for w in W):.0f}] p90/avg {spread:.2f}")
