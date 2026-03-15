"""
Agent: Daily AI Brief Writer.
Generates a comprehensive daily brief via Gemini and publishes it to Notion.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import notion_client
import gemini_client
from prompts import BRIEF_PROMPT
from utils import (
    get_today_iso,
    build_notion_rich_text,
    build_notion_children_blocks,
    chunk_rich_text,
)


def _get_top_items(items, count=3):
    """Get top N items by radar_score, return comma-separated titles."""
    sorted_items = sorted(
        items, key=lambda x: x.get("radar_score", 0), reverse=True
    )
    top = sorted_items[:count]
    return (
        ", ".join(item.get("title", "Unknown")[:60] for item in top) or "None"
    )


def _build_brief_properties(today, brief_data, analyzed, publish_stats):
    """Build Notion properties dict for the daily brief page."""
    title = f"AI Brief \u2014 {today}"
    return {
        "Date": {"title": [{"text": {"content": title}}]},
        "Brief Date": {"date": {"start": today}},
        "Executive Summary": {
            "rich_text": build_notion_rich_text(
                brief_data.get("executive_summary", "")
            )
        },
        "Top Story": {
            "rich_text": build_notion_rich_text(
                brief_data.get("top_story", "")
            )
        },
        "Models Count": {"number": len(analyzed.get("models", []))},
        "Tools Count": {"number": len(analyzed.get("tools", []))},
        "Research Count": {"number": len(analyzed.get("research", []))},
        "OSS Count": {"number": len(analyzed.get("github_repos", []))},
        "HF Count": {"number": len(analyzed.get("hf_models", []))},
        "Opportunities Count": {
            "number": len(analyzed.get("opportunities", []))
        },
        "P1 Alerts Count": {
            "number": analyzed.get("stats", {}).get("p1_count", 0)
        },
        "Status": {"select": {"name": "Published"}},
    }


def run(analyzed, publish_stats):
    """Generate and publish the daily AI brief.

    Args:
        analyzed: dict with keys like 'models', 'tools', 'research',
                  'github_repos', 'hf_models', 'opportunities', 'signals',
                  and 'stats'.
        publish_stats: dict with publishing statistics from earlier pipeline
                       stages (passed through to properties builder).
    """
    today = get_today_iso()
    title = f"AI Brief \u2014 {today}"

    # Skip if today's brief already exists
    if notion_client.title_exists_in_database(config.NOTION_DB_BRIEFS, title):
        print(f"[BRIEF] Brief already exists for {today}, skipping")
        return

    print(f"[BRIEF] Generating daily brief for {today}")

    # Gather stats and top items for the prompt
    stats = analyzed.get("stats", {})
    signals_summary = _get_top_items(analyzed.get("signals", []), 5)

    prompt = BRIEF_PROMPT.format(
        today=today,
        models_count=len(analyzed.get("models", [])),
        top_models=_get_top_items(analyzed.get("models", [])),
        tools_count=len(analyzed.get("tools", [])),
        top_tools=_get_top_items(analyzed.get("tools", [])),
        research_count=len(analyzed.get("research", [])),
        top_research=_get_top_items(analyzed.get("research", [])),
        oss_count=len(analyzed.get("github_repos", [])),
        top_oss=_get_top_items(analyzed.get("github_repos", [])),
        hf_count=len(analyzed.get("hf_models", [])),
        top_hf=_get_top_items(analyzed.get("hf_models", [])),
        p1_count=stats.get("p1_count", 0),
        opps_count=len(analyzed.get("opportunities", [])),
        signals_summary=signals_summary,
    )

    # Generate brief content via Gemini
    brief_data = gemini_client.generate_json(prompt, temperature=0.5)

    if not isinstance(brief_data, dict):
        print("[BRIEF] Failed to generate brief — Gemini returned non-dict")
        brief_data = {
            "executive_summary": (
                f"AI Radar collected {stats.get('raw_count', 0)} "
                f"signals on {today}."
            ),
            "top_story": "See individual databases for details.",
            "action_items": [
                "Review P1 alerts",
                "Check new tools",
                "Scan research papers",
            ],
            "arabic_summary": (
                "\u0627\u0644\u0646\u0638\u0627\u0645 \u062c\u0645\u0639 "
                "\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0646\u0647\u0627\u0631\u062f\u0647 "
                "\u0628\u0633 \u0645\u0642\u062f\u0631\u0634 \u064a\u0648\u0644\u062f "
                "\u0645\u0644\u062e\u0635 \u0643\u0627\u0645\u0644. "
                "\u0631\u0627\u062c\u0639 \u0627\u0644\u0642\u0648\u0627\u0639\u062f "
                "\u0643\u0644 \u0648\u0627\u062d\u062f\u0647 \u0644\u0648\u062d\u062f\u0647\u0627."
            ),
        }

    # Build Notion page properties and body blocks
    properties = _build_brief_properties(
        today, brief_data, analyzed, publish_stats
    )
    children = build_notion_children_blocks(brief_data)

    # Create the brief page in Notion
    result = notion_client.create_page(
        config.NOTION_DB_BRIEFS,
        properties,
        icon_emoji="\U0001f4f0",
        children=children,
    )

    if result:
        p1 = stats.get("p1_count", 0)
        print(f"[BRIEF] Brief created: {title} (P1 alerts: {p1})")
    else:
        print(f"[BRIEF] Failed to create brief for {today}")
