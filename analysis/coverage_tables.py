#!/usr/bin/env python3
"""all_runs.csv에서 커버리지 히트맵 표 여섯 개의 HTML을 생성한다.
축 매핑은 이 파일 안에 명시한다. CSV의 instance_type 열은 신뢰할 수 없다
(세션 B는 클라이언트 값이 들어가 있고 D·E 계열은 비어 있다) → stage로 매핑한다.
사용: coverage_tables.py results/all_runs.csv > /tmp/tables.html
"""
import csv, sys, collections, json

# stage → 인스턴스. 세션마다 고정이므로 표로 적는다. E1만 구성 이름으로 갈린다(혼합 쌍).
STAGE_INST = {
    "P": "g5.xlarge", "Ap": "g7e.2xlarge", "A": "g7.2xlarge", "C1": "g7e.2xlarge",
    "B": "g7.2xlarge", "D": "g7.2xlarge", "E2": "g7e.2xlarge", "E3": "g6e.2xlarge",
    "E4": "g7e.2xlarge",
}
INSTANCES = ["g5.xlarge", "g6.2xlarge", "g6e.2xlarge", "g7.2xlarge", "g7e.2xlarge"]

MODEL_LABEL = {
    "nvidia/Gemma-4-26B-A4B-NVFP4": "Gemma4 26B-A4B · NVFP4",
    "RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic": "Gemma4 26B-A4B · FP8",
    "google/gemma-4-26B-A4B-it": "Gemma4 26B-A4B · BF16",
    "nvidia/Gemma-4-31B-IT-NVFP4": "Gemma4 31B · NVFP4",
    "RedHatAI/gemma-4-31B-it-FP8-block": "Gemma4 31B · FP8",
    "google/gemma-4-31B-it": "Gemma4 31B · BF16",
    "RedHatAI/gemma-4-12B-it-FP8-Dynamic": "Gemma4 12B · FP8",
    "google/gemma-4-12B-it": "Gemma4 12B · BF16",
    "Qwen/Qwen3.6-35B-A3B-FP8": "Qwen3.6 35B-A3B · FP8",
    "Qwen/Qwen3-8B": "Qwen3-8B · BF16",
    "Qwen/Qwen3-1.7B": "Qwen3-1.7B · BF16",
}
MODEL_ORDER = list(dict.fromkeys(MODEL_LABEL.values()))

def instance_of(r):
    s = r["stage"]
    if s == "E1":
        c = r["config"]
        return "g6e.2xlarge" if c.startswith("l40s") else "g7e.2xlarge"
    return STAGE_INST.get(s, "기타")

# 구성 분류. 튜닝 여부는 이름에 든 표식으로 가른다.
TUNED_MARKS = ("tuned", "best", "_pg", "xfer_", "tcfix", "d1")
def config_of(r):
    c = r["config"]; cl = c.lower()
    if cl.startswith("b2"): return "B2 복제본"
    if cl.startswith("b1") or cl.startswith("l40s") or cl.startswith("pro6000") or cl == "dbg":
        return "B1 단일"
    if cl.startswith("p1") or cl.startswith("d1") or cl.startswith("xfer"):
        return "P1 튜닝" if any(m in cl for m in TUNED_MARKS) else "P1 분리"
    return "기타"
CONFIGS = ["B1 단일", "B2 복제본", "P1 분리", "P1 튜닝"]

def workload_of(r):
    w = r["workload"]
    return {"sharegpt": "ShareGPT", "random": "합성 격자"}.get(w, "Azure 트레이스" if w.startswith("azure") else "기타")
WORKLOADS = ["ShareGPT", "합성 격자", "Azure 트레이스"]

def inlen_bucket(r):
    if r["workload"] != "random": return None
    n = r.get("input_len_median")
    try: n = float(n)
    except (TypeError, ValueError): n = None
    if n is None: return None
    for lim, lab in ((2048, "1K"), (8192, "4K"), (24000, "16K"), (1e9, "32K")):
        if n < lim: return lab
    return None
INLENS = ["1K", "4K", "16K", "32K"]

RATES = ["0.25", "0.5", "1", "2", "4", "6", "8", "12", "16", "24", "inf", "self"]
def rate_of(r):
    v = (r["rate"] or "").strip()
    return v if v in RATES else None


# 대역폭 설정: network 열이 tc 값을 담고, 튜닝 세션의 tcfix_* 구성 이름에도 들어 있다.
BWS = ["제한 없음", "tc 5 Gbps", "tc 3 Gbps", "tc 2.5 Gbps", "tc 2 Gbps", "tc 1 Gbps", "배치 그룹"]
def bw_of(r):
    net = (r["network"] or "").lower(); c = r["config"].lower()
    if "_pg" in c or c.startswith("xfer_"): return "배치 그룹"
    for key, lab in (("5gbit", "tc 5 Gbps"), ("3gbit", "tc 3 Gbps"), ("2500mbit", "tc 2.5 Gbps"),
                     ("2gbit", "tc 2 Gbps"), ("1gbit", "tc 1 Gbps")):
        if key in net or key in c: return lab
    return "제한 없음"

def heat_class(n):
    if n == 0: return "z"
    if n <= 2: return "a"
    if n <= 5: return "b"
    if n <= 10: return "c"
    if n <= 20: return "d"
    return "e"

def table(rows, corner, row_labels, row_key, col_labels, col_key):
    cnt = collections.Counter()
    for r in rows:
        a, b = row_key(r), col_key(r)
        if a in row_labels and b in col_labels: cnt[(a, b)] += 1
    out = [f'<div class="tbl"><table class="heat"><thead><tr><th class="corner">{corner}</th>']
    out += [f'<th class="r">{c}</th>' for c in col_labels]
    out.append("</tr></thead><tbody>")
    for a in row_labels:
        out.append(f'<tr><th class="rh">{a}</th>')
        for b in col_labels:
            n = cnt[(a, b)]
            cls = heat_class(n)
            txt = str(n) if n else ""
            out.append(f'<td class="h {cls}" title="{a} × {b}: {n}런">{txt}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)

def main():
    rows = list(csv.DictReader(open(sys.argv[1])))
    rows = [r for r in rows if (r.get("discarded") or "False") not in ("True", "true")]
    model_lbl = lambda r: MODEL_LABEL.get(r["model"], "기타")
    print("<!-- MODEL_INSTANCE -->")
    print(table(rows, "모델 · 정밀도 \\ 인스턴스", MODEL_ORDER, model_lbl, INSTANCES, instance_of))
    print("<!-- INSTANCE_CONFIG -->")
    print(table(rows, "인스턴스 \\ 구성", INSTANCES, instance_of, CONFIGS, config_of))
    print("<!-- CONFIG_WORKLOAD -->")
    print(table(rows, "구성 \\ 워크로드", CONFIGS, config_of, WORKLOADS, workload_of))
    print("<!-- CONFIG_INLEN -->")
    print(table([r for r in rows if inlen_bucket(r)], "구성 \\ 입력 길이", CONFIGS, config_of, INLENS, inlen_bucket))
    print("<!-- CONFIG_RATE -->")
    print(table([r for r in rows if rate_of(r)], "구성 \\ 요청률 (req/s)", CONFIGS, config_of, RATES, rate_of))
    # 요약 수치
    summary = {
        "총런": len(rows),
        "세션": sorted(set(r["stage"] for r in rows)),
        "인스턴스별": collections.Counter(instance_of(r) for r in rows),
        "구성별": collections.Counter(config_of(r) for r in rows),
    }
    print("<!-- CONFIG_BW -->")
    print(table(rows, "구성 \\ 대역폭 설정", CONFIGS, config_of, BWS, bw_of))
    print("<!-- SUMMARY " + json.dumps(summary, ensure_ascii=False, default=dict) + " -->")

if __name__ == "__main__":
    main()
