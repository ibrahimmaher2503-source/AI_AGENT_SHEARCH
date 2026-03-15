# Contract: Notion API

**Version**: 2022-06-28
**Base URL**: `https://api.notion.com/v1`

## Headers (all requests)

```
Authorization: Bearer {NOTION_API_KEY}
Content-Type: application/json
Notion-Version: 2022-06-28
```

## Endpoints Used

### Query Database

```
POST /databases/{database_id}/query
```

**Request body** (filter by URL property):
```json
{
  "filter": {
    "property": "Source URL",
    "url": {
      "equals": "https://example.com/article"
    }
  },
  "page_size": 1
}
```

**Request body** (filter by title):
```json
{
  "filter": {
    "property": "Name",
    "title": {
      "equals": "Some Title"
    }
  },
  "page_size": 1
}
```

**Request body** (filter by rich_text field):
```json
{
  "filter": {
    "property": "Repo Name",
    "rich_text": {
      "equals": "owner/repo"
    }
  },
  "page_size": 1
}
```

**Response**: `{ "results": [...], "has_more": bool }`

### Create Page

```
POST /pages
```

**Request body**:
```json
{
  "parent": { "database_id": "{database_id}" },
  "icon": { "type": "emoji", "emoji": "🤖" },
  "properties": {
    "Name": { "title": [{ "text": { "content": "GPT-5" } }] },
    "Company": { "select": { "name": "OpenAI" } },
    "Radar Score": { "number": 85.5 },
    "Source URL": { "url": "https://openai.com/blog/gpt-5" },
    "Release Date": { "date": { "start": "2026-03-15" } },
    "TremoAI Relevant": { "checkbox": false },
    "Tags": { "multi_select": [{ "name": "Has API" }, { "name": "Free Tier" }] },
    "Key Capabilities": { "rich_text": [{ "text": { "content": "..." } }] }
  },
  "children": []
}
```

**Response**: `{ "id": "page-id", ... }` or error

## Rate Limits

- 3 requests/second average
- Retry on 429: wait 2 seconds, retry once
- Timeout: 30 seconds per request

## Rich Text Constraint

- Maximum 2000 characters per rich_text content block
- Use `chunk_rich_text()` to split longer content into multiple blocks
