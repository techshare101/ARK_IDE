import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": round(time.time() - _start_time, 2),
        "version": "3.0.0",
        "service": "ark-ide-backend",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check — verifies critical dependencies are configured."""
    checks: Dict[str, Any] = {}
    all_ready = True

    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY", "")
    checks["openai"] = {
        "ready": bool(openai_key and openai_key != "your_openai_key_here"),
        "detail": "API key configured" if openai_key else "OPENAI_API_KEY not set",
    }
    if not checks["openai"]["ready"]:
        all_ready = False

    # Check E2B key
    e2b_key = os.getenv("E2B_API_KEY", "")
    checks["e2b"] = {
        "ready": bool(e2b_key and e2b_key != "your_e2b_key_here"),
        "detail": "API key configured" if e2b_key else "E2B_API_KEY not set",
    }
    if not checks["e2b"]["ready"]:
        all_ready = False

    # Check MongoDB URL
    mongo_url = os.getenv("MONGODB_URL", "")
    checks["mongodb"] = {
        "ready": bool(mongo_url),
        "detail": "URL configured" if mongo_url else "MONGODB_URL not set",
    }

    return {
        "status": "ready" if all_ready else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Kubernetes-style liveness probe."""
    return {"status": "alive"}
