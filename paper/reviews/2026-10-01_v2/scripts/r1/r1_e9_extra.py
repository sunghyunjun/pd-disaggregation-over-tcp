# Round-3 R1 extra checks (read-only): (1) KV transfer time/m/in-flight by load, E8 vs E9;
# (2) decode-node receive Gbps (sar) in E9 1P1D runs; (3) SLO failure split TTFT vs gap;
# (4) strict-cell verdicts under a mean-of-repeats rule.
import re, glob, json, gzip, sys, datetime, os
P='<repo>'; os.chdir(P)
print('== (1) transfers')
for f in sorted(glob.glob('results/E8/xfer_E8/26_1P1D_*.log'))+sorted(glob.glob('results/E9/xfer_E9/*.log')):
    rows=[tuple(float(x) for x in m.groups()) for l in open(f) for m in [re.search(r'Num successful transfers=(\d+), Avg xfer time \(ms\)=([\d.]+), P90 xfer time \(ms\)=([\d.]+).*Avg MB per transfer=([\d.]+)',l)] if m]
    if not rows: continue
    n=sum(r[0] for r in rows); avg=sum(r[0]*r[1] for r in rows)/n; mb=sum(r[0]*r[3] for r in rows)/n
    print(f"{f.split('/')[-1]:42s} n={n:5.0f} mean {avg:5.0f} ms p90max {max(r[2] for r in rows):5.0f} m={mb/avg*1000*0.008389/9.54:.2f} offered {sum(r[0]*r[3] for r in rows)/(10*len(rows))*0.008389:4.1f} Gbps in-flight {sum(r[0]/10*r[1]/1000 for r in rows)/len(rows):.1f}")
print('== (2) D rx')
rx={}
for l in open('results/E9/collect/ip-172-31-84-188/collect_ip-172-31-84-188_e9_sar.txt'):
    p=l.split()
    if len(p)>=6 and p[1]=='enp39s0':
        h,m,s=map(int,p[0].split(':')); rx[h*3600+m*60+s]=float(p[4])*8/1e6
runs=sorted(glob.glob('results/E9/2026-*/result.json'))
for f in runs:
    d=json.load(open(f)); b=d['bench']
    if '1P1D' not in d['meta']['config']: continue
    end=datetime.datetime.strptime(b['date'],'%Y%m%d-%H%M%S'); e=end.hour*3600+end.minute*60+end.second; s=e-b['duration']
    xs=sorted(v for t,v in rx.items() if s+15<=t<=e-5)
    print(d['meta']['config'],d['meta']['rate'],'mean %.1f p50 %.1f p99 %.1f max %.1f Gbps'%(sum(xs)/len(xs),xs[len(xs)//2],xs[int(.99*len(xs))],xs[-1]))
print('== (3) failure split')
for f in sorted(glob.glob('results/E9/2026-*/bench.json'))+sorted(glob.glob('results/E8/*26_1P1D_aio_N0_random_r10/bench.json')):
    b=json.load(open(f)); n=len(b['ttfts']); tt=[t>1 for t in b['ttfts']]; gp=[(max(l)>0.05 if l else False) for l in b['itls']]
    print(f.split('/')[-2][-42:], f"TTFT>1s {sum(tt)/n:.3f} gap>50 {sum(gp)/n:.3f} gap-only {sum(g and not t for t,g in zip(tt,gp))/n:.3f}")
print('== (4) mean rule')
sys.path.insert(0,'harness'); import slo_sensitivity as S
cache=json.load(gzip.open('results/per_request.json.gz','rt'))
def mc(st,cfg,wl,inl,T,B,n=2):
    best=(0,None)
    for rate,rs in S.runs_for(cache,st,cfg,wl,inl).items():
        if sum(S.attain(r,T,B) for r in rs)/len(rs)>=0.9:
            g=sum(S.goodput(r,T,B) for r in rs)/len(rs)/n
            if g>best[0]: best=(g,rate/n)
    return best
for T,B in ((1,50),(1,40),(1,30)):
    rep=max(mc(('E9',),'26_B2_c1024','random','4096',T,B),mc(('E9',),'26_B2_c512','random','4096',T,B),mc(('E8',),'26_B2_c1024','random','4096',T,B))
    pd=max(mc(('E8',),'26_1P1D_aio','random','4096',T,B),mc(('E9',),'26_1P1D_aio_p8192','random','4096',T,B),mc(('E5','E7'),'26_1P1D','random','4096',T,B),mc(('E8',),'26_1P1D_toyi','random','4096',T,B))
    print('26B',T,B,rep,pd,'ratio %.2f'%(pd[0]/rep[0]))
rep=mc(('E8','E9'),'31_B2_c256','sharegpt',None,1,50); pd=max(mc(('E8','E9'),'31_1P1D_aio','sharegpt',None,1,50),mc(('E5','E7'),'31_1P1D','sharegpt',None,1,50))
print('31B 1 50',rep,pd,'ratio %.2f'%(pd[0]/rep[0]))
