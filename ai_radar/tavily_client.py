"""Tavily search API client."""

import time
import requests

import config

TAVILY_URL = "https://api.tavily.com/search"


def search(query, max_results=5):
    """Search Tavily for a single query. Returns list of result dicts."""
    payload = {
        "api_key": config.TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    try:
        resp = requests.post(TAVILY_URL, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"[TAVILY] Error {resp.status_code} for query: {query[:50]}")
            return []
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        print(f"[TAVILY] Request failed for query '{query[:50]}': {e}")
        return []


def multi_search(queries, max_results=5):
    """Search Tavily for multiple queries with rate limiting. Returns combined list."""
    all_results = []
    for i, query in enumerate(queries):
        print(f"[TAVILY] Running query {i+1}/{len(queries)}: {query[:60]}")
        results = search(query, max_results=max_results)
        all_results.extend(results)
        if i < len(queries) - 1:
            time.sleep(0.5)
    print(f"[TAVILY] Total results: {len(all_results)}")
    return all_results
