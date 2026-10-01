"""Meta-reviewer: chunk-dependent per-step cost, per-GPU prefill capacity, g7 consistent refit, TTFT-step differences."""
import sys, math
import numpy as np
sys.path.insert(0, 'harness'); sys.path.insert(0, sys.argv[1])
import boundary_model as bm
from m1_cross import base, rep, pd, gap_vec, CGRID, LS, dgap_line

def rep_split(par, L, G, Dsmall):
    """replica with per-step cost Dsmall for chunks <=512 (CUDA graph), base d+e above"""
    D0 = par['d'] + par['e']
    g = gap_vec(par, L, CGRID) - D0 + np.where(CGRID <= 512, Dsmall, D0)
    ok = CGRID[g <= G]
    if ok.size == 0: return None, math.inf
    c = int(ok.max()); D = Dsmall if c <= 512 else D0
    return c, par['o'] + math.ceil(L / c) * D + par['a'] * L + par['b'] * L * L / 2
def cross_split(G, m, Dsmall):
    first = None; stable = None; prev = False
    for L in LS:
        c, tr = rep_split(base, L, G, Dsmall); win = pd(base, L, m) < tr
        if win and first is None: first = (L, c)
        if win and not prev: stable = (L, c)
        prev = win
    return first, stable
print('TTFT-step differences (rate 1 total / rate 2 total): 2560->1024', (194-157)/2, (199-161)/2, ' 1024->512', (239-194)/4, (247-199)/4)
for Ds in (16.03, 14.0, 12.0):
    for m in (1.0, 1.5):
        print(f'  Dsmall={Ds} m={m}: G50 {cross_split(50, m, Ds)}  G30 {cross_split(30, m, Ds)}')

print('\nper-GPU prefill capacity (req/s/GPU): replicas 1/(TTFT-o) at largest admissible chunk; 1P1D 1/(2*P prefill at 8192)')
for G in (50, 30):
    for L in (8192, 16384, 24576, 32768):
        c, tr = rep(base, L, G)
        prep = (tr - base['o']) / 1000 if tr < math.inf else math.inf
        pP = (math.ceil(L / 8192) * (base['d'] + base['e']) + base['a'] * L + base['b'] * L * L / 2) / 1000
        print(f'  G{G} L={L}: replicas {1/prep:.3f}  1P1D {1/(2*pP):.3f}')

print('\nstable crossing (PD below replicas for all longer L up to end of scan)')
def stable(G, m):
    s = None; prev = False
    for L in LS:
        win = pd(base, L, m) < rep(base, L, G)[1]
        if win and not prev: s = L
        prev = win
    return s
for G in (50, 30):
    print(f'  G{G}: m1 {stable(G,1.0)}  m1.5 {stable(G,1.5)}  m1.8 {stable(G,1.8)}')

print('\nTTFT ratio rep/PD at L (m=1.5, m=1), G50 and G30')
for G in (50, 30):
    for L in (16384, 20480, 24576, 32768):
        c, tr = rep(base, L, G)
        print(f'  G{G} L={L}: rep {tr/1000:.2f}  PD m1.5 {pd(base,L,1.5)/1000:.2f} ({1-pd(base,L,1.5)/tr:.0%} lower)  m1 {pd(base,L,1.0)/1000:.2f} ({1-pd(base,L,1.0)/tr:.0%} lower)')

print('\nlongest L meeting both limits for a TTFT limit T (G50): replicas vs 1P1D m=1.5 (with decode-gap line cap 36.7K)')
for T in (1.0, 1.5, 2.0, 3.0, 5.0):
    lr = max([L for L in LS if rep(base, L, 50)[1] <= T * 1000], default=None)
    lp = max([L for L in LS if pd(base, L, 1.5) <= T * 1000 and dgap_line(L) <= 50], default=None)
    lp1 = max([L for L in LS if pd(base, L, 1.0) <= T * 1000 and dgap_line(L) <= 50], default=None)
    print(f'  T={T}: replicas up to {lr}, 1P1D m1.5 up to {lp}, m1 up to {lp1}')
for T in (1.0, 1.5, 2.0):
    lr = max([L for L in LS if rep(base, L, 30)[1] <= T * 1000], default=None)
    lp = max([L for L in LS if pd(base, L, 1.5) <= T * 1000 and dgap_line(L) <= 30], default=None)
    print(f'  G30 T={T}: replicas up to {lr}, 1P1D m1.5 up to {lp}')

print('\ng7 NVFP4 consistent refit (k0*c/2560 in fit and evaluation)')
d7 = 12.0; pts = [(4096, 131.2), (16384, 254.5)]; k0, b7 = 90.0, 4e-6
for _ in range(50):
    X, y = [], []
    for L, g in pts:
        k, p = max(bm.chunks(L, 2560), key=lambda kp: k0 * kp[0] / 2560 + b7 * kp[0] * (kp[1] + kp[0] / 2))
        X.append([k / 2560, k * (p + k / 2)]); y.append(g - d7)
    k0, b7 = np.linalg.solve(np.array(X), np.array(y))
st7 = lambda c, p: d7 + k0 * c / 2560 + b7 * c * (p + c / 2)
o7 = 278 - sum(st7(k, p) for k, p in bm.chunks(4096, 2560))
print(f'  k0={k0:.1f} b={b7*1e6:.3f}ns o7={o7:.0f}')
for L, g, t in [(4096, 131.2, 278), (16384, 254.5, 1430), (32000, 375.7, 3507)]:
    gm = max(st7(k, p) for k, p in bm.chunks(L, 2560)); tm = o7 + sum(st7(k, p) for k, p in bm.chunks(L, 2560))
    print(f'  L={L}: gap {g}/{gm:.1f} ({gm/g-1:+.1%})  TTFT {t}/{tm:.0f} ({tm/t-1:+.1%})')
