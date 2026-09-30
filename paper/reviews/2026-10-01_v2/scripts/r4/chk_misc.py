import sys, csv, statistics as st; sys.path.insert(0,'harness')
import slo_sensitivity as ss
C=ss.load_cache('safe_runs.csv'); rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
def att(r,T=1,B=50,skip=0,old=False):
    z=list(zip(r['ttft'],r['maxitl'],r['err']))[skip:]
    ok=0
    for t,m,e in z:
        if e or t>T: continue
        if m is None:
            if old: continue
            ok+=1
        elif m*1000<=B: ok+=1
    return ok/len(z)
# warm-up: audited runs before E7 (stages B,D,E1..E6)
d=[]
for rid,r in C.items():
    if r['safety']!='안전' or r['stage'] in ('E7','E8','E9'): continue
    a0=att(r); a5=att(r,skip=5); d.append((a5-a0,rid,round(a0,3),round(a5,3)))
d.sort()
flips=[x for x in d if (x[2]>=0.9)!=(x[3]>=0.9)]
print('warm-up: n',len(d),'max up',d[-1],'max down',d[0],'verdict flips',flips)
# one-token rule: old vs new, all audited chat runs (sharegpt/azure)
o=[]
for rid,r in C.items():
    if r['safety']!='안전': continue
    a_new=att(r); a_old=att(r,old=True)
    if a_new!=a_old: o.append((round(a_new-a_old,3),rid,round(a_old,3),round(a_new,3),r['workload']))
o.sort(reverse=True)
print('one-token: runs changed',len(o),'max',o[:4])
print('  flips across 0.9:',[x for x in o if x[2]<0.9<=x[3]])
nonflip=[x for x in o if not (x[2]<0.9<=x[3])]
print('  max raise among others', nonflip[:2])
# ShareGPT medians (audited)
ins=[];outs=[]
for rid,r in rows.items():
    if r['safety']=='안전' and r['workload']=='sharegpt':
        ins.append((int(r['input_len_median']),rid)); outs.append((int(r['output_len_median']),rid))
ins.sort(); outs.sort()
print('sharegpt audited runs',len(ins),'input median range',ins[0],ins[-1],'output',outs[:3],outs[-1])
# 30 ms capacities
def show(lab,st_,cfg,wl,rate,B):
    R=[(rid,r) for rid,r in sorted(C.items()) if r['stage'] in st_ and r['config'] in cfg and r['workload']==wl and float(r['rate'])==rate and r['safety']=='안전']
    print(lab,[round(att(r,1,B),3) for _,r in R])
for rate in (2,4,6,8): show(f'c512 @{rate/2} 30ms',('E9',),('26_B2_c512',),'random',rate,30)
for rate in (4,6,8): show(f'1P1D test @{rate/2} 30ms',('E5','E7','E8'),('26_1P1D','26_1P1D_toyi'),'random',rate,30)
for rate in (4,6,8): show(f'1P1D aio @{rate/2} 30ms',('E8',),('26_1P1D_aio',),'random',rate,30)
for rate in (1,2): show(f'FP8 c512 @{rate/2} 30ms',('E9',),('26F_B2_c512',),'random',rate,30)
for rate in (1,2): show(f'FP8 c512 @{rate/2} 40ms',('E9',),('26F_B2_c512',),'random',rate,40)
for rate in (1,2): show(f'FP8 1P1D @{rate/2} 30ms',('E7',),('26F_1P1D',),'random',rate,30)
for rate in (2,4,8,16): show(f'31 c256 @{rate/2} 30ms',('E8','E9'),('31_B2_c256',),'sharegpt',rate,30)
# E2 FP8 2 replicas 4K 0.5 total
for rid,r in rows.items():
    if r['stage']=='E2' and r['config']=='B2' and r['workload']=='random' and r['rate'] in ('0.5',) :
        print('E2 B2', rid, r['input_len_median'], 'itl_p99', r['itl_p99_ms'], 'ttft_p99', r['ttft_p99_ms'],'attain', r['attain_chat'], 'stall_frac', r['stall_req_frac'])
