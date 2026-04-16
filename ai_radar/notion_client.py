"""Notion API client for AI Radar."""

import requests
import time
import json

import config

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {config.NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _notion_request(method, url, payload=None):
    """Make a Notion API request with retry on 429."""
    for attempt in range(2):
        try:
            if method == "POST":
                resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
            else:
                resp = requests.get(url, headers=_headers(), timeout=30)
            if resp.status_code == 429:
                print(f"[NOTION] 429 received, retrying after 2s...")
                time.sleep(2)
                continue
            if resp.status_code >= 400:
                print(f"[NOTION] Error {resp.status_code}: {resp.text[:200]}")
                return None
            return resp.json()
        except Exception as e:
            print(f"[NOTION] Request failed: {e}")
            return None
    return None


def query_database(db_id, filter_payload=None):
    """Query a Notion database with optional filter. Returns list of results."""
    url = f"{NOTION_BASE}/databases/{db_id}/query"
    payload = {}
    if filter_payload:
        payload["filter"] = filter_payload
    payload["page_size"] = 10
    result = _notion_request("POST", url, payload)
    if result and "results" in result:
        return result["results"]
    return []


def create_page(db_id, properties, icon_emoji="\U0001f916", children=None):
    """Create a page in a Notion database. Returns response dict or None."""
    if config.DRY_RUN:
        # Extract title for logging
        title = ""
        for key, val in properties.items():
            if isinstance(val, dict) and "title" in val:
                title_arr = val["title"]
                if title_arr and isinstance(title_arr, list):
                    title = title_arr[0].get("text", {}).get("content", "")
                break
        print(f"[NOTION] DRY_RUN — would create page: {title}")
        print(f"[NOTION] DRY_RUN — properties: {json.dumps(properties, ensure_ascii=False)[:500]}")
        return {"id": "dry-run-id"}

    url = f"{NOTION_BASE}/pages"
    payload = {
        "parent": {"database_id": db_id},
        "icon": {"type": "emoji", "emoji": icon_emoji},
        "properties": properties,
    }
    if children:
        payload["children"] = children[:100]  # Notion limit: 100 children per request
    result = _notion_request("POST", url, payload)
    if result and "id" in result:
        return result
    return None


_URL_PROP_NAMES = ["Source URL", "URL"]
_TITLE_PROP_NAMES = ["Name", "Title", "Date", "Repo Name", "Model Name", "Alert Title", "Opportunity Title"]


def url_exists_in_database(db_id, url):
    """Check if a URL already exists in the database."""
    for prop_name in _URL_PROP_NAMES:
        filter_payload = {"property": prop_name, "url": {"equals": url}}
        results = query_database(db_id, filter_payload)
        if results:
            return True
    return False


def query_database_by_title(db_id, title):
    """Query a Notion database for pages matching a specific title. Returns list of page dicts."""
    for prop_name in _TITLE_PROP_NAMES:
        filter_payload = {"property": prop_name, "title": {"equals": title}}
        results = query_database(db_id, filter_payload)
        if results:
            return results
    return []


def title_exists_in_database(db_id, title):
    """Check if a title already exists in the database."""
    return len(query_database_by_title(db_id, title)) > 0


def query_database_by_titles(db_id, titles, prop_name="Date"):
    """Batch-query a Notion database for pages matching any of the given titles. Returns list of page dicts."""
    if not titles:
        return []
    filter_payload = {
        "or": [{"property": prop_name, "title": {"equals": t}} for t in titles]
    }
    return query_database(db_id, filter_payload)


def field_exists_in_database(db_id, field_name, value):
    """Check if a rich_text field value exists in the database."""
    filter_payload = {"property": field_name, "rich_text": {"equals": value}}
    results = query_database(db_id, filter_payload)
    return len(results) > 0
