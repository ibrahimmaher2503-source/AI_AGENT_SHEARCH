# Contract: GitHub REST API

**Base URL**: `https://api.github.com`

## Authentication (optional)

```
Authorization: Bearer {GITHUB_TOKEN}
```

With token: 5000 req/hr, `time.sleep(0.3)` between calls
Without token: 60 req/hr, `time.sleep(2)` between calls

## Search Repositories

```
GET /search/repositories?q={query}&sort=created&order=desc&per_page=5
```

**Response**:
```json
{
  "total_count": 42,
  "items": [
    {
      "full_name": "owner/repo",
      "html_url": "https://github.com/owner/repo",
      "description": "...",
      "stargazers_count": 150,
      "forks_count": 20,
      "language": "Python",
      "topics": ["ai", "llm"],
      "created_at": "2026-03-10T00:00:00Z",
      "pushed_at": "2026-03-14T00:00:00Z",
      "owner": { "login": "owner" }
    }
  ]
}
```

## Get Org Repos

```
GET /orgs/{org}/repos?sort=pushed&per_page=5
```

**Response**: Array of repository objects (same structure as search items)

## Get Latest Release

```
GET /repos/{owner}/{repo}/releases/latest
```

**Response**:
```json
{
  "tag_name": "v1.0.0",
  "name": "Release Name",
  "published_at": "2026-03-14T00:00:00Z",
  "html_url": "https://github.com/owner/repo/releases/tag/v1.0.0"
}
```

Returns 404 if no releases exist.

## Rate Limits

- Timeout: 30 seconds
- With token: `time.sleep(0.3)`
- Without token: `time.sleep(2)`
- On 403/429: increase sleep, log clearly
