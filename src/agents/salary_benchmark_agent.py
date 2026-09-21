"""Salary Benchmark Agent.

Collects role-level compensation ranges for a market. Prefers licensed/public
sources; where the user supplies numbers gathered manually from sites that
disallow scraping (e.g. Glassdoor), those are accepted as
"user-provided" citations rather than scraped directly.
"""
from __future__ import annotations

from anthropic import Anthropic

from src.config import config
from src.llm import complete_json
from src.schemas.report_schema import SalaryBenchmark
from src.seed import load_salaries

SYSTEM_PROMPT = """You are a compensation research analyst. Given a role and \
market, provide typical low/average/high total compensation figures, citing \
the source for each (public salary survey, government wage statistics, or a \
source the user explicitly provides). Do not scrape or fabricate numbers from \
sites whose terms of service prohibit automated scraping. If a role-level series \
is not published, report the closest official sector or occupation aggregate \
and say so in the citation. Return ONLY valid JSON matching: \
[{"role_title": str, "market": str, "low": float|null, "average": float|null, \
"high": float|null, "currency": str, "citation": {"claim": str, "source": str, \
"confidence": "high"|"medium"|"low", "is_synthetic": bool}}]"""


def benchmark_salary(
    role: str,
    market: str,
    user_provided_notes: str = "",
    *,
    offline: bool = False,
    search_context: str = "",
) -> list[SalaryBenchmark]:
    if offline:
        return load_salaries()

    client = Anthropic(api_key=config.anthropic_api_key)
    user_msg = f"Role: {role}\nMarket: {market}"
    if user_provided_notes:
        user_msg += (
            f"\nUser-provided data points to incorporate "
            f"(cite as user-provided): {user_provided_notes}"
        )
    if search_context:
        user_msg += f"\n\n{search_context}"
    return complete_json(
        client,
        system=SYSTEM_PROMPT,
        user=user_msg,
        model=list[SalaryBenchmark],
        model_name=config.model_name,
        max_tokens=config.max_tokens,
    )
