# Network-side sensitivity of the Section 6 boundary (read-only; reuses harness/boundary_model.py functions and params)
import sys, os, json, math
REPO = os.path.expanduser("<repo>")
sys.path.insert(0, os.path.join(REPO, "harness"))
import boundary_model as bm
P = json.load(open(os.path.join(REPO, "paper/figures_v4/boundary.json")))["fp8_g7e"]["params"]
par = {k: P[k] for k in "deabo"} if False else {"d": P["d"], "e": P["e"], "a": P["a"], "b": P["b"]}
o = P["o"]; R = 28.0; CF = 9.54; CP = 8192; MBIT = 8.388608
Ls = [int(round(2 ** (11 + i / 8))) for i in range(0, 41)]
Ts = [round(0.25 * 2 ** (i / 6), 3) for i in range(0, 32)]
KV = {"hybrid": lambda L: bm.kv_mib(L, 20, 200), "all220": lambda L: L * 220 / 1024,
      "glob120": lambda L: L * 120 / 1024}
def rep_best(L, G, p=par):
    best = None
    for c in range(128, 8193, 16):
        if max(bm.step(p, k, q) for k, q in bm.chunks(L, c)) <= G: best = c
    return (best, (o + bm.prefill(p, L, best)) if best else math.inf)
def pd(L, kv="hybrid", m=1.0, xs=1.0, p=par, r=R):
    return o + bm.prefill(p, L, CP) + xs * KV[kv](L) * MBIT / (m * CF) + r
def first(G, kv="hybrid", m=1.0, xs=1.0, bscale=1.0, r=R):
    p2 = dict(par); p2["b"] *= bscale
    for L in Ls:
        c, tr = rep_best(L, G, p2); tp = pd(L, kv, m, xs, p2, r)
        for T in Ts:
            if tp <= T * 1000 < tr: return (L, T)
    return None
print("check V(L) MiB hybrid:", {L: round(KV['hybrid'](L),1) for L in (4096, 16384, 32000, 32768, 65536)})
print("all220 32K MiB / GiB:", KV['all220'](32768), KV['all220'](32768)/1024, " hybrid 32K:", KV['hybrid'](32768))
print("transfer ms m=1: 4K", round(KV['hybrid'](4096)*MBIT/CF), " 16K", round(KV['hybrid'](16384)*MBIT/CF), " 32K", round(KV['hybrid'](32768)*MBIT/CF), " 64K", round(KV['hybrid'](65536)*MBIT/CF))
print("transfer ms all220 m=1: 16K", round(KV['all220'](16384)*MBIT/CF), " 32K", round(KV['all220'](32768)*MBIT/CF), " 64K", round(KV['all220'](65536)*MBIT/CF))
print("\nfirst PD-only (L, T):")
for G in (50, 30):
    for name, kw in [("m1", {}), ("m1.5", {"m": 1.5}), ("m1.8", {"m": 1.8}), ("m2.0", {"m": 2.0}), ("m0.8", {"m": 0.8}),
                     ("m1.8 b0.85", {"m": 1.8, "bscale": 0.85}), ("m1 b0.85", {"bscale": 0.85}),
                     ("x0.05", {"xs": 0.05}), ("x0.1", {"xs": 0.1}), ("x0.2", {"xs": 0.2}),
                     ("x0.05 r87", {"xs": 0.05, "r": 87}), ("x0.1 r87", {"xs": 0.1, "r": 87}),
                     ("glob120 m1", {"kv": "glob120"}), ("glob120 m1.8", {"kv": "glob120", "m": 1.8}),
                     ("all220 m1.8", {"kv": "all220", "m": 1.8}), ("all220 m2", {"kv": "all220", "m": 2.0})]:
        print(f"  G{G} {name:14s} {first(G, **kw)}")
print("\nfast-link window width (TTFT ms): L, replica TTFT, PD x0.05, PD x0.1, PD TCP m1, m1.8")
for G in (50, 30):
    for L in (4096, 5793, 8192, 11585, 16384, 21247, 32768):
        c, tr = rep_best(L, G)
        print(f"  G{G} L={L:6d} chunk={c} rep={tr:7.0f}  x0.05={pd(L,xs=0.05):6.0f}  x0.1={pd(L,xs=0.1):6.0f}  m1={pd(L):6.0f}  m1.8={pd(L,m=1.8):6.0f}")
print("\nKV production at prefill saturation (1P1D, P chunk 8192): L, prefill ms, V MiB, Gbps hybrid, Gbps all220, rho=xfer/prefill at m1 hybrid")
for L in (4096, 8192, 16384, 32768, 65536):
    tp = bm.prefill(par, L, CP)
    vh, va = KV['hybrid'](L), KV['all220'](L)
    print(f"  L={L:6d} prefill={tp:7.0f}  V={vh:6.0f}  {vh*MBIT/tp:5.2f} Gbps  all220 {va*MBIT/tp:5.2f} Gbps  rho_m1={vh*MBIT/CF/tp:4.2f}")
print("\nresidual sensitivity (TCP):")
for G in (50, 30):
    for r in (28, 53, 87):
        print(f"  G{G} r={r}: m1 {first(G, r=r)}  m1.5 {first(G, m=1.5, r=r)}  m1.8 {first(G, m=1.8, r=r)}")
print("\nPD TTFT at 4K: m1", round(pd(4096)), " m1.5", round(pd(4096, m=1.5)), " m1.8", round(pd(4096, m=1.8)))
print("transfer ms at m1.8: 16K", round(KV['hybrid'](16384)*MBIT/(1.8*CF)), " 32K", round(KV['hybrid'](32768)*MBIT/(1.8*CF)), " 64K", round(KV['hybrid'](65536)*MBIT/(1.8*CF)))
print("prefill (P, chunk 8192) ms: 16K", round(bm.prefill(par,16384,CP)), " 32K", round(bm.prefill(par,32768,CP)), " 64K", round(bm.prefill(par,65536,CP)))
print("offload: 140 MiB at 9.54 Gbps (one flow) ms:", round(140*MBIT/9.54,1), "; at 13.98 Gbps:", round(140*MBIT/13.98,1), "; PCIe 25 GB/s ms:", round(140*1048576/25e9*1000,1))
