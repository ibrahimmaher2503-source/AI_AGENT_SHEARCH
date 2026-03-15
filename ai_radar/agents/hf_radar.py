"""
Layer C: Hugging Face new and trending models radar.
Discovers recently published and trending models across key HF tasks,
converts them to normalised signal dicts for downstream scoring.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hf_client
from sources import HF_TASKS
from utils import get_today_iso, truncate

# Well-known orgs whose models receive high priority
KNOWN_ORGS = [
    "openai", "meta-llama", "google", "microsoft", "mistralai",
    "huggingface", "facebook", "stabilityai", "bigscience",
]


def _model_to_signal(model):
    """Convert an HF model dict to a normalised signal dict.
    Returns None if the model lacks a usable identifier.
    """
    model_id = model.get("modelId") or model.get("id", "")
    if not model_id:
        return None

    org = model_id.split("/")[0] if "/" in model_id else ""
    pipeline = model.get("pipeline_tag") or model.get("pipelineTag", "")
    downloads = model.get("downloads", 0)
    likes = model.get("likes", 0)
    last_mod = model.get("lastModified", "")

    # Extract license from model card metadata
    card_data = model.get("cardData", {}) or {}
    license_val = card_data.get("license", "") if isinstance(card_data, dict) else ""

    # Build human-readable content summary
    tags = model.get("tags", [])
    content_parts = []
    if pipeline:
        content_parts.append(f"Task: {pipeline}")
    content_parts.append(f"Downloads: {downloads:,}")
    content_parts.append(f"Likes: {likes}")
    if tags:
        content_parts.append(f"Tags: {', '.join(tags[:5])}")

    priority = "high" if org.lower() in KNOWN_ORGS else "medium"

    return {
        "title": model_id,
        "url": f"https://huggingface.co/{model_id}",
        "source": "huggingface.co",
        "type": "hf_model",
        "published_at": last_mod[:10] if last_mod else get_today_iso(),
        "content": truncate(" | ".join(content_parts), 500),
        "raw_score": min(downloads / 10000.0, 1.0),
        "source_priority": priority,
        "model_id": model_id,
        "organization": org,
        "task": pipeline,
        "downloads": downloads,
        "likes": likes,
        "last_modified": last_mod,
        "license": str(license_val),
        "pipeline_tag": pipeline,
    }


def _fetch_new_signals():
    """Fetch recently created models (last 3 days) across all configured tasks."""
    signals = []
    for task in HF_TASKS:
        print(f"[HF] Fetching task: {task} (new models, last 3 days)")
        models = hf_client.fetch_new_models(task, limit=20, days_back=3)
        count = 0
        for m in models:
            pipeline = m.get("pipeline_tag") or m.get("pipelineTag", "")
            if not pipeline:
                continue
            signal = _model_to_signal(m)
            if signal:
                signals.append(signal)
                count += 1
        print(f"[HF] Found {count} new models for {task}")
        time.sleep(0.5)
    return signals


def _fetch_trending_signals():
    """Fetch trending models (top downloads, updated in last 7 days) across tasks."""
    signals = []
    for task in HF_TASKS:
        print(f"[HF] Fetching task: {task} (trending models)")
        models = hf_client.fetch_trending_models(task, limit=10)
        count = 0
        for m in models:
            pipeline = m.get("pipeline_tag") or m.get("pipelineTag", "")
            if not pipeline:
                continue
            signal = _model_to_signal(m)
            if signal:
                signals.append(signal)
                count += 1
        print(f"[HF] Found {count} trending models for {task}")
        time.sleep(0.5)
    return signals


def _deduplicate(signals):
    """Remove duplicate signals by model_id, preserving first occurrence."""
    seen = set()
    unique = []
    for s in signals:
        mid = s.get("model_id", s["url"])
        if mid not in seen:
            seen.add(mid)
            unique.append(s)
    return unique


def run():
    """Run full HF radar. Returns list of deduplicated signal dicts."""
    print("[HF] Starting Hugging Face Radar")

    all_signals = []
    all_signals.extend(_fetch_new_signals())
    all_signals.extend(_fetch_trending_signals())

    unique = _deduplicate(all_signals)
    print(f"[HF] Total unique HF signals: {len(unique)}")
    return unique
