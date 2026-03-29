from server.a2a_protocol import AgentSkill
from server.agents.base import BaseAgent
from typing import Any
import json


class MarketingAgent(BaseAgent):
    name = "MarketingAgent"
    description = "Creates go-to-market strategy with launch plan, messaging, channels, and pricing"
    skills = [
        AgentSkill(
            id="gtm-strategy",
            name="Go-to-Market Strategy",
            description="Develop launch plan, pricing strategy, messaging, and channel mix",
            tags=["marketing", "GTM", "pricing", "launch"],
        ),
    ]

    def system_prompt(self) -> str:
        return """You are a VP of Marketing at a high-growth startup. Create a go-to-market strategy.

Return JSON with this exact structure:
{
  "launch_plan": [
    {"phase": "...", "timeline": "...", "activities": ["..."], "kpis": ["..."]}
  ],
  "messaging": {
    "tagline": "...",
    "elevator_pitch": "...",
    "key_messages": ["..."]
  },
  "channels": {
    "owned": ["..."],
    "earned": ["..."],
    "paid": ["..."]
  },
  "pricing": {
    "model": "...",
    "tiers": [{"name": "...", "price": "...", "features": "..."}]
  },
  "budget_allocation": {
    "content": "...", "community": "...", "paid": "...", "events": "..."
  }
}"""

    def build_prompt(self, task_input: str, context: dict[str, Any]) -> str:
        research = context.get("ResearchAgent", {})
        analysis = context.get("AnalysisAgent", {})
        ctx = json.dumps({"research": research, "analysis": analysis}, indent=2)
        return f"Startup idea: {task_input}\n\nResearch and analysis:\n{ctx}\n\nCreate a comprehensive GTM strategy."
