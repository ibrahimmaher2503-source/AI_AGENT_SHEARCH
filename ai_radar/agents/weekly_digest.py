"""
Agent: Weekly AI Digest Writer.
Reads the last 7 daily briefs from Notion, generates a weekly rollup via Gemini,
and publishes it as a new page in the Briefs database.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import notion_client
import gemini_client
from utils import get_today_iso, build_notion_rich_text, build_notion_children_blocks, chunk_rich_text

log = logging.getLogger("ai_radar.weekly")

WEEKLY_PROMPT = """You are Ibrahim's personal AI intelligence analyst. Generate a WEEKLY AI digest.

Week ending: {week_end}

Here are the daily brief summaries from the past 7 days:

{daily_summaries}

Based on all of the above, generate a weekly rollup as a JSON object with these fields:

1. "executive_summary" - string. 5-8 sentences summarizing the week's most important AI developments. What were the big themes?

2. "top_stories" - string. The 3-5 biggest stories of the week. For each, give the story and why it mattered.

3. "models_of_the_week" - string. The most significant model releases this week and why they stand out.

4. "tools_of_the_week" - string. The most useful new tools discovered this week.

5. "trends" - string. 3-5 emerging trends or patterns you noticed across the week's signals.

6. "marketing_playbook" - string. A concise playbook for Ibrahim's marketing agency: what new capabilities, tools, or strategies emerged this week that the agency should adopt?

7. "dev_playbook" - string. A concise playbook for Ibrahim as a developer: what new APIs, frameworks, or techniques should he explore or integrate?

8. "tremoai_weekly" - string. Summary of anything relevant to TremoAI this week. If nothing, say so.

9. "next_week_watchlist" - list of strings. 3-5 things to watch for next week based on this week's signals.

10. "arabic_summary" - string. 8-12 sentence weekly summary in Arabic. Cover the biggest stories, trends, and action items.

Return ONLY valid JSON. No markdown."""


def _fetch_daily_briefs(days=7):
    """Query the Briefs database for pages created in the last N days."""
    summaries = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        title = f"AI Brief \u2014 {day}"
        results = notion_client.query_database_by_title(config.NOTION_DB_BRIEFS, title)
        if results:
            page = results[0]
            props = page.get("properties", {})
            exec_summary = ""
            es_prop = props.get("Executive Summary", {}).get("rich_text", [])
            if es_prop:
                exec_summary = "".join(t.get("text", {}).get("content", "") for t in es_prop)
            top_story = ""
            ts_prop = props.get("Top Story", {}).get("rich_text", [])
            if ts_prop:
                top_story = "".join(t.get("text", {}).get("content", "") for t in ts_prop)

            models_count = props.get("Models Count", {}).get("number", 0) or 0
            tools_count = props.get("Tools Count", {}).get("number", 0) or 0
            p1_count = props.get("P1 Alerts Count", {}).get("number", 0) or 0

            summaries.append(
                f"### {day}\n"
                f"Executive Summary: {exec_summary}\n"
                f"Top Story: {top_story}\n"
                f"Models: {models_count}, Tools: {tools_count}, P1 Alerts: {p1_count}\n"
            )
    return "\n".join(summaries) if summaries else "No daily briefs found for this week."


def run():
    """Generate and publish the weekly AI digest."""
    today = get_today_iso()
    title = f"Weekly AI Digest \u2014 Week of {today}"

    if notion_client.title_exists_in_database(config.NOTION_DB_BRIEFS, title):
        log.info(f"Weekly digest already exists for {today}, skipping")
        return

    log.info(f"Generating weekly digest for week ending {today}")

    daily_summaries = _fetch_daily_briefs(days=7)
    log.info(f"Fetched daily briefs for weekly rollup")

    prompt = WEEKLY_PROMPT.format(week_end=today, daily_summaries=daily_summaries)
    digest_data = gemini_client.generate_json(prompt, temperature=0.5)

    if not isinstance(digest_data, dict):
        log.warning("Gemini returned non-dict for weekly digest, using fallback")
        digest_data = {
            "executive_summary": f"Weekly digest for the week ending {today}. See individual daily briefs for details.",
            "top_stories": "See daily briefs.",
            "trends": "No trends analysis available.",
            "next_week_watchlist": ["Review daily briefs"],
            "arabic_summary": "\u0645\u0644\u062e\u0635 \u0627\u0644\u0623\u0633\u0628\u0648\u0639 \u063a\u064a\u0631 \u0645\u062a\u0627\u062d. \u0631\u0627\u062c\u0639 \u0627\u0644\u0645\u0644\u062e\u0635\u0627\u062a \u0627\u0644\u064a\u0648\u0645\u064a\u0629.",
        }

    properties = {
        "Date": {"title": [{"text": {"content": title}}]},
        "Brief Date": {"date": {"start": today}},
        "Executive Summary": {"rich_text": build_notion_rich_text(digest_data.get("executive_summary", ""))},
        "Top Story": {"rich_text": build_notion_rich_text(digest_data.get("top_stories", ""))},
        "Status": {"select": {"name": "Published"}},
    }

    # Build children blocks
    blocks = []
    blocks.append({
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": chunk_rich_text(str(digest_data.get("executive_summary", ""))),
            "icon": {"type": "emoji", "emoji": "\U0001f4c5"},
        },
    })

    section_map = [
        ("top_stories", "Top Stories of the Week"),
        ("models_of_the_week", "Models of the Week"),
        ("tools_of_the_week", "Tools of the Week"),
        ("trends", "Emerging Trends"),
        ("marketing_playbook", "Marketing Agency Playbook"),
        ("dev_playbook", "Developer Playbook"),
        ("tremoai_weekly", "TremoAI Weekly"),
    ]
    for key, label in section_map:
        content = digest_data.get(key, "")
        if not content:
            continue
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": label}}]},
        })
        blocks.append({
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": chunk_rich_text(str(content))},
        })

    # Watchlist
    watchlist = digest_data.get("next_week_watchlist", [])
    if watchlist:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Next Week Watchlist"}}]},
        })
        for item in watchlist:
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": str(item)}}]},
            })

    # Arabic summary
    arabic = digest_data.get("arabic_summary", "")
    if arabic:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "\u0645\u0644\u062e\u0635 \u0627\u0644\u0623\u0633\u0628\u0648\u0639 \u0628\u0627\u0644\u0639\u0631\u0628\u064a"}}]},
        })
        blocks.append({
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": chunk_rich_text(str(arabic))},
        })

    result = notion_client.create_page(
        config.NOTION_DB_BRIEFS, properties,
        icon_emoji="\U0001f4c5", children=blocks,
    )

    if result:
        log.info(f"Weekly digest created: {title}")
    else:
        log.error(f"Failed to create weekly digest for {today}")
