# AI Radar — Automated Daily AI Intelligence Pipeline

AI Radar is a fully automated system that collects AI signals from 4 discovery layers, deduplicates them through 3-stage entity resolution, classifies and scores each signal via Gemini 2.0 Flash, assigns priority alerts (P1/P2/P3), publishes results to 9 Notion databases, and generates a daily intelligence brief — all running unattended via GitHub Actions at 8 AM Cairo time.

---

## How It Works

```
Layer A — Official Sources (company blogs via Tavily)
Layer B — GitHub Radar (repos, releases, org watchlist)
Layer C — HF Radar (new/trending models from Hugging Face)
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

**Layer A** — queries Tavily for official blogs from OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, Hugging Face, Microsoft.

**Layer B** — monitors 12 GitHub organizations for new repos and releases, plus 7 trending AI search queries.

**Layer C** — polls Hugging Face Hub API for new and trending models across 6 task categories (text-generation, image-to-text, text-to-image, ASR, TTS, image-classification).

**Layer D** — runs 15 Tavily web search queries covering model releases, tool launches, research papers, startup funding, and developer AI news.

---

## 9 Notion Databases

| Database | What it tracks |
|----------|---------------|
| **AI Models** | New model releases — company, type, pricing, capabilities, scores |
| **AI Tools** | AI tools & products — category, pricing, marketing use case, star rating |
| **AI Research** | Papers — institution, key findings, practical applications |
| **AI Signals** | Raw signals from all sources — funding, acquisitions, trends, launches |
| **Opportunities** | Actionable business opportunities triggered by signals |
| **Daily Briefs** | Daily AI intelligence summary with highlights and action items |
| **Open Source Radar** | Trending GitHub repos — stars, forks, language, topics |
| **HF Models Radar** | Hugging Face models — downloads, likes, license, pipeline tag |
| **Alerts** | P1/P2 priority alerts requiring attention |

---

## Radar Score

Each signal receives a composite score (0-100):

```
Score = Novelty(30%) + Credibility(25%) + Execution(20%) + Dev Value(15%) + Agency Value(10%)
```

Scored by Gemini 2.0 Flash. Maps to star rating: 80+ = 5 stars, 60-79 = 4 stars, etc.

---

## Alert Levels

| Level | Condition | Action |
|-------|-----------|--------|
| **P1** | Score >= 80, or high priority + score >= 70 | Immediate review |
| **P2** | Score >= 55 | Review within 24h |
| **P3** | Score >= 30 | Informational |
| None | Score < 30 | Logged only |

---

## Entity Resolution (Dedup)

3-stage pipeline before classification:

1. **Exact URL** — identical URLs grouped, highest priority wins
2. **Normalized URL** — strips `utm_*`, `ref`, `source` params, removes trailing slashes
3. **Title similarity** — 5-gram sliding window, 5+ consecutive shared words = duplicate

---

## Project Structure

```
.github/workflows/daily_hub.yml      # Cron: 6 AM UTC daily (at repo root)
ai_radar/
  agents/
    __init__.py
    collector.py                      # Layer A+D: Tavily web search
    github_radar.py                   # Layer B: GitHub orgs + search
    hf_radar.py                       # Layer C: HF Hub models
    analyzer.py                       # Entity resolution + Gemini classify + score
    publisher.py                      # Publish to 9 Notion databases
    brief_writer.py                   # Generate daily brief via Gemini
  config.py                           # Env var loader + validation
  gemini_client.py                    # Gemini API wrapper (JSON mode + retry)
  github_client.py                    # GitHub API wrapper
  hf_client.py                        # Hugging Face Hub API wrapper
  notion_client.py                    # Notion API wrapper (create, query, dedup)
  tavily_client.py                    # Tavily search wrapper
  main.py                             # Pipeline entry point
  prompts.py                          # Gemini prompt templates
  setup_notion.py                     # One-time: create all 9 databases
  smoke_test.py                       # Validation script
  sources.py                          # URLs, orgs, queries, HF tasks
  utils.py                            # Scoring, normalization, formatting
  requirements.txt                    # Only: requests
```

---

## Quick Start

### 1. Install

```bash
cd ai_radar
pip install -r requirements.txt
```

That's the only dependency. Everything else uses Python 3.11+ standard library.

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY="your-gemini-key"
export NOTION_API_KEY="your-notion-key"
export TAVILY_API_KEY="your-tavily-key"
export NOTION_PARENT_PAGE_ID="your-notion-page-id"
export GITHUB_TOKEN="ghp_your-token"  # optional, increases rate limit
```

**Where to get keys:**

| Key | Source |
|-----|--------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `NOTION_API_KEY` | [Notion Integrations](https://www.notion.so/my-integrations) |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com/) |
| `NOTION_PARENT_PAGE_ID` | From Notion page URL: `notion.so/Page-Name-{id}` |
| `GITHUB_TOKEN` | [GitHub Tokens](https://github.com/settings/tokens) (optional) |

### 3. Create Notion Databases

```bash
cd ai_radar
python setup_notion.py
```

This creates all 9 databases under your parent page. Copy the printed IDs:

```bash
export NOTION_DB_MODELS="..."
export NOTION_DB_TOOLS="..."
export NOTION_DB_RESEARCH="..."
export NOTION_DB_SIGNALS="..."
export NOTION_DB_OPPORTUNITIES="..."
export NOTION_DB_BRIEFS="..."
export NOTION_DB_OSS_RADAR="..."
export NOTION_DB_HF_RADAR="..."
export NOTION_DB_ALERTS="..."
```

### 4. Run Smoke Test

```bash
python smoke_test.py
```

### 5. Test with DRY_RUN (No Notion Writes)

```bash
DRY_RUN=true python main.py
```

Runs the full pipeline but skips writing to Notion — prints all payloads to stdout instead.

### 6. Run Live

```bash
python main.py
```

Collects from all 4 layers, deduplicates, classifies via Gemini, scores, publishes to 9 databases, and generates the daily brief.

---

## GitHub Actions (Automated Daily Run)

The workflow at `.github/workflows/daily_hub.yml` runs every day at **6 AM UTC (8 AM Cairo)**.

### Setup

Add these as **repository secrets** (Settings > Secrets > Actions):

- `GEMINI_API_KEY`
- `NOTION_API_KEY`
- `TAVILY_API_KEY`
- `GITHUB_TOKEN`
- `NOTION_PARENT_PAGE_ID`
- `NOTION_DB_MODELS`, `NOTION_DB_TOOLS`, `NOTION_DB_RESEARCH`, `NOTION_DB_SIGNALS`
- `NOTION_DB_OPPORTUNITIES`, `NOTION_DB_BRIEFS`, `NOTION_DB_OSS_RADAR`, `NOTION_DB_HF_RADAR`, `NOTION_DB_ALERTS`

### Manual Trigger

Go to **Actions > AI Radar Daily Run > Run workflow** — supports `workflow_dispatch`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing required: GEMINI_API_KEY` | Export all required env vars |
| `403` from Notion | Connect integration to your parent page in Notion |
| `429` from Gemini | Built-in rate limiting handles this; increase sleep in `analyzer.py` if needed |
| `401` from GitHub | Regenerate personal access token |
| Duplicate entries | Verify NOTION_DB_* IDs are correct |
| Smoke test import fail | Run from `ai_radar/` directory |
| Empty brief | Check TAVILY_API_KEY has remaining credits |

---

## Tech Stack

- **Python 3.11+** — single language, no frameworks
- **requests** — sole pip dependency
- **Gemini 2.0 Flash** — classification, scoring, brief generation
- **Tavily API** — web search for Layers A and D
- **GitHub API** — repo discovery for Layer B
- **Hugging Face Hub API** — model discovery for Layer C
- **Notion API** — 9 databases for storage and visualization
- **GitHub Actions** — daily cron automation

---

## License

Private project.
