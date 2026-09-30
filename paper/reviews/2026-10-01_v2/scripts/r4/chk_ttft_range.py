import sys, csv; sys.path.insert(0,'harness')
import slo_sensitivity as ss
from collections import defaultdict
C=ss.load_cache('safe_runs.csv'); rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
G={ '26B':('random','4096',{'R c512':[('E9','26_B2_c512')],'R c1024':[('E8','26_B2_c1024'),('E9','26_B2_c1024')],'R c1536':[('E8','26_B2_c1536')],
          'D test':[('E5','26_1P1D'),('E7','26_1P1D'),('E8','26_1P1D_toyi')],'D aio':[('E8','26_1P1D_aio')],'D p8192':[('E9','26_1P1D_aio_p8192')]}),
    'FP8':('random','4096',{'R c512':[('E9','26F_B2_c512')],'R c1024':[('E8','26F_B2_c1024')],'D test':[('E7','26F_1P1D')]}),
    '31B':('sharegpt',None,{'R c256':[('E8','31_B2_c256'),('E9','31_B2_c256')],'D test':[('E5','31_1P1D'),('E7','31_1P1D')],'D aio':[('E8','31_1P1D_aio'),('E9','31_1P1D_aio')]})}
allR=[];allD=[]; allRany=[]; allDany=[]
for w,(wl,inl,cfgs) in G.items():
    by=defaultdict(lambda: defaultdict(list))
    for lab,src in cfgs.items():
        for rid,r in C.items():
            if r['safety']!='안전' or r['workload']!=wl or r['network']!='N0': continue
            if inl and r['input_len_median']!=inl: continue
            if (r['stage'],r['config']) in src:
                by[float(r['rate'])/2][lab].append((ss.attain(r,1,50),float(rows[rid]['ttft_p50_ms'])))
    for load in sorted(by):
        d=by[load]
        passR=[l for l in d if l.startswith('R') and min(a for a,_ in d[l])>=0.9]
        passD=[l for l in d if l.startswith('D') and min(a for a,_ in d[l])>=0.9]
        s=' | '.join(f"{l}:{[round(a,3) for a,_ in d[l]]} ttft={[round(t) for _,t in d[l]]}" for l in sorted(d))
        print(w,load,'passR',passR,'passD',passD,'::',s)
        for l in d:
            if l.startswith('R'): allRany+= [t for _,t in d[l]]
            else: allDany+=[t for _,t in d[l]]
        if passR and passD:
            for l in passR: allR+=[t for _,t in d[l]]
            for l in passD: allD+=[t for _,t in d[l]]
print('both-passed loads: replicas TTFT p50 range %.0f-%.0f, 1P1D %.0f-%.0f'%(min(allR),max(allR),min(allD),max(allD)))
print('any measured: replicas %.0f-%.0f, 1P1D %.0f-%.0f'%(min(allRany),max(allRany),min(allDany),max(allDany)))
