from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any domain!
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow any header
)

# Load telemetry data from JSON file at startup
def load_telemetry():
    filename = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(filename) as f:
        return json.load(f)

telemetry_data = load_telemetry()

@app.post("/")
async def get_latency_metrics(data: dict):
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 0)

    result = {}

    for region in regions:
        records = [r for r in telemetry_data if r["region"] == region]
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = round(float(np.mean(latencies)), 2)
        p95_latency = round(float(np.percentile(latencies, 95)), 2)
        avg_uptime = round(float(np.mean(uptimes)), 3)
        breaches = sum(1 for l in latencies if l > threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
