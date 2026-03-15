"""
Utility functions for AI Radar pipeline.
Standard library only: datetime, json, urllib.parse, re.
"""

import datetime
import json
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


# ---------------------------------------------------------------------------
# 1. get_today_iso
# ---------------------------------------------------------------------------
def get_today_iso() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# 2. extract_domain
# ---------------------------------------------------------------------------
def extract_domain(url: str) -> str:
    """Parse URL and return domain without 'www.' prefix. Return '' on failure."""
    try:
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 3. normalize_url
# ---------------------------------------------------------------------------
def normalize_url(url: str) -> str:
    """Strip trailing slash, remove query params matching utm_*, ref, source."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Filter out tracking params
        filtered = {
            k: v for k, v in params.items()
            if not re.match(r"^utm_", k, re.IGNORECASE)
            and k.lower() not in ("ref", "source")
        }
        # Rebuild query string (flatten single-value lists)
        clean_query = urlencode(
            {k: v[0] if len(v) == 1 else v for k, v in filtered.items()},
            doseq=True,
        )
        cleaned = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, clean_query, parsed.fragment,
        ))
        return cleaned.rstrip("/")
    except Exception:
        return url.rstrip("/")


# ---------------------------------------------------------------------------
# 4. truncate
# ---------------------------------------------------------------------------
def truncate(text: str, max_len: int = 500) -> str:
    """Truncate text to max_len characters, append '...' if truncated."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


# ---------------------------------------------------------------------------
# 5. chunk_rich_text
# ---------------------------------------------------------------------------
def chunk_rich_text(text: str, max_len: int = 2000) -> list:
    """Split text into chunks of max_len at sentence boundaries ('. ').
    Each chunk is a dict: {"text": {"content": chunk_text}}.
    """
    if not text:
        return [{"text": {"content": ""}}]
    if len(text) <= max_len:
        return [{"text": {"content": text}}]

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append({"text": {"content": remaining}})
            break
        # Find last sentence boundary within max_len
        cut = remaining[:max_len].rfind(". ")
        if cut == -1:
            # No sentence boundary found; hard cut
            cut = max_len
        else:
            cut += 2  # include ". "
        chunks.append({"text": {"content": remaining[:cut]}})
        remaining = remaining[cut:]
    return chunks


# ---------------------------------------------------------------------------
# 6. title_similarity
# ---------------------------------------------------------------------------
def title_similarity(a: str, b: str) -> bool:
    """Check if titles share 5+ consecutive words (sliding window)."""
    words_a = a.lower().split()
    words_b = b.lower().split()
    if len(words_a) < 5 or len(words_b) < 5:
        return False
    # Build set of 5-grams from a
    ngrams_a = set()
    for i in range(len(words_a) - 4):
        ngrams_a.add(tuple(words_a[i:i + 5]))
    # Check if any 5-gram from b matches
    for i in range(len(words_b) - 4):
        if tuple(words_b[i:i + 5]) in ngrams_a:
            return True
    return False


# ---------------------------------------------------------------------------
# 7. normalize_select
# ---------------------------------------------------------------------------
def normalize_select(value: str, allowed: list, fallback: str) -> str:
    """Case-insensitive match of value against allowed list."""
    lower_val = value.lower().strip()
    for item in allowed:
        if item.lower().strip() == lower_val:
            return item
    return fallback


# ---------------------------------------------------------------------------
# 8. score_to_rating
# ---------------------------------------------------------------------------
def score_to_rating(score: int) -> str:
    """Convert numeric score (0-100) to star rating string."""
    if score >= 80:
        return "\u2b50\u2b50\u2b50\u2b50\u2b50"
    elif score >= 60:
        return "\u2b50\u2b50\u2b50\u2b50"
    elif score >= 40:
        return "\u2b50\u2b50\u2b50"
    elif score >= 20:
        return "\u2b50\u2b50"
    else:
        return "\u2b50"


# ---------------------------------------------------------------------------
# 9. normalize_company
# ---------------------------------------------------------------------------
def normalize_company(raw: str) -> str:
    """Map raw company name to canonical form (case-insensitive)."""
    key = raw.lower().strip()
    mapping = {
        "openai": "OpenAI",
        "open ai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
        "deepmind": "Google",
        "meta": "Meta",
        "facebook": "Meta",
        "mistral": "Mistral",
    }
    return mapping.get(key, "Other")


# ---------------------------------------------------------------------------
# 10. build_notion_rich_text
# ---------------------------------------------------------------------------
def build_notion_rich_text(text: str) -> list:
    """Return list of dicts for Notion rich_text property.
    Uses chunk_rich_text() for text longer than 2000 chars.
    """
    return chunk_rich_text(text, max_len=2000)


# ---------------------------------------------------------------------------
# 11. build_notion_children_blocks
# ---------------------------------------------------------------------------
def build_notion_children_blocks(brief_data: dict) -> list:
    """Build Notion page children blocks for the daily brief."""
    blocks = []

    # Executive summary callout
    exec_summary = brief_data.get("executive_summary", "")
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": chunk_rich_text(str(exec_summary)),
            "icon": {"type": "emoji", "emoji": "\U0001f4ca"},
        },
    })

    # Section keys with display labels
    section_keys = [
        ("top_story", "Top Story"),
        ("models_highlights", "Models Highlights"),
        ("tools_highlights", "Tools Highlights"),
        ("research_highlights", "Research Highlights"),
        ("github_radar", "GitHub Radar"),
        ("hf_radar", "HF Radar"),
        ("marketing_opportunities", "Marketing Opportunities"),
        ("dev_opportunities", "Dev Opportunities"),
        ("tremoai_updates", "TremoAI Updates"),
        ("p1_alerts_summary", "P1 Alerts Summary"),
    ]

    for key, label in section_keys:
        content = brief_data.get(key, "")
        if not content:
            continue
        # Divider between sections
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        # Heading
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": label}}],
            },
        })
        # Paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": chunk_rich_text(str(content)),
            },
        })

    # Action Items
    action_items = brief_data.get("action_items", [])
    if action_items:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "Action Items"}}],
            },
        })
        for item in action_items:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": str(item)}}],
                },
            })

    # Arabic summary
    arabic_summary = brief_data.get("arabic_summary", "")
    if arabic_summary:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "\u0645\u0644\u062e\u0635 \u0628\u0627\u0644\u0639\u0631\u0628\u064a"}}],
            },
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": chunk_rich_text(str(arabic_summary)),
            },
        })

    return blocks


# ---------------------------------------------------------------------------
# 12. format_arabic_explanation
# ---------------------------------------------------------------------------
def format_arabic_explanation(arabic: dict) -> str:
    """Format Arabic explanation dict into a readable string."""
    return (
        f"\U0001f50d \u0625\u064a\u0647 \u062f\u064a\u061f\n{arabic.get('\u0627\u064a\u0647_\u062f\u064a', '')}\n\n"
        f"\U0001f4a1 \u0647\u0633\u062a\u0641\u064a\u062f \u0645\u0646\u0647\u0627 \u0627\u0632\u0627\u064a\u061f\n{arabic.get('\u0647\u0633\u062a\u0641\u064a\u062f_\u0645\u0646\u0647\u0627_\u0627\u0632\u0627\u064a', '')}\n\n"
        f"\u26a1 \u062a\u0633\u062a\u062d\u0642 \u0648\u0642\u062a\u0643\u061f\n{arabic.get('\u062a\u0633\u062a\u062d\u0642_\u0648\u0642\u062a\u0643', '')}\n\n"
        f"\U0001f517 \u0645\u0634\u0627\u0628\u0647 \u0644\u0640: {arabic.get('\u0645\u0634\u0627\u0628\u0647_\u0644\u0640', '')}"
    )


# ---------------------------------------------------------------------------
# 13. calculate_radar_score
# ---------------------------------------------------------------------------
def calculate_radar_score(item: dict) -> float:
    """Calculate weighted radar score from item metrics."""
    return round(
        0.30 * item.get("novelty_score", 50)
        + 0.25 * item.get("credibility_score", 50)
        + 0.20 * item.get("execution_value", 50)
        + 0.15 * item.get("dev_value", 50)
        + 0.10 * item.get("agency_value", 50),
        1,
    )


# ---------------------------------------------------------------------------
# 14. assign_alert_level
# ---------------------------------------------------------------------------
def assign_alert_level(item: dict) -> str:
    """Assign alert level (P1/P2/P3/None) based on score and priority."""
    score = item.get("radar_score", 0)
    priority = item.get("source_priority", "medium")
    if score >= 80 or (priority == "high" and score >= 70):
        return "P1"
    elif score >= 55:
        return "P2"
    elif score >= 30:
        return "P3"
    return "None"


# ---------------------------------------------------------------------------
# 15. get_source_priority
# ---------------------------------------------------------------------------
def get_source_priority(url: str, sources: list) -> str:
    """Match URL domain against source list, return priority. Default 'low'."""
    domain = extract_domain(url)
    if not domain:
        return "low"
    for source in sources:
        source_url = source.get("url", "")
        source_domain = extract_domain(source_url)
        if source_domain and domain == source_domain:
            return source.get("priority", "low")
    return "low"
