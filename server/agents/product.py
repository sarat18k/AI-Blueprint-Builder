from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any
import json


class ProductAgent(BaseAgent):
    name = "ProductAgent"
    description = "Creates a detailed Product Requirements Document with features, personas, and timeline"
    skills = [
        AgentSkill(
            id="prd-creation",
            name="PRD Creation",
            description="Build comprehensive product requirements with user stories and acceptance criteria",
            tags=["product", "PRD", "requirements"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a senior product manager at a top tech company. Create a comprehensive PRD.

Return JSON with this exact structure:
{
  "title": "...",
  "vision": "...",
  "success_metrics": ["..."],
  "user_personas": [
    {"name": "...", "role": "...", "goals": ["..."], "frustrations": ["..."]}
  ],
  "features": {
    "mvp": [
      {"id": "F001", "name": "...", "priority": "P0", "description": "...", "acceptance_criteria": ["..."]}
    ],
    "future": [
      {"id": "F005", "name": "...", "priority": "P2"}
    ]
  },
  "non_functional": {
    "performance": "...", "availability": "...", "security": "..."
  },
  "timeline": {
    "phase_1": "...", "phase_2": "...", "phase_3": "..."
  }
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        research = context.get("ResearchAgent", {})
        analysis = context.get("AnalysisAgent", {})
        ctx = json.dumps({"research": research, "analysis": analysis}, indent=2)
        return f"Startup idea: {task_input}\n\nContext from prior agents:\n{ctx}\n\nCreate a detailed PRD."
