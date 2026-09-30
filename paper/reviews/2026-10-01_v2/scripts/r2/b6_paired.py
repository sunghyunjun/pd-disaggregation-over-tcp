"""R2 3차: 같은 시드 짝 차이(복제본 − 1P1D)의 계층 짝 부트스트랩(짝 재표집 → 같은 블록 번호 재표집). 읽기 전용."""
import json, glob, random
def oks(d, T=1.0, B=50):
    b = json.load(open(d + "/bench.json"))
    st = b["start_times"]; order = sorted(range(len(st)), key=lambda i: st[i])
    E = b.get("errors") or [""] * len(st)
    return [int((not E[i]) and b["ttfts"][i] is not None and b["ttfts"][i] <= T and (not b["itls"][i] or max(b["itls"][i]) * 1000 <= B)) for i in order]
def pboot(pairs, n=4000, blocks=20, seed=0):
    rnd = random.Random(seed); P = []
    for a, b in pairs:
        k = len(a) // blocks
        P.append([(sum(a[i:i+k]) - sum(b[i:i+k]), k) for i in range(0, len(a), k)])
    vals = []
    for _ in range(n):
        s = t = 0
        for _ in range(len(P)):
            bl = rnd.choice(P)
            for _ in range(len(bl)):
                d, k = rnd.choice(bl); s += d; t += k
        vals.append(s / t)
    vals.sort(); return vals[int(.025*n)], vals[int(.975*n)]
R = sorted(glob.glob("results/E9/*_E9_26_B2_c1024_N0_random_r8"))
A = sorted(glob.glob("results/E8/*_E8_26_1P1D_aio_N0_random_r8"))
P = sorted(glob.glob("results/E9/*_E9_26_1P1D_aio_p8192_N0_random_r8"))
for lab, X in (("vs E8 aio (3 seeds)", list(zip(R, A))), ("vs E9 P8192 same day (2 seeds)", list(zip(R[:2], P)))):
    pairs = [(oks(a), oks(b)) for a, b in X]
    diffs = [(sum(a) - sum(b)) / len(a) for a, b in pairs]
    lo, hi = pboot(pairs)
    print(lab, "per-seed diff", [round(d, 3) for d in diffs], "mean", round(sum(diffs)/len(diffs), 3), "95%", round(lo, 3), round(hi, 3))
    for (a, b) in pairs:
        print("   per-seed block CI", [round(x,3) for x in pboot([(a, b)])])
