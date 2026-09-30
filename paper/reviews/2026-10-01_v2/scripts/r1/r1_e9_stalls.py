# Decode-server ITL histogram diff (>50 ms) and proxy upstream gap clusters for E9 1P1D runs
import re, glob, json, collections
R='<repo>/results/E9'
def hist(f):
    h={}
    for l in open(f):
        m=re.match(r'vllm:inter_token_latency_seconds_bucket\{.*le="([^"]+)".*\} ([0-9.e+]+)',l)
        if m: h[m.group(1)]=float(m.group(2))
    return h
for pre in sorted(glob.glob(R+'/metrics_E9/*_pre_188.txt')):
    post=pre.replace('_pre_','_post_')
    a,b=hist(pre),hist(post)
    tot=b['+Inf']-a['+Inf']; le50=b['0.05']-a['0.05']; le75=b['0.075']-a['0.075']; le100=b['0.1']-a['0.1']
    print(pre.split('/')[-1].replace('_pre_188.txt',''), f"tokens {tot:.0f}  >50ms {tot-le50:.0f}  >75ms {tot-le75:.0f}  >100ms {tot-le100:.0f}")
# proxy upstream gap clusters: >=15 gaps >50 ms within 5 ms
runs={}
for f in sorted(glob.glob(R+'/2026-*/result.json')):
    d=json.load(open(f)); b=d['bench']; m=d['meta']
    import datetime
    end=datetime.datetime.strptime(b['date'],'%Y%m%d-%H%M%S').replace(tzinfo=datetime.timezone.utc).timestamp()
    runs[(m['config'],m['rate'],m['seed'])]=(end-b['duration']-5,end+5)
for tf,cfg in (('proxy_trace_E9_26_1P1D_aio_p8192.jsonl','26_1P1D_aio_p8192'),('proxy_trace_E9_31_1P1D_aio.jsonl','31_1P1D_aio')):
    ev=[json.loads(l) for l in open(R+'/'+tf)]
    gaps=[e for e in ev if e['k']=='gap' and e['ms']>50]
    for key,(t0,t1) in runs.items():
        if key[0]!=cfg: continue
        g=sorted([e for e in gaps if t0<=e['w']<=t1], key=lambda e:e['w'])
        cl=[];i=0
        while i<len(g):
            j=i
            while j+1<len(g) and g[j+1]['w']-g[i]['w']<=0.005: j+=1
            if j-i+1>=15: cl.append((g[i]['w']-t0, j-i+1, max(e['ms'] for e in g[i:j+1]), g[i]['n']))
            i=j+1
        print(cfg, key[1], key[2], 'upstream gaps>50ms', len(g), 'clusters(>=15 in 5ms):', len(cl), [(round(a),c,round(mx),n) for a,c,mx,n in cl][:25])
