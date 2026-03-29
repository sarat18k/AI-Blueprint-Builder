"""DocumentAgent: generates Word and PowerPoint documents from all agent outputs.

This agent does NOT call an LLM — it programmatically builds documents
from the structured outputs of all prior agents.
"""

from __future__ import annotations

from typing import Any

from server.a2a_protocol import (
    AgentSkill,
    Artifact,
    DataPart,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from server.agents.base import BaseAgent
from server.documents import generate_docx, generate_pptx


class DocumentAgent(BaseAgent):
    name = "DocumentAgent"
    description = "Generates a Word document and PowerPoint pitch deck from all agent outputs"
    skills = [
        AgentSkill(
            id="document-generation",
            name="Document Generation",
            description="Creates downloadable .docx and .pptx from the full startup blueprint",
            tags=["document", "word", "powerpoint", "export"],
        ),
    ]

    async def execute(self, task_input: str, context: dict[str, Any]) -> Task:
        """Override base execute entirely — no LLM call needed."""
        task = Task(
            status=TaskStatus(state=TaskState.WORKING),
            history=[
                Message(role="user", parts=[TextPart(text=task_input)])
            ],
        )

        try:
            docx_id = generate_docx(task_input, context)
            pptx_id = generate_pptx(task_input, context)

            result = {
                "docx_id": docx_id,
                "pptx_id": pptx_id,
                "docx_filename": "startup_plan.docx",
                "pptx_filename": "startup_pitch.pptx",
            }

            task.artifacts = [
                Artifact(
                    name="DocumentAgent_output",
                    description="Generated Word and PowerPoint documents",
                    parts=[DataPart(data=result)],
                )
            ]

            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text="Documents generated successfully.")],
                ),
            )

        except Exception as exc:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"Document generation failed: {exc}")],
                ),
            )

        return task

    def system_prompt(self) -> str:
        return ""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        return ""
