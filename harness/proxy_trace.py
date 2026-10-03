"""Round E8 (B2) proxy instrumentation. Only records what is needed to tell where the 'global stall' of the disaggregated configuration originates.

Records (one JSON object per line; each carries a perf_counter time t and a wall-clock time w so it can be aligned with the client's bench.json timestamps):
  gap  : a moment when the interval between stream chunks received from upstream (the decode server) exceeded GAP_MS. Evidence of an upstream stall
  lag  : a moment when the event loop slept for 5 ms and woke up more than LAG_MS late. Evidence of a stall in the proxy itself
  gc   : a moment when one Python GC pass took longer than GC_MS (generation included)
Usage: enabled only when the environment variable PROXY_TRACE=<path> is set. Without it every function is a no-op.
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
    """Call once from inside the event loop (app startup hook)."""
    if not PATH:
        return []
    gc.callbacks.append(_gc_cb)
    _rec("start", gap_ms=GAP_MS, lag_ms=LAG_MS, gc_ms=GC_MS)
    return [asyncio.ensure_future(_lag_monitor()), asyncio.ensure_future(_flusher())]


class Stream:
    """One upstream stream. Call tick() for every chunk inside the with block."""
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
