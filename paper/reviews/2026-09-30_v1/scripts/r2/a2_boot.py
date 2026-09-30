from lib import *
pts=[('26B c1024',('E8',),'26_B2_c1024','random',[6,8,10,12]),
     ('26B c1536',('E8',),'26_B2_c1536','random',[6,8]),
     ('26B c2560 E8',('E8',),'26_B2_c2560','random',[2,4]),
     ('26B c2560 E5E7',('E5','E7'),'26_B2','random',[2,4]),
     ('26B 1P1D aio',('E8',),'26_1P1D_aio','random',[6,8,10]),
     ('26B 1P1D toyi',('E8',),'26_1P1D_toyi','random',[6,8]),
     ('26B 1P1D toy E5E7',('E5','E7'),'26_1P1D','random',[4,6,8]),
     ('26F c1024',('E8',),'26F_B2_c1024','random',[1,2]),
     ('26F 1P1D E7',('E7',),'26F_1P1D','random',[1,2]),
     ('31B c256',('E8',),'31_B2_c256','sharegpt',[2,4,8,12]),
     ('31B c512',('E8',),'31_B2_c512','sharegpt',[2]),
     ('31B 1P1D aio',('E8',),'31_1P1D_aio','sharegpt',[8]),
     ('31B 1P1D toy E5E7',('E5','E7'),'31_1P1D','sharegpt',[2,4,8,16]),
]
for lab,st,cfg,wl,rates in pts:
    for rt in rates:
        rs=runs(st,cfg,wl,rt,'4096' if wl=='random' else None)
        if not rs: print(lab,rt,'-- none'); continue
        line=[]
        for rid in rs:
            a=att(rid); lo,hi=block_boot(rid); line.append(f"{ROWS[rid]['stage']}:{a:.3f}[{lo:.3f},{hi:.3f}]")
        extra=''
        if len(rs)>1:
            lo,hi=hier_boot(rs); m=sum(att(x) for x in rs)/len(rs); extra=f" | mean {m:.3f} hier[{lo:.3f},{hi:.3f}]"
        print(f"{lab:18} {rt/2:>5}/GPU n={len(rs)} "+' '.join(line)+extra)
