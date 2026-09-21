"""Regulatory Agent.

Surfaces visa/work-permit thresholds and shortage-occupation classification
for a given role + market. Modeled on the Germany EU Blue Card seed case.
"""
from __future__ import annotations

from anthropic import Anthropic

from src.config import config
from src.llm import complete_json
from src.schemas.report_schema import RegulatoryFinding
from src.seed import load_regulatory

SYSTEM_PROMPT = """You are an immigration/visa research analyst. Given a job role \
and a target country, identify the applicable work-visa salary threshold(s), \
whether the role's occupation classification qualifies for any reduced/shortage \
threshold, and any degree-recognition considerations. Cite the specific statute, \
government agency page, or official source for every figure. If you cannot find \
an authoritative source for a number, do not include it. Return ONLY valid JSON \
matching: [{"threshold_or_rule": str, "value": str, "citation": {"claim": str, \
"source": str, "confidence": "high"|"medium"|"low", "is_synthetic": false}}]"""


def check_regulatory(
    role: str,
    market: str,
    *,
    offline: bool = False,
    search_context: str = "",
) -> list[RegulatoryFinding]:
    if offline:
        return load_regulatory()

    client = Anthropic(api_key=config.anthropic_api_key)
    user = f"Role: {role}\nMarket: {market}"
    if search_context:
        user += f"\n\n{search_context}"
    return complete_json(
        client,
        system=SYSTEM_PROMPT,
        user=user,
        model=list[RegulatoryFinding],
        model_name=config.model_name,
        max_tokens=config.max_tokens,
    )
