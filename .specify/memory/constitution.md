<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - I. Python-Only, Minimal Dependencies
    - II. Reliability-First Pipeline
    - III. Zero Manual Intervention
    - IV. Deterministic & Idempotent
    - V. Explicit Simplicity
    - VI. Print-Only Observability
    - VII. DRY_RUN Safety Net
    - Technology Constraints
    - Development Workflow
    - Governance
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ (aligned — no changes needed)
    - .specify/templates/spec-template.md ✅ (aligned — no changes needed)
    - .specify/templates/tasks-template.md ✅ (aligned — no changes needed)
  Follow-up TODOs: None
-->

# AI Radar Constitution

## Core Principles

### I. Python-Only, Minimal Dependencies

The entire system MUST be written in Python 3.11+ using only the `requests` library as the sole external dependency. No SDKs (`notion-client`, `google-generativeai`, `tavily-python`), no frameworks (`langchain`, `llama-index`, `pydantic`, `pandas`, `numpy`), no async (`asyncio`, `celery`, `rq`), no databases (`sqlite`, `postgres`, `redis`), and no test frameworks (`pytest`). All external communication happens through REST APIs using `requests` with explicit `timeout` and `try/except` on every call.

### II. Reliability-First Pipeline

One failed item MUST NEVER crash the whole pipeline. Every HTTP call MUST include a `timeout` parameter and be wrapped in `try/except`. Failed API calls MUST be logged and skipped — the pipeline continues with remaining items. Gemini JSON parse failures MUST trigger one cleanup retry, then graceful degradation. Notion 429 responses MUST trigger one retry after `time.sleep(2)`, then log and continue. Rate limits MUST be respected with appropriate `time.sleep()` between calls.

### III. Zero Manual Intervention

The system MUST run daily via GitHub Actions (8 AM Cairo time / 6 AM UTC) without any human interaction. All configuration comes from environment variables. Missing required variables MUST cause immediate `sys.exit(1)` with a clear error message. The pipeline MUST be fully automated from collection through publication.

### IV. Deterministic & Idempotent

Re-running the pipeline MUST NOT create duplicate records. Every Notion write MUST be preceded by a duplicate check: URL match for models/tools/research/signals/alerts, repo full name for OSS Radar, model_id for HF Radar, title for Daily Briefs, title+target for Opportunities. Entity resolution MUST run BEFORE Gemini classification to avoid paying for duplicate analysis. The same input MUST produce the same output.

### V. Explicit Simplicity

Functions MUST be max ~50 lines. No unnecessary abstractions. No placeholder code — every file MUST contain complete, working implementation. No TODO comments. Code MUST be simple, explicit, and readable. Three similar lines of code are better than a premature abstraction. Favor reliability over cleverness.

### VI. Print-Only Observability

All logging MUST use `print()` with consistent `[PREFIX]` format. Prefixes: `[CONFIG]`, `[COLLECTOR]`, `[GITHUB]`, `[HF]`, `[ANALYZER]`, `[PUBLISHER]`, `[BRIEF]`, `[NOTION]`, `[GEMINI]`, `[TAVILY]`, `[MAIN]`, `[SETUP]`, `[SMOKE]`. All comments MUST be in English. No logging libraries.

### VII. DRY_RUN Safety Net

When `DRY_RUN=true`, the system MUST execute all collection, deduplication, classification, and scoring steps normally but MUST skip all Notion writes. Instead, it MUST print the payloads that would have been written. This allows safe testing of the full pipeline without touching production databases.

## Technology Constraints

The following technology choices are NON-NEGOTIABLE:

| Component | Choice |
|-----------|--------|
| Language | Python 3.11+ |
| LLM | Gemini 2.0 Flash via REST API |
| Web Search | Tavily API via REST |
| GitHub | GitHub REST API |
| Hugging Face | HF Hub API via REST |
| Storage | Notion API via REST |
| Scheduler | GitHub Actions cron |
| Dependencies | `requests` only (via pip) |

### Banned Technologies

SDKs: `notion-client`, `google-generativeai`, `tavily-python`
Frameworks: `langchain`, `llama-index`, `pydantic`, `pandas`, `numpy`
Async: `asyncio`, `celery`, `rq`
Databases: `sqlite`, `postgres`, `redis`
Testing: `pytest`
Any pip package other than `requests`

## Development Workflow

### Data Flow (Invariant)

```
Tavily + GitHub API + HF API
        |
Entity Resolution (dedup FIRST)
        |
Gemini Classification + Radar Scoring
        |
Alert Assignment (P1/P2/P3)
        |
9 Notion Databases + Daily Brief
```

### Collection Architecture

- **Layer A**: Official sources — company blogs, product pages, release announcements (via Tavily)
- **Layer B**: GitHub Radar — new repos, releases, trending signals, AI org watchlist
- **Layer C**: Hugging Face Radar — new models, high-download models, task-specific discovery
- **Layer D**: Curated web and news — Tavily search + newsletters + media

### Radar Score Formula (Invariant)

```
radar_score = 0.30 * novelty + 0.25 * credibility + 0.20 * execution_value + 0.15 * dev_value + 0.10 * agency_value
```

### Alert Classification (Invariant)

- **P1**: `radar_score >= 80` OR (`source_priority == "high"` AND `radar_score >= 70`) — Notify immediately
- **P2**: `radar_score >= 55` — Worth testing this week
- **P3**: `radar_score >= 30` — Archive only
- **None**: Below 30 — Skip

### Notion Value Normalization

All Notion select/multi-select values MUST be normalized before writing. Never write an invalid select value. Use `normalize_select()` with an allowed values list and a fallback default.

### Arabic Explanation Format

All items in AI Models, AI Tools, OSS Radar, and HF Models Radar MUST include a formatted Arabic explanation with four fields: `ايه_دي`, `هستفيد_منها_ازاي`, `تستحق_وقتك`, `مشابه_لـ` — written in Egyptian Arabic dialect.

## Governance

- This constitution supersedes all other development practices for the AI Radar project
- Amendments require: documentation of change, version increment, and updated ratification date
- All code MUST verify compliance with these principles before merging
- Version follows semantic versioning: MAJOR (principle removal/redefinition), MINOR (new principle/expansion), PATCH (clarification/typo)

**Version**: 1.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15
