"""Market Scanner Agent.

Given a role + market, returns target employers plus sourced TAM/demand
and funding-landscape claims.
"""
from __future__ import annotations

from anthropic import Anthropic

from src.config import config
from src.llm import complete_json
from src.schemas.report_schema import MarketScanResult
from src.seed import load_market_scan

SYSTEM_PROMPT = """You are a market-research analyst. Given a job role and a target \
country/market, identify 8-12 employers most likely to hire a candidate for that role \
and any publicly evidenced demand or funding-landscape signals. Prioritize companies \
with a documented history of international hiring. Return ONLY valid JSON matching: \
{"target_employers": [{"name": str, "industry": str, "sponsorship_signal": str, "notes": str}], \
"tam_or_demand": [{"claim": str, "source": str, "confidence": "high"|"medium"|"low", "is_synthetic": false}], \
"funding_landscape": [{"claim": str, "source": str, "confidence": "high"|"medium"|"low", "is_synthetic": false}]}. \
Use public, licensed sources only (government statistics, official immigration pages, \
company career pages, named research reports). Never invent a specific statistic you \
cannot attribute to a real, named source; if unsure, say so in notes rather than \
fabricating a number. Do not scrape Glassdoor, Payscale, or similar sites."""


def scan_market(
    role: str,
    market: str,
    *,
    offline: bool = False,
    search_context: str = "",
) -> MarketScanResult:
    if offline:
        return load_market_scan()

    client = Anthropic(api_key=config.anthropic_api_key)
    user = f"Role: {role}\nMarket: {market}"
    if search_context:
        user += f"\n\n{search_context}"
    return complete_json(
        client,
        system=SYSTEM_PROMPT,
        user=user,
        model=MarketScanResult,
        model_name=config.model_name,
        max_tokens=config.max_tokens,
    )
