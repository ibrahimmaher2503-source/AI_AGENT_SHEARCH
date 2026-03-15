# Contract: Tavily Search API

**Base URL**: `https://api.tavily.com/search`

## Search

```
POST https://api.tavily.com/search
```

**Request body**:
```json
{
  "api_key": "{TAVILY_API_KEY}",
  "query": "new AI model released today 2026",
  "max_results": 5,
  "search_depth": "basic"
}
```

**Response**:
```json
{
  "results": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "content": "Article snippet...",
      "score": 0.85,
      "published_date": "2026-03-15"
    }
  ]
}
```

## Limits

- Timeout: 30 seconds
- Rate: `time.sleep(0.5)` between queries
- Max results per query: 5
- Expected: 15 queries per run × 5 results = ~75 raw results
- If fewer than 3 results returned: log warning, continue
