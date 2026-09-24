#!/usr/bin/env python3
"""Convert Azure LLM inference traces (Splitwise, ISCA'24) to the Mooncake
jsonl format that `vllm bench serve --dataset-name timed_trace` replays.

Input : AzureLLMInferenceTrace_{code,conv}.csv  (TIMESTAMP, ContextTokens, GeneratedTokens)
Output: jsonl with {"timestamp": <ms since first request>, "input_length", "output_length", "hash_ids": [unique ids, one per 16-token chunk]}

Options let you take a time window and clamp lengths so the trace fits a 24 GB GPU.
"""
import argparse, csv, json, sys
from datetime import datetime

def parse_ts(s: str) -> datetime:
    # "2023-11-16 18:15:46.6805900" -> 7 fractional digits; python wants <=6
    head, _, frac = s.partition(".")
    frac = (frac + "000000")[:6]
    return datetime.strptime(f"{head}.{frac}", "%Y-%m-%d %H:%M:%S.%f")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--start-sec", type=float, default=0.0, help="window start (s from trace begin)")
    ap.add_argument("--duration-sec", type=float, default=None, help="window length (s)")
    ap.add_argument("--max-input", type=int, default=None, help="drop requests with ContextTokens above this")
    ap.add_argument("--max-output", type=int, default=None, help="clamp GeneratedTokens to this")
    ap.add_argument("--min-output", type=int, default=1)
    ap.add_argument("--chunk", type=int, default=16, help="hash chunk size; must match --timed-trace-chunk-hash-size (default 16). timed_trace builds the prompt ONLY from hash_ids, so every request needs ceil(input/chunk) ids")
    args = ap.parse_args()

    rows = []
    with open(args.csv, newline="") as f:
        for r in csv.DictReader(f):
            rows.append((parse_ts(r["TIMESTAMP"]), int(r["ContextTokens"]), int(r["GeneratedTokens"])))
    rows.sort(key=lambda x: x[0])
    t0 = rows[0][0]
    kept, dropped = 0, 0
    next_id = 0   # unique ids -> no shared prefixes (Azure traces carry no prefix info)
    in_lens, out_lens = [], []
    with open(args.out, "w") as w:
        for ts, ctx, gen in rows:
            rel = (ts - t0).total_seconds()
            if rel < args.start_sec:
                continue
            if args.duration_sec is not None and rel > args.start_sec + args.duration_sec:
                break
            if args.max_input is not None and ctx > args.max_input:
                dropped += 1; continue
            gen = max(args.min_output, gen if args.max_output is None else min(gen, args.max_output))
            n_chunks = max(1, -(-ctx // args.chunk))
            rec = {"timestamp": int(round((rel - args.start_sec) * 1000)),
                   "input_length": ctx, "output_length": gen, "hash_ids": list(range(next_id, next_id + n_chunks))}
            next_id += n_chunks
            w.write(json.dumps(rec) + "\n")
            kept += 1; in_lens.append(ctx); out_lens.append(gen)
    def q(xs, p):
        xs = sorted(xs); return xs[min(len(xs)-1, int(p*len(xs)))] if xs else None
    span = (in_lens and (kept / max(1e-9, (args.duration_sec or (rows[-1][0]-t0).total_seconds())))) or 0
    print(json.dumps({"kept": kept, "dropped_over_max_input": dropped,
                      "input_p50": q(in_lens,.5), "input_p90": q(in_lens,.9), "input_max": max(in_lens) if in_lens else None,
                      "output_p50": q(out_lens,.5), "output_p90": q(out_lens,.9),
                      "approx_req_per_s": round(span, 3)}, indent=1))

if __name__ == "__main__":
    main()
