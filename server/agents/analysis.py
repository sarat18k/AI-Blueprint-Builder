from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any
import json


class AnalysisAgent(BaseAgent):
    name = "AnalysisAgent"
    description = "Performs competitor analysis, SWOT analysis, and market positioning"
    skills = [
        AgentSkill(
            id="competitor-analysis",
            name="Competitive Analysis",
            description="Identify competitors, analyze strengths/weaknesses, define positioning",
            tags=["competitors", "SWOT", "positioning"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a senior competitive intelligence analyst. Analyze competitors and create SWOT analysis.

Return JSON with this exact structure:
{
  "competitors": [
    {"name": "...", "description": "...", "strengths": ["..."], "weaknesses": ["..."], "pricing": "...", "market_share": "..."}
  ],
  "swot": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  },
  "positioning": {
    "differentiation": "...",
    "value_proposition": "...",
    "target_positioning": "..."
  }
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        research = context.get("ResearchAgent", {})
        research_text = json.dumps(research, indent=2) if research else "No prior research available."
        return f"Startup idea: {task_input}\n\nMarket research context:\n{research_text}\n\nProvide competitor analysis with real companies where possible."
