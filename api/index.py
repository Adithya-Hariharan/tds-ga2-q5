from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry at cold start
with open(os.path.join(os.path.dirname(__file__), "../q-vercel-latency.json"), "r") as f:
    telemetry = json.load(f)

@app.post("/")
async def check_latency(request: Request):
    payload = await request.json()
    regions = payload["regions"]
    threshold_ms = payload["threshold_ms"]

    results = {}

    for region in regions:
        recs = [r for r in telemetry if r["region"] == region]
        lat = np.array([r["latency_ms"] for r in recs])
        up = np.array([r["uptime_pct"] for r in recs])
        breaches = int(np.sum(lat > threshold_ms))
        avg_latency = float(np.mean(lat)) if len(lat) else None
        p95_latency = float(np.percentile(lat, 95)) if len(lat) else None
        avg_uptime = float(np.mean(up)) if len(up) else None

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return JSONResponse(results)
