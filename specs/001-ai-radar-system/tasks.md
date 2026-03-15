# Tasks: AI Radar — Automated Daily Intelligence System

**Input**: Design documents from `/specs/001-ai-radar-system/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, configuration, and shared utilities

- [X] T001 Create project directory structure: `ai_radar/`, `ai_radar/agents/`, `ai_radar/.github/workflows/`
- [X] T002 Write `ai_radar/requirements.txt` with single dependency: `requests`
- [X] T003 [P] Write `ai_radar/config.py` — load all environment variables from `os.environ`, validate required vars at startup, `DRY_RUN` support, `sys.exit(1)` on missing required var with `[CONFIG]` logging
- [X] T004 [P] Write `ai_radar/utils.py` — all shared utility functions: `get_today_iso()`, `extract_domain()`, `normalize_url()`, `truncate()`, `chunk_rich_text()`, `title_similarity()`, `normalize_select()`, `score_to_rating()`, `normalize_company()`, `build_notion_rich_text()`, `build_notion_children_blocks()`, `format_arabic_explanation()`, `calculate_radar_score()`, `assign_alert_level()`, `get_source_priority()`
- [X] T005 [P] Write `ai_radar/sources.py` — SOURCES list (21 entries), GITHUB_ORGS (12 orgs), GITHUB_SEARCH_QUERIES (7 queries), HF_TASKS (6 tasks), TAVILY_QUERIES (15 queries)
- [X] T006 [P] Write `ai_radar/prompts.py` — CLASSIFY_PROMPT and BRIEF_PROMPT string constants with all format placeholders

**Checkpoint**: Configuration, utilities, source lists, and prompts ready — API clients can now be built

---

## Phase 2: Foundational (API Clients — Blocking Prerequisites)

**Purpose**: Reusable REST API clients that ALL user stories depend on

**CRITICAL**: No agent work can begin until these clients are complete

- [X] T007 [P] Write `ai_radar/notion_client.py` — `query_database()`, `create_page()`, `url_exists_in_database()`, `title_exists_in_database()`, `field_exists_in_database()` with Authorization + Notion-Version headers, 30s timeout, 429 retry with 2s wait, `[NOTION]` prefix logging, return None/[] on failure
- [X] T008 [P] Write `ai_radar/gemini_client.py` — `generate_text()`, `generate_json()` with API key as query param, 60s timeout, JSON cleanup (strip markdown fences), retry once on parse failure, temperature parameter, `[GEMINI]` prefix logging, return []/​{} on unrecoverable failure
- [X] T009 [P] Write `ai_radar/tavily_client.py` — `search()`, `multi_search()` with api_key in body, 30s timeout, 0.5s sleep between searches, `[TAVILY]` prefix logging, skip failed queries
- [X] T010 [P] Write `ai_radar/github_client.py` — `search_repos()`, `get_org_repos()`, `get_latest_release()` with optional Bearer auth, token-aware sleep (0.3s with token, 2s without), 30s timeout, `[GITHUB]` prefix logging, return []/None on failure
- [X] T011 [P] Write `ai_radar/hf_client.py` — `fetch_new_models()`, `fetch_trending_models()` with no auth, 0.5s sleep, 30s timeout, `[HF]` prefix logging, return [] on failure
- [X] T012 Write `ai_radar/agents/__init__.py` — empty package init

**Checkpoint**: All 5 API clients ready — agent implementation can now begin in parallel

---

## Phase 3: User Story 1 — Daily Automated Intelligence Collection (Priority: P1) MVP

**Goal**: Collect signals from all 4 layers and deduplicate via entity resolution

**Independent Test**: Run with `DRY_RUN=true`, verify signals collected from all layers, entity resolution reduces duplicates, no Notion writes

### Implementation for User Story 1

- [X] T013 [P] [US1] Write `ai_radar/agents/collector.py` — Layer A+D: iterate TAVILY_QUERIES via `tavily_client.multi_search()`, map results to signal schema (title, url, source, type, published_at, content max 500 chars, raw_score, source_priority matched from SOURCES), deduplicate exact URLs, `[COLLECTOR]` prefix logging with query progress (e.g., "Running query 3/15: ..."), return list of 50–75 signals
- [X] T014 [P] [US1] Write `ai_radar/agents/github_radar.py` — Layer B: implement `fetch_new_repos()` using `github_client.search_repos()` for each GITHUB_SEARCH_QUERIES, `fetch_org_releases()` using `github_client.get_org_repos()` + `get_latest_release()` for each GITHUB_ORGS (keep releases from last 3 days), `fetch_trending_signals()` for additional trending queries, `run()` function combining all three, map to signal schema with extra GitHub fields (repo_name, owner, stars, forks, language, topics, created_at, pushed_at, has_release), source_priority "high" for known orgs else "medium", `[GITHUB]` prefix logging
- [X] T015 [P] [US1] Write `ai_radar/agents/hf_radar.py` — Layer C: implement `fetch_new_models()` using `hf_client.fetch_new_models()` for each HF_TASKS (filter by last 3 days), `fetch_trending_models()` using `hf_client.fetch_trending_models()` for each HF_TASKS (filter by last 7 days), `run()` function combining both, map to signal schema with extra HF fields (model_id, organization, task, downloads, likes, last_modified, license, pipeline_tag), skip models without description, `[HF]` prefix logging
- [X] T016 [US1] Implement entity resolution in `ai_radar/agents/analyzer.py` — write `deduplicate_and_resolve()` function: Stage 1 exact URL grouping, Stage 2 normalized URL grouping (strip trailing slash + utm_*/ref/source params via `normalize_url()`), Stage 3 title similarity grouping (5+ consecutive shared words via `title_similarity()`), merge groups keeping highest source_priority + raw_score item as primary with secondary_sources list, `[ANALYZER]` prefix logging with reduction stats

**Checkpoint**: All 4 collection layers produce signals, entity resolution deduplicates them. Verify with `DRY_RUN=true`.

---

## Phase 4: User Story 2 — Intelligent Classification and Scoring (Priority: P1)

**Goal**: Classify, score, and assign alert levels to all deduplicated signals

**Independent Test**: Feed known signals into analyzer, verify types, scores, alert levels, Arabic explanations

### Implementation for User Story 2

- [X] T017 [US2] Implement Gemini classification in `ai_radar/agents/analyzer.py` — write `classify_batch()` function: chunk resolved entities into batches of max 10, format CLASSIFY_PROMPT from `prompts.py` with items JSON, call `gemini_client.generate_json()`, parse response matching by index, merge classification fields into items (type, importance_score, novelty_score, credibility_score, execution_value, dev_value, agency_value, tremoai_relevant, summary_en, arabic_explanation, why_it_matters, opportunities), log batch progress `[ANALYZER] Classifying batch 3/8 (10 items)...`
- [X] T018 [US2] Implement scoring and alerting in `ai_radar/agents/analyzer.py` — write `score_and_alert()` function: compute radar_score via `calculate_radar_score()` from utils, assign alert_level via `assign_alert_level()` from utils for each classified item
- [X] T019 [US2] Implement filtering and routing in `ai_radar/agents/analyzer.py` — write `filter_and_route()` function: remove items where type == "skip" OR importance_score < 25, separate remaining into models/tools/research/signals/github_repos/hf_models lists, collect all opportunities into flat list, collect all P1+P2 items into alerts list, compute stats dict
- [X] T020 [US2] Implement `run()` function in `ai_radar/agents/analyzer.py` — orchestrate full pipeline: call `deduplicate_and_resolve()` (from US1), then `classify_batch()`, then `score_and_alert()`, then `filter_and_route()`, return final analyzer output dict with all 8 lists + stats

**Checkpoint**: Analyzer transforms raw signals into classified, scored, routed items with alert levels and Arabic explanations

---

## Phase 5: User Story 3 — Publishing to 9 Notion Databases (Priority: P1)

**Goal**: Write all classified items to correct Notion databases with duplicate protection

**Independent Test**: Run publisher with known analyzed data, verify correct routing, property mapping, duplicate skipping

### Implementation for User Story 3

- [X] T021 [US3] Write property builders in `ai_radar/agents/publisher.py` — implement `build_model_properties()`, `build_tool_properties()`, `build_research_properties()`, `build_signal_properties()`, `build_oss_properties()`, `build_hf_properties()`, `build_opportunity_properties()`, `build_alert_properties()`, each mapping classified item fields to Notion property format with all select values normalized via `normalize_select()`, `normalize_company()` from utils, Arabic explanation formatted via `format_arabic_explanation()`, dates as ISO strings, rich text via `build_notion_rich_text()` with `chunk_rich_text()` for long content
- [X] T022 [US3] Write publish functions in `ai_radar/agents/publisher.py` — implement `publish_models()`, `publish_tools()`, `publish_research()`, `publish_signals()`, `publish_oss()`, `publish_hf()`, `publish_opportunities()`, `publish_alerts()`, each: iterate items, check duplicate (URL/title/field match via notion_client), skip if exists with log, respect DRY_RUN (print payload instead of write), call `notion_client.create_page()` with correct DB ID from config, `time.sleep(0.3)` between writes, count added/skipped, `[PUBLISHER]` prefix logging
- [X] T023 [US3] Implement `run()` function in `ai_radar/agents/publisher.py` — call all 8 publish functions with analyzed data, aggregate stats into publisher output dict, return stats

**Checkpoint**: All 9 Notion databases populated correctly, duplicates skipped, DRY_RUN prints payloads

---

## Phase 6: User Story 4 — Daily AI Intelligence Brief (Priority: P2)

**Goal**: Generate and publish a comprehensive daily brief to Notion

**Independent Test**: Feed known analyzed data into brief writer, verify brief contains all sections

### Implementation for User Story 4

- [X] T024 [US4] Write `ai_radar/agents/brief_writer.py` — implement `run(analyzed, publish_stats)` function: check if today's brief already exists via `notion_client.title_exists_in_database()` with title "AI Brief — YYYY-MM-DD", if exists log skip and return, extract top items per category (top 3 by radar_score), format BRIEF_PROMPT from `prompts.py` with all placeholders (today, counts, top items, signals summary), call `gemini_client.generate_json()` with temperature 0.5, build Notion properties (title, brief_date, executive_summary, top_story, counts, status="Published"), build children blocks via `build_notion_children_blocks()` (callout for executive_summary, heading_2 + paragraph per section, bulleted_list_item for action_items, divider between sections), call `notion_client.create_page()` with NOTION_DB_BRIEFS and children, respect DRY_RUN, `[BRIEF]` prefix logging

**Checkpoint**: Daily brief page created in Notion with all sections, structured blocks, and Arabic summary

---

## Phase 7: User Story 5 — One-Time Notion Database Setup (Priority: P2)

**Goal**: Create all 9 Notion databases with correct schemas

**Independent Test**: Run setup, verify 9 databases created with all properties, re-run skips existing

### Implementation for User Story 5

- [X] T025 [US5] Write `ai_radar/setup_notion.py` — define all 9 database schemas as dicts matching data-model.md (property names, types, select options with exact allowed values), implement `create_database()` function using Notion API `POST /v1/databases` with parent page_id, title, and properties, implement `run_setup()` that iterates all 9 schemas, checks if title already exists under parent via `notion_client.title_exists_in_database()`, skips if exists, creates if not, prints each DB ID in copy-paste format, `[SETUP]` prefix logging

**Checkpoint**: All 9 databases created with correct schemas, IDs printed for secrets configuration

---

## Phase 8: User Story 6 — Smoke Testing and Validation (Priority: P3)

**Goal**: Validate all modules and utility functions without real API calls

**Independent Test**: Run smoke_test.py, verify exit 0 on pass, exit 1 on fail

### Implementation for User Story 6

- [X] T026 [US6] Write `ai_radar/smoke_test.py` — plain Python only, no pytest: check required env vars present (warn missing, don't crash), import all modules (config, utils, notion_client, gemini_client, tavily_client, github_client, hf_client, sources, prompts, agents.collector, agents.github_radar, agents.hf_radar, agents.analyzer, agents.publisher, agents.brief_writer), test utils functions with known inputs (get_today_iso valid date, extract_domain, normalize_url strips tracking params, score_to_rating, title_similarity, normalize_company, calculate_radar_score, assign_alert_level), print PASS/FAIL per check with checkmark/cross, exit 0 if all pass else exit 1, `[SMOKE]` prefix logging

**Checkpoint**: Smoke test validates all modules and utility functions

---

## Phase 9: Integration & Deployment

**Goal**: Wire everything together and deploy

### Implementation

- [X] T027 Write `ai_radar/main.py` — orchestrate full pipeline: import config (triggers validation), call `collector.run()` for web signals, `github_radar.run()` for GitHub signals, `hf_radar.run()` for HF signals, merge all signals, call `analyzer.run(all_signals)`, print stats and breakdown, call `publisher.run(analyzed)`, print publish stats, call `brief_writer.run(analyzed, publish_stats)`, `[MAIN]` prefix logging with emoji indicators, wrap in `if __name__ == "__main__": main()`
- [X] T028 Write `ai_radar/.github/workflows/daily_hub.yml` — GitHub Actions workflow: cron `0 6 * * *` (8 AM Cairo), workflow_dispatch for manual runs, ubuntu-latest, Python 3.11, pip install requests, run `python main.py` with all secrets mapped to env vars, timeout-minutes 45

**Checkpoint**: Full pipeline runs end-to-end locally and via GitHub Actions

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [X] T029 [P] Write `ai_radar/README.md` — include: system description, 4-layer architecture diagram (ASCII), 9 Notion databases explained, Radar Score formula, alert system (P1/P2/P3), entity resolution explained, full file structure with one-line descriptions, all API keys with signup links, step-by-step setup guide, how to run locally + DRY_RUN, recommended Notion views per database, troubleshooting table, maintenance tips
- [X] T030 Run `python smoke_test.py` and verify exit code 0
- [ ] T031 Run `python main.py` with `DRY_RUN=true` and verify full pipeline completes without errors (REQUIRES API KEYS — manual validation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T003–T006) — BLOCKS all agents
- **US1 Collection (Phase 3)**: Depends on Foundational (T007–T012) — collector, github_radar, hf_radar use API clients
- **US2 Classification (Phase 4)**: Depends on US1 entity resolution (T016) — analyzer builds on dedup
- **US3 Publishing (Phase 5)**: Depends on US2 (T020) — publisher needs classified items
- **US4 Brief (Phase 6)**: Depends on US3 (T023) — brief needs publish stats
- **US5 Setup DB (Phase 7)**: Depends on Foundational (T007) — uses notion_client only
- **US6 Smoke Test (Phase 8)**: Depends on all modules existing (T001–T024)
- **Integration (Phase 9)**: Depends on US1–US4 (T013–T024)
- **Polish (Phase 10)**: Depends on Integration (T027–T028)

### User Story Dependencies

- **US1 (Collection)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (Classification)**: Depends on US1's entity resolution function (T016)
- **US3 (Publishing)**: Depends on US2's analyzer output (T020)
- **US4 (Brief)**: Depends on US3's publish stats (T023)
- **US5 (Setup DB)**: Independent — only needs notion_client from Phase 2
- **US6 (Smoke Test)**: Depends on all modules existing

### Within Each User Story

- Models/utilities before services
- Services before orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T003–T006 can run in parallel
- All Foundational tasks T007–T011 can run in parallel
- US1 tasks T013–T015 can run in parallel (3 independent layers)
- US5 (T025) can run in parallel with US1–US4
- T029 (README) can run in parallel with T030–T031

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all API clients in parallel:
Task: "Write notion_client.py"    # T007
Task: "Write gemini_client.py"    # T008
Task: "Write tavily_client.py"    # T009
Task: "Write github_client.py"    # T010
Task: "Write hf_client.py"        # T011
```

## Parallel Example: Phase 3 (US1 — Collection)

```bash
# Launch all 3 collection layers in parallel:
Task: "Write collector.py"        # T013 (Layer A+D)
Task: "Write github_radar.py"     # T014 (Layer B)
Task: "Write hf_radar.py"         # T015 (Layer C)

# Then sequentially:
Task: "Entity resolution"         # T016 (depends on all 3 above)
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only)

1. Complete Phase 1: Setup (T001–T006)
2. Complete Phase 2: Foundational API Clients (T007–T012)
3. Complete Phase 3: US1 Collection (T013–T016)
4. Complete Phase 4: US2 Classification (T017–T020)
5. Complete Phase 5: US3 Publishing (T021–T023)
6. **STOP and VALIDATE**: Run with `DRY_RUN=true`, verify end-to-end pipeline
7. Run live, check Notion databases

### Incremental Delivery

1. Setup + Foundational → API clients ready
2. Add US1 → Test collection with DRY_RUN (MVP foundation)
3. Add US2 → Test classification and scoring
4. Add US3 → Test publishing to Notion → **Core MVP complete**
5. Add US4 → Daily brief generated
6. Add US5 → Setup script for fresh deployments
7. Add US6 → Smoke tests for CI confidence
8. Integration → main.py + GitHub Actions → **Production ready**
9. Polish → README → **Fully documented**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are relative to `ai_radar/` project root
- Total: 31 tasks across 10 phases
