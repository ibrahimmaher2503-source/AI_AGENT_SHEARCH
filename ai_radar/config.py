"""
Configuration module for AI Radar.
Loads and validates all required environment variables at import time.
"""

import os
import sys

# Required environment variables
REQUIRED_VARS = [
    "GEMINI_API_KEY",
    "NOTION_API_KEY",
    "TAVILY_API_KEY",
    "NOTION_DB_MODELS",
    "NOTION_DB_TOOLS",
    "NOTION_DB_RESEARCH",
    "NOTION_DB_SIGNALS",
    "NOTION_DB_OPPORTUNITIES",
    "NOTION_DB_BRIEFS",
    "NOTION_DB_OSS_RADAR",
    "NOTION_DB_HF_RADAR",
    "NOTION_DB_ALERTS",
    "NOTION_PARENT_PAGE_ID",
]

# Load all required variables from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
NOTION_DB_MODELS = os.environ.get("NOTION_DB_MODELS")
NOTION_DB_TOOLS = os.environ.get("NOTION_DB_TOOLS")
NOTION_DB_RESEARCH = os.environ.get("NOTION_DB_RESEARCH")
NOTION_DB_SIGNALS = os.environ.get("NOTION_DB_SIGNALS")
NOTION_DB_OPPORTUNITIES = os.environ.get("NOTION_DB_OPPORTUNITIES")
NOTION_DB_BRIEFS = os.environ.get("NOTION_DB_BRIEFS")
NOTION_DB_OSS_RADAR = os.environ.get("NOTION_DB_OSS_RADAR")
NOTION_DB_HF_RADAR = os.environ.get("NOTION_DB_HF_RADAR")
NOTION_DB_ALERTS = os.environ.get("NOTION_DB_ALERTS")
NOTION_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID")

# Optional variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Validate required variables at module load time (skip in smoke test mode)
if os.environ.get("AI_RADAR_SKIP_VALIDATION") != "1":
    _skip_notion_dbs = DRY_RUN
    for _var in REQUIRED_VARS:
        if os.environ.get(_var) is None:
            if _skip_notion_dbs and (_var.startswith("NOTION_DB_") or _var == "NOTION_PARENT_PAGE_ID"):
                continue
            print(f"[CONFIG] Missing required: {_var}")
            sys.exit(1)

# Summary
print(f"[CONFIG] Loaded {len(REQUIRED_VARS)} environment variables")
print(f"[CONFIG] DRY_RUN: {DRY_RUN}")
