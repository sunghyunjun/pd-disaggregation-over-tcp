"""세션 E8(B2) 프록시 계측. 분리 구성의 '전역 정지'가 어디서 생기는지 가르기 위한 기록만 남긴다.

기록(JSON 한 줄씩, perf_counter 기준 t와 벽시계 w를 함께 적어 클라이언트 bench.json의 시각과 맞춘다):
  gap  : 상류(디코드 서버)에서 받은 스트림 조각 사이 간격이 GAP_MS를 넘은 순간. 상류 쪽 정지의 증거
  lag  : 이벤트 루프가 5 ms 잠들었다가 LAG_MS 넘게 늦게 깨어난 순간. 프록시 자신의 정지 증거
  gc   : 파이썬 GC 한 번이 GC_MS를 넘게 걸린 순간(세대 포함)
사용: 환경변수 PROXY_TRACE=경로 가 있을 때만 켜진다. 없으면 모든 함수가 아무 일도 하지 않는다.
"""
import asyncio, gc, json, os, time

PATH = os.environ.get("PROXY_TRACE", "")
GAP_MS = float(os.environ.get("PROXY_TRACE_GAP_MS", "40"))
LAG_MS = float(os.environ.get("PROXY_TRACE_LAG_MS", "20"))
GC_MS = float(os.environ.get("PROXY_TRACE_GC_MS", "5"))
_buf, _inflight, _gc_t0 = [], [0], [0.0]


def enabled():
    return bool(PATH)


def _rec(kind, **kw):
    if PATH:
        _buf.append(json.dumps({"k": kind, "t": round(time.perf_counter(), 6), "w": round(time.time(), 6), "n": _inflight[0], **kw}))


def _gc_cb(phase, info):
    if phase == "start":
        _gc_t0[0] = time.perf_counter()
    else:
        d = (time.perf_counter() - _gc_t0[0]) * 1000
        if d > GC_MS:
            _rec("gc", ms=round(d, 2), gen=info.get("generation"), collected=info.get("collected"))


async def _lag_monitor():
    while True:
        t0 = time.perf_counter()
        await asyncio.sleep(0.005)
        lag = (time.perf_counter() - t0 - 0.005) * 1000
        if lag > LAG_MS:
            _rec("lag", ms=round(lag, 2))


async def _flusher():
    while True:
        await asyncio.sleep(2)
        flush()


def flush():
    if PATH and _buf:
        with open(PATH, "a") as f:
            f.write("\n".join(_buf) + "\n")
        _buf.clear()


def start():
    """이벤트 루프 안에서 한 번 부른다(앱 시작 훅)."""
    if not PATH:
        return []
    gc.callbacks.append(_gc_cb)
    _rec("start", gap_ms=GAP_MS, lag_ms=LAG_MS, gc_ms=GC_MS)
    return [asyncio.ensure_future(_lag_monitor()), asyncio.ensure_future(_flusher())]


class Stream:
    """상류 스트림 한 건. with 블록 안에서 조각마다 tick()을 부른다."""
    def __init__(self, rid):
        self.rid, self.last = rid, None

    def __enter__(self):
        _inflight[0] += 1
        return self

    def __exit__(self, *a):
        _inflight[0] -= 1

    def tick(self):
        if not PATH:
            return
        now = time.perf_counter()
        if self.last is not None and (now - self.last) * 1000 > GAP_MS:
            _rec("gap", ms=round((now - self.last) * 1000, 2), rid=self.rid)
        self.last = now
