#!/usr/bin/env python3
"""collect_*_prom.tsv를 런 구간별로 요약. 마찰 #12 수정 후 수집 형식(TSV) 전용.

사용: parse_prom.py results/<stage>/collect_*_prom.tsv --runs results/<stage>
      각 런의 result.json에서 시작 시각과 duration을 읽어 구간 평균·최대와
      접두어 캐시 적중률(구간 증분 기반)을 계산한다.
"""
import argparse, glob, json, os, collections, datetime, sys

def load_tsv(paths):
    per_port = collections.defaultdict(lambda: collections.defaultdict(dict))  # port -> metric -> ts->val
    errors = collections.Counter()
    for p in paths:
        for line in open(p, errors='ignore'):
            f = line.rstrip('\n').split('\t')
            if len(f) != 4: continue
            ts, port, name, val = f
            if name == '_scrape_error':
                errors[port] += 1; continue
            try: per_port[port][name][int(ts)] = float(val)
            except ValueError: continue
    return per_port, errors

def run_windows(root):
    out = []
    for f in sorted(glob.glob(os.path.join(root, '*', 'result.json'))):
        try: d = json.load(open(f))
        except Exception: continue
        rid = d['meta']['run_id']
        # run_id 형식 2026-09-26T190317Z_...
        try:
            t0 = datetime.datetime.strptime(rid.split('_')[0], '%Y-%m-%dT%H%M%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError: continue
        dur = float(d.get('bench', {}).get('duration') or 0)
        out.append((rid, int(t0), int(t0 + dur) if dur else int(t0 + 200)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tsv', nargs='+')
    ap.add_argument('--runs', required=True, help='런 폴더들이 있는 디렉터리')
    a = ap.parse_args()
    per_port, errors = load_tsv(a.tsv)
    if errors: print('스크레이프 실패 횟수:', dict(errors), file=sys.stderr)
    if not per_port:
        print('경고: 파싱된 지표가 없습니다. 수집기가 비어 있었는지 확인하세요.', file=sys.stderr); return 1
    print(f"{'run_id':46}{'port':>5}{'running평균':>11}{'waiting평균':>12}{'KV사용률max':>12}{'선점':>6}{'접두어적중률':>13}")
    for rid, t0, t1 in run_windows(a.runs):
        for port, metrics in sorted(per_port.items()):
            def series(n):
                return [v for ts, v in metrics.get(n, {}).items() if t0 <= ts <= t1]
            run_ = series('vllm:num_requests_running'); wait_ = series('vllm:num_requests_waiting')
            kv = series('vllm:kv_cache_usage_perc')
            if not run_ and not kv: continue
            def delta(n):
                s = {ts: v for ts, v in metrics.get(n, {}).items() if t0 <= ts <= t1}
                return (max(s.values()) - min(s.values())) if len(s) > 1 else 0.0
            pre = delta('vllm:num_preemptions_total') or delta('vllm:num_preemptions')
            hits = delta('vllm:prefix_cache_hits_total') or delta('vllm:prefix_cache_hits')
            qs = delta('vllm:prefix_cache_queries_total') or delta('vllm:prefix_cache_queries')
            hr = (hits / qs) if qs else float('nan')
            print(f"{rid[:46]:46}{port:>5}{(sum(run_)/len(run_) if run_ else 0):11.1f}"
                  f"{(sum(wait_)/len(wait_) if wait_ else 0):12.1f}{(max(kv) if kv else 0):12.3f}{pre:6.0f}{hr:13.3f}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
