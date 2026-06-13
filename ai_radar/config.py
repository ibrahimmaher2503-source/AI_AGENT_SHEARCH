"""
Configuration module for AI Radar.
Loads and validates all required environment variables at import time.
"""

import os
import re
import sys

# A Notion ID is 32 hex characters (UUID without dashes). Users often paste a
# full URL or a dashed UUID into the secret by mistake, which produces an
# "invalid_request_url" 400 from the API. Extract/normalize it up front so we
# fail with a clear message instead of looping on bad URLs at runtime.
_HEX32_RE = re.compile(r"[0-9a-fA-F]{32}")


def _normalize_notion_id(raw):
    """Return the canonical 32-char Notion ID from a raw secret value.

    Accepts a bare ID, a dashed UUID, or a full Notion URL. Returns None when
    no valid 32-char hex ID can be extracted.
    """
    if not raw:
        return None
    candidate = raw.strip().replace("-", "")
    # A clean ID is exactly 32 hex chars.
    if re.fullmatch(r"[0-9a-fA-F]{32}", candidate):
        return candidate
    # Otherwise try to pull the last 32-hex run out of a URL/decorated value.
    matches = _HEX32_RE.findall(raw.replace("-", ""))
    return matches[-1] if matches else None

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

# Notion database IDs that must be valid 32-char IDs when publishing for real.
_NOTION_DB_VARS = [v for v in REQUIRED_VARS if v.startswith("NOTION_DB_")]

# Validate required variables at module load time (skip in smoke test mode)
if os.environ.get("AI_RADAR_SKIP_VALIDATION") != "1":
    # In DRY_RUN we never touch Notion, so the DB IDs / parent page are optional.
    _skip_notion_dbs = DRY_RUN
    for _var in REQUIRED_VARS:
        if os.environ.get(_var) is None:
            _is_notion_target = _var.startswith("NOTION_DB_") or _var == "NOTION_PARENT_PAGE_ID"
            if _skip_notion_dbs and _is_notion_target:
                continue
            print(f"[CONFIG] Missing required: {_var}")
            sys.exit(1)

    # Normalize and validate Notion database IDs so a pasted URL / dashed UUID
    # fails fast here instead of producing endless 400 invalid_request_url
    # errors at publish time.
    if not _skip_notion_dbs:
        _bad_ids = []
        _this_module = sys.modules[__name__]
        for _var in _NOTION_DB_VARS:
            _raw = getattr(_this_module, _var)
            _clean = _normalize_notion_id(_raw)
            if _clean is None:
                _bad_ids.append(_var)
            else:
                setattr(_this_module, _var, _clean)
        # Also normalize the parent page ID when present (used by setup/weekly).
        if NOTION_PARENT_PAGE_ID:
            NOTION_PARENT_PAGE_ID = _normalize_notion_id(NOTION_PARENT_PAGE_ID) or NOTION_PARENT_PAGE_ID
        if _bad_ids:
            print(
                "[CONFIG] Invalid Notion database ID(s): "
                + ", ".join(_bad_ids)
            )
            print(
                "[CONFIG] Each must be a 32-character Notion ID (or a Notion URL "
                "containing one). Copy it from the database URL and update the "
                "matching GitHub Secret."
            )
            sys.exit(1)

# Summary
print(f"[CONFIG] Loaded {len(REQUIRED_VARS)} environment variables")
print(f"[CONFIG] DRY_RUN: {DRY_RUN}")
