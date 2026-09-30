#!/usr/bin/env python3
"""Debug proxy: forwards to an upstream vLLM server and logs the first N request bodies and any non-200
responses (body included). Used to find why `bench serve --dataset-name timed_trace` gets 400s.
Usage: dump_proxy.py --port 8001 --upstream http://127.0.0.1:8000 --log results/dump.log --n 3
"""
import argparse, json, aiohttp
from aiohttp import web
async def handle(req):
    app=req.app; body=await req.read()
    async with app["sess"].request(req.method, app["up"]+req.rel_url.path_qs, data=body, headers={"Content-Type": req.content_type}) as r:
        data=await r.read()
        if app["seen"]<app["n"] or r.status!=200:
            app["seen"]+=1
            with open(app["log"],"a") as f:
                f.write(f"=== {req.method} {req.rel_url.path_qs} -> {r.status}\nREQUEST: {body[:3000].decode(errors='replace')}\nRESPONSE: {data[:2000].decode(errors='replace')}\n\n")
        return web.Response(status=r.status, body=data, content_type=r.headers.get("Content-Type","application/json").split(";")[0])
async def on_start(app): app["sess"]=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--port",type=int,default=8001); ap.add_argument("--upstream",default="http://127.0.0.1:8000"); ap.add_argument("--log",default="dump.log"); ap.add_argument("--n",type=int,default=3)
    a=ap.parse_args(); app=web.Application(); app.update(up=a.upstream,log=a.log,n=a.n,seen=0); app.on_startup.append(on_start)
    app.router.add_route("*","/{tail:.*}",handle); web.run_app(app,port=a.port,access_log=None)
