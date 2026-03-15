"""
Analyzer agent: Entity resolution, deduplication, Gemini classification,
scoring, alerting, and filtering/routing of collected signals.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gemini_client
from prompts import CLASSIFY_PROMPT
from utils import (normalize_url, title_similarity, calculate_radar_score,
                   assign_alert_level, get_today_iso)


def _pick_primary(group):
    """Pick the item with highest source_priority + raw_score from a group."""
    priority_map = {"high": 3, "medium": 2, "low": 1}
    return max(
        group,
        key=lambda x: (
            priority_map.get(x.get("source_priority", "low"), 0),
            x.get("raw_score", 0),
        ),
    )


def _priority_rank(item):
    """Return a comparable rank tuple for an item."""
    priority_map = {"high": 3, "medium": 2, "low": 1}
    return (
        priority_map.get(item.get("source_priority", "low"), 0),
        item.get("raw_score", 0),
    )


def deduplicate_and_resolve(items):
    """Stage A: Entity resolution. Returns list of resolved entities."""
    # Step 1: Group by exact URL
    url_groups = {}
    for item in items:
        url = item.get("url", "")
        if url in url_groups:
            url_groups[url].append(item)
        else:
            url_groups[url] = [item]

    # Step 2: Merge exact URL groups, keep best
    merged = []
    for url, group in url_groups.items():
        primary = _pick_primary(group)
        primary["secondary_sources"] = [
            i["url"] for i in group if i["url"] != primary["url"]
        ]
        primary["canonical_url"] = primary["url"]
        primary["primary_source"] = primary.get("source", "")
        merged.append(primary)

    # Step 3: Merge by normalized URL
    norm_groups = {}
    for item in merged:
        norm = normalize_url(item["url"])
        if norm in norm_groups:
            existing = norm_groups[norm]
            existing["secondary_sources"].extend(
                [item["url"]] + item.get("secondary_sources", [])
            )
            if _priority_rank(item) > _priority_rank(existing):
                item["secondary_sources"] = existing["secondary_sources"]
                norm_groups[norm] = item
        else:
            norm_groups[norm] = item
    merged = list(norm_groups.values())

    # Step 4: Merge by title similarity (5+ consecutive shared words)
    final = []
    used = set()
    for i, item_a in enumerate(merged):
        if i in used:
            continue
        group = [item_a]
        for j, item_b in enumerate(merged):
            if j <= i or j in used:
                continue
            if title_similarity(item_a.get("title", ""), item_b.get("title", "")):
                group.append(item_b)
                used.add(j)
        primary = _pick_primary(group)
        for g in group:
            if g["url"] != primary["url"]:
                primary.setdefault("secondary_sources", []).append(g["url"])
        primary["canonical_url"] = primary["url"]
        primary["primary_source"] = primary.get("source", "")
        final.append(primary)

    return final


def classify_batch(items):
    """Stage B: Send items to Gemini for classification in batches of 10."""
    batch_size = 10
    all_classified = []

    for batch_start in range(0, len(items), batch_size):
        batch = items[batch_start : batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(items) + batch_size - 1) // batch_size
        print(
            f"[ANALYZER] Classifying batch {batch_num}/{total_batches}"
            f" ({len(batch)} items)..."
        )

        # Prepare items for prompt
        items_for_prompt = []
        for i, item in enumerate(batch):
            items_for_prompt.append({
                "index": i,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "type": item.get("type", ""),
                "content": item.get("content", "")[:300],
                "published_at": item.get("published_at", ""),
            })

        prompt = CLASSIFY_PROMPT.format(
            count=len(batch),
            items_json=json.dumps(items_for_prompt, ensure_ascii=False),
        )

        results = gemini_client.generate_json(prompt, temperature=0.3)

        if not isinstance(results, list):
            print(f"[ANALYZER] Batch {batch_num} returned non-list, skipping")
            for item in batch:
                _apply_defaults(item)
                all_classified.append(item)
            continue

        # Merge classification results into items
        classified_indices = set()
        for result in results:
            idx = result.get("index", -1)
            if 0 <= idx < len(batch):
                classified_indices.add(idx)
                item = batch[idx]
                for key in [
                    "type", "importance_score", "novelty_score",
                    "credibility_score", "execution_value", "dev_value",
                    "agency_value", "tremoai_relevant", "summary_en",
                    "arabic_explanation", "why_it_matters", "opportunities",
                ]:
                    if key in result:
                        item[key] = result[key]
                all_classified.append(item)

        # Add any items that didn't get classified with defaults
        for i, item in enumerate(batch):
            if i not in classified_indices:
                _apply_defaults(item)
                all_classified.append(item)

        # Rate-limit between batches
        if batch_start + batch_size < len(items):
            time.sleep(1)

    return all_classified


def _apply_defaults(item):
    """Apply default classification values to an unclassified item."""
    item.setdefault("type", "skip")
    item.setdefault("importance_score", 30)
    item.setdefault("novelty_score", 50)
    item.setdefault("credibility_score", 50)
    item.setdefault("execution_value", 50)
    item.setdefault("dev_value", 50)
    item.setdefault("agency_value", 50)
    item.setdefault("tremoai_relevant", False)
    item.setdefault("summary_en", item.get("title", "")[:20])
    item.setdefault("arabic_explanation", {})
    item.setdefault("why_it_matters", "")
    item.setdefault("opportunities", [])


def score_and_alert(items):
    """Stage C+D: Calculate radar score and assign alert level."""
    for item in items:
        item["radar_score"] = calculate_radar_score(item)
        item["alert_level"] = assign_alert_level(item)
    return items


def filter_and_route(items):
    """Stage E: Filter out skips/low-importance and route to categories."""
    models, tools, research, signals = [], [], [], []
    github_repos, hf_models, opportunities, alerts = [], [], [], []
    skipped = 0

    for item in items:
        if item.get("type") == "skip" or item.get("importance_score", 0) < 25:
            skipped += 1
            continue

        t = item.get("type", "signal")
        if t == "model":
            models.append(item)
        elif t == "tool":
            tools.append(item)
        elif t == "research":
            research.append(item)
        elif t == "github_repo":
            github_repos.append(item)
        elif t == "hf_model":
            hf_models.append(item)
        else:
            signals.append(item)

        # Collect opportunities
        for opp in item.get("opportunities", []):
            if isinstance(opp, dict) and opp.get("title"):
                opp["triggered_by"] = item.get("title", "")
                opportunities.append(opp)

        # Collect P1+P2 alerts
        if item.get("alert_level") in ("P1", "P2"):
            alerts.append(item)

    p1_count = sum(1 for a in alerts if a.get("alert_level") == "P1")
    p2_count = sum(1 for a in alerts if a.get("alert_level") == "P2")

    return {
        "models": models,
        "tools": tools,
        "research": research,
        "signals": signals,
        "github_repos": github_repos,
        "hf_models": hf_models,
        "opportunities": opportunities,
        "alerts": alerts,
        "stats": {
            "analyzed_count": len(items),
            "skipped_count": skipped,
            "p1_count": p1_count,
            "p2_count": p2_count,
        },
    }


def run(all_signals):
    """Run full analysis pipeline: dedup -> classify -> score -> filter."""
    raw_count = len(all_signals)
    print(f"[ANALYZER] Starting analysis of {raw_count} raw signals")

    # Stage A: Entity resolution
    resolved = deduplicate_and_resolve(all_signals)
    deduped_count = len(resolved)
    print(
        f"[ANALYZER] Entity resolution: {raw_count} -> {deduped_count} unique entities"
    )

    # Stage B: Gemini classification
    classified = classify_batch(resolved)

    # Stage C+D: Scoring and alerting
    scored = score_and_alert(classified)

    # Stage E: Filtering and routing
    result = filter_and_route(scored)

    # Add dedup stats
    result["stats"]["raw_count"] = raw_count
    result["stats"]["deduped_count"] = deduped_count

    print(
        f"[ANALYZER] Analysis complete — "
        f"P1: {result['stats']['p1_count']}, "
        f"P2: {result['stats']['p2_count']}, "
        f"Skipped: {result['stats']['skipped_count']}"
    )
    return result
