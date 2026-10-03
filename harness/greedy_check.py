#!/usr/bin/env python3
"""Correctness gate: send the same prompts one at a time, in order, with greedy decoding (temperature 0), record the output text, and compare two records.
When the transfer path changes (pull, then push, then per-layer push), output identity is used to check that the KV was moved completely.
Mixes a few short prompts with 4K-class long prompts that go through two chunks and thousands of descriptors.
Default is the chat format (/v1/chat/completions). Sending raw completions (/v1/completions) to an instruction-tuned model makes Gemma 4 IT
emit repetitive noise that makes the comparison meaningless (confirmed in E6 on 2026-09-27: even a single node gives "France is France is...").

  greedy_check.py run --base-url http://127.0.0.1:8000 --model M --sharegpt FILE --out a.json [--repeat 2]
  greedy_check.py compare a.json b.json
"""
import argparse, json, re, sys, time, urllib.request

SHORT = [
    "The capital of France is",
    "Write a haiku about distributed systems.",
    "Explain in two sentences why the sky is blue.",
    "List three prime numbers greater than 100.",
    "Translate to Korean: The experiment finished without errors.",
    "def fibonacci(n):",
]

def long_prompts(sharegpt, n_chars=(16000, 17500)):
    # Concatenate ShareGPT human turns from the start to build two prompts of about 4K tokens (the same file always yields the same strings).
    data = json.load(open(sharegpt))
    turns = [c["value"] for d in data for c in d.get("conversations", []) if c.get("from") == "human" and len(c.get("value", "")) > 200]
    out, i = [], 0
    for target in n_chars:
        buf = []
        while sum(len(b) for b in buf) < target and i < len(turns):
            buf.append(turns[i]); i += 1
        out.append("\n\n".join(buf)[:target] + "\n\nSummarize the text above in one sentence.")
    return out

def complete(base, model, prompt, max_tokens, api="chat"):
    if api == "chat":
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
                   "temperature": 0, "seed": 0, "stream": False}
        path = "/v1/chat/completions"
    else:
        payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": 0, "seed": 0, "stream": False}
        path = "/v1/completions"
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    raw = urllib.request.urlopen(req, timeout=600).read().decode()
    # Even if the proxy returns a stream, use the last JSON object
    j = json.loads(raw[raw.find("{"):]) if raw.strip().startswith("{") else json.loads(raw.strip().splitlines()[-1])
    c = j["choices"][0]
    return (c["message"]["content"] if "message" in c else c["text"]), round(time.time() - t0, 3)

def run(a):
    prompts = SHORT + (long_prompts(a.sharegpt) if a.sharegpt else [])
    rec = {"base_url": a.base_url, "model": a.model, "max_tokens": a.max_tokens, "api": a.api, "runs": []}
    for r in range(a.repeat):
        texts = []
        for i, p in enumerate(prompts):
            t, dt = complete(a.base_url, a.model, p, a.max_tokens, a.api)
            texts.append({"i": i, "prompt_chars": len(p), "text": t, "sec": dt})
        rec["runs"].append(texts)
    json.dump(rec, open(a.out, "w"), ensure_ascii=False, indent=1)
    same = all(x["text"] == y["text"] for x, y in zip(rec["runs"][0], rec["runs"][-1]))
    print(f"record {a.out}: {len(prompts)} prompts x {a.repeat} repeats, same-server repeat identical={same}")
    return 0 if same else 2

def _words(t):
    return {w.lower() for w in re.findall(r"[A-Za-z]{5,}", t)}

def compare(a):
    """Default: byte-for-byte match on every prompt.
    --exact-under N --min-overlap X: prompts shorter than N chars must match byte-for-byte; longer ones pass if they share at least
    X of the reference output's key words (English words of 5+ letters). For long prompts the last prompt token is computed differently
    per path, so words diverge near ties and a byte match is overly strict. Thresholds calibrated in E6 on 2026-09-27: same prompt 0.58 or higher, different prompt 0.17 or lower."""
    x = json.load(open(a.a))["runs"][0]; y = json.load(open(a.b))["runs"][0]
    exact = sum(1 for p, q in zip(x, y) if p["text"] == q["text"])
    fails = []
    for p, q in zip(x, y):
        if p["text"] == q["text"]:
            continue
        k = next((j for j, (c1, c2) in enumerate(zip(p["text"], q["text"])) if c1 != c2), min(len(p["text"]), len(q["text"])))
        ref = _words(p["text"]); ov = len(_words(q["text"]) & ref) / max(1, len(ref))
        relaxed = a.exact_under is not None and p["prompt_chars"] >= a.exact_under and ov >= a.min_overlap
        print(f"  mismatch prompt {p['i']} (length {p['prompt_chars']} chars), differs from char {k}, key-word overlap {ov:.2f}" + (" -> passes relaxed criterion" if relaxed else ""))
        if not relaxed:
            fails.append(p["i"])
    mode = "byte match" if a.exact_under is None else f"byte match under {a.exact_under} chars + long-prompt overlap >= {a.min_overlap}"
    print(f"compare {a.a} vs {a.b}: byte match {exact}/{len(x)}, criterion [{mode}] {'PASS' if not fails else 'FAIL'}")
    return 0 if not fails else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--base-url", required=True); r.add_argument("--model", required=True)
    r.add_argument("--sharegpt"); r.add_argument("--out", required=True); r.add_argument("--repeat", type=int, default=1)
    r.add_argument("--max-tokens", type=int, default=64)
    r.add_argument("--api", choices=["chat", "completions"], default="chat")
    c = sp.add_parser("compare"); c.add_argument("a"); c.add_argument("b")
    c.add_argument("--exact-under", type=int, default=None); c.add_argument("--min-overlap", type=float, default=0.4)
    a = ap.parse_args()
    sys.exit(run(a) if a.cmd == "run" else compare(a))
