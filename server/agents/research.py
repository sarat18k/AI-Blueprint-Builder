from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    description = "Gathers market data, industry size, trends, and target audience analysis"
    skills = [
        AgentSkill(
            id="market-research",
            name="Market Research",
            description="Analyze market size, growth, segments, and target demographics",
            tags=["market", "research", "TAM"],
            examples=["Research the AI code review market"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a world-class market research analyst. Given a startup idea and industry, produce a comprehensive market research report.

Return JSON with this exact structure:
{
  "market_overview": {
    "market_size": "...",
    "growth_rate": "...",
    "key_segments": ["...", "..."]
  },
  "target_audience": {
    "primary": {"segment": "...", "pain_points": ["..."], "buying_behavior": "..."},
    "secondary": {"segment": "...", "pain_points": ["..."]}
  },
  "trends": ["...", "..."],
  "risks": ["...", "..."]
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        return f"Conduct market research for this startup idea:\n\n{task_input}\n\nBe specific with numbers, real market data, and actionable insights."
