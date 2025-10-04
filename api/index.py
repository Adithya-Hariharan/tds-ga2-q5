import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

def load_telemetry():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "q-vercel-latency.json")
    with open(path, "r") as f:
        return json.load(f)

telemetry = load_telemetry()

@app.post("/")
async def endpoint(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    out = {}
    for region in regions:
        region_data = [r for r in telemetry if r["region"] == region]
        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        breaches = sum(1 for r in region_data if r["latency_ms"] > threshold)
        out[region] = {
            "avg_latency": float(np.mean(latencies)) if latencies else None,
            "p95_latency": float(np.percentile(latencies, 95)) if latencies else None,
            "avg_uptime": float(np.mean(uptimes)) if uptimes else None,
            "breaches": breaches
        }
    return out
