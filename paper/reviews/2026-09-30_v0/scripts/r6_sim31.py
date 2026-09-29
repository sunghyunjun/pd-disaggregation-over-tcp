# Extrapolate 31B replica chat attainment below 1 req/s/GPU from the measured
# mapping (max co-scheduled prompt on the same replica -> P(max gap <= 50 ms)).
import json, glob, os, csv, random, bisect
os.chdir('<repo>')
rows={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
rids=sorted(k for k,r in rows.items() if r['safety']!='제외' and r['config']=='31_B2' and r['workload']=='sharegpt' and r['rate']=='2')
edges=[0,100,200,300,400,600,800,2000]; cnt=[[0,0] for _ in edges]
reqs=[]
for rid in rids:
    b=json.load(open(where[rid])); n=len(b['ttfts']); S=b['start_times']; L=b['latencies']; T=b['ttfts']; I=b['input_lens']
    order=sorted(range(n),key=lambda i:S[i]); rep={i:k%2 for k,i in enumerate(order)}
    for i in range(n):
        if not b['itls'][i]: continue
        reqs.append((I[i], L[i]-T[i]))
        co=[I[j] for j in range(n) if j!=i and rep[j]==rep[i] and S[i]+T[i]<=S[j]<=S[i]+L[i]]
        cm=max(co) if co else 0
        k=bisect.bisect_right(edges,cm)-1; cnt[k][0]+=1; cnt[k][1]+=max(b['itls'][i])*1000<=50
p=[(c[1]/c[0] if c[0] else None) for c in cnt]
print('bins',list(zip(edges,[c[0] for c in cnt],[None if x is None else round(x,2) for x in p])))
def pass_prob(cm):
    k=bisect.bisect_right(edges,cm)-1
    while p[k] is None: k-=1
    return p[k]
rnd=random.Random(0)
for lam_gpu in [1.0,0.5,0.25]:
    tot=0; N=40000
    for _ in range(N):
        inp,dec=rnd.choice(reqs)
        # arrivals on the same replica during decode window: Poisson(lam*dec)
        k=0; t=rnd.expovariate(lam_gpu)
        while t<dec: k+=1; t+=rnd.expovariate(lam_gpu)
        cm=max([rnd.choice(reqs)[0] for _ in range(k)],default=0)
        tot+=pass_prob(cm)
    print('per-GPU rate %.2f -> predicted replica gap attainment %.2f'%(lam_gpu,tot/N))
