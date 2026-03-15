"""Hugging Face API client for model discovery."""

import time
import requests
from datetime import datetime, timedelta

import config

HF_API = "https://huggingface.co/api"


def fetch_new_models(task, limit=20, days_back=3):
    """Fetch recently modified models for a task. Returns list of model dicts."""
    url = f"{HF_API}/models"
    params = {
        "sort": "lastModified",
        "direction": "-1",
        "limit": limit,
        "pipeline_tag": task,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[HF] Error {resp.status_code} for task: {task}")
            return []
        models = resp.json()
        # Client-side date filtering
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        filtered = [m for m in models if m.get("lastModified", "") >= cutoff]
        return filtered
    except Exception as e:
        print(f"[HF] Failed for task {task}: {e}")
        return []


def fetch_trending_models(task, limit=10):
    """Fetch top downloaded models for a task (updated in last 7 days). Returns list."""
    url = f"{HF_API}/models"
    params = {
        "sort": "downloads",
        "direction": "-1",
        "limit": limit,
        "pipeline_tag": task,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[HF] Trending error {resp.status_code} for task: {task}")
            return []
        models = resp.json()
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        filtered = [m for m in models if m.get("lastModified", "") >= cutoff]
        return filtered
    except Exception as e:
        print(f"[HF] Trending failed for task {task}: {e}")
        return []
