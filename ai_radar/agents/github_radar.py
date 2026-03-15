"""
Layer B: GitHub new repos, releases, and org watchlist.
Discovers new AI repositories, checks watched orgs for releases,
and finds trending AI projects on GitHub.
"""

import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import github_client
from sources import GITHUB_ORGS, GITHUB_SEARCH_QUERIES
from utils import get_today_iso


# List of known high-priority orgs for signal scoring
KNOWN_ORGS = [
    "openai", "anthropics", "google-deepmind", "facebookresearch",
    "mistralai", "huggingface", "microsoft", "ollama-org",
    "langchain-ai", "run-llama", "chroma-core", "ggerganov",
]


def _repo_to_signal(repo, release=None):
    """Convert a GitHub repo dict to a normalised signal dict."""
    full_name = repo.get("full_name", "")
    desc = repo.get("description") or ""
    stars = repo.get("stargazers_count", 0)
    owner = repo.get("owner", {}).get("login", "")
    topics = repo.get("topics", [])

    if not full_name:
        return None

    # Determine source priority based on org membership
    priority = "high" if owner.lower() in KNOWN_ORGS else "medium"

    content_parts = [desc]
    if topics:
        content_parts.append(f"Topics: {', '.join(topics[:10])}")
    content_parts.append(f"Stars: {stars}")

    return {
        "title": f"{full_name}: {desc[:100]}" if desc else full_name,
        "url": repo.get("html_url", f"https://github.com/{full_name}"),
        "source": "github.com",
        "type": "github_repo",
        "published_at": repo.get("created_at", get_today_iso()),
        "content": " | ".join(content_parts)[:500],
        "raw_score": min(stars / 1000.0, 1.0),
        "source_priority": priority,
        "repo_name": full_name,
        "owner": owner,
        "stars": stars,
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language") or "Other",
        "topics": topics,
        "created_at": repo.get("created_at", ""),
        "pushed_at": repo.get("pushed_at", ""),
        "has_release": release is not None,
    }


def fetch_new_repos(queries):
    """Search GitHub for new AI repos matching queries. Returns list of signal dicts."""
    results = []
    for i, query in enumerate(queries):
        print(f"[GITHUB] Searching repos {i+1}/{len(queries)}: {query[:60]}")
        repos = github_client.search_repos(query, max_results=5)
        for repo in repos:
            signal = _repo_to_signal(repo)
            if signal:
                results.append(signal)
        github_client._sleep()
    print(f"[GITHUB] Found {len(results)} repos from search")
    return results


def fetch_org_releases(orgs):
    """Check watched orgs for recent releases. Returns list of signal dicts."""
    results = []
    cutoff = (datetime.utcnow() - timedelta(days=3)).isoformat()
    for org in orgs:
        print(f"[GITHUB] Fetching org repos: {org}")
        repos = github_client.get_org_repos(org, max_results=5)
        github_client._sleep()
        for repo in repos:
            pushed = repo.get("pushed_at", "")
            # Only check repos pushed in last 7 days
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            if pushed < week_ago:
                continue
            owner = repo.get("owner", {}).get("login", org)
            repo_name = repo.get("name", "")
            release = github_client.get_latest_release(owner, repo_name)
            github_client._sleep()
            if release:
                pub = release.get("published_at", "")
                if pub >= cutoff:
                    signal = _repo_to_signal(repo, release=release)
                    if signal:
                        signal["type"] = "github_release"
                        signal["has_release"] = True
                        print(f"[GITHUB] Found release: {repo_name} ({release.get('tag_name', '')})")
                        results.append(signal)
    print(f"[GITHUB] Found {len(results)} releases from orgs")
    return results


def fetch_trending_signals(queries=None):
    """Search for trending AI repos. Returns list of signal dicts."""
    # Build trending queries dynamically based on current date
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    trending_queries = [
        f"AI stars:>200 pushed:>{week_ago} language:Python",
        f"LLM stars:>100 pushed:>{week_ago} language:Python",
        f"machine learning stars:>200 pushed:>{week_ago}",
    ]
    results = []
    for q in trending_queries:
        repos = github_client.search_repos(q, max_results=5)
        for repo in repos:
            signal = _repo_to_signal(repo)
            if signal:
                results.append(signal)
        github_client._sleep()
    print(f"[GITHUB] Found {len(results)} trending signals")
    return results


def run():
    """Run full GitHub radar. Returns list of deduplicated signal dicts."""
    print("[GITHUB] Starting GitHub Radar")
    all_signals = []

    # Fetch new repos from configured search queries
    new_repos = fetch_new_repos(GITHUB_SEARCH_QUERIES)
    all_signals.extend(new_repos)

    # Fetch releases from watched organisations
    org_releases = fetch_org_releases(GITHUB_ORGS)
    all_signals.extend(org_releases)

    # Fetch trending signals
    trending = fetch_trending_signals()
    all_signals.extend(trending)

    # Deduplicate by URL
    seen = set()
    unique = []
    for s in all_signals:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique.append(s)

    print(f"[GITHUB] Total unique GitHub signals: {len(unique)}")
    return unique


if __name__ == "__main__":
    signals = run()
    for s in signals[:5]:
        print(f"  {s['stars']}* {s['title'][:80]}")
