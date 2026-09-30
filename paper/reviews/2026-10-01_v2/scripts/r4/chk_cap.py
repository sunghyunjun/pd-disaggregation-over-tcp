import sys, json, glob, os, bisect; sys.path.insert(0,'harness')
W={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
def inflight(b):
    st,lat=b['start_times'],b['latencies']
    se=sorted(s+l for s,l in zip(st,lat))
    order=sorted(range(len(st)),key=lambda i:st[i])
    inf=[0]*len(st)
    for k,i in enumerate(order):
        inf[i]=k-bisect.bisect_right(se,st[i])
    return inf
for rid in sorted(W):
    if not ('_E8_26_B2_c1024_' in rid or '_E8_26_B2_c1536_N0_random_r8' in rid or '_E8_31_B2_c256_N0_sharegpt_r12' in rid or '_E9_26_B2_c1024' in rid): continue
    b=json.load(open(W[rid])); inf=inflight(b)
    T,I,E=b['ttfts'],b['itls'],b.get('errors') or ['']*len(b['ttfts'])
    n=len(T)
    tf=[i for i in range(n) if (not E[i]) and T[i]>1]
    tf100=[i for i in tf if inf[i]>=100]
    gf=[i for i in range(n) if (not E[i]) and T[i]<=1 and I[i] and max(I[i])>0.05]
    gfall=[i for i in range(n) if I[i] and max(I[i])>0.05]
    below=[i for i in range(n) if inf[i]<100]
    okb=sum(1 for i in below if (not E[i]) and T[i]<=1 and (not I[i] or max(I[i])<=0.05))
    att=sum(1 for i in range(n) if (not E[i]) and T[i]<=1 and (not I[i] or max(I[i])<=0.05))/n
    print(f"{rid[18:]:40s} n={n} att={att:.3f} maxinf={max(inf)} frac>=100={sum(1 for x in inf if x>=100)/n:.2f} TTFTfail={len(tf)} (arr>=100: {len(tf100)}) gapfail(all)={len(gfall)} gapfail(ttft ok)={len(gf)} err={sum(1 for e in E if e)} below100 att={okb}/{len(below)}")
