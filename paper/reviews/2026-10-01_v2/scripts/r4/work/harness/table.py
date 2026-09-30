#!/usr/bin/env python3
"""Pretty-print selected columns of analyze.py TSV (stdin) as a markdown table, sorted by request_rate."""
import sys
cols=sys.argv[1].split(",") if len(sys.argv)>1 else ["request_rate","completed","ttft_p50_ms","ttft_p90_ms","tbt_p50_ms","tbt_p99_ms","stall_req_frac","output_tok_per_s","attain_chat","goodput_chat_tok_s","attain_doc"]
rows=[l.rstrip("\n").split("\t") for l in sys.stdin if "\t" in l]
h=rows[0]; idx=[h.index(c) for c in cols]
def key(r):
    try: return float(r[h.index("request_rate")])
    except: return 1e9
def f(x):
    try: v=float(x); return f"{v:.2f}".rstrip("0").rstrip(".")
    except: return x
print("| "+" | ".join(cols)+" |"); print("|"+"---|"*len(cols))
for r in sorted(rows[1:], key=key): print("| "+" | ".join(f(r[i]) for i in idx)+" |")
