import json, glob, os, csv, statistics as st
os.chdir('<repo>')
rows={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
rids=sorted(k for k,r in rows.items() if r['safety']!='제외' and r['config']=='31_B2' and r['workload']=='sharegpt' and r['rate']=='2')
bins=[(0,100),(100,200),(200,400),(400,800),(800,100000)]
agg={b:[0,0,[]] for b in bins}
for rid in rids:
    b=json.load(open(where[rid]))
    n=len(b['ttfts']); S=b['start_times']; L=b['latencies']; T=b['ttfts']; I=b['input_lens']; O=b['output_lens']
    # round-robin by send order (start_times sorted)
    order=sorted(range(n),key=lambda i:S[i]); rep={i:k%2 for k,i in enumerate(order)}
    for i in range(n):
        if not b['itls'][i]: continue
        mx=max(b['itls'][i])*1000
        t0=S[i]+T[i]; t1=S[i]+L[i]
        co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and t0<=S[j]<=t1]
        cm=max(co) if co else 0
        for lo,hi in bins:
            if lo<=cm<hi:
                a=agg[(lo,hi)]; a[0]+=1; a[1]+=(mx<=50); a[2].append(mx)
print('31B replicas x2, ShareGPT @2 total, 4 runs pooled: max co-scheduled prompt (same replica, during decode) -> gap attainment')
for k,(n,ok,v) in agg.items():
    if n: print(k,'n=%d'%n,'gap<=50ms %.2f'%(ok/n),'median maxgap %.1f ms'%st.median(v))
b=json.load(open(where[rids[0]]))
I=b['input_lens']; print('ShareGPT input len: median',st.median(I),'mean %.0f'%st.mean(I),'p90',sorted(I)[int(.9*len(I))],'max',max(I))
# decode-only baseline: median itl
allitl=[x*1000 for it in b['itls'] for x in it]; print('median ITL %.1f ms'%st.median(allitl))
