from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any
import json


class CodeAgent(BaseAgent):
    name = "CodeAgent"
    description = "Generates production-ready MVP code for backend API and frontend application"
    skills = [
        AgentSkill(
            id="mvp-code",
            name="MVP Code Generation",
            description="Generate backend and frontend code with deployment config",
            tags=["code", "backend", "frontend", "MVP"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a senior full-stack engineer. Generate production-ready MVP code.

Return JSON with this exact structure:
{
  "project_structure": ["dir/file1.py", "dir/file2.tsx"],
  "backend": {
    "main_app": "...full code...",
    "models": "...full code...",
    "api_routes": "...full code...",
    "config": "...full code..."
  },
  "frontend": {
    "app_component": "...full code...",
    "api_client": "...full code..."
  },
  "deployment": {
    "dockerfile": "...full code...",
    "docker_compose": "...full code..."
  },
  "setup_instructions": ["step1", "step2"]
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        arch = context.get("ArchitectAgent", {})
        prd = context.get("ProductAgent", {})
        ctx = json.dumps({"architecture": arch, "prd": prd}, indent=2)
        return f"Startup idea: {task_input}\n\nArchitecture and PRD:\n{ctx}\n\nGenerate complete MVP code."
