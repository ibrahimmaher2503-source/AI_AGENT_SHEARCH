"""
One-time setup script that creates all 9 Notion databases with correct schemas.
Run once to bootstrap the Notion workspace, then copy the printed DB IDs
into your GitHub Secrets / .env file.

Usage:
    NOTION_API_KEY=secret_xxx NOTION_PARENT_PAGE_ID=abc123 python setup_notion.py
"""

import sys
import os
import requests
import time

# No config import - only needs env vars
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")
NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers():
    """Return standard Notion API headers."""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _select(options):
    """Build a select property schema."""
    return {"select": {"options": [{"name": o} for o in options]}}


def _multi_select(options):
    """Build a multi_select property schema."""
    return {"multi_select": {"options": [{"name": o} for o in options]}}


def _db_exists(title):
    """Check if a database with this title already exists. Returns its ID or empty string."""
    url = f"{NOTION_BASE}/search"
    payload = {"query": title, "filter": {"property": "object", "value": "database"}}
    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for r in results:
                db_title = ""
                for t in r.get("title", []):
                    db_title += t.get("plain_text", "")
                if db_title == title:
                    return r.get("id", "")
        return ""
    except Exception:
        return ""


def _create_database(title, icon_emoji, properties):
    """Create a Notion database under the parent page. Skips if it already exists."""
    existing_id = _db_exists(title)
    if existing_id:
        print(f"[SETUP] Skipped (exists): {title} -> {existing_id}")
        return existing_id

    url = f"{NOTION_BASE}/databases"
    payload = {
        "parent": {"type": "page_id", "page_id": NOTION_PARENT_PAGE_ID},
        "icon": {"type": "emoji", "emoji": icon_emoji},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": properties,
    }
    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
        if resp.status_code == 200:
            db_id = resp.json().get("id", "")
            print(f"[SETUP] Created: {title} -> {db_id}")
            return db_id
        else:
            print(f"[SETUP] Error creating {title}: {resp.status_code} {resp.text[:200]}")
            return ""
    except Exception as e:
        print(f"[SETUP] Failed to create {title}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Database schemas
# ---------------------------------------------------------------------------

MODELS_SCHEMA = {
    "Name": {"title": {}},
    "Company": _select(["OpenAI", "Anthropic", "Google", "Meta", "Mistral", "Other"]),
    "Model Type": _select(["LLM", "Image", "Video", "Audio", "Multimodal", "Code", "Other"]),
    "Release Date": {"date": {}},
    "Key Capabilities": {"rich_text": {}},
    "Context Window": {"rich_text": {}},
    "Pricing": _select(["Free", "Freemium", "Paid", "API Only"]),
    "Radar Score": {"number": {"format": "number"}},
    "Importance Score": {"number": {"format": "number"}},
    "Marketing Relevance": _select(["High", "Medium", "Low"]),
    "Dev Relevance": _select(["High", "Medium", "Low"]),
    "TremoAI Relevant": {"checkbox": {}},
    "Alert Level": _select(["P1", "P2", "P3", "None"]),
    "Arabic Explanation": {"rich_text": {}},
    "Source URL": {"url": {}},
    "Added Date": {"date": {}},
    "Notes": {"rich_text": {}},
}

TOOLS_SCHEMA = {
    "Name": {"title": {}},
    "URL": {"url": {}},
    "Category": _select([
        "Coding", "Image", "Video", "Writing", "SEO",
        "Ads", "Analytics", "Automation", "Research", "Other",
    ]),
    "Description": {"rich_text": {}},
    "Pricing": _select(["Free", "Freemium", "Paid"]),
    "Tags": _multi_select([
        "Open Source", "Has API", "Laravel Package", "Flutter Package",
        "Mobile App", "Arabic Support", "Free Tier",
    ]),
    "Radar Score": {"number": {"format": "number"}},
    "Popularity Score": {"number": {"format": "number"}},
    "Rating": _select(["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]),
    "Marketing Use Case": _select([
        "Ads", "Copy", "Video", "SEO", "Analytics", "Social", "None",
    ]),
    "Has API": {"checkbox": {}},
    "Laravel Package URL": {"url": {}},
    "Flutter Package URL": {"url": {}},
    "TremoAI Relevant": {"checkbox": {}},
    "Alert Level": _select(["P1", "P2", "P3", "None"]),
    "Arabic Explanation": {"rich_text": {}},
    "Tried": {"checkbox": {}},
    "Added Date": {"date": {}},
    "Notes": {"rich_text": {}},
}

RESEARCH_SCHEMA = {
    "Title": {"title": {}},
    "Authors": {"rich_text": {}},
    "Institution": _select([
        "OpenAI", "Google", "Meta", "Stanford", "MIT", "DeepMind", "Academic", "Other",
    ]),
    "Published Date": {"date": {}},
    "Abstract Summary": {"rich_text": {}},
    "Key Findings": {"rich_text": {}},
    "Practical Applications": {"rich_text": {}},
    "Radar Score": {"number": {"format": "number"}},
    "Importance Score": {"number": {"format": "number"}},
    "Dev Relevance": _select(["High", "Medium", "Low"]),
    "Marketing Relevance": _select(["High", "Medium", "Low"]),
    "TremoAI Relevant": {"checkbox": {}},
    "Source URL": {"url": {}},
    "Added Date": {"date": {}},
}

SIGNALS_SCHEMA = {
    "Title": {"title": {}},
    "Source": _select([
        "Twitter/X", "Reddit", "HackerNews", "ProductHunt", "GitHub",
        "HuggingFace", "Newsletter", "Blog", "News", "Other",
    ]),
    "Type": _select([
        "Model Release", "Tool Launch", "Funding", "Acquisition",
        "Research", "Open Source", "Trend", "Other",
    ]),
    "Published At": {"date": {}},
    "Summary": {"rich_text": {}},
    "Radar Score": {"number": {"format": "number"}},
    "Importance Score": {"number": {"format": "number"}},
    "Processed": {"checkbox": {}},
    "URL": {"url": {}},
    "Added Date": {"date": {}},
}

OPPORTUNITIES_SCHEMA = {
    "Opportunity Title": {"title": {}},
    "Type": _select([
        "SaaS Idea", "Marketing Service", "Dev Tool", "Automation",
        "Content Strategy", "Partnership", "Other",
    ]),
    "Description": {"rich_text": {}},
    "Triggered By": {"rich_text": {}},
    "Target": _select([
        "Agency Clients", "My SaaS", "BikeRide", "DragonIsland",
        "BNPL", "Personal", "Other",
    ]),
    "Effort": _select(["Low", "Medium", "High"]),
    "Potential Impact": _select(["High", "Medium", "Low"]),
    "Action Items": {"rich_text": {}},
    "Status": _select(["New", "Exploring", "In Progress", "Done", "Dismissed"]),
    "Added Date": {"date": {}},
}

DAILY_BRIEFS_SCHEMA = {
    "Date": {"title": {}},
    "Brief Date": {"date": {}},
    "Executive Summary": {"rich_text": {}},
    "Top Story": {"rich_text": {}},
    "Models Count": {"number": {"format": "number"}},
    "Tools Count": {"number": {"format": "number"}},
    "Research Count": {"number": {"format": "number"}},
    "OSS Count": {"number": {"format": "number"}},
    "HF Count": {"number": {"format": "number"}},
    "Opportunities Count": {"number": {"format": "number"}},
    "P1 Alerts Count": {"number": {"format": "number"}},
    "Status": _select(["Published", "Draft"]),
}

OSS_RADAR_SCHEMA = {
    "Repo Name": {"title": {}},
    "Owner": {"rich_text": {}},
    "URL": {"url": {}},
    "Description": {"rich_text": {}},
    "Language": _select(["Python", "JavaScript", "TypeScript", "Rust", "Go", "Other"]),
    "Stars": {"number": {"format": "number"}},
    "Forks": {"number": {"format": "number"}},
    "Topics": {"rich_text": {}},
    "Created At": {"date": {}},
    "Last Push": {"date": {}},
    "Has Release": {"checkbox": {}},
    "Radar Score": {"number": {"format": "number"}},
    "Dev Relevance": _select(["High", "Medium", "Low"]),
    "TremoAI Relevant": {"checkbox": {}},
    "Arabic Explanation": {"rich_text": {}},
    "Why It Matters": {"rich_text": {}},
    "Added Date": {"date": {}},
}

HF_MODELS_SCHEMA = {
    "Model Name": {"title": {}},
    "Organization": {"rich_text": {}},
    "URL": {"url": {}},
    "Task": _select([
        "Text Generation", "Image Generation", "Speech",
        "Vision", "Multimodal", "Classification", "Other",
    ]),
    "Downloads": {"number": {"format": "number"}},
    "Likes": {"number": {"format": "number"}},
    "Last Modified": {"date": {}},
    "License": {"rich_text": {}},
    "Pipeline Tag": {"rich_text": {}},
    "Radar Score": {"number": {"format": "number"}},
    "Dev Relevance": _select(["High", "Medium", "Low"]),
    "TremoAI Relevant": {"checkbox": {}},
    "Arabic Explanation": {"rich_text": {}},
    "Why It Matters": {"rich_text": {}},
    "Added Date": {"date": {}},
}

ALERTS_SCHEMA = {
    "Alert Title": {"title": {}},
    "Level": _select(["P1", "P2", "P3"]),
    "Source Type": _select(["Model", "Tool", "Research", "OSS", "HF Model", "Signal"]),
    "Summary": {"rich_text": {}},
    "Source URL": {"url": {}},
    "Radar Score": {"number": {"format": "number"}},
    "Action Required": {"rich_text": {}},
    "Status": _select(["New", "Reviewed", "Dismissed"]),
    "Added Date": {"date": {}},
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Ordered list: (display title, emoji, schema)
ALL_DATABASES = [
    ("AI Models", "\U0001f916", MODELS_SCHEMA),
    ("AI Tools", "\U0001f6e0\ufe0f", TOOLS_SCHEMA),
    ("AI Research", "\U0001f4c4", RESEARCH_SCHEMA),
    ("AI Signals", "\U0001f4e1", SIGNALS_SCHEMA),
    ("Opportunities", "\U0001f4a1", OPPORTUNITIES_SCHEMA),
    ("Daily Briefs", "\U0001f4f0", DAILY_BRIEFS_SCHEMA),
    ("Open Source Radar", "\U0001f52d", OSS_RADAR_SCHEMA),
    ("HF Models Radar", "\U0001f917", HF_MODELS_SCHEMA),
    ("Alerts", "\U0001f6a8", ALERTS_SCHEMA),
]

# Map display title to env-var name for easy copy-paste
ENV_MAP = {
    "AI Models": "NOTION_DB_MODELS",
    "AI Tools": "NOTION_DB_TOOLS",
    "AI Research": "NOTION_DB_RESEARCH",
    "AI Signals": "NOTION_DB_SIGNALS",
    "Opportunities": "NOTION_DB_OPPORTUNITIES",
    "Daily Briefs": "NOTION_DB_BRIEFS",
    "Open Source Radar": "NOTION_DB_OSS",
    "HF Models Radar": "NOTION_DB_HF",
    "Alerts": "NOTION_DB_ALERTS",
}


def main():
    """Create all 9 Notion databases and print the IDs for env config."""
    if not NOTION_API_KEY:
        print("[SETUP] Missing NOTION_API_KEY")
        sys.exit(1)
    if not NOTION_PARENT_PAGE_ID:
        print("[SETUP] Missing NOTION_PARENT_PAGE_ID")
        sys.exit(1)

    print("[SETUP] Creating 9 Notion databases...")
    print()

    created = {}
    for title, emoji, schema in ALL_DATABASES:
        db_id = _create_database(title, emoji, schema)
        env_name = ENV_MAP.get(title, "UNKNOWN")
        created[env_name] = db_id
        time.sleep(0.5)  # Respect Notion rate limits

    print()
    print("=" * 60)
    print("Copy these database IDs to your GitHub Secrets / .env:")
    print("=" * 60)
    for env_name, db_id in created.items():
        print(f"  {env_name}={db_id}")
    print("=" * 60)
    print("[SETUP] Done!")


if __name__ == "__main__":
    main()
