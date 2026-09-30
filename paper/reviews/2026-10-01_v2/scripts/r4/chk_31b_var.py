import json, glob, os, csv
rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
rids=sorted(k for k,r in rows.items() if r['safety']=='안전' and r['config'] in ('31_B2','31_B2_c2560') and r['workload']=='sharegpt' and r['rate']=='2')
B=[(0,200),(200,400),(400,800),(800,10**6)]
def run(variant, ids):
    agg={b:[0,0] for b in B}
    for rid in ids:
        b=json.load(open(where[rid])); n=len(b['ttfts']); S=b['start_times']; L=b['latencies']; T=b['ttfts']; I=b['input_lens']
        order=sorted(range(n),key=lambda i:S[i]); rep={i:k%2 for k,i in enumerate(order)}
        for i in range(n):
            if not b['itls'][i]: continue
            mx=max(b['itls'][i])*1000
            if variant=='arrive_during_decode': t0,t1=S[i]+T[i],S[i]+L[i]; co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and t0<=S[j]<=t1]
            elif variant=='arrive_during_life': t0,t1=S[i],S[i]+L[i]; co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and t0<=S[j]<=t1]
            elif variant=='prefill_done_during_decode': t0,t1=S[i]+T[i],S[i]+L[i]; co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and t0<=S[j]+T[j]<=t1]
            elif variant=='all_replicas': t0,t1=S[i]+T[i],S[i]+L[i]; co=[I[j] for j in range(n) if j!=i and t0<=S[j]<=t1]
            cm=max(co) if co else 0
            for lo,hi in B:
                if lo<=cm<hi: agg[(lo,hi)][0]+=1; agg[(lo,hi)][1]+=(mx<=50)
    return {k:(v[0],round(v[1]/v[0],3) if v[0] else None) for k,v in agg.items()}
for v in ('arrive_during_decode','arrive_during_life','prefill_done_during_decode','all_replicas'):
    print(v,'5 runs',run(v,rids)); print(v,'E5+E7 only',run(v,rids[:4]))
