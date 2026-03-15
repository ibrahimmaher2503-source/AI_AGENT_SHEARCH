# :brain: AI Radar — Automated Daily AI Intelligence System

AI Radar is a fully automated pipeline that collects AI signals from 4 discovery layers, deduplicates them through 3-stage entity resolution, classifies and scores each signal via Gemini, assigns priority alerts (P1/P2/P3), publishes results to 9 Notion databases, and generates a daily intelligence brief. The entire pipeline runs unattended via GitHub Actions every day at 8 AM Cairo time (6 AM UTC).

---

## 4-Layer Architecture

```
Layer A — Official Sources (company blogs via Tavily)
Layer B — GitHub Radar (repos, releases, org watchlist)
Layer C — HF Radar (new/trending models)
Layer D — Curated Web (Tavily search + newsletters)
            |
    Entity Resolution (3-stage dedup)
            |
    Gemini Classification + Scoring
            |
    Alert Assignment (P1/P2/P3)
            |
    9 Notion Databases + Daily Brief
```

**Layer A** queries Tavily for official company blogs (OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, Hugging Face, Microsoft).

**Layer B** monitors 12 GitHub organizations for new repos and releases, plus runs 7 search queries for trending AI repos.

**Layer C** polls the Hugging Face Hub API for new and trending models across 6 task categories (text-generation, image-to-text, text-to-image, ASR, TTS, image-classification).

**Layer D** runs 15 Tavily web search queries covering model releases, tool launches, research papers, startup funding, and developer-focused AI news.

---

## 9 Notion Databases

| Emoji | Database | Description |
|-------|----------|-------------|
| :robot: | **AI Models** | New model releases with company, type, pricing, capabilities, and relevance scores |
| :hammer_and_wrench: | **AI Tools** | AI tools and products with category, pricing, marketing use case, and star rating |
| :page_facing_up: | **AI Research** | Research papers with institution, key findings, practical applications |
| :satellite: | **AI Signals** | Raw signals from all sources — funding rounds, acquisitions, trends, launches |
| :bulb: | **Opportunities** | Actionable business opportunities triggered by discovered signals |
| :newspaper: | **Daily Briefs** | Daily AI intelligence summary with executive summary, highlights, and action items |
| :telescope: | **Open Source Radar** | Trending GitHub repos with stars, forks, language, topics, and release status |
| :hugs: | **HF Models Radar** | Hugging Face models with downloads, likes, license, pipeline tag |
| :rotating_light: | **Alerts** | Priority alerts (P1/P2) requiring immediate attention |

---

## Radar Score Formula

Each signal receives a **Radar Score** (0-100) calculated as a weighted sum of five dimensions scored by Gemini:

```
Radar Score = (Novelty x 0.30)
            + (Credibility x 0.25)
            + (Execution Value x 0.20)
            + (Dev Value x 0.15)
            + (Agency Value x 0.10)
```

| Weight | Dimension | What it measures |
|--------|-----------|-----------------|
| 30% | Novelty | How new/unique is this compared to existing solutions |
| 25% | Credibility | Source reliability and evidence quality |
| 20% | Execution Value | Practical usefulness for immediate implementation |
| 15% | Dev Value | Relevance for developers (APIs, SDKs, frameworks) |
| 10% | Agency Value | Relevance for marketing agencies and business operations |

The score maps to a star rating: 80+ = 5 stars, 60-79 = 4 stars, 40-59 = 3 stars, 20-39 = 2 stars, below 20 = 1 star.

---

## Alert System

Alerts are assigned based on Radar Score and source priority:

| Level | Condition | Action |
|-------|-----------|--------|
| **P1** | Score >= 80, OR source_priority == "high" AND score >= 70 | Immediate review required |
| **P2** | Score >= 55 | Review within 24 hours |
| **P3** | Score >= 30 | Informational, review when convenient |
| **None** | Score < 30 | No alert, logged to database only |

P1 and P2 alerts are written to the Alerts database with status "New" for tracking.

---

## Entity Resolution

Signals from all 4 layers are deduplicated through a 3-stage entity resolution pipeline before classification:

1. **Exact URL match** — Groups signals sharing the identical URL. Keeps the one with the highest source priority and raw score.
2. **Normalized URL match** — Strips tracking parameters (`utm_*`, `ref`, `source`), removes trailing slashes, and merges signals that resolve to the same canonical URL.
3. **Title similarity** — Uses a sliding-window 5-gram comparison. If two titles share 5 or more consecutive words, they are merged as duplicates.

At each stage, the "winner" retains a list of `secondary_sources` for audit.

---

## File Structure

```
ai_radar/
├── .github/
│   └── workflows/
│       └── daily_hub.yml          # GitHub Actions workflow — daily cron at 6 AM UTC
├── agents/
│   ├── __init__.py                # Package init for agents module
│   ├── collector.py               # Layer A+D: Tavily web search collector
│   ├── github_radar.py            # Layer B: GitHub org monitoring + repo search
│   ├── hf_radar.py                # Layer C: Hugging Face Hub new/trending models
│   ├── analyzer.py                # Entity resolution, Gemini classification, scoring, routing
│   ├── publisher.py               # Writes classified items to all 9 Notion databases
│   └── brief_writer.py            # Generates daily AI brief via Gemini and publishes to Notion
├── config.py                      # Environment variable loader and validator
├── gemini_client.py               # Gemini API wrapper (generate_json with retry)
├── github_client.py               # GitHub API wrapper (search repos, list org repos, releases)
├── hf_client.py                   # Hugging Face Hub API wrapper (list models by task)
├── main.py                        # Pipeline entry point — orchestrates all layers
├── notion_client.py               # Notion API wrapper (create page, query DB, dedup checks)
├── prompts.py                     # Gemini prompt templates (classification, brief generation)
├── requirements.txt               # Python dependencies (requests)
├── setup_notion.py                # One-time script to create all 9 Notion databases
├── smoke_test.py                  # Validation script for imports, env vars, and utility functions
├── sources.py                     # Source URLs, GitHub orgs, search queries, HF tasks
├── utils.py                       # Utility functions (scoring, dedup, Notion helpers, formatting)
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

**Total: 22 files** (including workflow, init, gitignore, and README).

---

## API Keys Required

| Key | Where to get it | Required |
|-----|----------------|----------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | **Yes** |
| `NOTION_API_KEY` | [Notion Integrations](https://www.notion.so/my-integrations) | **Yes** |
| `TAVILY_API_KEY` | [Tavily.com](https://tavily.com/) | **Yes** |
| `GITHUB_TOKEN` | [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) | Optional (increases rate limit from 60 to 5000 req/hr) |

You also need `NOTION_PARENT_PAGE_ID` — the ID of the Notion page where databases will be created. Get it from the page URL: `https://notion.so/Your-Page-{page_id}`.

---

## Step-by-Step Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-radar.git
cd ai-radar/ai_radar
```

### 2. Install dependencies

```bash
pip install requests
```

That is the only external dependency. Everything else uses Python standard library.

### 3. Set environment variables

Create a `.env` file or export directly:

```bash
export GEMINI_API_KEY="your-gemini-key"
export NOTION_API_KEY="secret_your-notion-key"
export TAVILY_API_KEY="tvly-your-tavily-key"
export NOTION_PARENT_PAGE_ID="your-notion-page-id"
export GITHUB_TOKEN="ghp_your-github-token"  # optional
```

### 4. Run setup_notion.py to create databases

```bash
python setup_notion.py
```

This creates all 9 Notion databases under your parent page and prints their IDs. If a database already exists (matching title), it skips creation and returns the existing ID.

### 5. Copy database IDs to your environment

The setup script outputs lines like:

```
NOTION_DB_MODELS=abc123...
NOTION_DB_TOOLS=def456...
```

Add all 9 database IDs to your environment variables:

```bash
export NOTION_DB_MODELS="abc123"
export NOTION_DB_TOOLS="def456"
export NOTION_DB_RESEARCH="..."
export NOTION_DB_SIGNALS="..."
export NOTION_DB_OPPORTUNITIES="..."
export NOTION_DB_BRIEFS="..."
export NOTION_DB_OSS_RADAR="..."
export NOTION_DB_HF_RADAR="..."
export NOTION_DB_ALERTS="..."
```

### 6. Run the smoke test

```bash
python smoke_test.py
```

Validates that all imports work, all environment variables are set, and utility functions return expected values.

### 7. Test with DRY_RUN

```bash
DRY_RUN=true python main.py
```

Runs the full pipeline but skips writing to Notion. Useful for verifying API connectivity and classification output.

### 8. Run live

```bash
python main.py
```

Executes the full pipeline: collect from all 4 layers, deduplicate, classify via Gemini, score, publish to 9 databases, and generate the daily brief.

### 9. Push to GitHub for automation

Add all environment variables as GitHub repository secrets under **Settings > Secrets and variables > Actions**. The workflow at `.github/workflows/daily_hub.yml` runs automatically every day at 6 AM UTC (8 AM Cairo time).

Required secrets:
- `GEMINI_API_KEY`
- `NOTION_API_KEY`
- `TAVILY_API_KEY`
- `GITHUB_TOKEN`
- `NOTION_PARENT_PAGE_ID`
- `NOTION_DB_MODELS`, `NOTION_DB_TOOLS`, `NOTION_DB_RESEARCH`, `NOTION_DB_SIGNALS`
- `NOTION_DB_OPPORTUNITIES`, `NOTION_DB_BRIEFS`, `NOTION_DB_OSS_RADAR`, `NOTION_DB_HF_RADAR`, `NOTION_DB_ALERTS`

---

## How to Run Locally

### Full live run

```bash
export GEMINI_API_KEY="..." NOTION_API_KEY="..." TAVILY_API_KEY="..."
export NOTION_DB_MODELS="..." NOTION_DB_TOOLS="..." NOTION_DB_RESEARCH="..."
export NOTION_DB_SIGNALS="..." NOTION_DB_OPPORTUNITIES="..." NOTION_DB_BRIEFS="..."
export NOTION_DB_OSS_RADAR="..." NOTION_DB_HF_RADAR="..." NOTION_DB_ALERTS="..."
export NOTION_PARENT_PAGE_ID="..."

cd ai_radar
python main.py
```

### DRY_RUN mode (no Notion writes)

```bash
DRY_RUN=true python main.py
```

In DRY_RUN mode, the pipeline collects, deduplicates, classifies, and scores all signals, but skips publishing to Notion. All output is printed to stdout so you can verify the results.

### Trigger manually on GitHub

Go to **Actions > AI Radar -- Daily Run > Run workflow** and click the button. The workflow supports `workflow_dispatch` for on-demand runs.

---

## Recommended Notion Views

### AI Models

| View Name | Type | Configuration |
|-----------|------|---------------|
| P1 Models Today | Table | Filter: Alert Level = P1, Added Date = Today |
| Top Scored This Week | Table | Filter: Added Date is within past week. Sort: Radar Score descending |
| By Company | Board | Group by: Company |
| TremoAI Relevant | Table | Filter: TremoAI Relevant = checked |

### AI Tools

| View Name | Type | Configuration |
|-----------|------|---------------|
| New Tools Today | Gallery | Filter: Added Date = Today. Sort: Radar Score descending |
| Marketing Tools | Table | Filter: Marketing Use Case is not "None" |
| Not Yet Tried | Table | Filter: Tried = unchecked, Radar Score >= 60 |
| By Category | Board | Group by: Category |

### AI Research

| View Name | Type | Configuration |
|-----------|------|---------------|
| High Impact Papers | Table | Filter: Radar Score >= 70. Sort: Published Date descending |
| By Institution | Board | Group by: Institution |

### AI Signals

| View Name | Type | Configuration |
|-----------|------|---------------|
| Unprocessed | Table | Filter: Processed = unchecked. Sort: Radar Score descending |
| Today's Signals | Table | Filter: Added Date = Today |
| By Type | Board | Group by: Type |

### Opportunities

| View Name | Type | Configuration |
|-----------|------|---------------|
| New Opportunities | Table | Filter: Status = "New". Sort: Potential Impact ascending (High first) |
| By Target | Board | Group by: Target |
| Active | Table | Filter: Status = "In Progress" or "Exploring" |

### Daily Briefs

| View Name | Type | Configuration |
|-----------|------|---------------|
| Latest Briefs | Table | Sort: Brief Date descending |
| Timeline | Timeline | Date property: Brief Date |

### Open Source Radar

| View Name | Type | Configuration |
|-----------|------|---------------|
| Hot Repos | Table | Filter: Stars >= 100. Sort: Radar Score descending |
| By Language | Board | Group by: Language |
| Recent Releases | Table | Filter: Has Release = checked. Sort: Last Push descending |

### HF Models Radar

| View Name | Type | Configuration |
|-----------|------|---------------|
| Trending Models | Table | Sort: Downloads descending |
| By Task | Board | Group by: Task |
| High Scored | Table | Filter: Radar Score >= 70. Sort: Likes descending |

### Alerts

| View Name | Type | Configuration |
|-----------|------|---------------|
| P1 Alerts (Active) | Table | Filter: Level = P1, Status = "New". Sort: Radar Score descending |
| All Active | Table | Filter: Status = "New". Sort: Level ascending (P1 first) |
| Reviewed | Table | Filter: Status = "Reviewed" |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Missing required: GEMINI_API_KEY` | Environment variable not set | Export all required env vars before running |
| `403` from Notion API | Integration not connected to parent page | Open the parent page in Notion > "..." > Connections > Add your integration |
| `429 Too Many Requests` from Gemini | Rate limit exceeded | The pipeline has built-in `time.sleep()` between batches; if it still hits limits, increase the sleep in `analyzer.py` |
| `401` from GitHub API | Invalid or expired token | Generate a new personal access token at github.com/settings/tokens |
| Duplicate entries in Notion | First run after schema change | The publisher checks for existing URLs/titles before inserting; duplicates usually mean the dedup query failed — verify DB IDs are correct |
| `smoke_test.py` fails on imports | Running from wrong directory | `cd ai_radar` before running, or use `python ai_radar/smoke_test.py` |
| Gemini returns non-list response | Prompt too long or malformed JSON | Reduce batch size in `analyzer.py` (default is 10); check `prompts.py` for format issues |
| `setup_notion.py` skips all databases | Databases already exist with same titles | This is expected behavior; it returns existing IDs instead of creating duplicates |
| GitHub Actions workflow not triggering | Cron schedule inactive on fork | Push a commit to the default branch, or trigger manually via `workflow_dispatch` |
| Empty daily brief | No signals collected | Check that `TAVILY_API_KEY` is valid and has remaining credits |

---

## Maintenance Tips

- **Update Tavily search queries monthly** — Edit `TAVILY_QUERIES` in `sources.py` to reflect current AI trends and terminology. Remove outdated year references.
- **Review the GitHub org watchlist** — Add new AI organizations to `GITHUB_ORGS` in `sources.py` as they emerge. Remove orgs that are no longer active.
- **Update GitHub search queries** — Adjust date filters in `GITHUB_SEARCH_QUERIES` to match the current month/year.
- **Check API rate limits** — Tavily has a monthly quota. Gemini has per-minute limits. Monitor usage if running multiple times per day.
- **Review Notion database schemas** — If you add new select options in the code (e.g., new company names), update the corresponding database schema in Notion or re-run `setup_notion.py`.
- **Clean up old signals** — Periodically archive signals older than 30 days in Notion to keep databases fast.
- **Monitor workflow runs** — Check the Actions tab on GitHub weekly. Failed runs usually indicate expired API keys or rate limit issues.
- **Update HF task categories** — Add new Hugging Face pipeline tags to `HF_TASKS` in `sources.py` as new model types emerge.
