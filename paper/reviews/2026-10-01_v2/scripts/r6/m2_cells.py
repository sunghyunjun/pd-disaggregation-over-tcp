# 종합 심사 스팟 체크(읽기 전용): 그림 4 아래 줄 칸별 양쪽 최선 구성, 요청률, 절단 여부, 비율
import sys, gzip, json, os, collections
REPO = "<repo>"
sys.path.insert(0, REPO + "/harness"); os.chdir(REPO)
import slo_sensitivity as S
cache = json.load(gzip.open(S.CACHE, "rt"))
res = S.sensitivity(cache)
for key in ("26b_4k_tuned", "26f_4k_tuned", "31b_chat_tuned"):
    g = res[key]
    print("==", key)
    edge = 0
    for i, T in enumerate(S.T_GRID):
        for j, B in enumerate(S.B_GRID):
            best = {}
            for side in (False, True):
                labs = [l for l in g["members"] if (l.startswith("Replicas") != side)]
                c = [(g["members"][l]["capacity"][i][j], g["members"][l]["censored"][i][j], l, g["members"][l]["supported_per_gpu"][i][j]) for l in labs]
                v = max(x[0] for x in c)
                w = [x for x in c if x[0] == v]
                best[side] = (v, any(x[1] for x in w if v > 0), [x[2] for x in w], w[0][3])
            rep = best[False][:2]; pd = best[True][:2]
            cls = S.classify(rep, pd)
            r = pd[0] / rep[0] if rep[0] > 0 else float('nan')
            if cls == "unknown" or (cls == "r_better" and r > 0.78) or (T, B) in ((1.0, 50), (1.0, 30), (1.0, 40)):
                print(f"  T={T:<4} B={B:<3} {cls:9s} ratio={r:.4f}  R:{best[False][2]}@{best[False][3]} cens={best[False][1]}  D:{best[True][2]}@{best[True][3]} cens={best[True][1]}")
