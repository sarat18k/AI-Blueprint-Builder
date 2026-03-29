"""Google A2A Protocol implementation.

Implements the Agent-to-Agent protocol specification:
- Agent Cards for capability discovery
- Task lifecycle (submitted -> working -> completed / failed)
- Structured message parts (text, data)
- Artifact outputs
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Agent Card (/.well-known/agent.json) ─────────────────────────────

class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = []
    examples: list[str] = []


class AgentCapabilities(BaseModel):
    streaming: bool = True
    pushNotifications: bool = False
    stateTransitionHistory: bool = True


class AgentProvider(BaseModel):
    organization: str
    url: str


class AgentCard(BaseModel):
    """A2A Agent Card — served at /.well-known/agent.json"""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    documentationUrl: str | None = None
    provider: AgentProvider
    capabilities: AgentCapabilities = AgentCapabilities()
    authentication: dict[str, Any] | None = None
    defaultInputModes: list[str] = ["text"]
    defaultOutputModes: list[str] = ["text", "data"]
    skills: list[AgentSkill] = []


# ── Task lifecycle ───────────────────────────────────────────────────

class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TextPart(BaseModel):
    type: str = "text"
    text: str


class DataPart(BaseModel):
    type: str = "data"
    data: dict[str, Any]


class FilePart(BaseModel):
    type: str = "file"
    file: dict[str, str]


Part = TextPart | DataPart | FilePart


class Message(BaseModel):
    role: str  # "user" or "agent"
    parts: list[Part]
    metadata: dict[str, Any] | None = None


class Artifact(BaseModel):
    name: str
    description: str | None = None
    parts: list[Part]
    index: int = 0
    metadata: dict[str, Any] | None = None


class TaskStatus(BaseModel):
    state: TaskState
    message: Message | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    sessionId: str | None = None
    status: TaskStatus
    history: list[Message] = []
    artifacts: list[Artifact] = []
    metadata: dict[str, Any] | None = None


# ── JSON-RPC style request/response ─────────────────────────────────

class TaskSendParams(BaseModel):
    id: str | None = None
    sessionId: str | None = None
    message: Message
    metadata: dict[str, Any] | None = None


class TaskQueryParams(BaseModel):
    id: str
    historyLength: int | None = None


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None
