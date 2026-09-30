#!/usr/bin/env python3
"""R3 round-2: sender-side (P) per-connection rate while busy = d(bytes_acked)/d(busy),
plus rwnd/sndbuf-limited time shares, from first/last ss sample of each run (read-only)."""
import re, sys
EXCL = {22, 5201, 5600}
conn_re = re.compile(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)")
def ms(tok, line):
    m = re.search(r"\b" + tok + r":(\d+)ms", line); return int(m.group(1)) if m else 0
def num(tok, line):
    m = re.search(r"\b" + tok + r":(\d+)", line); return int(m.group(1)) if m else 0
def snap(path):
    S, cur, ts, key = [], {}, None, None
    for line in open(path, errors="replace"):
        line = line.rstrip()
        if line.startswith("# "):
            if ts is not None: S.append((ts, cur))
            ts, cur, key = float(line[2:]), {}, None; continue
        m = conn_re.match(line.strip())
        if m:
            lp, rp = int(m.group(2)), int(m.group(4)); key = None if (lp in EXCL or rp in EXCL) else (lp, rp); continue
        if key:
            cur[key] = dict(acked=num("bytes_acked", line), busy=ms("busy", line), rwnd=ms("rwnd_limited", line),
                            sndbuf=ms("sndbuf_limited", line), retrans=num("bytes_retrans", line))
    if ts is not None: S.append((ts, cur))
    return S
for p in sys.argv[1:]:
    S = snap(p); a, b = S[0][1], S[-1][1]
    print(f"\n{p.split('/')[-1]}")
    TB = TBusy = 0
    for k in sorted(b):
        if k not in a: continue
        dB = b[k]["acked"] - a[k]["acked"]; dT = b[k]["busy"] - a[k]["busy"]
        dR = b[k]["rwnd"] - a[k]["rwnd"]; dS = b[k]["sndbuf"] - a[k]["sndbuf"]; dX = b[k]["retrans"] - a[k]["retrans"]
        if dB < 2**20: continue
        TB += dB; TBusy += dT
        print(f"  {k}: {dB/2**20:8.1f} MiB  busy {dT:6d} ms -> {dB*8/dT/1e6 if dT else float('nan'):6.2f} Gbps while busy; "
              f"rwnd_lim {dR} ms ({100*dR/max(dT,1):.0f}%), sndbuf_lim {dS} ms ({100*dS/max(dT,1):.0f}%), retrans {dX/2**20:.2f} MiB")
    # also cumulative (lifetime) numbers from last sample for context
