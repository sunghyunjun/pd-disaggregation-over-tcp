"""R2 3차: 아래 줄 판정의 규칙 민감도. (1) 논문 규칙(모든 반복 ≥0.9, 최소 굿풋) (2) 반복 평균 규칙 (3) 동률 띠를 격자 한 칸(0.75~1.33)으로.
각 규칙에서 범주별 셀 수와, 논문 규칙 대비 바뀐 셀. 읽기 전용."""
import sys, collections
sys.path.insert(0, "harness")
import slo_sensitivity as ss
cache = ss.load_cache("results/safe_runs.csv")
T, B = ss.T_GRID, ss.B_GRID
AB = {'neither':'-','r_only':'R','r_better':'r','similar':'=','d_better':'d','d_only':'D','unknown':'?'}

def cap(by_rate, gpus, T_, B_, rule):
    best, br_ = 0.0, None
    for rate, rs in by_rate.items():
        a = [ss.attain(r, T_, B_) for r in rs]; g = [ss.goodput(r, T_, B_) for r in rs]
        ok = min(a) >= 0.9 if rule == "min" else sum(a)/len(a) >= 0.9
        if ok:
            v = (min(g) if rule == "min" else sum(g)/len(g)) / gpus
            if v > best: best, br_ = v, rate
    return best, (br_ is not None and br_ == max(by_rate))

def side(key, pd, T_, B_, rule):
    g = [x for x in ss.GROUPS if x[0] == key][0]
    c = []
    for lab, stages, cfg, wl, inl, n in g[2]:
        if lab.startswith("Replicas") == pd: continue
        br = ss.runs_for(cache, stages, cfg, wl, inl)
        if br: c.append(cap(br, n, T_, B_, rule))
    if not c: return (0.0, False)
    v = max(x[0] for x in c); return (v, any(x[1] for x in c if x[0] == v and v > 0))

def grid(key, rule, hi=1.25, lo=0.8):
    return [[ss.classify(side(key, False, t, b, rule), side(key, True, t, b, rule), hi, lo) for b in B] for t in T]

for key in ("26b_4k_tuned", "26f_4k_tuned", "31b_chat_tuned"):
    base = grid(key, "min")
    for name, G in (("paper", base), ("mean-rule", grid(key, "mean")), ("band .75-1.33", grid(key, "min", 1.34, 0.749))):
        cnt = collections.Counter(AB[x] for row in G for x in row)
        ch = [(T[i], B[j], AB[base[i][j]] + ">" + AB[G[i][j]]) for i in range(len(T)) for j in range(len(B)) if G[i][j] != base[i][j]]
        print(key, name, dict(cnt), "changed:", ch[:40])
