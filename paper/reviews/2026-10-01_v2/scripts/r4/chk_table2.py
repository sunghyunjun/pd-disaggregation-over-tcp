import sys, csv, statistics as st; sys.path.insert(0,'harness')
import slo_sensitivity as ss
C=ss.load_cache('safe_runs.csv')
rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
P=3.363
def runs(stages,cfgs,wl,rate,safe=True):
    out=[]
    for rid,r in sorted(C.items()):
        if r['stage'] in stages and r['config'] in cfgs and r['workload']==wl and r['network']=='N0' and float(r['rate'])==rate and (r['safety']=='안전' or not safe):
            if wl=='random' and r['input_len_median']!='4096': continue
            out.append((rid,r))
    return out
def show(lab,stages,cfgs,wl,rate,gpus=2):
    R=runs(stages,cfgs,wl,rate)
    if not R: print(lab,'NO RUNS'); return
    at=[ss.attain(r,1.0,50) for _,r in R]
    gp=[ss.goodput(r,1.0,50) for _,r in R]
    gpcsv=[float(rows[rid]['goodput_chat_tok_s']) for rid,_ in R]
    t50=[float(rows[rid]['ttft_p50_ms']) for rid,_ in R]
    itl=[float(rows[rid]['itl_p50_ms']) for rid,_ in R]
    pooled=st.median([t*1000 for _,r in R for t in r['ttft']])
    cost=P/(min(gp)/gpus*3600/1e6)
    costcsv=P/(min(gpcsv)/gpus*3600/1e6)
    print(f"{lab:38s} n={len(R)} att={[round(a,3) for a in at]} cost=${cost:.3f} (csv ${costcsv:.3f}) ttft_p50/run={t50} pooled={pooled:.0f} itl_p50={itl} ids={[rid[:18] for rid,_ in R]}")
print('--- 26B 4K')
show('c2560 @1/GPU',('E5','E7','E8'),('26_B2','26_B2_c2560'),'random',2)
show('c1024 E9 @5',('E9',),('26_B2_c1024',),'random',10)
show('c1024 E9 @4',('E9',),('26_B2_c1024',),'random',8)
show('c1024 E8 @3',('E8',),('26_B2_c1024',),'random',6)
show('c512 @4',('E9',),('26_B2_c512',),'random',8)
show('c512 @3',('E9',),('26_B2_c512',),'random',6)
show('1P1D all proxies @3',('E5','E7','E8'),('26_1P1D','26_1P1D_toyi','26_1P1D_aio'),'random',6)
show('1P1D aio @3',('E8',),('26_1P1D_aio',),'random',6)
show('1P1D test @3',('E5','E7','E8'),('26_1P1D','26_1P1D_toyi'),'random',6)
show('1P1D aio @4',('E8',),('26_1P1D_aio',),'random',8)
show('1P1D test @4',('E5','E7','E8'),('26_1P1D','26_1P1D_toyi'),'random',8)
show('1P1D p8192 @4',('E9',),('26_1P1D_aio_p8192',),'random',8)
print('--- 26B FP8 4K')
show('F c2560 @0.5',('E7',),('26F_B2',),'random',1)
show('F c1024 @1',('E8',),('26F_B2_c1024',),'random',2)
show('F c1024 @0.5',('E8',),('26F_B2_c1024',),'random',1)
show('F c512 @1',('E9',),('26F_B2_c512',),'random',2)
show('F c512 @0.5',('E9',),('26F_B2_c512',),'random',1)
show('F 1P1D @1',('E7',),('26F_1P1D',),'random',2)
show('F 1P1D @0.5',('E7',),('26F_1P1D',),'random',1)
print('--- 31B chat')
show('31 c256 @8',('E9',),('31_B2_c256',),'sharegpt',16)
show('31 c256 @4',('E8',),('31_B2_c256',),'sharegpt',8)
show('31 c256 @2',('E8',),('31_B2_c256',),'sharegpt',4)
show('31 c256 @1',('E8',),('31_B2_c256',),'sharegpt',2)
show('31 1P1D aio @4',('E8','E9'),('31_1P1D_aio',),'sharegpt',8)
show('31 1P1D test @4',('E5','E7'),('31_1P1D',),'sharegpt',8)
show('31 1P1D test @2',('E5','E7'),('31_1P1D',),'sharegpt',4)
show('31 1P1D test @1',('E5','E7'),('31_1P1D',),'sharegpt',2)
show('31 1P1D aio @6',('E9',),('31_1P1D_aio',),'sharegpt',12)
show('31 c2560 @1',('E5','E7','E8'),('31_B2','31_B2_c2560'),'sharegpt',2)
