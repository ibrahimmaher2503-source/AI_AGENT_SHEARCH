# Research: AI Radar — Automated Daily Intelligence System

**Date**: 2026-03-15
**Feature**: `001-ai-radar-system`

## R1: Tavily Search API — Best Approach for Web Signal Collection

**Decision**: Use Tavily REST API (`POST https://api.tavily.com/search`) with `api_key` in the request body, `max_results=5` per query, and `search_depth="basic"` for speed.

**Rationale**: Tavily provides structured search results with titles, URLs, content snippets, and relevance scores — exactly what the collector needs. The REST API requires only `requests`. Rate limits are generous for 15 queries per run.

**Alternatives considered**:
- Direct web scraping of blog pages: Rejected — fragile, requires HTML parsing libraries (BeautifulSoup/lxml), violates `requests`-only constraint
- Google Custom Search API: Rejected — 100 queries/day free limit is tight, requires separate API key management
- SerpAPI: Rejected — adds SDK dependency, pricing is less predictable

## R2: Gemini 2.0 Flash — JSON Classification Strategy

**Decision**: Use Gemini 2.0 Flash via REST (`POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`) with API key as query parameter. Send batches of max 10 items. Use temperature 0.3 for classification (deterministic), 0.5 for brief writing (creative). Parse JSON from response text with cleanup (strip markdown fences) and one retry on parse failure.

**Rationale**: Gemini 2.0 Flash is fast, cheap, and handles structured JSON output well. Batching 10 items reduces API calls from ~70 to ~7. The cleanup-and-retry pattern handles the most common failure mode (markdown code fences around JSON).

**Alternatives considered**:
- GPT-4o via OpenAI API: Rejected — more expensive, adds another API key, not specified in requirements
- Claude API: Rejected — same reasons; Gemini is explicitly required
- Single-item classification: Rejected — 70+ API calls instead of 7; slower and more expensive

## R3: Notion API — Database Operations and Duplicate Protection

**Decision**: Use Notion API v2022-06-28 via REST. For duplicate checks: query the database with a filter on the URL/title/field property, check if results are non-empty. For page creation: POST to `/v1/pages` with properties dict and optional children blocks. Rate limit: 3 requests/second with `time.sleep(0.3)` between writes; retry once on 429 after 2-second wait.

**Rationale**: Notion's filter API allows efficient duplicate checking without downloading entire databases. The 2022-06-28 version is stable and well-documented. The 3 req/s rate is within Notion's published limits.

**Alternatives considered**:
- `notion-client` Python SDK: Rejected — violates `requests`-only constraint
- Local cache/file-based dedup: Rejected — not persistent across GitHub Actions runs; Notion is the source of truth
- Batch API: Rejected — Notion doesn't have a true batch create endpoint

## R4: GitHub REST API — Rate Limiting Strategy

**Decision**: Use GitHub REST API v3. With token: `Authorization: Bearer {token}` header, 5000 req/hr, `time.sleep(0.3)` between calls. Without token: 60 req/hr, `time.sleep(2)` between calls. For search: `GET /search/repositories` with query string. For orgs: `GET /orgs/{org}/repos?sort=pushed&per_page=5`. For releases: `GET /repos/{owner}/{repo}/releases/latest`.

**Rationale**: The public API works without auth for basic discovery. With a token (GitHub Actions provides `GITHUB_TOKEN` automatically), rate limits are 83x higher. The sleep-based throttling is simple and predictable.

**Alternatives considered**:
- GitHub GraphQL API: Rejected — more complex queries for same data; REST is simpler and sufficient
- PyGithub SDK: Rejected — violates `requests`-only constraint
- Web scraping GitHub trending: Rejected — fragile, no API stability guarantees

## R5: Hugging Face Hub API — Model Discovery

**Decision**: Use HF Hub REST API (`GET https://huggingface.co/api/models`) with query parameters: `sort=lastModified` or `sort=downloads`, `direction=-1`, `limit=20`, `pipeline_tag={task}`. No authentication required for public models. Filter by `lastModified` date client-side to keep only recent models.

**Rationale**: The HF API is free, unauthenticated, and returns structured model metadata including downloads, likes, tags, and license. Client-side date filtering is simpler than building complex API filters.

**Alternatives considered**:
- `huggingface_hub` Python SDK: Rejected — violates `requests`-only constraint
- Web scraping HF pages: Rejected — fragile, unnecessary when API exists
- HF Datasets API: Rejected — models are the focus, not datasets

## R6: Entity Resolution — Deduplication Strategy

**Decision**: Three-stage deduplication: (1) exact URL match, (2) normalized URL match (strip trailing slash, remove utm_*/ref/source query params), (3) title similarity (5+ consecutive shared words). When merging: keep the item with highest source_priority + raw_score as primary; collect all other URLs into `secondary_sources` list. Run entity resolution BEFORE Gemini classification to avoid paying for duplicate analysis.

**Rationale**: URL-based dedup catches most duplicates (same article shared across aggregators). Normalized URL catches tracking-parameter variants. Title similarity catches different articles about the same event. The 5-word threshold balances precision (avoids false matches) with recall (catches most real duplicates).

**Alternatives considered**:
- Embedding-based similarity: Rejected — requires vector library, violates constraints
- Fuzzy string matching (Levenshtein): Rejected — requires `fuzzywuzzy`/`rapidfuzz` library
- LLM-based dedup: Rejected — expensive, slow, and entity resolution should reduce items before LLM calls

## R7: Arabic Explanation — Egyptian Dialect Format

**Decision**: 4-field structured format in Egyptian Arabic dialect: `ايه_دي` (what is it), `هستفيد_منها_ازاي` (how to benefit), `تستحق_وقتك` (worth your time?), `مشابه_لـ` (similar to). Format with emoji prefixes for Notion readability. Generated by Gemini as part of the classification prompt.

**Rationale**: Egyptian Arabic is Ibrahim's native dialect and the most widely understood Arabic dialect. The 4-field structure provides consistent, scannable intelligence. Including it in the classification prompt avoids a separate LLM call.

**Alternatives considered**:
- Separate Arabic generation pass: Rejected — doubles LLM costs for marginal quality improvement
- Modern Standard Arabic: Rejected — less natural for quick daily scanning; Egyptian dialect is more practical
- Free-form Arabic text: Rejected — inconsistent structure makes scanning harder

## R8: Notion Rich Text — 2000 Character Limit

**Decision**: Notion rich text blocks have a 2000-character limit per block. Implement `chunk_rich_text()` in utils.py to split long text into multiple blocks at sentence boundaries. For Arabic explanations, the 4-field format naturally stays under 2000 chars. For brief sections, split at paragraph boundaries.

**Rationale**: Notion's API rejects rich text content exceeding 2000 characters. Proactive chunking prevents silent data loss.

**Alternatives considered**:
- Truncation: Rejected — loses important content
- Multiple properties: Rejected — clutters the database schema
- External storage (file URLs): Rejected — adds complexity, violates self-contained principle
