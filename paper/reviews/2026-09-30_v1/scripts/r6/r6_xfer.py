#!/usr/bin/env python3
"""Chair check (read-only): vLLM KV-transfer 10 s windows -> Gbps and m = rate/9.54 by run; transfer-weighted mean;
max window; mean descriptors. Run: python3 r6_xfer.py"""
import glob, re, os, statistics as st
MIB = 1.048576
for f in sorted(glob.glob("results/E8/xfer_E8/*.log")):
    w = []
    for line in open(f, errors="replace"):
        m = re.search(r"Num successful transfers=(\d+), Avg xfer time \(ms\)=([0-9.]+).*Avg MB per transfer=([0-9.]+).*descriptors=([0-9.]+)", line)
        if m:
            n, t, mb, dsc = int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
            w.append((n, t, mb, dsc, mb * MIB * 8 / t))
    big = [x for x in w if x[2] > 100]
    if not big: continue
    med = st.median(x[4] for x in big)
    wmean = sum(x[0] * x[2] for x in big) * MIB * 8 / sum(x[0] * x[1] for x in big)
    print(f"{os.path.basename(f)[:-7]:34s} win={len(big):3d} MB={st.median(x[2] for x in big):6.1f} xfer_ms_med={st.median(x[1] for x in big):6.1f} "
          f"Gbps med={med:5.2f} wmean={wmean:5.2f} max={max(x[4] for x in big):5.2f} m_med={med/9.54:4.2f} desc_med={st.median(x[3] for x in big):6.0f}")
