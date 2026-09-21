"""Report Builder.

Merges the outputs of the three research agents into one MarketEntryReport,
then renders both a Markdown brief (for humans) and a JSON file (for
downstream tools / re-use).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from src.schemas.report_schema import (
    MarketEntryReport,
    MarketScanResult,
    RegulatoryFinding,
    SalaryBenchmark,
    SourcedClaim,
)


def build_report(
    role: str,
    market: str,
    employers: list,
    regulatory: list[RegulatoryFinding],
    salaries: list[SalaryBenchmark],
    key_findings: list[SourcedClaim],
    caveats: list[str],
    tam_or_demand: list[SourcedClaim] | None = None,
    funding_landscape: list[SourcedClaim] | None = None,
    run_mode: str = "offline",
    generated_at: str | None = None,
) -> MarketEntryReport:
    scan = employers if isinstance(employers, MarketScanResult) else None
    target_employers = scan.target_employers if scan else employers
    tam = tam_or_demand if tam_or_demand is not None else (scan.tam_or_demand if scan else [])
    funding = (
        funding_landscape
        if funding_landscape is not None
        else (scan.funding_landscape if scan else [])
    )
    return MarketEntryReport(
        role=role,
        market=market,
        generated_at=generated_at or date.today().isoformat(),
        target_employers=target_employers,
        regulatory_findings=regulatory,
        salary_benchmarks=salaries,
        key_findings=key_findings,
        caveats=caveats,
        tam_or_demand=tam,
        funding_landscape=funding,
        run_mode=run_mode,
    )


def _claim_line(claim: SourcedClaim) -> str:
    tag = " **(SYNTHETIC)**" if claim.is_synthetic else ""
    return f"- {claim.claim}{tag} — *{claim.source}* [{claim.confidence}]"


def _fmt_money(value: float | None, currency: str) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.0f} {currency}"


def render_markdown(report: MarketEntryReport) -> str:
    lines = [
        f"# {report.role} — {report.market} Market-Entry Brief",
        f"_Generated {report.generated_at} · run mode: `{report.run_mode}`_",
        "",
        "Every quantitative claim below carries a source URL or dataset reference. "
        "Items tagged **(SYNTHETIC)** are placeholders and must not be treated as findings.",
        "",
        "## Key Findings",
    ]
    if report.key_findings:
        lines.extend(_claim_line(item) for item in report.key_findings)
    else:
        lines.append("- No key findings were derived for this run.")

    lines.extend(["", "## TAM / demand signals"])
    if report.tam_or_demand:
        lines.extend(_claim_line(item) for item in report.tam_or_demand)
    else:
        lines.append("- No TAM/demand claims returned.")

    lines.extend(["", "## Target Employers"])
    if report.target_employers:
        for employer in report.target_employers:
            extra = f" {employer.notes}" if employer.notes else ""
            lines.append(
                f"- **{employer.name}** ({employer.industry}) — "
                f"{employer.sponsorship_signal}.{extra}"
            )
    else:
        lines.append("- No target employers returned.")

    lines.extend(["", "## Regulatory Findings"])
    if report.regulatory_findings:
        for finding in report.regulatory_findings:
            tag = " **(SYNTHETIC)**" if finding.citation.is_synthetic else ""
            lines.append(
                f"- **{finding.threshold_or_rule}**: {finding.value}{tag} — "
                f"*{finding.citation.source}* [{finding.citation.confidence}]"
            )
    else:
        lines.append("- No regulatory findings returned.")

    lines.extend(["", "## Salary Benchmarks"])
    if report.salary_benchmarks:
        for salary in report.salary_benchmarks:
            tag = " **(SYNTHETIC)**" if salary.citation.is_synthetic else ""
            lines.append(
                f"- **{salary.role_title}** ({salary.market}): "
                f"{_fmt_money(salary.low, salary.currency)} – "
                f"{_fmt_money(salary.high, salary.currency)} "
                f"(avg {_fmt_money(salary.average, salary.currency)}){tag} — "
                f"*{salary.citation.source}* [{salary.citation.confidence}]"
            )
    else:
        lines.append("- No salary benchmarks returned.")

    lines.extend(["", "## Funding landscape"])
    if report.funding_landscape:
        lines.extend(_claim_line(item) for item in report.funding_landscape)
    else:
        lines.append("- No funding-landscape claims returned.")

    lines.extend(["", "## Caveats"])
    if report.caveats:
        lines.extend(f"- {caveat}" for caveat in report.caveats)
    else:
        lines.append("- None recorded.")

    lines.extend(
        [
            "",
            "## Sourcing integrity",
            "- Public/government sources only unless a figure is explicitly marked "
            "`user-provided` or **(SYNTHETIC)**.",
            "- This brief is research automation output, not legal, immigration, or tax advice.",
        ]
    )
    return "\n".join(lines) + "\n"


def save_report(
    report: MarketEntryReport,
    output_dir: str,
    *,
    stem: str | None = None,
) -> tuple[str, str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if stem:
        base = f"{output_dir}/{stem}"
    else:
        base = f"{output_dir}/{report.market}_{report.role}_{report.generated_at}".replace(" ", "_")
    md_path, json_path = f"{base}.md", f"{base}.json"
    Path(md_path).write_text(render_markdown(report), encoding="utf-8")
    Path(json_path).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return md_path, json_path
