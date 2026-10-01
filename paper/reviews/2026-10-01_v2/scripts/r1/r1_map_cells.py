# Who-wins bottom row: per-config per-rate attainment (min/each run) at key SLO cells, run counts, censoring
import sys, json, gzip
sys.path.insert(0, 'harness')
import slo_sensitivity as S
cache = json.load(gzip.open('results/per_request.json.gz','rt'))
res = S.sensitivity(cache)
cells = [(1.0,30),(1.0,40),(1.0,50),(0.5,50),(0.75,40),(3.0,75),(3.0,250 if 250 in S.B_GRID else 300),(5.0,300)]
for key in ('26b_4k_tuned','26f_4k_tuned','31b_chat_tuned'):
    print('=====',key)
    for lab, stages, cfg, wl, inl, n in [m for k,t,ms in S.GROUPS if k==key for m in ms]:
        br = S.runs_for(cache, stages, cfg, wl, inl)
        if not br: continue
        line=[]
        for rate, rs in br.items():
            a30=[round(S.attain(r,1.0,30),3) for r in rs]; a50=[round(S.attain(r,1.0,50),3) for r in rs]
            line.append(f"{rate/n:g}:{len(rs)}r 50ms{a50} 30ms{a30}")
        print(f"  {lab:24s}", ' | '.join(line))
    # bottom row counts
    g=res[key]
    rep=S.best_of(g,False); pd=S.best_of(g,True)
    K=[[S.classify(rep[i][j],pd[i][j]) for j in range(len(S.B_GRID))] for i in range(len(S.T_GRID))]
    from collections import Counter
    print('  bottom-row verdict counts', Counter(x for row in K for x in row))
    for i,T in enumerate(S.T_GRID):
        print('   T=%.2f'%T, ' '.join(f"{K[i][j][:6]:6s}({rep[i][j][0]:.0f}{'*' if rep[i][j][1] else ''}/{pd[i][j][0]:.0f}{'*' if pd[i][j][1] else ''})" for j in range(len(S.B_GRID))))
