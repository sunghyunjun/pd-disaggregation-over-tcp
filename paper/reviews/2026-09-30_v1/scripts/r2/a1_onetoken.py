# one-token-output fix: which runs changed, which crossed 0.9, which verdicts flipped
from lib import *
import collections
ch=[]
for rid,r in ROWS.items():
    if r['safety']=='제외' or r['workload']!='sharegpt': continue
    if rid not in WHERE: continue
    R=reqs(rid); n1=sum(1 for x in R if x['mx'] is None and not x['err'])
    a_new=sum(ok(x) for x in R)/len(R); a_old=sum(ok(x,fix=False) for x in R)/len(R)
    ch.append((rid,r['stage'],r['config'],r['rate'],len(R),n1,a_old,a_new,r['safety']))
print('sharegpt runs',len(ch),'max delta',max(c[7]-c[6] for c in ch), 'min delta',min(c[7]-c[6] for c in ch))
print('one-token frac range', min(c[5]/c[4] for c in ch), max(c[5]/c[4] for c in ch))
for c in ch:
    if (c[6]<0.9)!=(c[7]<0.9): print('CROSS 0.9:',c)
# big deltas
for c in sorted(ch,key=lambda c:c[6]-c[7])[:6]: print('delta',round(c[7]-c[6],3),c[1],c[2],c[3],c[4],c[5],round(c[6],3),round(c[7],3))
# 31B 1P1D aio at 8 detail
for rid in runs(('E8',),'31_1P1D_aio','sharegpt',8):
    R=reqs(rid); print(rid, len(R), 'onetoken',sum(1 for x in R if x['mx'] is None), 'old',round(att(rid,fix=False),3),'new',round(att(rid),3))
