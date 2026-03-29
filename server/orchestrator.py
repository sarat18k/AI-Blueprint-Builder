"""Orchestrator: manages the agent execution pipeline with real-time status updates."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

from server.a2a_protocol import Task, TaskState
from server.agents.base import BaseAgent
from server.agents.research import ResearchAgent
from server.agents.analysis import AnalysisAgent
from server.agents.product import ProductAgent
from server.agents.architect import ArchitectAgent
from server.agents.code import CodeAgent
from server.agents.marketing import MarketingAgent
from server.agents.pitch import PitchAgent
from server.agents.document import DocumentAgent
from server.llm import AGENT_MODEL_DISPLAY, AGENT_MODEL_REASON, get_current_tier

logger = logging.getLogger(__name__)

EXECUTION_PLAN: list[str | list[str]] = [
    "ResearchAgent",
    "AnalysisAgent",
    ["ProductAgent", "MarketingAgent"],
    "ArchitectAgent",
    "CodeAgent",
    "PitchAgent",
    "DocumentAgent",
]

AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "ResearchAgent": ResearchAgent,
    "AnalysisAgent": AnalysisAgent,
    "ProductAgent": ProductAgent,
    "ArchitectAgent": ArchitectAgent,
    "CodeAgent": CodeAgent,
    "MarketingAgent": MarketingAgent,
    "PitchAgent": PitchAgent,
    "DocumentAgent": DocumentAgent,
}

AGENT_LABELS: dict[str, str] = {
    "ResearchAgent": "Market Research",
    "AnalysisAgent": "Competitor Analysis",
    "ProductAgent": "Product Requirements",
    "MarketingAgent": "Go-to-Market Strategy",
    "ArchitectAgent": "System Architecture",
    "CodeAgent": "MVP Code Generation",
    "PitchAgent": "Investor Pitch Deck",
    "DocumentAgent": "Document Export",
}

AGENT_MODEL_LABELS = AGENT_MODEL_DISPLAY

StatusCallback = Callable[[dict[str, Any]], Awaitable[None]]


async def run_pipeline(
    task_input: str,
    on_status: StatusCallback | None = None,
) -> dict[str, Any]:
    agents: dict[str, BaseAgent] = {}
    for name, cls in AGENT_CLASSES.items():
        agents[name] = cls()

    context: dict[str, Any] = {}
    results: dict[str, Any] = {}
    timings: dict[str, float] = {}

    async def notify(event: dict[str, Any]) -> None:
        if on_status:
            await on_status(event)

    ordered_agents = []
    for step in EXECUTION_PLAN:
        if isinstance(step, list):
            ordered_agents.extend(step)
        else:
            ordered_agents.append(step)

    await notify({
        "type": "pipeline_start",
        "tier": get_current_tier(),
        "agents": [
            {
                "name": name,
                "label": AGENT_LABELS.get(name, name),
                "model": AGENT_MODEL_LABELS.get(name, ""),
                "model_reason": AGENT_MODEL_REASON.get(name, ""),
                "description": agents[name].description,
            }
            for name in ordered_agents
        ],
    })

    for step in EXECUTION_PLAN:
        if isinstance(step, list):
            # parallel execution
            async def _run_one(agent_name: str) -> tuple[str, Task | None, float, Exception | None]:
                await notify({"type": "agent_start", "agent": agent_name})
                t0 = time.perf_counter()
                try:
                    agent = agents[agent_name]
                    task = await agent.execute(task_input, context)
                    elapsed = time.perf_counter() - t0
                    return agent_name, task, elapsed, None
                except Exception as exc:
                    elapsed = time.perf_counter() - t0
                    return agent_name, None, elapsed, exc

            group = await asyncio.gather(
                *[_run_one(n) for n in step],
            )

            for agent_name, task, elapsed, exc in group:
                timings[agent_name] = elapsed
                if exc:
                    err_msg = str(exc)[:200]
                    results[agent_name] = {"error": err_msg}
                    await notify({"type": "agent_error", "agent": agent_name, "error": err_msg})
                    logger.error("[%s] Failed in parallel: %s", agent_name, err_msg)
                elif task and task.status.state == TaskState.COMPLETED and task.artifacts:
                    data = _extract_data(task)
                    context[agent_name] = data
                    results[agent_name] = data
                    await notify({
                        "type": "agent_done",
                        "agent": agent_name,
                        "elapsed": round(elapsed, 2),
                        "data": data,
                    })
                else:
                    err = _extract_error(task) if task else "Agent returned no result"
                    results[agent_name] = {"error": err}
                    await notify({"type": "agent_error", "agent": agent_name, "error": err})
        else:
            name = step
            await notify({"type": "agent_start", "agent": name})
            t0 = time.perf_counter()
            try:
                agent = agents[name]
                task = await agent.execute(task_input, context)
            except Exception as exc:
                elapsed = time.perf_counter() - t0
                timings[name] = elapsed
                err_msg = str(exc)[:200]
                results[name] = {"error": err_msg}
                await notify({"type": "agent_error", "agent": name, "error": err_msg})
                logger.error("[%s] Failed: %s", name, err_msg)
                continue

            elapsed = time.perf_counter() - t0
            timings[name] = elapsed

            if task.status.state == TaskState.COMPLETED and task.artifacts:
                data = _extract_data(task)
                context[name] = data
                results[name] = data
                await notify({
                    "type": "agent_done",
                    "agent": name,
                    "elapsed": round(elapsed, 2),
                    "data": data,
                })
            else:
                err = _extract_error(task)
                results[name] = {"error": err}
                await notify({"type": "agent_error", "agent": name, "error": err})

    final = {
        "results": results,
        "timings": timings,
        "agent_cards": {
            name: agent.agent_card.model_dump() for name, agent in agents.items()
        },
    }

    await notify({"type": "pipeline_done", "data": final})
    return final


def _extract_data(task: Task) -> dict[str, Any]:
    for artifact in task.artifacts:
        for part in artifact.parts:
            if hasattr(part, "data") and isinstance(part.data, dict):
                return part.data
    return {}


def _extract_error(task: Task | None) -> str:
    if task and task.status.message:
        for part in task.status.message.parts:
            if hasattr(part, "text"):
                return part.text[:200]
    return "Unknown error"
