# 종합 심사 스팟 체크(읽기 전용): 26B/31B 결정점의 달성률, TTFT 중앙값, TPOT/ITL, 둘 다 통과한 부하의 TTFT 범위
import csv, sys, statistics, gzip, json, os
REPO = "<repo>"
sys.path.insert(0, REPO + "/harness")
os.chdir(REPO)
import slo_sensitivity as S
cache = json.load(gzip.open(S.CACHE, "rt"))
rows = {r["run_id"]: r for r in csv.DictReader(open("results/safe_runs.csv"))}

def med(xs): return statistics.median(xs)

def show(group, workload, inlen, filt=None):
    print(f"== {group}")
    for key, title, members in S.GROUPS:
        if key != group: continue
        for lab, stages, cfg, wl, inl, n in members:
            br = S.runs_for(cache, stages, cfg, wl, inl)
            for rate, rs in br.items():
                per = rate / n
                if filt and not filt(per): continue
                out = []
                for r in rs:
                    rid = [k for k, v in cache.items() if v is r][0]
                    c = rows.get(rid, {})
                    out.append("%.3f ttft50=%4.0f tpot=%s itl50=%s" % (S.attain(r, 1.0, 50), med(r["ttft"])*1000,
                               c.get("tpot_mean_ms","")[:5], c.get("itl_p50_ms","")[:5]))
                print(f"  {lab:24s} {per:4.2f}/GPU  " + " | ".join(out))

show("26b_4k_tuned", "random", "4096", lambda p: p >= 3)
show("31b_chat_tuned", "sharegpt", None, lambda p: p >= 2)
show("26f_4k_tuned", "random", "4096")
