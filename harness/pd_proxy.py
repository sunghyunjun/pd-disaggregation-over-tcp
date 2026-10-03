#!/usr/bin/env python3
"""Round E8 (B2): aiohttp proxy for the disaggregated (1P1D) configuration. Relays P to D with the same library as the replicas path (rr_proxy.py).
The request flow matches vLLM v0.30.0 tests/v1/kv_connector/nixl_integration/toy_proxy_server.py:
  1) send the request to the prefill node with max_tokens=1, stream=False, kv_transfer_params={do_remote_decode: True}
  2) attach the kv_transfer_params from that response to the original request and send a streaming request to the decode node
  3) pass the decode node's stream through to the client unchanged
Prefill and decode nodes are each picked round-robin. Setting PROXY_TRACE enables the harness/proxy_trace.py instrumentation.
Usage: pd_proxy.py --port 8000 --prefill http://P:8100 [...] --decode http://D:8200 [...]
"""
import argparse, itertools, json, os, resource, sys, uuid
import aiohttp
from aiohttp import web

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proxy_trace as pt  # noqa: E402


def prefill_body(req):
    d = dict(req)
    d["kv_transfer_params"] = {"do_remote_decode": True, "do_remote_prefill": False, "remote_engine_id": None,
                               "remote_block_ids": None, "remote_host": None, "remote_port": None}
    d["stream"] = False
    d["max_tokens"] = 1
    if "max_completion_tokens" in d:
        d["max_completion_tokens"] = 1
    d.pop("stream_options", None)
    d.pop("min_tokens", None)
    d.pop("min_completion_tokens", None)
    return d


async def handle(req):
    api = req.path[len("/v1"):]            # /completions or /chat/completions
    body = await req.json()
    rid = str(uuid.uuid4())
    hdr = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}", "X-Request-Id": rid}
    sess = req.app["sess"]
    p = next(req.app["prr"])
    async with sess.post(p + "/v1" + api, json=prefill_body(body), headers=hdr) as r:
        r.raise_for_status()
        pj = await r.json(content_type=None)
    ktp = pj.get("kv_transfer_params") or {}
    if ktp:
        body["kv_transfer_params"] = ktp
    d = next(req.app["drr"])
    async with sess.post(d + "/v1" + api, json=body, headers=hdr) as r:
        resp = web.StreamResponse(status=r.status, headers={"Content-Type": r.headers.get("Content-Type", "application/json")})
        await resp.prepare(req)
        with pt.Stream(rid) as s:
            async for chunk in r.content.iter_any():
                s.tick()
                await resp.write(chunk)
        await resp.write_eof()
        return resp


async def health(req):
    return web.json_response({"status": "ok"})


async def on_start(app):
    app["sess"] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None),
                                        connector=aiohttp.TCPConnector(limit=0))
    app["tasks"] = pt.start()


async def on_stop(app):
    for t in app.get("tasks", []):
        t.cancel()
    pt.flush()
    await app["sess"].close()


if __name__ == "__main__":
    _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(65536, _hard), _hard))
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--prefill", nargs="+", required=True)
    ap.add_argument("--decode", nargs="+", required=True)
    a = ap.parse_args()
    app = web.Application()
    app["prr"], app["drr"] = itertools.cycle(a.prefill), itertools.cycle(a.decode)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)
    app.router.add_post("/v1/completions", handle)
    app.router.add_post("/v1/chat/completions", handle)
    app.router.add_get("/healthcheck", health)
    web.run_app(app, port=a.port, access_log=None)
