# Agentic Market-Entry & Fundraising Diligence Pipeline

**Turns a "which country / which role / which company should I target next" question into a sourced, structured brief in minutes instead of hours — using a four-agent research pipeline (Python + Claude API + optional MCP).**

Built as the productionized version of a real market-entry research method: the same sourced-claim discipline used for COO-track work (Hong Kong market-entry at Heal & Soul; operating systems that contributed to **$25M+** raised and a **60%** cut in time-to-insight).

## Result (lead with this)

| | Manual research | This pipeline |
|---|---|---|
| Time to produce a market-entry brief | ~15 hours | ~90 minutes (6x) |
| Output | Unstructured notes, mixed sources | Structured JSON + Markdown, every claim sourced |
| Consistency across markets | Varies by researcher fatigue/bias | Same schema, same rigor, every run |
| Demo in this repo | Original long-form notes | Offline seed: [Germany · Head of Operations](sample_output/Germany_Head_of_Operations.md) |

The 15h → 90m figure is the measured baseline for the equivalent two-track (COO/Ops vs Product) Germany visa-and-employer scan. Offline pipeline runtime on this seed is seconds (no API). Live runs add model + search latency; log wall-clock time from `python -m src.pipeline` against that 15-hour baseline.

## What it does

Given a **target role + target country/market**, the pipeline runs four agents and assembles one brief:

1. **Market Scanner** — employer list, TAM/demand signals, funding landscape
2. **Regulatory Agent** — visa/work-permit thresholds, shortage-occupation / ISCO classification, compliance flags (validated against the Germany EU Blue Card case in `sample_output/`)
3. **Salary Benchmark Agent** — compensation ranges from public statistical sources (not Glassdoor/Payscale scrapes)
4. **Report Builder** — merges agent outputs into a cited Markdown brief + machine-readable JSON

## Why this exists

Hiring teams asking "can you actually operationalize research?" get a cloneable answer: a schema that **refuses unsourced claims**, a seed case study that a recruiter can run with no API key, and a live path for new markets when an Anthropic key is present.

The seed is a **two-track** Germany brief (COO/Ops vs Product). The load-bearing finding is not "Germany hires internationally" — it is that **job title ≠ ISCO code**, so a Head of Operations often sits on the standard 2026 EU Blue Card threshold (€50,700) unless duties fall in shortage groups 132/133/134, while a Product/ICT track more often qualifies for the reduced threshold (€45,934.20).

## Architecture

```
src/
├── config.py              # API keys, model, optional MCP endpoint
├── llm.py                 # JSON extract + Pydantic validate + one retry
├── mcp_client.py          # optional public-source search (fail-open)
├── seed.py                # Germany Head of Operations fixture loader
├── pipeline.py            # Orchestrator — offline or live
├── agents/
│   ├── market_scanner.py
│   ├── regulatory_agent.py
│   ├── salary_benchmark_agent.py
│   └── report_builder.py
└── schemas/
    └── report_schema.py   # SourcedClaim is mandatory on every figure
fixtures/
└── germany_head_of_operations.json
sample_output/
├── Germany_Head_of_Operations.md
└── Germany_Head_of_Operations.json
```

```
CLI  →  offline? ──yes──► seed fixture ──► Report Builder ──► Markdown + JSON
              └──no───► optional MCP search
                        → Market Scanner / Regulatory / Salary (Claude JSON)
                        → Pydantic validation (retry once)
                        → Report Builder
```

## Quickstart (no API key)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline --offline --role "Head of Operations" --market "Germany"
pytest
```

Output: `sample_output/Germany_Head_of_Operations.md` and `.json`.

### Live run (optional)

```bash
cp .env.example .env        # add ANTHROPIC_API_KEY
python -m src.pipeline --role "Head of Operations" --market "Germany"
```

If `MCP_SERVER_URL` is set, the orchestrator POSTs to `{MCP_SERVER_URL}/search` and prepends hits. If it is blank, agents still run and must cite government or company URLs. Preferred domains are listed in `src/mcp_client.py` (Destatis, BAMF, Make it in Germany, Eurostat, BA, EY, KfW, SEC/Companies House).

## Data & sourcing integrity

- Every claim carries a source URL, dataset name, or `user-provided, <source>, accessed <date>`.
- **Public, licensed sources only**: Destatis, BAMF, Make it in Germany, §18g AufenthG, Bundesagentur für Arbeit, EY Startup-Barometer, KfW VC Dashboard. No Glassdoor/Payscale scraping.
- User-pasted figures from ToS-restricted sites are accepted only as `user-provided` citations.
- Placeholder rows are tagged `is_synthetic: true` and render as **(SYNTHETIC)** in Markdown. The seed includes one such row on purpose, so reviewers can see the control working.

## Seed case study

The committed artifact is a Germany · Head of Operations brief rebuilt from **public 2026 sources** (not a private IC memo):

- Standard EU Blue Card 2026: **€50,700** gross / year
- Shortage / recent-graduate / qualifying IT: **€45,934.20**, BA approval
- Shortage ISCO-08 groups: 132, 133, 134, 21, 221, 222, 225, 226, 23, 25
- Destatis 2025 full-time mean **€64,441** / median **€54,066**; ICT sector mean **€86,638**
- German VC 2025: EY **€8.4bn** (716 rounds) vs KfW/Dealroom **€7.2bn** (1,444 deals) — both cited, not averaged

Read it: [sample_output/Germany_Head_of_Operations.md](sample_output/Germany_Head_of_Operations.md)

## Reference materials

- Anthropic API ([docs.claude.com](https://docs.claude.com))
- Optional MCP search/doc-retrieval server
- [Make it in Germany — EU Blue Card](https://www.make-it-in-germany.com/en/visa-residence/types/eu-blue-card)
- [§ 18g AufenthG](https://www.gesetze-im-internet.de/aufenthg_2004/__18g.html)
- [Destatis earnings](https://www.destatis.de/EN/Themes/Labour/Earnings/Earnings-Earnings-Differences/Tables/yearly-gross-earnings.html)
- Python 3.10+

## Roadmap

- [ ] Per-claim source-authority tier beyond high/medium/low
- [ ] Second market as a validation case (Hong Kong skilled-worker path)
- [ ] HTML artifact in addition to Markdown
- [ ] Mocked live-client tests for each agent (see TODOs in `tests/test_pipeline.py`)
