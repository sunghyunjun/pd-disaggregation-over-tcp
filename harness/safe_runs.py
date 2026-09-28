#!/usr/bin/env python3
"""all_runs.csv의 각 런을 결론에 쓸 수 있는지 분류한다(2026-09-28 결함 점검 기준).
  안전: 접두어 캐시 끔, 폐기·기동 실패 아님, 클라이언트 한계 구간 아님
  주의: 측정은 유효하나 해석에 단서가 필요한 구간(E5 ShareGPT 32 req/s 이상 = 클라이언트 프록시 CPU 한계)
  제외: 접두어 캐시 켬 또는 미기록(세션 A·A′·C1·P, B의 ShareGPT·Azure, D3 사다리, E2 Azure), 폐기, 기동 실패
사용: safe_runs.py results/all_runs.csv -o results/safe_runs.csv
"""
import argparse, csv, collections

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def classify(r):
    s, w, p = r["stage"], r["workload"], r["prefix_caching"]
    if r.get("discarded") == "True": return "제외", "폐기 런"
    if s in ("A", "Ap", "C1", "P"): return "제외", "접두어 캐시 켬 또는 미기록, 같은 시드 반복"
    if p == "on": return "제외", "접두어 캐시 켬"
    if f(r["ttft_p50_ms"]) == 0: return "제외", "기동 실패 런"
    if s == "E5" and w == "sharegpt" and f(r["rate"]) >= 32: return "주의", "클라이언트 프록시 한계 구간"
    return "안전", ""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    for r in rows:
        r["safety"], r["safety_reason"] = classify(r)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    c = collections.Counter(r["safety"] for r in rows)
    print(f"wrote {a.out}: 안전 {c['안전']}, 주의 {c['주의']}, 제외 {c['제외']} (총 {len(rows)})")

if __name__ == "__main__":
    main()
