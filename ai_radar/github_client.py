"""GitHub API client for repository and release lookups."""

import time
import requests

import config

GITHUB_API = "https://api.github.com"


def _headers():
    """Build request headers, including auth token if available."""
    h = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return h


def _sleep():
    """Rate-limit pause: short with token, longer without."""
    if config.GITHUB_TOKEN:
        time.sleep(0.3)
    else:
        time.sleep(2)


def search_repos(query, max_results=5):
    """Search GitHub repositories. Returns list of repo dicts."""
    url = f"{GITHUB_API}/search/repositories"
    params = {"q": query, "sort": "created", "order": "desc", "per_page": max_results}
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[GITHUB] Search error {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[GITHUB] Search failed: {e}")
        return []


def get_org_repos(org, max_results=10):
    """Get repos from a GitHub org sorted by push date. Returns list."""
    url = f"{GITHUB_API}/orgs/{org}/repos"
    params = {"sort": "pushed", "per_page": max_results}
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[GITHUB] Org repos error {resp.status_code} for {org}")
            return []
        return resp.json()
    except Exception as e:
        print(f"[GITHUB] Org repos failed for {org}: {e}")
        return []


def get_latest_release(owner, repo):
    """Get latest release for a repo. Returns dict or None."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None
