from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any
import json


class ArchitectAgent(BaseAgent):
    name = "ArchitectAgent"
    description = "Designs system architecture, selects tech stack, defines services and data models"
    skills = [
        AgentSkill(
            id="system-design",
            name="System Design",
            description="Create scalable architecture with tech stack, services, and infrastructure",
            tags=["architecture", "system-design", "tech-stack"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a principal systems architect. Design a production-grade system architecture.

Return JSON with this exact structure:
{
  "architecture_style": "...",
  "system_diagram": "...",
  "tech_stack": {
    "backend": {"language": "...", "framework": "...", "database": "..."},
    "frontend": {"framework": "...", "styling": "...", "bundler": "..."},
    "infrastructure": {"cloud": "...", "containers": "...", "ci_cd": "..."}
  },
  "services": [
    {"name": "...", "responsibility": "...", "tech": "...", "endpoints": ["..."]}
  ],
  "data_model": [
    {"entity": "...", "fields": ["..."]}
  ],
  "security": {
    "authentication": "...", "authorization": "...", "encryption": "..."
  },
  "scalability": {
    "phase_1": "...", "phase_2": "...", "phase_3": "..."
  }
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        prd = context.get("ProductAgent", {})
        ctx = json.dumps(prd, indent=2) if prd else "No PRD available."
        return f"Startup idea: {task_input}\n\nProduct requirements:\n{ctx}\n\nDesign a production-grade architecture."
