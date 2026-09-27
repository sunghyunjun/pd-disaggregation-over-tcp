#!/usr/bin/env python3
"""정확성 관문: 같은 프롬프트를 그리디(temperature 0)로 한 개씩 순서대로 보내 출력 텍스트를 기록하고, 두 기록을 비교한다.
전송 경로를 바꿨을 때(끌어오기 → 푸시 → 레이어별 푸시) KV가 빠짐없이 옮겨졌는지를 출력 동일성으로 본다.
짧은 프롬프트 몇 개와, 청크 두 번·디스크립터 수천 개를 거치는 4K급 긴 프롬프트를 섞는다.
기본은 채팅 양식(/v1/chat/completions). 지시 튜닝 모델에 원문 완성(/v1/completions)을 보내면 Gemma 4 IT는
반복 잡음을 내서 비교가 무의미해진다(2026-09-27 E6에서 확인: 단일 노드도 "France is France is…").

  greedy_check.py run --base-url http://127.0.0.1:8000 --model M --sharegpt FILE --out a.json [--repeat 2]
  greedy_check.py compare a.json b.json
"""
import argparse, json, sys, time, urllib.request

SHORT = [
    "The capital of France is",
    "Write a haiku about distributed systems.",
    "Explain in two sentences why the sky is blue.",
    "List three prime numbers greater than 100.",
    "Translate to Korean: The experiment finished without errors.",
    "def fibonacci(n):",
]

def long_prompts(sharegpt, n_chars=(16000, 17500)):
    # ShareGPT의 사람 발화를 앞에서부터 이어 붙여 약 4K 토큰 두 개를 만든다(파일이 같으면 항상 같은 문자열).
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
    # 프록시가 스트림으로 되돌려도 마지막 JSON 객체를 쓴다
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
    print(f"기록 {a.out}: 프롬프트 {len(prompts)}개 × {a.repeat}회, 같은 서버 반복 일치={same}")
    return 0 if same else 2

def compare(a):
    x = json.load(open(a.a))["runs"][0]; y = json.load(open(a.b))["runs"][0]
    bad = []
    for p, q in zip(x, y):
        if p["text"] != q["text"]:
            k = next((j for j, (c1, c2) in enumerate(zip(p["text"], q["text"])) if c1 != c2), min(len(p["text"]), len(q["text"])))
            bad.append((p["i"], p["prompt_chars"], k))
    print(f"비교 {a.a} ↔ {a.b}: {len(x) - len(bad)}/{len(x)} 일치")
    for i, n, k in bad:
        print(f"  불일치 프롬프트 {i} (길이 {n}자), {k}번째 글자부터 다름")
    return 0 if not bad else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--base-url", required=True); r.add_argument("--model", required=True)
    r.add_argument("--sharegpt"); r.add_argument("--out", required=True); r.add_argument("--repeat", type=int, default=1)
    r.add_argument("--max-tokens", type=int, default=64)
    r.add_argument("--api", choices=["chat", "completions"], default="chat")
    c = sp.add_parser("compare"); c.add_argument("a"); c.add_argument("b")
    a = ap.parse_args()
    sys.exit(run(a) if a.cmd == "run" else compare(a))
