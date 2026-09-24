#!/usr/bin/env python3
"""Minimal round-robin OpenAI-compatible proxy for the B2 baseline (streaming pass-through).
Usage: rr_proxy.py --port 8000 --upstreams http://10.0.0.11:8000 http://10.0.0.12:8000
"""
import argparse, itertools, aiohttp
from aiohttp import web

async def handle(req):
    up = next(req.app["rr"])
    url = up + req.rel_url.path_qs
    body = await req.read()
    async with req.app["sess"].request(req.method, url, data=body, headers={"Content-Type": req.content_type}) as r:
        resp = web.StreamResponse(status=r.status, headers={"Content-Type": r.headers.get("Content-Type", "application/json")})
        await resp.prepare(req)
        async for chunk in r.content.iter_any():
            await resp.write(chunk)
        await resp.write_eof(); return resp

async def on_start(app): app["sess"] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None))
async def on_stop(app): await app["sess"].close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8000); ap.add_argument("--upstreams", nargs="+", required=True)
    a = ap.parse_args()
    app = web.Application(); app["rr"] = itertools.cycle(a.upstreams)
    app.on_startup.append(on_start); app.on_cleanup.append(on_stop)
    app.router.add_route("*", "/{tail:.*}", handle)
    web.run_app(app, port=a.port, access_log=None)
