#!/usr/bin/env python3
"""Round E8 (step B3): count the TCP connections that carried the KV transfer, and each connection's share, from
the output of harness/ss_sample.sh (report Section 4.3).
Usage: ss_parse.py FILE [--min-bytes 1000000]
- A connection is a (local port, remote port) pair. Ports 22, 5201, and 5600 are excluded.
- Per-connection volume is the growth of bytes_acked (sending side) and bytes_received (receiving side) between samples.
- Prints the number of connections that carried more than min-bytes over the whole file, each connection's total
  and share, and the distribution of how many connections moved bytes in the same sample.
"""
import re, sys, collections

EXCL = {22, 5201, 5600}
path = sys.argv[1]
minb = int(sys.argv[sys.argv.index("--min-bytes") + 1]) if "--min-bytes" in sys.argv else 1_000_000
samples, cur, ts = [], {}, None
conn_re = re.compile(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)")
for line in open(path, errors="replace"):
    line = line.rstrip("\n")
    if line.startswith("# "):
        if ts is not None:
            samples.append((ts, cur))
        ts, cur, key = float(line[2:]), {}, None
        continue
    m = conn_re.match(line.strip())
    if m:
        lp, rp = int(m.group(2)), int(m.group(4))
        key = None if (lp in EXCL or rp in EXCL) else (lp, rp)
        continue
    if key is not None:
        a = re.search(r"bytes_acked:(\d+)", line)
        r = re.search(r"bytes_received:(\d+)", line)
        cur[key] = (int(a.group(1)) if a else 0) + (int(r.group(1)) if r else 0)
if ts is not None:
    samples.append((ts, cur))

tot = collections.Counter()
active_per_sample = []
for (t0, s0), (t1, s1) in zip(samples, samples[1:]):
    n = 0
    for k, v in s1.items():
        d = v - s0.get(k, v)
        if d > 0:
            tot[k] += d
            if d > 64 * 1024:
                n += 1
    active_per_sample.append(n)
big = {k: v for k, v in tot.items() if v >= minb}
S = sum(big.values()) or 1
print(f"samples={len(samples)}  connections_seen={len(tot)}  carrying>={minb/1e6:.1f}MB: {len(big)}")
for k, v in sorted(big.items(), key=lambda x: -x[1]):
    print(f"  ports {k}: {v/2**20:9.1f} MiB  {100*v/S:5.1f}%")
dist = collections.Counter(active_per_sample)
busy = [n for n in active_per_sample if n > 0]
print("connections moving >64KiB per sample (count: samples):", dict(sorted(dist.items())))
if busy:
    print(f"while transferring: mean {sum(busy)/len(busy):.2f}, max {max(busy)} connections active")
