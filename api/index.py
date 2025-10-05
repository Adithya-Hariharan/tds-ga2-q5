# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import json
from typing import List, Dict, Any

# --- Embedded Telemetry Data ---
# Loaded directly as a string, as file I/O is restricted in serverless.
TELEMETRY_DATA_JSON = """
[
  { "region": "apac", "service": "catalog", "latency_ms": 135.67, "uptime_pct": 97.962, "timestamp": 20250301 },
  { "region": "apac", "service": "support", "latency_ms": 120.37, "uptime_pct": 97.413, "timestamp": 20250302 },
  { "region": "apac", "service": "recommendations", "latency_ms": 205.33, "uptime_pct": 97.303, "timestamp": 20250303 },
  { "region": "apac", "service": "support", "latency_ms": 167.86, "uptime_pct": 98.447, "timestamp": 20250304 },
  { "region": "apac", "service": "analytics", "latency_ms": 119.84, "uptime_pct": 98.168, "timestamp": 20250305 },
  { "region": "apac", "service": "checkout", "latency_ms": 199.35, "uptime_pct": 98.578, "timestamp": 20250306 },
  { "region": "apac", "service": "catalog", "latency_ms": 166.79, "uptime_pct": 98.35, "timestamp": 20250307 },
  { "region": "apac", "service": "payments", "latency_ms": 168.25, "uptime_pct": 98.268, "timestamp": 20250308 },
  { "region": "apac", "service": "analytics", "latency_ms": 180.11, "uptime_pct": 97.433, "timestamp": 20250309 },
  { "region": "apac", "service": "checkout", "latency_ms": 200.76, "uptime_pct": 99.103, "timestamp": 20250310 },
  { "region": "apac", "service": "checkout", "latency_ms": 102.04, "uptime_pct": 98.198, "timestamp": 20250311 },
  { "region": "apac", "service": "support", "latency_ms": 174.19, "uptime_pct": 98.694, "timestamp": 20250312 },
  { "region": "emea", "service": "analytics", "latency_ms": 220.65, "uptime_pct": 97.23, "timestamp": 20250301 },
  { "region": "emea", "service": "support", "latency_ms": 131.64, "uptime_pct": 97.105, "timestamp": 20250302 },
  { "region": "emea", "service": "payments", "latency_ms": 158.24, "uptime_pct": 98.757, "timestamp": 20250303 },
  { "region": "emea", "service": "support", "latency_ms": 202.74, "uptime_pct": 98.306, "timestamp": 20250304 },
  { "region": "emea", "service": "support", "latency_ms": 139.15, "uptime_pct": 99.063, "timestamp": 20250305 },
  { "region": "emea", "service": "recommendations", "latency_ms": 228.69, "uptime_pct": 98.304, "timestamp": 20250306 },
  { "region": "emea", "service": "recommendations", "latency_ms": 142.16, "uptime_pct": 98.115, "timestamp": 20250307 },
  { "region": "emea", "service": "catalog", "latency_ms": 197.94, "uptime_pct": 98.682, "timestamp": 20250308 },
  { "region": "emea", "service": "payments", "latency_ms": 232.25, "uptime_pct": 97.69, "timestamp": 20250309 },
  { "region": "emea", "service": "checkout", "latency_ms": 198.85, "uptime_pct": 97.201, "timestamp": 20250310 },
  { "region": "emea", "service": "payments", "latency_ms": 175.26, "uptime_pct": 98.995, "timestamp": 20250311 },
  { "region": "emea", "service": "recommendations", "latency_ms": 229.96, "uptime_pct": 99.176, "timestamp": 20250312 },
  { "region": "amer", "service": "payments", "latency_ms": 181.16, "uptime_pct": 99.301, "timestamp": 20250301 },
  { "region": "amer", "service": "catalog", "latency_ms": 122.82, "uptime_pct": 97.909, "timestamp": 20250302 },
  { "region": "amer", "service": "analytics", "latency_ms": 192.83, "uptime_pct": 97.514, "timestamp": 20250303 },
  { "region": "amer", "service": "analytics", "latency_ms": 218.5, "uptime_pct": 99.233, "timestamp": 20250304 },
  { "region": "amer", "service": "analytics", "latency_ms": 218.56, "uptime_pct": 98.259, "timestamp": 20250305 },
  { "region": "amer", "service": "catalog", "latency_ms": 218.7, "uptime_pct": 98.769, "timestamp": 20250306 },
  { "region": "amer", "service": "support", "latency_ms": 116.79, "uptime_pct": 98.285, "timestamp": 20250307 },
  { "region": "amer", "service": "recommendations", "latency_ms": 192.58, "uptime_pct": 99.386, "timestamp": 20250308 },
  { "region": "amer", "service": "checkout", "latency_ms": 215.84, "uptime_pct": 98.31, "timestamp": 20250309 },
  { "region": "amer", "service": "recommendations", "latency_ms": 181.32, "uptime_pct": 99.053, "timestamp": 20250310 },
  { "region": "amer", "service": "catalog", "latency_ms": 154.42, "uptime_pct": 98.54, "timestamp": 20250311 },
  { "region": "amer", "service": "payments", "latency_ms": 185.44, "uptime_pct": 98.442, "timestamp": 20250312 }
]
"""

# Load the data once at the module level
TELEMETRY_RECORDS = json.loads(TELEMETRY_DATA_JSON)

app = FastAPI()

# 1. CORS Configuration (FIXED to allow all methods for preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # ALLOW ALL METHODS (POST, GET, and crucial OPTIONS)
    allow_headers=["*"],
)

# Pydantic model for the request body validation
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def calculate_metrics(records: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
    """Calculates metrics for a list of telemetry records."""
    if not records:
        return {
            "avg_latency": 0.0,
            "p95_latency": 0.0,
            "avg_uptime": 0.0,
            "breaches": 0,
        }

    latencies = [r['latency_ms'] for r in records]
    uptimes = [r['uptime_pct'] for r in records]

    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    avg_uptime = np.mean(uptimes)
    breaches = sum(1 for latency in latencies if latency > threshold)

    return {
        "avg_latency": round(float(avg_latency), 3),
        "p95_latency": round(float(p95_latency), 3),
        "avg_uptime": round(float(avg_uptime), 3),
        "breaches": breaches,
    }

# --- HEALTH CHECK ENDPOINT (To prevent "Method Not Allowed" on browser/GET) ---
@app.get("/")
def health_check():
    """
    Handles GET requests for health checks and browser visits.
    """
    return {"status": "ok", "message": "Latency check API is running. Send a POST request to this endpoint."}


# --- MAIN ENDPOINT FOR THE CHALLENGE ---
# 2. Accept a POST request with the specified JSON body
@app.post("/")
def check_latency(request_data: LatencyRequest):
    """
    Processes the request to return per-region latency and uptime metrics.
    """
    selected_regions = [r.lower() for r in request_data.regions]
    threshold = request_data.threshold_ms

    # Group records by region
    region_data = {}
    for record in TELEMETRY_RECORDS:
        region = record['region'].lower()
        if region in selected_regions:
            if region not in region_data:
                region_data[region] = []
            region_data[region].append(record)

    # Calculate metrics for each selected region
    response = {}
    for region, records in region_data.items():
        metrics = calculate_metrics(records, threshold)
        response[region] = metrics

    # 3. Return per-region metrics
    return response
