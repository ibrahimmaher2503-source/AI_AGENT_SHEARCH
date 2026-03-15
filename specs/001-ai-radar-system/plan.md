# Implementation Plan: AI Radar — Automated Daily Intelligence System

**Branch**: `001-ai-radar-system` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-radar-system/spec.md`

## Summary

Build a fully automated AI intelligence pipeline that collects signals from 4 layers (Tavily web search, GitHub API, Hugging Face API, curated sources), deduplicates via entity resolution, classifies and scores via Gemini 2.0 Flash, publishes to 9 Notion databases with duplicate protection, generates P1/P2/P3 alerts, and writes a daily intelligence brief — all running unattended on GitHub Actions at 8 AM Cairo time. Python 3.11 with `requests` as the sole dependency.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `requests` (sole pip package)
**Storage**: Notion API via REST (9 databases)
**Testing**: Plain Python smoke tests (no pytest)
**Target Platform**: GitHub Actions (ubuntu-latest), local dev (Windows/Linux/macOS)
**Project Type**: Automation pipeline / CLI script
**Performance Goals**: Complete full daily run within 45 minutes
**Constraints**: Only `requests` allowed; no SDKs, no async, no databases, no frameworks; max ~50 lines per function; `print()` logging only
**Scale/Scope**: Single developer, ~150 signals/day, 9 Notion databases, 22 source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Python-Only, Minimal Dependencies | PASS | Only `requests` used; no SDKs or frameworks |
| II. Reliability-First Pipeline | PASS | Every HTTP call has timeout + try/except; single failures never crash pipeline |
| III. Zero Manual Intervention | PASS | GitHub Actions cron at 6 AM UTC; all config via env vars |
| IV. Deterministic & Idempotent | PASS | Duplicate checks before every Notion write; entity resolution before classification |
| V. Explicit Simplicity | PASS | Max ~50 line functions; no abstractions; complete code in every file |
| VI. Print-Only Observability | PASS | All logging via `print()` with `[PREFIX]` format |
| VII. DRY_RUN Safety Net | PASS | DRY_RUN=true skips all Notion writes, prints payloads |

**Gate result: ALL PASS — proceed to Phase 0**

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-radar-system/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── notion-api.md
│   ├── gemini-api.md
│   ├── tavily-api.md
│   ├── github-api.md
│   └── hf-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai_radar/
├── main.py                      # Pipeline entry point — orchestrates all layers
├── config.py                    # Environment variable loading + validation
├── utils.py                     # Shared utility functions (scoring, normalization, formatting)
├── prompts.py                   # LLM prompt templates (CLASSIFY_PROMPT, BRIEF_PROMPT)
├── sources.py                   # Source lists, org watchlists, search queries
├── notion_client.py             # Notion REST API client (query, create, dedup checks)
├── gemini_client.py             # Gemini 2.0 Flash REST API client (text + JSON generation)
├── tavily_client.py             # Tavily search REST API client
├── github_client.py             # GitHub REST API client (search, orgs, releases)
├── hf_client.py                 # Hugging Face Hub REST API client (models)
├── agents/
│   ├── __init__.py              # Package init
│   ├── collector.py             # Layer A+D: Tavily web search for official + curated sources
│   ├── github_radar.py          # Layer B: GitHub new repos, releases, org watchlist
│   ├── hf_radar.py              # Layer C: Hugging Face new + trending models
│   ├── analyzer.py              # Entity resolution + Gemini classification + scoring + alerts
│   ├── publisher.py             # Route and write to all 9 Notion databases
│   └── brief_writer.py          # Generate and publish Daily AI Brief
├── setup_notion.py              # One-time: create all 9 Notion databases
├── smoke_test.py                # Validation: imports, env vars, utility function tests
├── requirements.txt             # Single line: requests
├── README.md                    # Full documentation
└── .github/
    └── workflows/
        └── daily_hub.yml        # GitHub Actions cron (6 AM UTC = 8 AM Cairo)
```

**Structure Decision**: Flat single-project layout at repository root. The `agents/` subdirectory groups the 6 pipeline stages. API clients are top-level for shared use. No nested packages, no src/ indirection — matches the constitution's explicit simplicity principle.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
