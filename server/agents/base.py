"""Base agent with A2A protocol compliance."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from server.a2a_protocol import (
    AgentCard,
    AgentCapabilities,
    AgentProvider,
    AgentSkill,
    Artifact,
    DataPart,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from server.llm import call_llm, call_llm_json


class BaseAgent(ABC):
    """Base A2A-compliant agent.

    Each subclass defines:
    - name, description, skills
    - system_prompt for LLM
    - build_prompt() to construct the user message
    - parse_response() to structure the LLM output
    """

    name: str = "BaseAgent"
    description: str = ""
    skills: list[AgentSkill] = []
    model: str = ""
    max_tokens: int = 4096

    @property
    def agent_card(self) -> AgentCard:
        return AgentCard(
            name=self.name,
            description=self.description,
            url=f"http://localhost:8000/agents/{self.name}",
            provider=AgentProvider(
                organization="A2A Startup Builder",
                url="http://localhost:8000",
            ),
            capabilities=AgentCapabilities(
                streaming=True,
                stateTransitionHistory=True,
            ),
            skills=self.skills,
        )

    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str: ...

    def parse_response(self, raw: str) -> dict[str, Any]:
        """Try to parse JSON from LLM response, handling markdown fences and extra text."""
        cleaned = raw.strip()

        # Strategy 1: strip ```json ... ``` wrappers (greedy to get largest block)
        match = re.search(r"```(?:json)?\s*([\s\S]*)```", cleaned)
        if match:
            cleaned = match.group(1).strip()

        # Strategy 2: try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strategy 3: find the outermost { ... } block
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass

        # Strategy 4: find the outermost [ ... ] block
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end > start:
            try:
                result = json.loads(cleaned[start:end + 1])
                if isinstance(result, list):
                    return {"items": result}
            except json.JSONDecodeError:
                pass

        return {"raw_output": raw}

    async def execute(self, task_input: str, context: dict[str, Any]) -> Task:
        """Run the full A2A task lifecycle."""
        task = Task(
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[
                Message(role="user", parts=[TextPart(text=task_input)])
            ],
        )

        # transition to working
        task.status = TaskStatus(state=TaskState.WORKING)

        try:
            prompt = self.build_prompt(task_input, context)
            raw_response = await call_llm_json(
                agent_name=self.name,
                system_prompt=self.system_prompt(),
                user_prompt=prompt,
                max_tokens=self.max_tokens,
            )

            parsed = self.parse_response(raw_response)

            # build artifacts
            task.artifacts = [
                Artifact(
                    name=f"{self.name}_output",
                    description=f"Output from {self.name}",
                    parts=[DataPart(data=parsed)],
                )
            ]

            task.history.append(
                Message(role="agent", parts=[DataPart(data=parsed)])
            )

            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"{self.name} completed successfully.")],
                ),
            )

        except Exception as exc:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"Error: {exc}")],
                ),
            )

        return task
