import os
from datetime import datetime, timezone

from fastapi import FastAPI


app = FastAPI(title="ConfusionLayer API")


@app.get("/api/health")
def health() -> dict[str, str | bool | int]:
    return {
        "ok": True,
        "service": "confusionlayer-backend",
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "ai_daily_call_limit": int(os.getenv("AI_DAILY_CALL_LIMIT", "50")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

