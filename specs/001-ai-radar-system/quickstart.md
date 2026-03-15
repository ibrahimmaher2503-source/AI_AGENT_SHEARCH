# Quickstart: AI Radar

## Prerequisites

- Python 3.11+
- API keys: Gemini, Notion, Tavily (required); GitHub token (optional)
- A Notion workspace with an integration and a parent page

## 1. Clone and Install

```bash
git clone <repo-url>
cd ai_radar
pip install requests
```

## 2. Set Up Notion Databases

```bash
export NOTION_API_KEY="your-notion-api-key"
export NOTION_PARENT_PAGE_ID="your-parent-page-id"
python setup_notion.py
```

Copy the 9 printed database IDs into your environment (or GitHub Secrets).

## 3. Configure Environment Variables

```bash
export GEMINI_API_KEY="your-gemini-key"
export NOTION_API_KEY="your-notion-key"
export TAVILY_API_KEY="your-tavily-key"
export GITHUB_TOKEN="your-github-token"  # optional

export NOTION_DB_MODELS="..."
export NOTION_DB_TOOLS="..."
export NOTION_DB_RESEARCH="..."
export NOTION_DB_SIGNALS="..."
export NOTION_DB_OPPORTUNITIES="..."
export NOTION_DB_BRIEFS="..."
export NOTION_DB_OSS_RADAR="..."
export NOTION_DB_HF_RADAR="..."
export NOTION_DB_ALERTS="..."
export NOTION_PARENT_PAGE_ID="..."
```

## 4. Run Smoke Test

```bash
python smoke_test.py
```

All checks should show PASS. Warnings about missing optional env vars are OK.

## 5. Dry Run (Safe — No Notion Writes)

```bash
export DRY_RUN=true
python main.py
```

Verify:
- Signals collected from all 4 layers
- Entity resolution reduces count
- Classification and scoring complete
- Notion payloads printed (not written)

## 6. Live Run

```bash
export DRY_RUN=false
python main.py
```

Check your Notion databases — records should appear with scores, alerts, and Arabic explanations.

## 7. Deploy to GitHub Actions

1. Push code to GitHub
2. Add all environment variables as repository secrets
3. The workflow runs daily at 8 AM Cairo time (6 AM UTC)
4. Manual trigger available via `workflow_dispatch`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing required: GEMINI_API_KEY` | Set the environment variable |
| `[GEMINI] JSON parse failed` | Normal — retries automatically; check Gemini API status if persistent |
| `[NOTION] 429 received` | Rate limiting — built-in retry handles this |
| `[GITHUB] Rate limit` | Add GITHUB_TOKEN for 5000 req/hr instead of 60 |
| Pipeline completes with 0 items | Check API keys and network; each layer logs failures independently |
