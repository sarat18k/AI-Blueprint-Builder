"""OpenRouter multi-LLM client with model tier switching.

Two tiers available:
  Standard — fast, cost-effective models for quick iteration
  Premium  — best-in-class models for production-quality output

Each agent uses the model best suited for its task within the selected tier.
"""

from __future__ import annotations

import asyncio
import logging
import os
import httpx
from typing import Any

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 3
MAX_INPUT_LENGTH = 50_000

# ── Model Tiers ──────────────────────────────────────────────────────
#
# Standard: optimized for speed and cost
# Premium:  optimized for output quality (Opus 4.6, Sonnet 4.6, etc.)

MODEL_TIERS: dict[str, dict[str, str]] = {
    "standard": {
        "ResearchAgent":  "perplexity/sonar-pro",
        "AnalysisAgent":  "anthropic/claude-sonnet-4",
        "ProductAgent":   "anthropic/claude-sonnet-4",
        "ArchitectAgent": "anthropic/claude-sonnet-4",
        "CodeAgent":      "anthropic/claude-sonnet-4",
        "MarketingAgent": "openai/gpt-4.1",
        "PitchAgent":     "google/gemini-2.5-flash",
        "DocumentAgent":  "local",
    },
    "premium": {
        "ResearchAgent":  "perplexity/sonar-pro",
        "AnalysisAgent":  "anthropic/claude-opus-4",
        "ProductAgent":   "anthropic/claude-opus-4",
        "ArchitectAgent": "anthropic/claude-sonnet-4",
        "CodeAgent":      "anthropic/claude-sonnet-4",
        "MarketingAgent": "openai/gpt-4.1",
        "PitchAgent":     "google/gemini-2.5-pro",
        "DocumentAgent":  "local",
    },
}

MODEL_DISPLAY: dict[str, dict[str, str]] = {
    "standard": {
        "ResearchAgent":  "Perplexity Sonar Pro",
        "AnalysisAgent":  "Claude Sonnet 4",
        "ProductAgent":   "Claude Sonnet 4",
        "ArchitectAgent": "Claude Sonnet 4",
        "CodeAgent":      "Claude Sonnet 4",
        "MarketingAgent": "GPT-4.1",
        "PitchAgent":     "Gemini 2.5 Flash",
        "DocumentAgent":  "Local",
    },
    "premium": {
        "ResearchAgent":  "Perplexity Sonar Pro",
        "AnalysisAgent":  "Claude Opus 4",
        "ProductAgent":   "Claude Opus 4",
        "ArchitectAgent": "Claude Sonnet 4",
        "CodeAgent":      "Claude Sonnet 4",
        "MarketingAgent": "GPT-4.1",
        "PitchAgent":     "Gemini 2.5 Pro",
        "DocumentAgent":  "Local",
    },
}

# Flat display/reason maps — updated when tier changes
_current_tier: str = "premium"

AGENT_MODEL_DISPLAY: dict[str, str] = dict(MODEL_DISPLAY["premium"])

AGENT_MODEL_REASON: dict[str, str] = {
    "ResearchAgent":  "Live web search with cited sources",
    "AnalysisAgent":  "Deep reasoning for nuanced competitive analysis",
    "ProductAgent":   "Complex structured document generation",
    "ArchitectAgent": "Precise system design, fast and accurate",
    "CodeAgent":      "Best code generation quality at speed",
    "MarketingAgent": "Creative copywriting and brand messaging",
    "PitchAgent":     "Long-context synthesis of all outputs",
    "DocumentAgent":  "Generates .docx and .pptx locally",
}


def get_current_tier() -> str:
    return _current_tier


def set_tier(tier: str) -> None:
    global _current_tier
    if tier not in MODEL_TIERS:
        raise ValueError(f"Unknown tier: {tier}. Use 'standard' or 'premium'.")
    _current_tier = tier
    AGENT_MODEL_DISPLAY.update(MODEL_DISPLAY[tier])
    logger.info("Model tier switched to: %s", tier)


def get_tier_info() -> dict[str, Any]:
    return {
        "current": _current_tier,
        "tiers": {
            "standard": {
                "label": "Standard",
                "description": "Fast and cost-effective",
                "models": MODEL_DISPLAY["standard"],
            },
            "premium": {
                "label": "Premium",
                "description": "Best-in-class output quality",
                "models": MODEL_DISPLAY["premium"],
            },
        },
    }


def get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment or .env")
    return key


async def call_llm(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Call OpenRouter with the model for current tier, with retry logic."""
    tier_models = MODEL_TIERS.get(_current_tier, MODEL_TIERS["premium"])
    model = tier_models.get(agent_name, "anthropic/claude-sonnet-4")
    api_key = get_api_key()

    if len(user_prompt) > MAX_INPUT_LENGTH:
        user_prompt = user_prompt[:MAX_INPUT_LENGTH] + "\n\n[Content truncated for length]"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "A2A Startup Builder",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)

                if resp.status_code == 429:
                    wait = min(2 ** attempt, 30)
                    logger.warning("[%s] Rate limited, retrying in %ds (attempt %d/%d)", agent_name, wait, attempt, MAX_RETRIES)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"No response from {model} for {agent_name}")

            return choices[0]["message"]["content"]

        except httpx.TimeoutException:
            last_error = TimeoutError(f"{agent_name}: request to {model} timed out (attempt {attempt}/{MAX_RETRIES})")
            logger.warning("[%s] Timeout (attempt %d/%d)", agent_name, attempt, MAX_RETRIES)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                last_error = exc
                wait = min(2 ** attempt, 30)
                await asyncio.sleep(wait)
                continue
            last_error = RuntimeError(f"{agent_name}: API error {exc.response.status_code} from {model}")
            logger.error("[%s] HTTP %d: %s", agent_name, exc.response.status_code, exc.response.text[:200])
            break
        except Exception as exc:
            last_error = exc
            logger.error("[%s] Unexpected error (attempt %d/%d): %s", agent_name, attempt, MAX_RETRIES, exc)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)

    raise last_error or RuntimeError(f"{agent_name}: all {MAX_RETRIES} retries exhausted")


async def call_llm_json(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> str:
    """Call LLM and request JSON output."""
    system_prompt += "\n\nYou MUST respond with valid JSON only. No markdown, no code fences, no explanation."
    return await call_llm(agent_name, system_prompt, user_prompt, temperature, max_tokens)
