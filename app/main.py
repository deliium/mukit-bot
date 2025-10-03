"""FastAPI entry point for the Mukit Bot web interface."""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Mukit Bot", version="1.0.0")

# Status file for communication with the bot process
STATUS_FILE = Path("/tmp/mukit_bot_status.json")


def get_bot_status() -> Dict[str, Any]:
    """Get the current status of the bot process."""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        else:
            return {"status": "not_running", "error": "Status file not found"}
    except Exception as e:
        return {"status": "error", "error": f"Failed to read status: {e}"}


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
async def healthz() -> JSONResponse:
    bot_status = get_bot_status()
    return JSONResponse({
        "status": "ok", 
        "bot_status": bot_status["status"],
        "bot_error": bot_status.get("error"),
        "bot_running": bot_status["status"] == "running"
    })


@app.get("/bot/status")
async def bot_status() -> JSONResponse:
    """Get detailed bot status."""
    return JSONResponse(get_bot_status())
