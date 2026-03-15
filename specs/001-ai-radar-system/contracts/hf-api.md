# Contract: Hugging Face Hub API

**Base URL**: `https://huggingface.co/api`

## Authentication

None required for public models.

## List Models (sorted by last modified)

```
GET /models?sort=lastModified&direction=-1&limit=20&pipeline_tag={task}
```

## List Models (sorted by downloads)

```
GET /models?sort=downloads&direction=-1&limit=10&pipeline_tag={task}
```

**Response**: Array of model objects:
```json
[
  {
    "modelId": "meta-llama/Llama-3-70B",
    "author": "meta-llama",
    "lastModified": "2026-03-14T12:00:00.000Z",
    "downloads": 500000,
    "likes": 1200,
    "pipeline_tag": "text-generation",
    "tags": ["text-generation", "transformers"],
    "cardData": {
      "license": "llama3"
    },
    "siblings": [...]
  }
]
```

## Key Fields

| Response Field | Maps To |
|----------------|---------|
| modelId | model_id, title |
| author | organization |
| lastModified | last_modified, published_at |
| downloads | downloads |
| likes | likes |
| pipeline_tag | pipeline_tag, task |
| cardData.license | license |

## Model URL Construction

```
https://huggingface.co/{modelId}
```

## Limits

- Timeout: 30 seconds
- Rate: `time.sleep(0.5)` between requests
- No auth required
- Client-side filtering: only keep models modified within `days_back` days
- Skip models without a description or pipeline_tag
