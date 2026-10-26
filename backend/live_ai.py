"""Optional live provider-backed review for the campus dining plan.

The deterministic planner remains the source of quantities and safety gates.
The live model reviews those facts and returns a structured explanation only.
"""
from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits


class LiveReview(BaseModel):
    summary: str = Field(description="A concise explanation for the dining manager.")
    risk_notes: list[str] = Field(default_factory=list)
    suggested_follow_up: str = Field(description="One practical follow-up, or 'None'.")


def _agent() -> Agent[None, LiveReview]:
    portkey_key = os.getenv("PORTKEY_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if portkey_key:
        provider = OpenAIProvider(
            base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            api_key=portkey_key,
        )
    elif openai_key:
        provider = OpenAIProvider(api_key=openai_key)
    else:
        raise RuntimeError("No PORTKEY_API_KEY or OPENAI_API_KEY is configured")

    model = OpenAIChatModel(os.getenv("MODEL_NAME", "gpt-6-luna"), provider=provider)
    return Agent(
        model,
        name="dining_live_review",
        output_type=LiveReview,
        system_prompt=(
            "You are the final review agent for a campus dining operations team. "
            "Review only the supplied structured facts. Do not invent demand, prices, "
            "inventory, or user preferences. Do not place orders or change records. "
            "The deterministic planner owns quantities and safety gates; you explain "
            "the tradeoffs and identify risks for a human manager. Return concise JSON."
        ),
        model_settings={"openai_reasoning_effort": "none"},
    )


def run_live_review(plan: dict[str, Any], history: list[dict[str, Any]], inventory: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "Review this draft prep plan. Cite only the supplied facts.\n\n"
        + json.dumps(
            {"context": context, "plan": plan, "sales_history": history, "inventory": inventory},
            indent=2,
            default=str,
        )
    )
    result = _agent().run_sync(
        prompt,
        usage_limits=UsageLimits(request_limit=1, total_tokens_limit=6000),
    )
    usage = result.usage
    return {
        "model": os.getenv("MODEL_NAME", "gpt-6-luna"),
        "review": result.output.model_dump(),
        "usage": {
            "requests": usage.requests,
            "input_tokens": usage.input_tokens,
            "cached_input_tokens": usage.cache_read_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.input_tokens + usage.cache_read_tokens + usage.output_tokens,
            "cost": usage.cost,
        },
    }
