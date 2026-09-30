import json, glob, os, csv, statistics as st
rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
rids=sorted(k for k,r in rows.items() if r['safety']=='안전' and r['config'] in ('31_B2','31_B2_c2560') and r['workload']=='sharegpt' and r['rate']=='2')
print(len(rids), [r[:18]+rows[r]['config'] for r in rids])
for bins in ([(0,200),(200,400),(400,800),(800,10**6)],[(0,100),(100,200),(200,400),(400,800),(800,10**6)]):
  agg={b:[0,0] for b in bins}; perrun={b:[] for b in bins}
  for rid in rids:
    b=json.load(open(where[rid]))
    n=len(b['ttfts']); S=b['start_times']; L=b['latencies']; T=b['ttfts']; I=b['input_lens']
    order=sorted(range(n),key=lambda i:S[i]); rep={i:k%2 for k,i in enumerate(order)}
    loc={bb:[0,0] for bb in bins}
    for i in range(n):
        if not b['itls'][i]: continue
        mx=max(b['itls'][i])*1000
        t0=S[i]+T[i]; t1=S[i]+L[i]
        co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and t0<=S[j]<=t1]
        cm=max(co) if co else 0
        for lo,hi in bins:
            if lo<=cm<hi:
                agg[(lo,hi)][0]+=1; agg[(lo,hi)][1]+=(mx<=50); loc[(lo,hi)][0]+=1; loc[(lo,hi)][1]+=(mx<=50)
    for bb in bins:
        if loc[bb][0]: perrun[bb].append(round(loc[bb][1]/loc[bb][0],3))
  for k,(n,ok) in agg.items(): print(k,'n=%d ok=%d frac=%.3f'%(n,ok,ok/n if n else 0),'per run',perrun[k])
