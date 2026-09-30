# Median TTFT, median/mean ITL, mean TPOT, per-request longest gap p50/p90 by config and per-GPU rate (26B 4K and 31B chat), audited runs only
import json, gzip, glob, os, csv, statistics as st
os.chdir('<repo>')
safe={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
want={('E5','26_B2'),('E7','26_B2'),('E8','26_B2_c2560'),('E8','26_B2_c2048'),('E8','26_B2_c1536'),('E8','26_B2_c1024'),('E9','26_B2_c1024'),('E9','26_B2_c512'),
      ('E8','26_1P1D_aio'),('E8','26_1P1D_toyi'),('E9','26_1P1D_aio_p8192'),('E5','26_1P1D'),('E7','26_1P1D'),
      ('E8','31_B2_c256'),('E9','31_B2_c256'),('E8','31_1P1D_aio'),('E9','31_1P1D_aio'),('E5','31_1P1D'),('E7','31_1P1D'),('E7','26F_1P1D'),('E8','26F_B2_c1024'),('E9','26F_B2_c512')}
rows=[]
for p in glob.glob('results/E*/*/bench.json'):
    rid=os.path.basename(os.path.dirname(p)); r=safe.get(rid)
    if not r or (r['stage'],r['config']) not in want or r['network']!='N0': continue
    if r['config'].startswith('26') and r['workload']!='random': continue
    if r['config'].startswith('31') and r['workload']!='sharegpt': continue
    b=json.load(open(p)); itl=[x for l in b['itls'] for x in l]
    mx=[max(l) for l in b['itls'] if l]
    rows.append((r['config'],r['stage'],float(r['rate'])/2,r['safety'],b['median_ttft_ms'],b['p99_ttft_ms'],1000*st.median(itl),1000*st.mean(itl),b['mean_tpot_ms'],1000*st.median(mx),1000*sorted(mx)[int(0.9*len(mx))],b['output_throughput']/2))
for x in sorted(rows):
    print("%-20s %-3s %4.2f %-3s TTFTp50 %6.0f p99 %6.0f | ITL med %5.1f mean %5.1f TPOT %5.1f | maxgap p50 %5.1f p90 %5.1f | out tok/s/GPU %6.0f"%x)
