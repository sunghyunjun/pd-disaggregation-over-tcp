#!/usr/bin/env python3
"""R3 round-3: per-second prefill-node NIC tx (sar -n DEV, kB=1024, includes headers) during 1P1D runs.
Aggregate wire rate the P node sent, to compare with the ~20 Gbps shared limit and offered load."""
import statistics as st
R = "<repo>/results/"
def load(p):
    out = []
    for l in open(p):
        f = l.split()
        if len(f) >= 6 and f[1].startswith("enp"):
            h, m, s = map(int, f[0].split(":"))
            out.append((h * 3600 + m * 60 + s, float(f[5]) * 1024 * 8 / 1e9, float(f[4]) * 1024 * 8 / 1e9))
    return out
def t(x):
    h, m, s = map(int, x.split(":")); return h * 3600 + m * 60 + s
E8 = load(R + "E8/collect/ip-172-31-87-176/collect_ip-172-31-87-176_e8_sar.txt")   # P node in E8 (P176)
E9 = load(R + "E9/collect/ip-172-31-82-93/collect_ip-172-31-82-93_e9_sar.txt")     # P node in E9 (P93)
runs = [  # label, data, start, end, offered GiB/s-ish (req/s total x MiB)
    ("E8 toyi 7var r8#0 (4/GPU)", E8, "01:05:00", "01:08:56", 8 * 140),
    ("E8 toyi 7var r8#1", E8, "01:08:56", "01:12:52", 8 * 140),
    ("E8 toyi 7var r8#2", E8, "01:12:52", "01:16:45", 8 * 140),
    ("E8 toyi 7var r6 (3/GPU)", E8, "01:16:45", "01:20:30", 6 * 140),
    ("E8 aio 7var r8#0 (4/GPU)", E8, "01:26:13", "01:30:08", 8 * 140),
    ("E8 aio 7var r8#1", E8, "01:30:08", "01:34:04", 8 * 140),
    ("E8 aio 7var r8#2", E8, "01:34:04", "01:37:58", 8 * 140),
    ("E8 aio 7var r6 (3/GPU)", E8, "01:37:58", "01:41:42", 6 * 140),
    ("E8 seg r0.5 (0.25/GPU)", E8, "01:43:46", "01:47:25", 0.5 * 140),
    ("E8 seg r1 (0.5/GPU)", E8, "01:47:25", "01:50:45", 1 * 140),
    ("E8 def r0.5", E8, "01:52:48", "01:56:28", 0.5 * 140),
    ("E8 31B 7var r0.25 4K", E8, "02:28:09", "02:35:18", 0.25 * 560),
    ("E8 aio 7var r10 (5/GPU)", E8, "03:12:23", "03:16:29", 10 * 140),
    ("E8 31B chat aio r8#0", E8, "03:23:35", "03:27:11", 8 * 105),
    ("E8 31B chat aio r8#1", E8, "03:27:11", "03:30:48", 8 * 105),
    ("E9 p8192 SEG r8#0 (4/GPU)", E9, "15:07:50", "15:11:45", 8 * 140),
    ("E9 p8192 SEG r8#1", E9, "15:11:45", "15:15:45", 8 * 140),
    ("E9 p8192 SEG r10 (5/GPU)", E9, "15:15:45", "15:19:56", 10 * 140),
]
print(f"{'run':30s} {'n':>4s} {'offered':>7s} {'mean':>6s} {'p50':>6s} {'p90':>6s} {'p99':>6s} {'max':>6s} {'s>15G':>6s} {'s>18G':>6s}")
for lab, D, a, b, off in runs:
    xs = [g for (ts, g, _) in D if t(a) <= ts < t(b)]
    act = [x for x in xs if x > 0.5]
    if not act: print(lab, "no data"); continue
    q = sorted(act)
    pc = lambda p: q[min(len(q) - 1, int(p * len(q)))]
    print(f"{lab:30s} {len(act):4d} {off*8*1.048576/1000:7.2f} {st.mean(act):6.2f} {pc(.5):6.2f} {pc(.9):6.2f} {pc(.99):6.2f} {max(act):6.2f} {sum(x>15 for x in act):6d} {sum(x>18 for x in act):6d}")
