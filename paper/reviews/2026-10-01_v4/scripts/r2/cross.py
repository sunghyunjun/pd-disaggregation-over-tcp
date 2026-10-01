# continuous crossing of replica vs 1P1D low-load TTFT (reviewer R2 scratch). Run from repo root.
import sys, math
sys.path.insert(0, 'harness')
import boundary_model as bm
KIB, MIB = 1024, 1024*1024
CFLOW, CP = 9.54, 8192

def make(par):
    def gap(L, c): return max(bm.step(par, k, p) for k, p in bm.chunks(L, c))
    def best(L, G):
        b = None
        for c in range(128, 8193, 16):
            if gap(L, c) <= G: b = c
        return b
    return gap, best

def crossing(par, G=50, m=1.0, R=28.0, kv=(20, 200), xs=1.0, Lmin=3000, Lmax=70000, step=64, Dttft=None):
    """first L (step 64) where PD TTFT < replica TTFT (replica at largest admissible chunk)"""
    gap, best = make(par)
    pt = dict(par)
    if Dttft is not None:   # per-step overhead used in TTFT differs from the gap fit
        pt['e'] = Dttft - par['d']
    for L in range(Lmin, Lmax, step):
        c = best(L, G)
        tr = math.inf if c is None else par['o'] + bm.prefill(pt, L, c)
        V = bm.kv_mib(L, *kv)
        tp = par['o'] + bm.prefill(pt, L, CP) + xs * V * 8.388608 / (m * CFLOW) + R
        if tp < tr:
            return L, c, round(tr), round(tp)
    return None

def fit(points, d=7.0, o_ttft=157.0):
    e, a, b = bm.fit_eab(points, d)
    par = {'d': d, 'e': e, 'a': a, 'b': b}
    par['o'] = o_ttft - bm.prefill(par, 4096, 2560)
    return par
