# 종합 심사 스팟 체크(읽기 전용): 26B 완화 칸(TTFT 3·5 s × 간격 100–300 ms)에서 1P1D 계열의 요청률별 달성률
import sys, gzip, json, os
REPO = "<repo>"
sys.path.insert(0, REPO + "/harness"); os.chdir(REPO)
import slo_sensitivity as S
cache = json.load(gzip.open(S.CACHE, "rt"))
for key, title, members in S.GROUPS:
    if key != "26b_4k_tuned": continue
    for lab, stages, cfg, wl, inl, n in members:
        if lab.startswith("Replicas c2") or lab.startswith("Replicas c15") : continue
        br = S.runs_for(cache, stages, cfg, wl, inl)
        for rate, rs in br.items():
            per = rate / n
            if per < 4: continue
            cells = []
            for T, B in ((3.0, 100), (3.0, 300), (5.0, 100), (5.0, 300)):
                cells.append(f"T{T:g}/B{B}: " + ",".join("%.3f" % S.attain(r, T, B) for r in rs))
            print(f"{lab:24s} {per:4.1f}/GPU  " + "  ".join(cells))
