"""
Layer A+D: Collect AI signals from official sources via Tavily web search.
Returns a list of normalised signal dicts ready for scoring/filtering.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tavily_client
from sources import SOURCES, TAVILY_QUERIES
from utils import extract_domain, truncate, get_source_priority, get_today_iso


def run():
    """Collect signals from Tavily web search (Layer A+D). Returns list of signal dicts."""
    print(f"[COLLECTOR] Starting collection — {len(TAVILY_QUERIES)} queries")

    # Use Tavily multi_search for all queries
    raw_results = tavily_client.multi_search(TAVILY_QUERIES, max_results=5)

    # Convert to signal schema
    signals = []
    seen_urls = set()

    for r in raw_results:
        url = r.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        domain = extract_domain(url)
        priority = get_source_priority(url, SOURCES)

        signal = {
            "title": r.get("title", "").strip(),
            "url": url,
            "source": domain,
            "type": _guess_type(domain),
            "published_at": r.get("published_date", get_today_iso()),
            "content": truncate(r.get("content", ""), 500),
            "raw_score": min(r.get("score", 0.5), 1.0),
            "source_priority": priority,
        }
        signals.append(signal)

    print(f"[COLLECTOR] Collected {len(signals)} unique signals (from {len(raw_results)} raw results)")
    return signals


def _guess_type(domain):
    """Guess signal type from domain name."""
    domain = domain.lower()
    if any(x in domain for x in ["arxiv", "paperswithcode", "scholar"]):
        return "research"
    if "github.com" in domain:
        return "github_repo"
    if "huggingface.co" in domain:
        return "hf_model"
    if any(x in domain for x in [
        "openai.com", "anthropic.com", "deepmind",
        "meta.com", "mistral.ai", "googleblog",
    ]):
        return "company"
    if any(x in domain for x in [
        "techcrunch", "venturebeat", "theverge", "wired", "reuters",
    ]):
        return "news"
    if any(x in domain for x in ["producthunt", "theresanai", "futurepedia"]):
        return "products"
    return "signal"
