"""R2 3차: 1토큰 규칙 전후 달성률(엄격 SLO)과 0.9 교차 런, E9 포함. 읽기 전용."""
import gzip, json
C = json.load(gzip.open("results/per_request.json.gz", "rt"))
def att(r, new):
    ok = 0
    for t, m, e in zip(r["ttft"], r["maxitl"], r["err"]):
        if e or t > 1.0: continue
        if m is None:
            ok += 1 if new else 0
        elif m * 1000 <= 50: ok += 1
    return ok / len(r["ttft"])
rows = []
for rid, r in C.items():
    if r["workload"] != "sharegpt": continue
    a0, a1 = att(r, False), att(r, True)
    n1 = sum(1 for m in r["maxitl"] if m is None)
    rows.append((a1 - a0, rid, r["stage"], r["config"], r["rate"], r["safety"], a0, a1, n1 / len(r["ttft"])))
rows.sort(reverse=True)
print("chat runs", len(rows), "max delta", round(rows[0][0], 3))
print("crossing 0.9:")
for d, rid, s, c, rate, saf, a0, a1, f1 in rows:
    if a0 < 0.9 <= a1: print(f"  {s} {c} r{rate} {saf} {a0:.3f}->{a1:.3f} one-token {f1:.3f}")
print("E9 chat:")
for d, rid, s, c, rate, saf, a0, a1, f1 in rows:
    if s == "E9": print(f"  {c} r{rate} {a0:.3f}->{a1:.3f} one-token {f1:.3f}")
print("top deltas:")
for x in rows[:5]: print("  ", x[2], x[3], x[4], x[5], round(x[6],3), round(x[7],3), round(x[0],3))
print("one-token frac range (chat):", round(min(x[8] for x in rows),3), round(max(x[8] for x in rows),3))
