"""R2 3차: '양쪽이 통과한 모든 부하에서 조정 복제본의 첫 토큰이 빨랐다' 점검. 요청률(GPU당)별 TTFT 중앙값과 통과 여부. 읽기 전용."""
import sys, statistics as st
sys.path.insert(0, "harness")
import slo_sensitivity as ss
cache = ss.load_cache("results/safe_runs.csv")
def med(xs): return st.median(xs)
for key in ("26b_4k_tuned", "26f_4k_tuned", "31b_chat_tuned"):
    g = [x for x in ss.GROUPS if x[0] == key][0]
    print("==", key)
    table = {}
    for lab, stages, cfg, wl, inl, n in g[2]:
        if "c2560" in lab or lab in ("Replicas (3)",): continue
        br = ss.runs_for(cache, stages, cfg, wl, inl)
        for rate, rs in br.items():
            att = [ss.attain(r, 1.0, 50) for r in rs]
            p = min(att) >= 0.9
            ttm = [med(r["ttft"]) * 1000 for r in rs]
            table.setdefault(rate / n, []).append((lab, p, [round(x) for x in ttm], [round(a, 3) for a in att]))
    for pg in sorted(table):
        print(f"  {pg:g}/GPU")
        for lab, p, ttm, att in table[pg]:
            print(f"     {'PASS' if p else 'fail'} {lab:24s} TTFT p50 {ttm} att {att}")
