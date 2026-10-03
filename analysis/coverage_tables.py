#!/usr/bin/env python3
"""Generate the HTML of six coverage heatmap tables from all_runs.csv (how many runs per model x instance,
instance x configuration, configuration x workload, input length, request rate, and bandwidth setting).
The axis mappings are spelled out in this file. The instance_type column of the CSV is not reliable (round B
holds the client's value and the D and E rounds are empty), so the instance is mapped from the round code.
Usage: coverage_tables.py results/all_runs.csv > /tmp/tables.html
"""
import csv, sys, collections, json

# round code -> instance. Fixed within a round, so written as a table. Only E1 splits by configuration name (mixed pair).
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
    return STAGE_INST.get(s, "other")

# Configuration classes. Whether a disaggregated run is tuned is decided by markers in its name.
TUNED_MARKS = ("tuned", "best", "_pg", "xfer_", "tcfix", "d1")
def config_of(r):
    c = r["config"]; cl = c.lower()
    if cl.startswith("b2"): return "B2 replicas"
    if cl.startswith("b1") or cl.startswith("l40s") or cl.startswith("pro6000") or cl == "dbg":
        return "B1 single"
    if cl.startswith("p1") or cl.startswith("d1") or cl.startswith("xfer"):
        return "P1 tuned" if any(m in cl for m in TUNED_MARKS) else "P1 disaggregated"
    return "other"
CONFIGS = ["B1 single", "B2 replicas", "P1 disaggregated", "P1 tuned"]

def workload_of(r):
    w = r["workload"]
    return {"sharegpt": "ShareGPT", "random": "Synthetic grid"}.get(w, "Azure trace" if w.startswith("azure") else "other")
WORKLOADS = ["ShareGPT", "Synthetic grid", "Azure trace"]

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


# Bandwidth setting: the network column carries the tc value, and the tuning round's tcfix_* configuration names carry it too.
BWS = ["No limit", "tc 5 Gbps", "tc 3 Gbps", "tc 2.5 Gbps", "tc 2 Gbps", "tc 1 Gbps", "Placement group"]
def bw_of(r):
    net = (r["network"] or "").lower(); c = r["config"].lower()
    if "_pg" in c or c.startswith("xfer_"): return "Placement group"
    for key, lab in (("5gbit", "tc 5 Gbps"), ("3gbit", "tc 3 Gbps"), ("2500mbit", "tc 2.5 Gbps"),
                     ("2gbit", "tc 2 Gbps"), ("1gbit", "tc 1 Gbps")):
        if key in net or key in c: return lab
    return "No limit"

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
            out.append(f'<td class="h {cls}" title="{a} × {b}: {n} runs">{txt}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)

def main():
    rows = list(csv.DictReader(open(sys.argv[1])))
    rows = [r for r in rows if (r.get("discarded") or "False") not in ("True", "true")]
    model_lbl = lambda r: MODEL_LABEL.get(r["model"], "other")
    print("<!-- MODEL_INSTANCE -->")
    print(table(rows, "Model · precision \\ instance", MODEL_ORDER, model_lbl, INSTANCES, instance_of))
    print("<!-- INSTANCE_CONFIG -->")
    print(table(rows, "Instance \\ configuration", INSTANCES, instance_of, CONFIGS, config_of))
    print("<!-- CONFIG_WORKLOAD -->")
    print(table(rows, "Configuration \\ workload", CONFIGS, config_of, WORKLOADS, workload_of))
    print("<!-- CONFIG_INLEN -->")
    print(table([r for r in rows if inlen_bucket(r)], "Configuration \\ input length", CONFIGS, config_of, INLENS, inlen_bucket))
    print("<!-- CONFIG_RATE -->")
    print(table([r for r in rows if rate_of(r)], "Configuration \\ request rate (req/s)", CONFIGS, config_of, RATES, rate_of))
    # summary numbers
    summary = {
        "total_runs": len(rows),
        "rounds": sorted(set(r["stage"] for r in rows)),
        "by_instance": collections.Counter(instance_of(r) for r in rows),
        "by_config": collections.Counter(config_of(r) for r in rows),
    }
    print("<!-- CONFIG_BW -->")
    print(table(rows, "Configuration \\ bandwidth setting", CONFIGS, config_of, BWS, bw_of))
    print("<!-- SUMMARY " + json.dumps(summary, ensure_ascii=False, default=dict) + " -->")

if __name__ == "__main__":
    main()
