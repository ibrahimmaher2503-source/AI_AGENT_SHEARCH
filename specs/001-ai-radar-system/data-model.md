# Data Model: AI Radar — Automated Daily Intelligence System

**Date**: 2026-03-15
**Feature**: `001-ai-radar-system`

## Entity Overview

```
Signal (raw) ──→ Resolved Entity (deduped) ──→ Classified Item (scored)
                                                      │
                              ┌────────────────────────┼────────────────────────┐
                              ▼                        ▼                        ▼
                         9 Notion DBs              Alerts DB              Daily Brief
```

## E1: Signal (Raw Collection Output)

A raw piece of AI intelligence collected from any of the 4 layers.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| title | str | Signal headline | All layers |
| url | str | Source URL | All layers |
| source | str | Domain name (e.g., "github.com") | Extracted from URL |
| type | str | Rough type guess ("company", "news", "github_repo", "hf_model") | Layer-specific |
| published_at | str | ISO date string | API response |
| content | str | Description/summary, max 500 chars | API response, truncated |
| raw_score | float | Layer-specific relevance (0.0–1.0) | Computed per layer |
| source_priority | str | "high" / "medium" / "low" | Matched from SOURCES list |

### Layer-specific extra fields

**GitHub signals** (Layer B) additionally carry:

| Field | Type | Description |
|-------|------|-------------|
| repo_name | str | "owner/repo" |
| owner | str | Repository owner |
| stars | int | Star count |
| forks | int | Fork count |
| language | str | Primary language |
| topics | list[str] | Repository topics |
| created_at | str | ISO date |
| pushed_at | str | ISO date |
| has_release | bool | Whether a recent release exists |

**Hugging Face signals** (Layer C) additionally carry:

| Field | Type | Description |
|-------|------|-------------|
| model_id | str | Full model ID (e.g., "meta-llama/Llama-3") |
| organization | str | Org extracted from model_id |
| task | str | Pipeline task |
| downloads | int | Download count |
| likes | int | Like count |
| last_modified | str | ISO date |
| license | str | License identifier |
| pipeline_tag | str | Pipeline tag |

## E2: Resolved Entity (Post-Deduplication)

A deduplicated signal produced by entity resolution.

| Field | Type | Description |
|-------|------|-------------|
| title | str | Canonical title (from highest-priority source) |
| canonical_url | str | Primary URL |
| primary_source | str | Domain of best source |
| secondary_sources | list[str] | Other URLs covering same event |
| source | str | Domain |
| type | str | Inherited from primary signal |
| published_at | str | Earliest published date |
| content | str | Best content (from highest-priority source) |
| raw_score | float | Highest raw_score among merged items |
| source_priority | str | Highest priority among merged items |
| *(layer-specific fields)* | * | Preserved from primary signal |

### Entity Resolution Rules

1. **Exact URL match** → same entity
2. **Normalized URL match** → strip trailing `/`, remove `utm_*`, `ref`, `source` query params
3. **Title similarity** → 5+ consecutive shared words → likely same entity
4. **Merge priority**: keep item with highest `source_priority` (high > medium > low), break ties by `raw_score`

## E3: Classified Item (Post-Gemini Analysis)

A resolved entity enriched with LLM classification, scoring, and Arabic explanation.

| Field | Type | Description |
|-------|------|-------------|
| *(all Resolved Entity fields)* | * | Inherited |
| type | str | LLM-assigned: "model" / "tool" / "research" / "signal" / "github_repo" / "hf_model" / "skip" |
| importance_score | int | 1–100 |
| novelty_score | int | 0–100 |
| credibility_score | int | 0–100 |
| execution_value | int | 0–100 |
| dev_value | int | 0–100 |
| agency_value | int | 0–100 |
| radar_score | float | Weighted composite (0–100) |
| alert_level | str | "P1" / "P2" / "P3" / "None" |
| tremoai_relevant | bool | Relevant to TremoAI project |
| summary_en | str | English summary, max 20 words |
| why_it_matters | str | One sentence, Ibrahim-specific |
| arabic_explanation | dict | 4 keys: ايه_دي, هستفيد_منها_ازاي, تستحق_وقتك, مشابه_لـ |
| opportunities | list[dict] | 0–2 actionable opportunities |

### Radar Score Formula

```
radar_score = 0.30 * novelty_score
            + 0.25 * credibility_score
            + 0.20 * execution_value
            + 0.15 * dev_value
            + 0.10 * agency_value
```

### Alert Level Rules

| Condition | Level |
|-----------|-------|
| radar_score >= 80 OR (source_priority == "high" AND radar_score >= 70) | P1 |
| radar_score >= 55 | P2 |
| radar_score >= 30 | P3 |
| radar_score < 30 | None |

### Filtering Rules

Remove items where: `type == "skip"` OR `importance_score < 25`

## E4: Opportunity

| Field | Type | Allowed Values |
|-------|------|----------------|
| title | str | Free text |
| type | str | SaaS Idea / Marketing Service / Dev Tool / Automation / Content Strategy / Partnership / Other |
| description | str | 2–3 sentences |
| target | str | Agency Clients / My SaaS / BikeRide / DragonIsland / BNPL / Personal / Other |

## E5: Analyzer Output (Pipeline State Between Analyzer and Publisher)

| Field | Type | Description |
|-------|------|-------------|
| models | list[ClassifiedItem] | Items with type == "model" |
| tools | list[ClassifiedItem] | Items with type == "tool" |
| research | list[ClassifiedItem] | Items with type == "research" |
| signals | list[ClassifiedItem] | Items with type == "signal" |
| github_repos | list[ClassifiedItem] | Items with type == "github_repo" |
| hf_models | list[ClassifiedItem] | Items with type == "hf_model" |
| opportunities | list[Opportunity] | All extracted opportunities |
| alerts | list[ClassifiedItem] | All P1 + P2 items across types |
| stats | dict | raw_count, deduped_count, analyzed_count, skipped_count, p1_count, p2_count |

## E6: Publisher Stats

| Field | Type |
|-------|------|
| models_added / models_skipped | int |
| tools_added / tools_skipped | int |
| research_added / research_skipped | int |
| signals_added / signals_skipped | int |
| oss_added / oss_skipped | int |
| hf_added / hf_skipped | int |
| opportunities_added | int |
| alerts_added / alerts_skipped | int |

## Notion Database Schemas

### DB1: AI Models (NOTION_DB_MODELS)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Name | title | — |
| Company | select | OpenAI / Anthropic / Google / Meta / Mistral / Other |
| Model Type | select | LLM / Image / Video / Audio / Multimodal / Code / Other |
| Release Date | date | — |
| Key Capabilities | rich_text | — |
| Context Window | rich_text | — |
| Pricing | select | Free / Freemium / Paid / API Only |
| Radar Score | number | 0–100 |
| Importance Score | number | 1–100 |
| Marketing Relevance | select | High / Medium / Low |
| Dev Relevance | select | High / Medium / Low |
| TremoAI Relevant | checkbox | — |
| Alert Level | select | P1 / P2 / P3 / None |
| Arabic Explanation | rich_text | 4-field formatted block |
| Source URL | url | — |
| Added Date | date | — |
| Notes | rich_text | — |

### DB2: AI Tools (NOTION_DB_TOOLS)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Name | title | — |
| URL | url | — |
| Category | select | Coding / Image / Video / Writing / SEO / Ads / Analytics / Automation / Research / Other |
| Description | rich_text | — |
| Pricing | select | Free / Freemium / Paid |
| Tags | multi_select | Open Source / Has API / Laravel Package / Flutter Package / Mobile App / Arabic Support / Free Tier |
| Radar Score | number | 0–100 |
| Popularity Score | number | 1–100 |
| Rating | select | ⭐ / ⭐⭐ / ⭐⭐⭐ / ⭐⭐⭐⭐ / ⭐⭐⭐⭐⭐ |
| Marketing Use Case | select | Ads / Copy / Video / SEO / Analytics / Social / None |
| Has API | checkbox | — |
| Laravel Package URL | url | — |
| Flutter Package URL | url | — |
| TremoAI Relevant | checkbox | — |
| Alert Level | select | P1 / P2 / P3 / None |
| Arabic Explanation | rich_text | 4-field formatted block |
| Tried | checkbox | default false |
| Added Date | date | — |
| Notes | rich_text | — |

### DB3: AI Research (NOTION_DB_RESEARCH)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Title | title | — |
| Authors | rich_text | — |
| Institution | select | OpenAI / Google / Meta / Stanford / MIT / DeepMind / Academic / Other |
| Published Date | date | — |
| Abstract Summary | rich_text | — |
| Key Findings | rich_text | — |
| Practical Applications | rich_text | — |
| Radar Score | number | 0–100 |
| Importance Score | number | 1–100 |
| Dev Relevance | select | High / Medium / Low |
| Marketing Relevance | select | High / Medium / Low |
| TremoAI Relevant | checkbox | — |
| Source URL | url | — |
| Added Date | date | — |

### DB4: AI Signals (NOTION_DB_SIGNALS)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Title | title | — |
| Source | select | Twitter/X / Reddit / HackerNews / ProductHunt / GitHub / HuggingFace / Newsletter / Blog / News / Other |
| Type | select | Model Release / Tool Launch / Funding / Acquisition / Research / Open Source / Trend / Other |
| Published At | date | — |
| Summary | rich_text | — |
| Radar Score | number | 0–100 |
| Importance Score | number | 1–100 |
| Processed | checkbox | default false |
| URL | url | — |
| Added Date | date | — |

### DB5: Opportunities (NOTION_DB_OPPORTUNITIES)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Opportunity Title | title | — |
| Type | select | SaaS Idea / Marketing Service / Dev Tool / Automation / Content Strategy / Partnership / Other |
| Description | rich_text | — |
| Triggered By | rich_text | — |
| Target | select | Agency Clients / My SaaS / BikeRide / DragonIsland / BNPL / Personal / Other |
| Effort | select | Low / Medium / High |
| Potential Impact | select | High / Medium / Low |
| Action Items | rich_text | — |
| Status | select | New / Exploring / In Progress / Done / Dismissed |
| Added Date | date | — |

### DB6: Daily Briefs (NOTION_DB_BRIEFS)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Date | title | format: "AI Brief — YYYY-MM-DD" |
| Brief Date | date | — |
| Executive Summary | rich_text | — |
| Top Story | rich_text | — |
| Models Count | number | — |
| Tools Count | number | — |
| Research Count | number | — |
| OSS Count | number | — |
| HF Count | number | — |
| Opportunities Count | number | — |
| P1 Alerts Count | number | — |
| Status | select | Published / Draft |

### DB7: Open Source Radar (NOTION_DB_OSS_RADAR)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Repo Name | title | format: "owner/repo" |
| Owner | rich_text | — |
| URL | url | — |
| Description | rich_text | — |
| Language | select | Python / JavaScript / TypeScript / Rust / Go / Other |
| Stars | number | — |
| Forks | number | — |
| Topics | rich_text | comma-separated |
| Created At | date | — |
| Last Push | date | — |
| Has Release | checkbox | — |
| Radar Score | number | 0–100 |
| Dev Relevance | select | High / Medium / Low |
| TremoAI Relevant | checkbox | — |
| Arabic Explanation | rich_text | 4-field formatted block |
| Why It Matters | rich_text | — |
| Added Date | date | — |

### DB8: HF Models Radar (NOTION_DB_HF_RADAR)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Model Name | title | — |
| Organization | rich_text | — |
| URL | url | — |
| Task | select | Text Generation / Image Generation / Speech / Vision / Multimodal / Classification / Other |
| Downloads | number | — |
| Likes | number | — |
| Last Modified | date | — |
| License | rich_text | — |
| Pipeline Tag | rich_text | — |
| Radar Score | number | 0–100 |
| Dev Relevance | select | High / Medium / Low |
| TremoAI Relevant | checkbox | — |
| Arabic Explanation | rich_text | 4-field formatted block |
| Why It Matters | rich_text | — |
| Added Date | date | — |

### DB9: Alerts (NOTION_DB_ALERTS)

| Property | Notion Type | Select Options |
|----------|-------------|----------------|
| Alert Title | title | — |
| Level | select | P1 / P2 / P3 |
| Source Type | select | Model / Tool / Research / OSS / HF Model / Signal |
| Summary | rich_text | — |
| Source URL | url | — |
| Radar Score | number | 0–100 |
| Action Required | rich_text | — |
| Status | select | New / Reviewed / Dismissed |
| Added Date | date | — |

## Value Normalization Maps

### Company Normalization

| Input (case-insensitive) | Output |
|--------------------------|--------|
| openai, open ai | OpenAI |
| anthropic | Anthropic |
| google, deepmind | Google |
| meta, facebook | Meta |
| mistral | Mistral |
| *(anything else)* | Other |

### Pricing Normalization

| Input (case-insensitive) | Output |
|--------------------------|--------|
| free, open source | Free |
| freemium, free tier | Freemium |
| paid, subscription | Paid |
| api only | API Only |
| *(anything else)* | Freemium |

### Rating from Score

| Score Range | Rating |
|-------------|--------|
| 80–100 | ⭐⭐⭐⭐⭐ |
| 60–79 | ⭐⭐⭐⭐ |
| 40–59 | ⭐⭐⭐ |
| 20–39 | ⭐⭐ |
| 0–19 | ⭐ |
