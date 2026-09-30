#!/usr/bin/env python3
"""R3 round-3: does the 256 KiB receive-window cap (D-side wscale 2) explain the ~20 Gbps aggregate of 31B 7-var transfers?
Per ss interval on the P (sender) side: active connections (>64 KiB moved), measured aggregate Gbps,
per-connection srtt at interval end, window bound sum(262140 B * 8 / srtt), and share of busy time that was rwnd-limited."""
import re, sys, statistics as st, collections
EXCL = {22, 5201, 5600}
conn_re = re.compile(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)")
def f(tok, line, pat=r"(\d+)"):
    m = re.search(r"\b" + tok + ":" + pat, line); return m.group(1) if m else None
def parse(p):
    S, cur, ts, key = [], {}, None, None
    for line in open(p, errors="replace"):
        line = line.rstrip()
        if line.startswith("# "):
            if ts is not None: S.append((ts, cur))
            ts, cur, key = float(line[2:]), {}, None; continue
        m = conn_re.match(line.strip())
        if m:
            lp, rp = int(m.group(2)), int(m.group(4)); key = None if (lp in EXCL or rp in EXCL) else (lp, rp); continue
        if key:
            rtt = f("rtt", line, r"([\d.]+)")
            ws = f("wscale", line, r"(\d+,\d+)")
            cur[key] = dict(acked=int(f("bytes_acked", line) or 0), busy=int(f("busy", line, r"(\d+)ms") or 0),
                            rwnd=int(f("rwnd_limited", line, r"(\d+)ms") or 0), rtt=float(rtt) if rtt else None,
                            ws=ws, cwnd=int(f("cwnd", line) or 0))
    if ts is not None: S.append((ts, cur))
    return S
for p in sys.argv[1:]:
    S = parse(p)
    ws = collections.Counter(v["ws"] for _, s in S for v in s.values())
    snd_ws = int(ws.most_common(1)[0][0].split(",")[0])
    maxwin = 65535 << snd_ws
    by = collections.defaultdict(lambda: dict(agg=[], bound=[], rtt=[], rw=[], cw=[]))
    for (t0, s0), (t1, s1) in zip(S, S[1:]):
        dt = t1 - t0
        act = [k for k in s1 if k in s0 and s1[k]["acked"] - s0[k]["acked"] > 64 * 1024]
        if not act: continue
        n = len(act)
        agg = sum(s1[k]["acked"] - s0[k]["acked"] for k in act) * 8 / dt / 1e9
        rtts = [s1[k]["rtt"] for k in act if s1[k]["rtt"]]
        bound = sum(maxwin * 8 / (r / 1000) / 1e9 for r in rtts)
        db = sum(s1[k]["busy"] - s0[k]["busy"] for k in act); dr = sum(s1[k]["rwnd"] - s0[k]["rwnd"] for k in act)
        d = by[n]; d["agg"].append(agg); d["bound"].append(bound); d["rtt"] += rtts
        if db > 0: d["rw"].append(dr / db)
        d["cw"] += [s1[k]["cwnd"] for k in act]
    print(f"\n{p.split('/')[-1]}: sender sees peer wscale {snd_ws} -> max rwnd {maxwin} B; wscale tally {dict(ws)}")
    for n in sorted(by):
        d = by[n]
        if len(d["agg"]) < 3: continue
        print(f"  {n} active: intervals {len(d['agg']):4d}  aggregate p50 {st.median(d['agg']):5.1f} p90 {sorted(d['agg'])[int(.9*len(d['agg']))]:5.1f} Gbps | "
              f"srtt p50 {st.median(d['rtt']):.3f} ms | window bound p50 {st.median(d['bound']):6.1f} Gbps | rwnd-limited share of busy p50 {st.median(d['rw']) if d['rw'] else float('nan'):.2f} | cwnd p50 {st.median(d['cw']):.0f} segs")
