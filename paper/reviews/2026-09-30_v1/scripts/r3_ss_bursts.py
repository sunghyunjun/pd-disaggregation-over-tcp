#!/usr/bin/env python3
"""R3 round-2 check: per-transfer (burst) analysis of E8 ss samples (read-only)."""
import re, sys, collections, statistics as st
EXCL = {22, 5201, 5600}
conn_re = re.compile(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)")
FIELDS = ["bytes_acked", "bytes_received", "bytes_retrans", "cwnd", "rtt", "minrtt", "rcv_space", "rcv_ssthresh"]
def parse(path):
    samples, cur, ts, key = [], {}, None, None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# "):
            if ts is not None: samples.append((ts, cur))
            ts, cur, key = float(line[2:]), {}, None; continue
        m = conn_re.match(line.strip())
        if m:
            lp, rp = int(m.group(2)), int(m.group(4))
            key = None if (lp in EXCL or rp in EXCL) else (lp, rp); continue
        if key is not None:
            d = {}
            for f in FIELDS:
                mm = re.search(r"\b" + f + r":([\d.]+)(?:/[\d.]+)?", line)
                d[f] = float(mm.group(1)) if mm else 0.0
            d["rwnd_limited"] = bool(re.search(r"rwnd_limited", line))
            d["sndbuf_limited"] = bool(re.search(r"sndbuf_limited", line))
            d["line"] = line
            cur[key] = d
    if ts is not None: samples.append((ts, cur))
    return samples

def analyze(path, thr=64*1024):
    S = parse(path)
    keys = sorted({k for _, s in S for k in s})
    # first-sample cumulative (pre-run, includes warmup)
    first = S[0][1]
    print(f"\n=== {path.split('/')[-1]}  samples={len(S)} span={S[-1][0]-S[0][0]:.1f}s")
    dts = [b[0]-a[0] for a, b in zip(S, S[1:])]
    print(f"  sample interval: median {st.median(dts)*1000:.1f} ms, p90 {sorted(dts)[int(.9*len(dts))]*1000:.1f}, max {max(dts)*1000:.1f}")
    for k in keys:
        d0 = first.get(k)
        if d0: print(f"  conn {k}: at start acked+recv={(d0['bytes_acked']+d0['bytes_received'])/2**20:8.1f} MiB  minrtt={d0['minrtt']} ms")
    # deltas
    rows = []
    for (t0, s0), (t1, s1) in zip(S, S[1:]):
        dd = {}
        for k in keys:
            if k in s1 and k in s0:
                v1 = s1[k]["bytes_acked"] + s1[k]["bytes_received"]
                v0 = s0[k]["bytes_acked"] + s0[k]["bytes_received"]
                dd[k] = max(0, v1 - v0)
            elif k in s1:
                dd[k] = 0
        rows.append((t0, t1, dd))
    # bursts: consecutive intervals with any conn moving > thr
    bursts, cur = [], None
    for t0, t1, dd in rows:
        act = sum(v for v in dd.values())
        if any(v > thr for v in dd.values()):
            if cur is None: cur = {"t0": t0, "t1": t1, "n": 0, "bytes": collections.Counter()}
            cur["t1"] = t1; cur["n"] += 1
            for k, v in dd.items(): cur["bytes"][k] += v
        else:
            if cur is not None: bursts.append(cur); cur = None
    if cur: bursts.append(cur)
    tot = sum(sum(b["bytes"].values()) for b in bursts)
    print(f"  bursts={len(bursts)}  total={tot/2**20:.1f} MiB")
    # per-burst connection counts (conns carrying >1 MiB in the burst) and size
    ncon = collections.Counter(); sizes = []; nint = collections.Counter()
    shares = collections.Counter()
    fifth = None
    big4 = sorted(keys, key=lambda k: -sum(b["bytes"][k] for b in bursts))
    fifth = big4[4] if len(big4) > 4 else None
    fifth_bursts = []
    splits = collections.Counter()
    for b in bursts:
        tb = sum(b["bytes"].values()); sizes.append(tb)
        used = [k for k, v in b["bytes"].items() if v > 1 * 2**20]
        ncon[len(used)] += 1; nint[b["n"]] += 1
        if fifth and b["bytes"][fifth] > 2**20:
            fifth_bursts.append((b["t0"] - S[0][0], tb / 2**20, b["bytes"][fifth] / 2**20, len(used)))
        # split pattern in MiB rounded
        pat = tuple(sorted((round(v / 2**20) for v in b["bytes"].values() if v > 2**20), reverse=True))
        splits[pat] += 1
    print(f"  burst size MiB: median {st.median(sizes)/2**20:.1f}, min {min(sizes)/2**20:.1f}, max {max(sizes)/2**20:.1f}")
    print(f"  conns >1MiB per burst: {dict(sorted(ncon.items()))}")
    print(f"  intervals per burst: {dict(sorted(nint.items()))}")
    print(f"  top split patterns (MiB per conn): {splits.most_common(8)}")
    if fifth:
        print(f"  5th conn {fifth}: bursts using it: {len(fifth_bursts)}")
        for x in fifth_bursts[:10]: print(f"    t+{x[0]:.1f}s burst {x[1]:.1f} MiB, on 5th {x[2]:.1f} MiB, conns used {x[3]}")
    # TCP state summary on the main conns
    rw = collections.Counter(); cw = []; rtts = []; retr = collections.Counter()
    for _, s in S:
        for k, d in s.items():
            if d["rwnd_limited"]: rw[k] += 1
            cw.append(d["cwnd"]); rtts.append(d["minrtt"])
    last = S[-1][1]
    for k in keys:
        if k in last:
            L = last[k]
            print(f"  end {k}: retrans_bytes={L['bytes_retrans']:.0f} cwnd={L['cwnd']:.0f} rcv_space={L['rcv_space']:.0f} rcv_ssthresh={L['rcv_ssthresh']:.0f} minrtt={L['minrtt']}")
    return bursts, S

if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
