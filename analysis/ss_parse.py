#!/usr/bin/env python3
"""세션 E8(B3): ss_sample.sh 출력에서 KV 전송에 쓰인 TCP 연결 수와 연결별 몫을 센다.
사용: ss_parse.py FILE [--min-bytes 1000000]
- 연결 = (로컬 포트, 원격 포트) 쌍. 22·5201·5600 포트는 뺀다.
- 샘플 사이 bytes_acked(송신 쪽)·bytes_received(수신 쪽) 증가량으로 연결별 전송량을 구한다.
- 출력: 전체 기간에 min-bytes 넘게 나른 연결 수, 연결별 총량과 비율, 동시에 바이트가 움직인 연결 수의 분포.
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
