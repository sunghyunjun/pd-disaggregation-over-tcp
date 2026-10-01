"""Meta-reviewer (round 4): continuous crossing of the Section 6 model, sensitivities, decode-gap line, uncertainty.
Read-only; run from repo root: uv run --with numpy python3 <this file>"""
import sys, math
import numpy as np
sys.path.insert(0, 'harness')
import boundary_model as bm
KIB, MIB, MBIT = 1024, 1024 * 1024, 8.388608
CF, CP, R0 = 9.54, 8192, 28.0
CGRID = np.arange(128, 8193, 16)

def fit(points, d=7.0, ttft0=157.0):
    e, a, b = bm.fit_eab(points, d)
    par = {'d': d, 'e': e, 'a': a, 'b': b}
    par['o'] = ttft0 - bm.prefill(par, 4096, 2560)
    return par

def gap_vec(par, L, c):
    """longest step for chunk sizes c (array): max of last full chunk and the last (partial) chunk"""
    D = par['d'] + par['e']
    n = np.ceil(L / c)
    r = L - (n - 1) * c                               # last chunk size
    pf = np.maximum(n - 2, 0) * c                    # start of last full chunk (if n>=2)
    full = np.where(n >= 2, D + par['a'] * c + par['b'] * c * (pf + c / 2), 0)
    last = D + par['a'] * r + par['b'] * r * ((n - 1) * c + r / 2)
    return np.maximum(full, last)

def rep(par, L, G):
    g = gap_vec(par, L, CGRID)
    ok = CGRID[g <= G]
    if ok.size == 0:
        return None, math.inf
    c = int(ok.max()); n = math.ceil(L / c)
    return c, par['o'] + n * (par['d'] + par['e']) + par['a'] * L + par['b'] * L * L / 2

def V(L, kv='hybrid'):
    if kv == 'hybrid': return bm.kv_mib(L, 20, 200)
    if kv == 'g220': return L * 220 * KIB / MIB
    if kv == 'g120': return L * 120 * KIB / MIB

def pd(par, L, m=1.0, xs=1.0, kv='hybrid', R=R0):
    n = math.ceil(L / CP)
    pre = n * (par['d'] + par['e']) + par['a'] * L + par['b'] * L * L / 2
    return par['o'] + pre + xs * V(L, kv) * MBIT / (m * CF) + R

def dgap_line(L):   # 1P1D decode-node longest gap, p90: E2 4K (rate 0.5 total) 14.4, E2 16K (0.25 total) 27.8
    return 14.4 + (27.8 - 14.4) * (L - 4096) / (16384 - 4096)

LS = list(range(2048, 65537, 64))
def crossing(par, G, m=1.0, xs=1.0, kv='hybrid', R=R0, rep_scale=1.0, pd_scale=1.0, Dttft=None):
    """first L where PD TTFT < replica TTFT; also checks if it reverses later (returns n_reversals)"""
    pt = dict(par)
    if Dttft is not None: pt['e'] = Dttft - par['d']
    first, rev, prev = None, 0, None
    for L in LS:
        c, tr = rep(par, L, G)
        if c is not None and Dttft is not None:
            tr = pt['o'] + math.ceil(L / c) * Dttft + pt['a'] * L + pt['b'] * L * L / 2
        tr *= rep_scale
        tp = pd(pt, L, m, xs, kv, R) * pd_scale
        win = tp < tr
        if win and first is None: first = (L, round(tp), round(tr) if tr < math.inf else None, c)
        if prev is not None and prev and not win: rev += 1
        prev = win
    return first, rev

base = fit([(4096, 2560, 62.9), (4096, 1024, 43.6), (4096, 512, 27.2), (16384, 2560, 150.2)])
print('base', {k: round(v, 7) for k, v in base.items()}, 'd+e', round(base['d'] + base['e'], 2))

print('\n== continuous crossing (L, PD TTFT ms, replica TTFT ms, replica chunk), reversals after first crossing')
cases = [('m=1 (v4 map)', {}), ('m=1.5', {'m': 1.5}), ('m=1.8', {'m': 1.8}), ('m=2.0', {'m': 2.0}),
         ('residual 87 ms, m=1.5', {'m': 1.5, 'R': 87}),
         ('fast x0.05', {'xs': 0.05}), ('fast x0.1', {'xs': 0.1}), ('fast x0.2', {'xs': 0.2}),
         ('fast x0.1, m=1.5', {'xs': 0.1, 'm': 1.5}),
         ('all-global 220 KiB, m=1', {'kv': 'g220'}), ('all-global 220, m=1.5', {'kv': 'g220', 'm': 1.5}),
         ('global-shape 120 KiB, m=1.5', {'kv': 'g120', 'm': 1.5}), ('global-shape 120 KiB, m=1.8', {'kv': 'g120', 'm': 1.8}),
         ('16K-error corrected m=1.5 (rep x820/756, pd x1286/1370)', {'m': 1.5, 'rep_scale': 820 / 756, 'pd_scale': 1286 / 1370}),
         ('16K-error corrected m=1', {'rep_scale': 820 / 756, 'pd_scale': 1286 / 1370}),
         ('D=11.25 in TTFT, m=1.5', {'m': 1.5, 'Dttft': 11.25}), ('D=11.25 in TTFT, m=1', {'Dttft': 11.25})]
for name, kw in cases:
    for G in (50, 30):
        print(f'  G{G} {name:55s}', crossing(base, G, **kw))
for bs in (0.85, 0.9):
    p2 = dict(base); p2['b'] *= bs
    for G in (50, 30):
        for m in (1.0, 1.5):
            print(f'  G{G} b x{bs} m={m}', crossing(p2, G, m=m), ' 16K gap', round(bm.gap(p2, 16384, 2560), 1))

print('\n== curve values')
for G in (50, 30):
    for L in (4096, 8192, 12288, 14336, 16384, 18432, 20480, 24576, 32768, 49152, 65536):
        c, tr = rep(base, L, G)
        print(f'  G{G} L={L:6d} chunk {c} rep {tr/1000:6.3f} | pd m1 {pd(base,L)/1000:6.3f} m1.5 {pd(base,L,1.5)/1000:6.3f} m1.8 {pd(base,L,1.8)/1000:6.3f} | dgap {dgap_line(L):5.1f}')

print('\n== decode-gap line: L where 1P1D decode-node p90 gap reaches G')
for G in (30, 50):
    print(f'  G{G}: L = {4096 + (G - 14.4) / (27.8 - 14.4) * 12288:.0f}')
print('  g7 NVFP4 1P1D p90 (session B, 0.125/GPU): 4K 18.7, 16K 29.5, 32K 43.3; line through 4K,16K predicts 32K',
      round(18.7 + (29.5 - 18.7) * (32000 - 4096) / 12288, 1))

print('\n== feasibility windows with decode-gap line (only-PD region exists for some T): L ranges')
def window(par, G, m=1.0, line=True, T=None, **kw):
    out = []
    for L in LS:
        c, tr = rep(par, L, G)
        tp = pd(par, L, m, **kw)
        pd_gap_ok = (dgap_line(L) <= G) if line else (par['d'] <= G)
        ok = pd_gap_ok and tp < tr and (T is None or tp <= T * 1000)
        if T is not None: ok = ok and not (tr <= T * 1000)
        out.append(ok)
    segs, s = [], None
    for L, ok in zip(LS, out):
        if ok and s is None: s = L
        if not ok and s is not None: segs.append((s, L - 64)); s = None
    if s is not None: segs.append((s, LS[-1]))
    return segs
for G in (50, 30):
    for m in (1.0, 1.5, 1.8):
        print(f'  G{G} m={m}: no line {window(base,G,m,line=False)} | line {window(base,G,m)} | strict T=1s line {window(base,G,m,T=1.0)} | T=1.5 {window(base,G,m,T=1.5)} | T=2 {window(base,G,m,T=2.0)} | T=3 {window(base,G,m,T=3.0)}')

print('\n== where TTFT curves pass 1 s')
for G in (50, 30):
    for L in LS:
        if rep(base, L, G)[1] > 1000: print(f'  G{G} replicas > 1 s from {L}'); break
for m in (1.0, 1.5, 1.8):
    for L in LS:
        if pd(base, L, m) > 1000: print(f'  PD m={m} > 1 s from {L}'); break

print('\n== leave-one-out')
meas = [(4096, 2560, 62.9), (4096, 1024, 43.6), (4096, 512, 27.2), (16384, 2560, 150.2)]
for i in range(4):
    p = fit([x for j, x in enumerate(meas) if j != i])
    print(f'  drop {meas[i][:2]}: e={p["e"]:.2f} a={p["a"]*1e3:.2f}us b={p["b"]*1e6:.3f}ns d+e={p["d"]+p["e"]:.1f} pred {bm.gap(p, meas[i][0], meas[i][1]):.1f} vs {meas[i][2]}'
          f' | m1 G50 {crossing(p,50)[0]} G30 {crossing(p,30)[0]} | m1.5 G50 {crossing(p,50,m=1.5)[0]} G30 {crossing(p,30,m=1.5)[0]}')

print('\n== joint fit on 9 FP8 gap points (d=7) and covariance band')
nine = meas + [(4096, 2560, 66.9), (4096, 1024, 44.2), (4096, 512, 28.8), (4096, 2560, 63.1), (16384, 2560, 148.7)]
p9 = fit(nine)
# linearised covariance
X, y = [], []
for L, c, g in nine:
    k, pp = max(bm.chunks(L, c), key=lambda kp: p9['a'] * kp[0] + p9['b'] * kp[0] * (kp[1] + kp[0] / 2))
    X.append([1.0, k, k * (pp + k / 2)]); y.append(g - 7.0)
X, y = np.array(X), np.array(y)
beta = np.array([p9['e'], p9['a'], p9['b']]); res = y - X @ beta
s2 = res @ res / (len(y) - 3); cov = s2 * np.linalg.inv(X.T @ X)
print('  e,a,b', p9['e'], p9['a'], p9['b'], ' se', np.sqrt(np.diag(cov)), ' resid', np.round(res, 2))
for m in (1.0, 1.5):
    print(f'  9-pt m={m}: G50', crossing(p9, 50, m=m)[0], ' G30', crossing(p9, 30, m=m)[0])
rng = np.random.default_rng(0)
for m in (1.0, 1.5):
    xs50, xs30 = [], []
    for s in rng.multivariate_normal(beta, cov, 400):
        pp = {'d': 7.0, 'e': s[0], 'a': s[1], 'b': s[2]}; pp['o'] = 157 - bm.prefill(pp, 4096, 2560)
        c50 = crossing(pp, 50, m=m)[0]; c30 = crossing(pp, 30, m=m)[0]
        xs50.append(c50[0] if c50 else 65536); xs30.append(c30[0] if c30 else 65536)
    print(f'  9-pt sampled m={m}: G50 2.5/50/97.5% {np.percentile(xs50,[2.5,50,97.5])}  G30 {np.percentile(xs30,[2.5,50,97.5])}')
