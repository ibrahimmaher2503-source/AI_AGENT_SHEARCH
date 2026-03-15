# Contract: Gemini 2.0 Flash API

**Base URL**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`

## Authentication

API key as query parameter: `?key={GEMINI_API_KEY}`

## Generate Content

```
POST /v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}
```

**Request body**:
```json
{
  "contents": [
    {
      "parts": [
        { "text": "{prompt}" }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.3
  }
}
```

**Response**:
```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          { "text": "{generated_text}" }
        ]
      }
    }
  ]
}
```

**Extract text**: `response["candidates"][0]["content"]["parts"][0]["text"]`

## JSON Parsing Strategy

1. Extract raw text from response
2. Clean up: `.replace("```json", "").replace("```", "").strip()`
3. Attempt `json.loads()`
4. On parse failure: retry request once
5. On second failure: log first 200 chars, return `[]` or `{}`

## Parameters

| Use Case | Temperature |
|----------|-------------|
| Classification (CLASSIFY_PROMPT) | 0.3 |
| Brief writing (BRIEF_PROMPT) | 0.5 |

## Limits

- Timeout: 60 seconds
- Batch size: max 10 items per classification request
- Rate: generous for low-volume use (~15 requests/day)
