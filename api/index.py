from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/")
async def get_latency_metrics(data: dict):
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 0)

    # Simulated telemetry data example (replace with actual records)
    # Here should be your eShopCo telemetry data source. For demo, we mock.
    telemetry_data = {
        "apac": [
            {"latency": 150, "uptime": 99.9},
            {"latency": 190, "uptime": 99.7},
            {"latency": 210, "uptime": 99.6},
        ],
        "amer": [
            {"latency": 130, "uptime": 99.8},
            {"latency": 180, "uptime": 99.9},
            {"latency": 185, "uptime": 99.8},
        ],
    }

    result = {}

    for region in regions:
        records = telemetry_data.get(region, [])
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency"] for r in records]
        uptimes = [r["uptime"] for r in records]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
