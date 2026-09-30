"""R2 3차: who-wins 아래 줄의 셀별 근거(최선 구성, 요청률, 절단 여부, 반복 수). 읽기 전용."""
import sys, os
sys.path.insert(0, "harness")
import slo_sensitivity as ss
cache = ss.load_cache("results/safe_runs.csv")
res = ss.sensitivity(cache)
T, B = ss.T_GRID, ss.B_GRID

def detail(key, T_, B_):
    g = [x for x in ss.GROUPS if x[0] == key][0]
    out = []
    for lab, stages, cfg, wl, inl, n in g[2]:
        br = ss.runs_for(cache, stages, cfg, wl, inl)
        if not br: continue
        cap, cen = ss.capacity(br, n, T_, B_)
        sup = ss.supported(br, n, T_, B_)
        # 최고 통과 요청률과 그 점의 반복별 달성률
        rates = {r/n: [round(ss.attain(x, T_, B_), 3) for x in rs] for r, rs in br.items()}
        out.append((lab, round(cap,1), cen, sup, rates))
    return out

if __name__ == "__main__":
    key = sys.argv[1]; T_ = float(sys.argv[2]); B_ = float(sys.argv[3])
    for lab, cap, cen, sup, rates in detail(key, T_, B_):
        print(f"{lab:24s} cap={cap:7.1f} cens={cen!s:5} sup={sup:g}  " + " ".join(f"{k:g}:{v}" for k, v in rates.items()))
