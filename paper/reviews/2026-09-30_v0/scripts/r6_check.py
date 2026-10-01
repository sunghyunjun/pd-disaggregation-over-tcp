import json, glob, os, csv, statistics as st
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..']*3)))  # repo root
rows={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
def pick(cfg,wl,rate,stages=('E5','E7')):
    return sorted(k for k,r in rows.items() if r['safety']!='제외' and r['config']==cfg and r['workload']==wl and r['rate']==rate and r['stage'] in stages and r['network']=='N0')
def q(v,p):
    v=sorted(v); return v[min(len(v)-1,int(p*len(v)))]
print("== 26B 4K replicas: per-request max ITL (ms) and attainment at thresholds")
for cfg,rate in [('26_B2','2'),('26_B2','4'),('26_B3','3'),('26_B3','6'),('26_1P1D','6'),('26_1P1D','8')]:
    for rid in pick(cfg,'random',rate):
        b=json.load(open(where[rid]))
        if b['input_lens'][0]<4000: continue
        mx=[max(i)*1000 if i else None for i in b['itls']]
        t=[x*1000 for x in b['ttfts']]
        ok=lambda B:sum(1 for m,tt in zip(mx,t) if m is not None and m<=B and tt<=1000)/len(mx)
        v=[m for m in mx if m]
        print(rid[:30],cfg,rate,'n',len(mx),'maxITL p10/50/90 %.1f/%.1f/%.1f'%(q(v,.1),q(v,.5),q(v,.9)),'att45 %.3f att50 %.3f att55 %.3f att60 %.3f'%(ok(45),ok(50),ok(55),ok(60)))
