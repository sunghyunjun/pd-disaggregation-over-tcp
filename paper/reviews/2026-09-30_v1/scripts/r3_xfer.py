#!/usr/bin/env python3
"""R3 round-2: vLLM 'KV Transfer metrics' windows -> Gbps (MiB*8*1.048576/s) and per-transfer rate (MB/avg time)."""
import re, sys, statistics as st
pat = re.compile(r"Num successful transfers=(\d+), Avg xfer time \(ms\)=([\d.]+), P90 xfer time \(ms\)=([\d.]+).*Avg MB per transfer=([\d.]+), Throughput \(MB/s\)=([\d.]+), Avg number of descriptors=([\d.]+)")
CAP = 9.54
for p in sys.argv[1:]:
    W = []
    for line in open(p):
        m = pat.search(line)
        if m:
            n, avg, p90, mb, thr, desc = int(m[1]), float(m[2]), float(m[3]), float(m[4]), float(m[5]), float(m[6])
            W.append((n, avg, p90, mb, thr, desc))
    if not W: continue
    main = [w for w in W if w[3] > 100]   # drop warm-up (ShareGPT) windows
    g_thr = [w[4] * 8 * 1.048576 / 1000 for w in main]           # vLLM throughput field -> Gbps
    g_rate = [w[3] * 8 * 1.048576 / w[1] for w in main]         # MB/avg time -> Gbps
    ntr = sum(w[0] for w in main)
    # transfer-weighted avg time
    wavg = sum(w[0] * w[1] for w in main) / ntr
    mb = st.median([w[3] for w in main])
    print(f"{p.split('/')[-1]:40s} win={len(main):2d} xfers={ntr:3d} MiB={mb:6.1f} "
          f"thrGbps med={st.median(g_thr):5.2f} [{min(g_thr):5.2f},{max(g_thr):5.2f}]  "
          f"MB/avgt med={st.median(g_rate):5.2f}  avgt(ms) med={st.median([w[1] for w in main]):6.1f} range=[{min(w[1] for w in main):.0f},{max(w[1] for w in main):.0f}] "
          f"wavg={wavg:.1f} -> {mb*8*1.048576/wavg:5.2f} Gbps m={mb*8*1.048576/wavg/CAP:4.2f}  desc=[{min(w[5] for w in main):.0f},{max(w[5] for w in main):.0f}]")
