"""FastAPI server with A2A protocol, SSE pipeline, history, and document downloads."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from server.a2a_protocol import AgentCard, AgentProvider, AgentCapabilities, AgentSkill
from server.orchestrator import run_pipeline, AGENT_CLASSES, AGENT_LABELS, AGENT_MODEL_LABELS
from server.llm import AGENT_MODEL_REASON, get_current_tier, set_tier, get_tier_info
from server.history import init_db, save_run, list_runs, get_run
from server.documents import get_file, cleanup_downloads_on_startup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(name)-25s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

_load_dotenv()
init_db()
cleanup_downloads_on_startup()

if not os.getenv("OPENROUTER_API_KEY"):
    logger.warning("OPENROUTER_API_KEY not set — LLM calls will fail. Add it to .env")

app = FastAPI(title="A2A Startup Builder", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Simple in-memory rate limiter: max 3 concurrent runs
_active_runs = 0
_MAX_CONCURRENT = 3


# ── A2A Protocol: Agent Card discovery ───────────────────────────────

@app.get("/.well-known/agent.json")
async def get_master_agent_card():
    card = AgentCard(
        name="A2A Startup Builder",
        description="Orchestrates multiple AI agents to build a complete startup plan from a single idea",
        url="http://localhost:8000",
        version="1.0.0",
        provider=AgentProvider(organization="A2A Multi-Agent System", url="http://localhost:8000"),
        capabilities=AgentCapabilities(streaming=True, stateTransitionHistory=True),
        skills=[
            AgentSkill(
                id="startup-builder",
                name="Autonomous Startup Builder",
                description="Takes a startup idea and produces market research, competitor analysis, PRD, system design, MVP code, GTM strategy, pitch deck, and exportable documents",
                tags=["startup", "ai", "multi-agent"],
                examples=["Build a startup plan for an AI-powered code review platform"],
            ),
        ],
    )
    return card.model_dump()


@app.get("/agents/{agent_name}/agent.json")
async def get_agent_card(agent_name: str):
    cls = AGENT_CLASSES.get(agent_name)
    if not cls:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    try:
        return cls().agent_card.model_dump()
    except Exception:
        return JSONResponse({"error": "Failed to load agent card"}, status_code=500)


@app.get("/agents")
async def list_agents_endpoint():
    agents = []
    for name, cls in AGENT_CLASSES.items():
        agent = cls()
        agents.append({
            "name": name,
            "label": AGENT_LABELS.get(name, name),
            "model": AGENT_MODEL_LABELS.get(name, ""),
            "model_reason": AGENT_MODEL_REASON.get(name, ""),
            "description": agent.description,
            "card_url": f"/agents/{name}/agent.json",
        })
    return agents


# ── Model Tier Switching ─────────────────────────────────────────────

@app.get("/api/tier")
async def get_tier():
    return get_tier_info()


@app.post("/api/tier")
async def switch_tier(request: Request):
    body = await request.json()
    tier = body.get("tier", "").strip().lower()
    try:
        set_tier(tier)
        return get_tier_info()
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


# ── SSE: real-time pipeline execution ────────────────────────────────

@app.post("/api/run")
async def run_sse(request: Request):
    global _active_runs

    body = await request.json()
    task_input = body.get("task", "").strip()

    # Input validation
    if not task_input or len(task_input) < 10:
        return JSONResponse({"error": "Task must be at least 10 characters"}, status_code=400)
    if len(task_input) > 5000:
        return JSONResponse({"error": "Task must be under 5000 characters"}, status_code=400)

    # Rate limit
    if _active_runs >= _MAX_CONCURRENT:
        return JSONResponse({"error": "Server busy. Please try again shortly."}, status_code=429)

    _active_runs += 1
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_status(event: dict[str, Any]) -> None:
        await queue.put(event)

    async def run_and_finish() -> None:
        global _active_runs
        try:
            final = await run_pipeline(task_input=task_input, on_status=on_status)
            try:
                save_run(task_input, final.get("results", {}), final.get("timings", {}))
            except Exception as exc:
                logger.error("Failed to save run to history: %s", exc)
        except Exception as exc:
            logger.error("Pipeline failed: %s", exc)
            await queue.put({"type": "error", "error": str(exc)[:300]})
        finally:
            _active_runs -= 1
            await queue.put(None)

    async def event_stream():
        task = asyncio.create_task(run_and_finish())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ── History ──────────────────────────────────────────────────────────

@app.get("/api/history")
async def api_history(limit: int = 50, offset: int = 0):
    return list_runs(limit=min(limit, 100), offset=max(offset, 0))


@app.get("/api/history/{run_id}")
async def api_history_detail(run_id: str):
    run = get_run(run_id)
    if not run:
        return JSONResponse({"error": "Run not found"}, status_code=404)
    return run


# ── Document downloads ───────────────────────────────────────────────

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    # Validate file_id format
    if not file_id.isalnum() or len(file_id) > 20:
        return JSONResponse({"error": "Invalid file ID"}, status_code=400)
    path = get_file(file_id)
    if not path or not path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if path.suffix == ".pptx":
        media = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return FileResponse(str(path), filename=path.name, media_type=media)


# ── Frontend routes ──────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/history")
async def serve_history():
    return FileResponse(str(STATIC_DIR / "history.html"))
