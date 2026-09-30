"""R2 3차: 아래 줄 각 셀의 최선 구성·요청률·반복 수·최소 달성률, 경계(최소 <0.95) 여부. 읽기 전용."""
import sys
sys.path.insert(0, "harness")
import slo_sensitivity as ss
cache = ss.load_cache("results/safe_runs.csv")
T, B = ss.T_GRID, ss.B_GRID
AB = {'neither':'-','r_only':'R','r_better':'r','similar':'=','d_better':'d','d_only':'D','unknown':'?'}

def best(key, pdside, T_, B_, keep=lambda l: True):
    g = [x for x in ss.GROUPS if x[0] == key][0]
    cands = []
    for lab, stages, cfg, wl, inl, n in g[2]:
        if lab.startswith("Replicas") == pdside or not keep(lab): continue
        br = ss.runs_for(cache, stages, cfg, wl, inl)
        if not br: continue
        best_, rate_ = 0.0, None
        for rate, rs in br.items():
            if min(ss.attain(r, T_, B_) for r in rs) >= 0.9:
                gg = min(ss.goodput(r, T_, B_) for r in rs) / n
                if gg > best_: best_, rate_ = gg, rate
        if rate_ is None: continue
        cen = rate_ == max(br)
        att = [ss.attain(r, T_, B_) for r in br[rate_]]
        cands.append((best_, lab, rate_ / n, cen, len(att), min(att)))
    if not cands: return None
    return max(cands)

if __name__ == "__main__":
    key = sys.argv[1]
    for T_ in T:
        for B_ in B:
            a = best(key, False, T_, B_); b = best(key, True, T_, B_)
            ra = (a[0], a[3]) if a else (0.0, False); rb = (b[0], b[3]) if b else (0.0, False)
            k = ss.classify(ra, rb)
            ratio = (rb[0] / ra[0]) if ra[0] > 0 and rb[0] > 0 else float('nan')
            fa = f"{a[1]}@{a[2]:g} n={a[4]} min={a[5]:.3f}{' C' if a[3] else ''}" if a else "-"
            fb = f"{b[1]}@{b[2]:g} n={b[4]} min={b[5]:.3f}{' C' if b[3] else ''}" if b else "-"
            print(f"T={T_:<4} B={B_:<3} {AB[k]}  ratio={ratio:6.4f}  REP[{fa}]  PD[{fb}]")
