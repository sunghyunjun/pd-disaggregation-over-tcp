# Parse vLLM KV transfer logs (read-only) -> per-log transfer-weighted mean time, MiB/transfer, Gbps, m (vs 9.54), descriptors
import re, glob, os, statistics as st, sys
pat = re.compile(r"Num successful transfers=(\d+), Avg xfer time \(ms\)=([\d.]+), P90 xfer time \(ms\)=([\d.]+).*Avg MB per transfer=([\d.]+), Throughput \(MB/s\)=([\d.]+), Avg number of descriptors=([\d.]+)")
GB = 8.388608  # Mbit per MiB
rows = []
for f in sorted(glob.glob(os.path.expanduser("<repo>/results/E*/xfer_E*/*.log"))):
    W = []
    for line in open(f, errors="ignore"):
        m = pat.search(line)
        if m:
            n, t, p90, mb, thr, d = int(m[1]), float(m[2]), float(m[3]), float(m[4]), float(m[5]), float(m[6])
            if n > 0 and mb > 0: W.append((n, t, p90, mb, thr, d))
    if not W: continue
    N = sum(w[0] for w in W)
    tw = sum(w[0]*w[1] for w in W)/N
    mbw = sum(w[0]*w[3] for w in W)/N
    gb_windows = [w[3]*GB/w[1] for w in W if w[0] >= 1]   # per-window Gbps = MiB*8.39/ms
    gbps_med = st.median(gb_windows)
    dw = sum(w[0]*w[5] for w in W)/N
    rows.append((f.split("results/")[1], N, tw, mbw, mbw*GB/tw, gbps_med, gbps_med/9.54, dw))
sel = sys.argv[1] if len(sys.argv) > 1 else ""
print(f"{'log':58s} {'N':>5s} {'t_w ms':>7s} {'MiB':>6s} {'Gbps_w':>6s} {'Gbps_med':>8s} {'m_med':>5s} {'desc':>6s}")
for r in rows:
    if sel in r[0]:
        print(f"{r[0]:58s} {r[1]:5d} {r[2]:7.1f} {r[3]:6.1f} {r[4]:6.2f} {r[5]:8.2f} {r[6]:5.2f} {r[7]:6.0f}")
