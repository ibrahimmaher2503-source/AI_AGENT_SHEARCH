# Feature Specification: AI Radar — Automated Daily Intelligence System

**Feature Branch**: `001-ai-radar-system`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Build a production-ready, automated AI intelligence pipeline that collects from 4 layers (official blogs, GitHub, Hugging Face, web/news), deduplicates via entity resolution, scores with a multi-dimensional Radar Score, publishes to 9 Notion databases, generates P1/P2/P3 alerts, and writes a daily brief — all running unattended via GitHub Actions at 8 AM Cairo time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily Automated Intelligence Collection (Priority: P1)

Every morning, the system automatically collects AI signals from 4 layers: official company blogs and curated web sources via Tavily search (Layer A+D), new/trending GitHub repositories and releases from watched AI organizations (Layer B), and new/trending Hugging Face models across key tasks (Layer C). The collected signals are deduplicated using entity resolution so the same announcement from 5 different sources appears as 1 record.

**Why this priority**: Without collection, there is no intelligence. This is the foundation that everything else depends on. Entity resolution prevents wasted LLM calls and duplicate Notion records.

**Independent Test**: Run the collection pipeline with `DRY_RUN=true` and verify that raw signals are collected from all 4 layers, entity resolution reduces duplicates, and no external writes occur.

**Acceptance Scenarios**:

1. **Given** the system starts at 8 AM Cairo time via GitHub Actions, **When** all API keys are configured, **Then** it collects 50–150 raw signals across all 4 layers within 30 minutes
2. **Given** the same AI model release appears on OpenAI blog, TechCrunch, and VentureBeat, **When** entity resolution runs, **Then** these 3 items are merged into 1 canonical record with secondary sources preserved
3. **Given** one API (e.g., Tavily) is temporarily down, **When** collection runs, **Then** the pipeline continues with the remaining layers and logs the failure clearly
4. **Given** `DRY_RUN=true`, **When** collection and deduplication run, **Then** all processing completes normally but no Notion writes occur

---

### User Story 2 - Intelligent Classification and Scoring (Priority: P1)

After deduplication, every unique signal is classified by an LLM into one of 7 types (model, tool, research, signal, github_repo, hf_model, skip) and scored on 5 dimensions: novelty, credibility, execution value, developer value, and agency value. A weighted Radar Score (0–100) is computed, and each item receives an alert level (P1/P2/P3/None). Items also receive an Arabic explanation in Egyptian dialect and actionable opportunity suggestions.

**Why this priority**: Classification and scoring are what transform raw data into actionable intelligence. Without scoring, Ibrahim cannot prioritize what to look at first.

**Independent Test**: Feed a known set of pre-collected signals into the analyzer and verify classification types, score ranges, alert levels, and Arabic explanation format are all correct.

**Acceptance Scenarios**:

1. **Given** 70 deduplicated signals, **When** the analyzer processes them in batches of 10, **Then** each item receives a type, importance score, 5 dimension scores, radar score, and alert level
2. **Given** an official GPT-5 release announcement from openai.com with radar_score 85, **When** alert assignment runs, **Then** it receives alert level "P1"
3. **Given** a low-quality aggregator post with radar_score 22, **When** filtering runs, **Then** the item is removed (importance_score < 25 or type == "skip")
4. **Given** a new AI ad-copy tool, **When** classification runs, **Then** the Arabic explanation contains all 4 fields (ايه_دي, هستفيد_منها_ازاي, تستحق_وقتك, مشابه_لـ) in Egyptian Arabic

---

### User Story 3 - Publishing to 9 Notion Databases (Priority: P1)

Classified and scored items are routed to the correct Notion database based on type: models, tools, research, signals, opportunities, OSS radar, HF radar, alerts, and daily briefs. Every record includes all required properties with normalized select values. Duplicate protection prevents re-adding items that already exist.

**Why this priority**: Notion is the single source of truth. Without publishing, the intelligence stays in logs and is useless.

**Independent Test**: Run the publisher with a known set of analyzed items against test Notion databases and verify correct routing, property mapping, duplicate skipping, and rate limit handling.

**Acceptance Scenarios**:

1. **Given** analyzed items with types model/tool/research/signal/github_repo/hf_model, **When** the publisher runs, **Then** each item is written to the correct Notion database with all properties populated
2. **Given** a tool that already exists in the Tools database (same URL), **When** the publisher encounters it, **Then** it skips the duplicate and logs the skip
3. **Given** Notion returns a 429 rate limit response, **When** the publisher receives it, **Then** it waits 2 seconds, retries once, and continues on second failure
4. **Given** all select values are raw strings from Gemini, **When** properties are built, **Then** all selects are normalized to valid Notion values (e.g., "openai" → "OpenAI", unknown pricing → "Freemium")
5. **Given** P1 and P2 items exist, **When** publishing completes, **Then** those items also appear in the Alerts database

---

### User Story 4 - Daily AI Intelligence Brief (Priority: P2)

After all items are published, the system generates a comprehensive daily brief summarizing the day's findings. The brief includes an executive summary, top story, highlights per category (models, tools, research, OSS, HF), marketing and dev opportunities, TremoAI updates, P1 alert summary, concrete action items, and an Arabic summary in Egyptian dialect. The brief is published as a Notion page with structured blocks.

**Why this priority**: The brief is the "product" — the single page Ibrahim reads every morning to get his competitive edge. It depends on all other stories being complete.

**Independent Test**: Feed known analyzed data and publish stats into the brief writer and verify the generated brief contains all required sections with meaningful content.

**Acceptance Scenarios**:

1. **Given** today's analyzed data with 5 models, 8 tools, 3 research papers, **When** the brief writer runs, **Then** a brief titled "AI Brief — 2026-03-15" is created in the Briefs database
2. **Given** a brief for today already exists, **When** the brief writer checks, **Then** it skips creation and logs that today's brief already exists
3. **Given** the brief data, **When** the Notion page is created, **Then** it includes callout blocks, heading sections, paragraph content, bulleted action items, and dividers
4. **Given** 3 P1 alerts today, **When** the brief is written, **Then** the P1 alerts summary section specifically names each alert and what action is required

---

### User Story 5 - One-Time Notion Database Setup (Priority: P2)

A setup script creates all 9 Notion databases with the correct schemas (properties, types, select options) under a specified parent page. It prints the database IDs for the user to copy into GitHub Secrets. It skips databases that already exist (by title match).

**Why this priority**: This is a one-time setup task. Without it, the main pipeline has nowhere to write. But it only needs to run once.

**Independent Test**: Run setup against a test Notion parent page and verify all 9 databases are created with correct schemas, IDs are printed, and re-running skips existing databases.

**Acceptance Scenarios**:

1. **Given** `NOTION_API_KEY` and `NOTION_PARENT_PAGE_ID` are set, **When** `setup_notion.py` runs, **Then** 9 databases are created with all properties matching the specification
2. **Given** the "AI Models" database already exists under the parent page, **When** setup runs again, **Then** it skips that database and logs the skip
3. **Given** setup completes successfully, **When** the user reads the output, **Then** all 9 database IDs are printed in a copy-paste-ready format

---

### User Story 6 - Smoke Testing and Validation (Priority: P3)

A smoke test script validates that all modules import correctly, all required environment variables are present, and all utility functions produce correct outputs — without making any real API calls. It provides clear PASS/FAIL output per check.

**Why this priority**: Nice-to-have for CI validation and confidence before deployment, but the system can function without it.

**Independent Test**: Run `smoke_test.py` and verify it exits 0 when all checks pass and exits 1 when any check fails.

**Acceptance Scenarios**:

1. **Given** all environment variables are set, **When** the smoke test runs, **Then** it reports PASS for env var checks
2. **Given** all modules exist, **When** import checks run, **Then** all modules import without error
3. **Given** utility functions, **When** tested with known inputs, **Then** outputs match expected values (e.g., `normalize_company("openai")` → `"OpenAI"`, `assign_alert_level({"radar_score": 82, "source_priority": "high"})` → `"P1"`)

---

### Edge Cases

- What happens when Gemini returns malformed JSON? → Log first 300 chars, skip that batch, continue with next batch
- What happens when GitHub rate limit is hit without a token? → Increase sleep to 10 seconds, log clearly, continue with remaining requests
- What happens when Tavily returns fewer than 3 results for a query? → Log and continue, do not retry
- What happens when a Notion select value doesn't match allowed options? → Normalize to the closest match or use fallback default
- What happens when all APIs fail simultaneously? → Each layer fails independently, pipeline completes with 0 items, brief reports "No data collected today"
- What happens when the system runs twice in the same day? → Duplicate protection prevents any duplicate records; brief check prevents duplicate briefs

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect AI signals from official company blogs, GitHub repositories, Hugging Face models, and curated web sources daily without manual intervention
- **FR-002**: System MUST deduplicate signals using entity resolution (exact URL match, normalized URL match, title similarity with 5+ consecutive shared words) before any LLM classification
- **FR-003**: System MUST classify each signal into one of 7 types (model, tool, research, signal, github_repo, hf_model, skip) using an LLM
- **FR-004**: System MUST score each signal on 5 dimensions (novelty, credibility, execution value, dev value, agency value) and compute a weighted Radar Score
- **FR-005**: System MUST assign alert levels (P1/P2/P3/None) based on Radar Score and source priority
- **FR-006**: System MUST publish classified items to the correct Notion database (9 databases total) with all properties populated and normalized
- **FR-007**: System MUST check for duplicate records before every Notion write (by URL, repo name, model ID, or title depending on database)
- **FR-008**: System MUST generate a daily intelligence brief with executive summary, category highlights, opportunities, action items, and Arabic summary
- **FR-009**: System MUST include Arabic explanations (Egyptian dialect, 4-field format) for items in Models, Tools, OSS Radar, and HF Radar databases
- **FR-010**: System MUST support `DRY_RUN` mode that executes all processing but skips Notion writes
- **FR-011**: System MUST continue operating when any single API call, item, or batch fails — one failure never crashes the pipeline
- **FR-012**: System MUST validate all required environment variables at startup and exit immediately with a clear error if any are missing
- **FR-013**: System MUST run automatically via a scheduled workflow at 8 AM Cairo time (6 AM UTC) daily
- **FR-014**: System MUST respect API rate limits with appropriate delays between calls (configurable per API)
- **FR-015**: System MUST log all operations using `print()` with consistent `[PREFIX]` format

### Key Entities

- **Signal**: A raw piece of AI intelligence from any source — has title, URL, source, type, content, published date, raw score, and source priority
- **Resolved Entity**: A deduplicated signal with canonical URL, primary source, and list of secondary sources
- **Classified Item**: A resolved entity enriched with LLM classification (type, scores, Arabic explanation, opportunities)
- **Radar Score**: Weighted composite of 5 dimension scores (novelty 30%, credibility 25%, execution value 20%, dev value 15%, agency value 10%)
- **Alert**: A P1 or P2 classified item that demands immediate attention
- **Daily Brief**: A summary report combining all classified items, statistics, highlights, and actionable recommendations
- **Opportunity**: A concrete business or development opportunity extracted from a classified item

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System collects 50–150 unique signals per daily run across all 4 collection layers
- **SC-002**: Entity resolution reduces raw signal count by at least 20% through deduplication
- **SC-003**: Every published item has a valid Radar Score (0–100) and alert level assigned
- **SC-004**: Zero duplicate records are created in any Notion database across multiple consecutive runs
- **SC-005**: Pipeline completes a full daily run within 45 minutes (GitHub Actions timeout)
- **SC-006**: System achieves 95%+ uptime — single API failures do not prevent the pipeline from completing
- **SC-007**: Daily brief is published by 8:30 AM Cairo time with all required sections populated
- **SC-008**: All Arabic explanations in Notion contain all 4 required fields in Egyptian dialect
- **SC-009**: `DRY_RUN=true` executes the full pipeline without creating any Notion records
- **SC-010**: `smoke_test.py` passes all checks (exit code 0) before deployment

### Assumptions

- All external APIs (Gemini, Tavily, GitHub, Hugging Face, Notion) are generally available with documented rate limits
- Gemini 2.0 Flash is capable of reliably classifying AI signals and producing valid JSON output with one retry
- GitHub public API provides sufficient data without authentication for basic repo discovery (60 req/hr)
- The user (Ibrahim) has a Notion workspace with an integration configured and a parent page for database creation
- The system is maintained by a single developer and does not require multi-tenant or multi-user support
- Egyptian Arabic dialect in explanations does not need formal linguistic validation — conversational accuracy is sufficient
