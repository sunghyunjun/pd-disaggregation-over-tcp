import json, math, sys
sys.path.insert(0, 'harness')
import boundary_model as bm
B = json.load(open(sys.argv[1]))
P = B["fp8_g7e"]["params"]; print("params", P)
c = B["curves"]; Lf = c["L"]
for G in (50, 30):
    rep = c[f"G{G}"]["replica_ttft_s"]; pdh = c["pd_hybrid_m1_s"]
    cross = None
    for i in range(1, len(Lf)):
        r0, r1 = rep[i-1], rep[i]
        if r0 is not None and r1 is not None and pdh[i-1] >= r0 and pdh[i] < r1:
            # linear interp in log L
            f = (pdh[i-1]-r0)/((pdh[i-1]-r0)-(pdh[i]-r1))
            cross = Lf[i-1]*(Lf[i]/Lf[i-1])**f
            print(f"G{G}: curve crossing between {Lf[i-1]} and {Lf[i]}, ~{cross:.0f}; rep {r0:.3f},{r1:.3f} pd {pdh[i-1]:.3f},{pdh[i]:.3f}")
    last = max(L for L, r in zip(Lf, rep) if r is not None)
    first_none = min((L for L, r in zip(Lf, rep) if r is None), default=None)
    print(f"G{G}: last feasible L on fine grid {last}, first infeasible {first_none}")
    print("  grid first_pd_only", B["map"]["grid"][f"G{G}_hybrid_m1"]["first_pd_only"])
    # all-global vs replica (incl. infeasible)
    ag = c["pd_all_global_m1_s"]
    w = [(L, r, a) for L, r, a in zip(Lf, rep, ag) if (r is None or a < r)]
    print("  all-global PD better than replicas (or replicas infeasible) at:", [(L, r, round(a,2)) for L, r, a in w][:5], "... n=", len(w))
    fl = c["pd_fast_link_s"]
    w = [(L, r, round(f,3)) for L, r, f in zip(Lf, rep, fl) if (r is None or f < r)]
    print("  fast link PD better at:", w[:4])
