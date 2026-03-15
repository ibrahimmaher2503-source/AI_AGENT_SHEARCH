"""
Publisher agent for AI Radar.
Publishes classified items to all 9 Notion databases with duplicate protection.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import notion_client
from utils import (normalize_company, normalize_select, score_to_rating,
                   format_arabic_explanation, build_notion_rich_text,
                   chunk_rich_text, get_today_iso)


# ---------------------------------------------------------------------------
# Notion property value helpers
# ---------------------------------------------------------------------------

def _title(text):
    """Build a Notion title property value."""
    return {"title": [{"text": {"content": str(text or "")}}]}


def _rich(text):
    """Build a Notion rich_text property value, chunking long text."""
    return {"rich_text": build_notion_rich_text(str(text or ""))}


def _select(value):
    """Build a Notion select property value."""
    return {"select": {"name": str(value or "")}}


def _multi_select(values):
    """Build a Notion multi_select property value from a list of strings."""
    if not values:
        return {"multi_select": []}
    return {"multi_select": [{"name": str(v)} for v in values]}


def _number(value):
    """Build a Notion number property value."""
    try:
        return {"number": float(value) if value is not None else 0}
    except (TypeError, ValueError):
        return {"number": 0}


def _checkbox(value):
    """Build a Notion checkbox property value."""
    return {"checkbox": bool(value)}


def _url(value):
    """Build a Notion url property value. None for empty strings."""
    if not value or not str(value).strip():
        return {"url": None}
    return {"url": str(value)}


def _date(value):
    """Build a Notion date property value. Extracts YYYY-MM-DD from ISO string."""
    if not value:
        return {"date": {"start": get_today_iso()}}
    return {"date": {"start": str(value)[:10]}}


def _arabic(item):
    """Extract and format arabic_explanation from item."""
    arabic = item.get("arabic_explanation", "")
    if isinstance(arabic, dict):
        return format_arabic_explanation(arabic)
    return str(arabic or "")


# ---------------------------------------------------------------------------
# Property builders for each database type
# ---------------------------------------------------------------------------

def _build_model_properties(item):
    """Build Notion properties dict for the AI Models database."""
    today = get_today_iso()
    model_types = ["LLM", "Image", "Video", "Audio", "Multimodal", "Code", "Other"]
    pricing_opts = ["Free", "Freemium", "Paid", "API Only"]
    relevance_opts = ["High", "Medium", "Low"]
    alert_opts = ["P1", "P2", "P3", "None"]

    return {
        "Name": _title(item.get("title", "")),
        "Company": _select(normalize_company(item.get("company", "Other"))),
        "Model Type": _select(normalize_select(
            item.get("model_type", "Other"), model_types, "Other")),
        "Release Date": _date(item.get("published_at", today)),
        "Key Capabilities": _rich(item.get("summary_en", "")),
        "Context Window": _rich(""),
        "Pricing": _select(normalize_select(
            item.get("pricing", "Freemium"), pricing_opts, "Freemium")),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Importance Score": _number(item.get("importance_score", 0)),
        "Marketing Relevance": _select(normalize_select(
            item.get("marketing_relevance", "Medium"), relevance_opts, "Medium")),
        "Dev Relevance": _select(normalize_select(
            item.get("dev_relevance", "Medium"), relevance_opts, "Medium")),
        "TremoAI Relevant": _checkbox(item.get("tremoai_relevant", False)),
        "Alert Level": _select(normalize_select(
            item.get("alert_level", "None"), alert_opts, "None")),
        "Arabic Explanation": _rich(_arabic(item)),
        "Source URL": _url(item.get("url", "") or item.get("canonical_url", "")),
        "Added Date": _date(today),
        "Notes": _rich(item.get("why_it_matters", "")),
    }


def _build_tool_properties(item):
    """Build Notion properties dict for the AI Tools database."""
    today = get_today_iso()
    cat_opts = ["Coding", "Image", "Video", "Writing", "SEO", "Ads",
                "Analytics", "Automation", "Research", "Other"]
    pricing_opts = ["Free", "Freemium", "Paid"]
    mkt_opts = ["Ads", "Copy", "Video", "SEO", "Analytics", "Social", "None"]
    relevance_opts = ["High", "Medium", "Low"]
    alert_opts = ["P1", "P2", "P3", "None"]

    return {
        "Name": _title(item.get("title", "")),
        "URL": _url(item.get("url", "") or item.get("canonical_url", "")),
        "Category": _select(normalize_select(
            item.get("category", "Other"), cat_opts, "Other")),
        "Description": _rich(item.get("content", "") or item.get("summary_en", "")),
        "Pricing": _select(normalize_select(
            item.get("pricing", "Freemium"), pricing_opts, "Freemium")),
        "Tags": _multi_select([]),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Popularity Score": _number(item.get("importance_score", 0)),
        "Rating": _select(score_to_rating(item.get("radar_score", 0))),
        "Marketing Use Case": _select(normalize_select(
            item.get("marketing_use_case", "None"), mkt_opts, "None")),
        "Has API": _checkbox(False),
        "TremoAI Relevant": _checkbox(item.get("tremoai_relevant", False)),
        "Alert Level": _select(normalize_select(
            item.get("alert_level", "None"), alert_opts, "None")),
        "Arabic Explanation": _rich(_arabic(item)),
        "Tried": _checkbox(False),
        "Added Date": _date(today),
        "Notes": _rich(item.get("why_it_matters", "")),
    }


def _build_research_properties(item):
    """Build Notion properties dict for the Research Papers database."""
    today = get_today_iso()
    inst_opts = ["OpenAI", "Google", "Meta", "Stanford", "MIT",
                 "DeepMind", "Academic", "Other"]
    relevance_opts = ["High", "Medium", "Low"]

    return {
        "Title": _title(item.get("title", "")),
        "Authors": _rich(""),
        "Institution": _select(normalize_select(
            item.get("institution", "Other"), inst_opts, "Other")),
        "Published Date": _date(item.get("published_at", today)),
        "Abstract Summary": _rich(item.get("content", "")),
        "Key Findings": _rich(item.get("summary_en", "")),
        "Practical Applications": _rich(item.get("why_it_matters", "")),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Importance Score": _number(item.get("importance_score", 0)),
        "Dev Relevance": _select(normalize_select(
            item.get("dev_relevance", "Medium"), relevance_opts, "Medium")),
        "Marketing Relevance": _select(normalize_select(
            item.get("marketing_relevance", "Medium"), relevance_opts, "Medium")),
        "TremoAI Relevant": _checkbox(item.get("tremoai_relevant", False)),
        "Source URL": _url(item.get("url", "") or item.get("canonical_url", "")),
        "Added Date": _date(today),
    }


def _build_signal_properties(item):
    """Build Notion properties dict for the Signals database."""
    today = get_today_iso()
    source_opts = ["Twitter/X", "Reddit", "HackerNews", "ProductHunt",
                   "GitHub", "HuggingFace", "Newsletter", "Blog", "News", "Other"]
    type_opts = ["Model Release", "Tool Launch", "Funding", "Acquisition",
                 "Research", "Open Source", "Trend", "Other"]

    return {
        "Title": _title(item.get("title", "")),
        "Source": _select(normalize_select(
            item.get("source", "Other"), source_opts, "Other")),
        "Type": _select(normalize_select(
            item.get("signal_type", item.get("type", "Other")), type_opts, "Other")),
        "Published At": _date(item.get("published_at", today)),
        "Summary": _rich(item.get("summary_en", "") or item.get("content", "")),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Importance Score": _number(item.get("importance_score", 0)),
        "Processed": _checkbox(False),
        "URL": _url(item.get("url", "") or item.get("canonical_url", "")),
        "Added Date": _date(today),
    }


def _build_oss_properties(item):
    """Build Notion properties dict for the OSS Radar database."""
    today = get_today_iso()
    lang_opts = ["Python", "JavaScript", "TypeScript", "Rust", "Go", "Other"]
    relevance_opts = ["High", "Medium", "Low"]

    topics = item.get("topics", [])
    if isinstance(topics, list):
        topics_str = ", ".join(str(t) for t in topics)
    else:
        topics_str = str(topics or "")

    return {
        "Repo Name": _title(item.get("repo_name", item.get("title", ""))),
        "Owner": _rich(item.get("owner", "")),
        "URL": _url(item.get("url", "") or item.get("html_url", "")),
        "Description": _rich(item.get("content", "") or item.get("description", "")),
        "Language": _select(normalize_select(
            item.get("language", "Other"), lang_opts, "Other")),
        "Stars": _number(item.get("stars", 0)),
        "Forks": _number(item.get("forks", 0)),
        "Topics": _rich(topics_str),
        "Created At": _date(item.get("created_at", today)),
        "Last Push": _date(item.get("pushed_at", today)),
        "Has Release": _checkbox(item.get("has_release", False)),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Dev Relevance": _select(normalize_select(
            item.get("dev_relevance", "Medium"), relevance_opts, "Medium")),
        "TremoAI Relevant": _checkbox(item.get("tremoai_relevant", False)),
        "Arabic Explanation": _rich(_arabic(item)),
        "Why It Matters": _rich(item.get("why_it_matters", "")),
        "Added Date": _date(today),
    }


def _build_hf_properties(item):
    """Build Notion properties dict for the HuggingFace Radar database."""
    today = get_today_iso()
    task_opts = ["Text Generation", "Image Generation", "Speech", "Vision",
                 "Multimodal", "Classification", "Other"]
    relevance_opts = ["High", "Medium", "Low"]

    return {
        "Model Name": _title(item.get("model_id", item.get("title", ""))),
        "Organization": _rich(item.get("organization", "")),
        "URL": _url(item.get("url", "")),
        "Task": _select(normalize_select(
            item.get("task", item.get("pipeline_tag", "Other")), task_opts, "Other")),
        "Downloads": _number(item.get("downloads", 0)),
        "Likes": _number(item.get("likes", 0)),
        "Last Modified": _date(item.get("last_modified", today)),
        "License": _rich(item.get("license", "")),
        "Pipeline Tag": _rich(item.get("pipeline_tag", "")),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Dev Relevance": _select(normalize_select(
            item.get("dev_relevance", "Medium"), relevance_opts, "Medium")),
        "TremoAI Relevant": _checkbox(item.get("tremoai_relevant", False)),
        "Arabic Explanation": _rich(_arabic(item)),
        "Why It Matters": _rich(item.get("why_it_matters", "")),
        "Added Date": _date(today),
    }


def _build_opportunity_properties(item):
    """Build Notion properties dict for the Opportunities database."""
    today = get_today_iso()
    type_opts = ["SaaS Idea", "Marketing Service", "Dev Tool", "Automation",
                 "Content Strategy", "Partnership", "Other"]
    target_opts = ["Agency Clients", "My SaaS", "BikeRide", "DragonIsland",
                   "BNPL", "Personal", "Other"]
    effort_opts = ["Low", "Medium", "High"]
    impact_opts = ["High", "Medium", "Low"]

    return {
        "Opportunity Title": _title(item.get("title", "")),
        "Type": _select(normalize_select(
            item.get("opportunity_type", item.get("type", "Other")),
            type_opts, "Other")),
        "Description": _rich(item.get("description", "") or item.get("content", "")),
        "Triggered By": _rich(item.get("triggered_by", "")),
        "Target": _select(normalize_select(
            item.get("target", "Other"), target_opts, "Other")),
        "Effort": _select(normalize_select(
            item.get("effort", "Medium"), effort_opts, "Medium")),
        "Potential Impact": _select(normalize_select(
            item.get("potential_impact", "Medium"), impact_opts, "Medium")),
        "Action Items": _rich(""),
        "Status": _select("New"),
        "Added Date": _date(today),
    }


def _build_alert_properties(item):
    """Build Notion properties dict for the Alerts database."""
    today = get_today_iso()
    level_opts = ["P1", "P2", "P3"]
    # Map item type to source type
    source_type_map = {
        "model": "Model",
        "tool": "Tool",
        "research": "Research",
        "oss": "OSS",
        "hf": "HF Model",
        "signal": "Signal",
    }
    source_type_opts = ["Model", "Tool", "Research", "OSS", "HF Model", "Signal"]
    raw_source = source_type_map.get(item.get("type", ""), "Signal")

    return {
        "Alert Title": _title(item.get("title", "")),
        "Level": _select(normalize_select(
            item.get("alert_level", "P3"), level_opts, "P3")),
        "Source Type": _select(normalize_select(
            raw_source, source_type_opts, "Signal")),
        "Summary": _rich(item.get("summary_en", "")),
        "Source URL": _url(item.get("url", "") or item.get("canonical_url", "")),
        "Radar Score": _number(item.get("radar_score", 0)),
        "Action Required": _rich(item.get("why_it_matters", "")),
        "Status": _select("New"),
        "Added Date": _date(today),
    }


# ---------------------------------------------------------------------------
# Generic publish function with dedup
# ---------------------------------------------------------------------------

def _publish_items(items, db_id, build_fn, type_name, dedup_fn):
    """Publish a list of items to a Notion database with dedup check.
    Returns (added_count, skipped_count).
    """
    added, skipped = 0, 0
    icons = {
        "model": "\U0001f916", "tool": "\U0001f6e0\ufe0f",
        "research": "\U0001f4c4", "signal": "\U0001f4e1",
        "oss": "\U0001f52d", "hf": "\U0001f917",
        "opportunity": "\U0001f4a1", "alert": "\U0001f6a8",
    }
    icon = icons.get(type_name, "\U0001f4cc")

    for item in items:
        if dedup_fn(item):
            print(f"[PUBLISHER] Skipped existing: "
                  f"{item.get('title', '')[:50]} ({type_name})")
            skipped += 1
            continue

        props = build_fn(item)
        result = notion_client.create_page(db_id, props, icon_emoji=icon)
        if result:
            score = item.get("radar_score", 0)
            level = item.get("alert_level", "")
            print(f"[PUBLISHER] Added {type_name}: "
                  f"{item.get('title', '')[:50]} "
                  f"(radar_score: {score}, {level})")
            added += 1
        time.sleep(0.3)

    return added, skipped


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(analyzed):
    """Publish all analyzed items to Notion databases. Returns stats dict."""
    print("[PUBLISHER] Starting publication to Notion databases")
    stats = {}

    # 1. Models
    a, s = _publish_items(
        analyzed.get("models", []), config.NOTION_DB_MODELS,
        _build_model_properties, "model",
        lambda item: notion_client.url_exists_in_database(
            config.NOTION_DB_MODELS,
            item.get("url", "") or item.get("canonical_url", "")))
    stats["models_added"], stats["models_skipped"] = a, s

    # 2. Tools
    a, s = _publish_items(
        analyzed.get("tools", []), config.NOTION_DB_TOOLS,
        _build_tool_properties, "tool",
        lambda item: notion_client.url_exists_in_database(
            config.NOTION_DB_TOOLS,
            item.get("url", "") or item.get("canonical_url", "")))
    stats["tools_added"], stats["tools_skipped"] = a, s

    # 3. Research
    a, s = _publish_items(
        analyzed.get("research", []), config.NOTION_DB_RESEARCH,
        _build_research_properties, "research",
        lambda item: notion_client.url_exists_in_database(
            config.NOTION_DB_RESEARCH,
            item.get("url", "") or item.get("canonical_url", "")))
    stats["research_added"], stats["research_skipped"] = a, s

    # 4. Signals
    a, s = _publish_items(
        analyzed.get("signals", []), config.NOTION_DB_SIGNALS,
        _build_signal_properties, "signal",
        lambda item: notion_client.url_exists_in_database(
            config.NOTION_DB_SIGNALS,
            item.get("url", "") or item.get("canonical_url", "")))
    stats["signals_added"], stats["signals_skipped"] = a, s

    # 5. GitHub / OSS Radar
    a, s = _publish_items(
        analyzed.get("github_repos", []), config.NOTION_DB_OSS_RADAR,
        _build_oss_properties, "oss",
        lambda item: notion_client.title_exists_in_database(
            config.NOTION_DB_OSS_RADAR,
            item.get("repo_name", item.get("title", ""))))
    stats["oss_added"], stats["oss_skipped"] = a, s

    # 6. HuggingFace Radar
    a, s = _publish_items(
        analyzed.get("hf_models", []), config.NOTION_DB_HF_RADAR,
        _build_hf_properties, "hf",
        lambda item: notion_client.title_exists_in_database(
            config.NOTION_DB_HF_RADAR,
            item.get("model_id", item.get("title", ""))))
    stats["hf_added"], stats["hf_skipped"] = a, s

    # 7. Opportunities
    a, s = _publish_items(
        analyzed.get("opportunities", []), config.NOTION_DB_OPPORTUNITIES,
        _build_opportunity_properties, "opportunity",
        lambda item: notion_client.title_exists_in_database(
            config.NOTION_DB_OPPORTUNITIES,
            item.get("title", "")))
    stats["opportunities_added"], stats["opportunities_skipped"] = a, s

    # 8. Alerts
    a, s = _publish_items(
        analyzed.get("alerts", []), config.NOTION_DB_ALERTS,
        _build_alert_properties, "alert",
        lambda item: notion_client.url_exists_in_database(
            config.NOTION_DB_ALERTS,
            item.get("url", "") or item.get("canonical_url", "")))
    stats["alerts_added"], stats["alerts_skipped"] = a, s

    # Summary
    total_added = sum(v for k, v in stats.items() if k.endswith("_added"))
    total_skipped = sum(v for k, v in stats.items() if k.endswith("_skipped"))
    print(f"[PUBLISHER] Publication complete: "
          f"{total_added} added, {total_skipped} skipped")

    return stats
