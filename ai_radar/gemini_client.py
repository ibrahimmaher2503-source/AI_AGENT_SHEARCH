"""Gemini API client for text and JSON generation."""

import requests
import json
import time

import config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def generate_text(prompt, temperature=0.3):
    """Send prompt to Gemini, return generated text string."""
    url = f"{GEMINI_URL}?key={config.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"[GEMINI] Error {resp.status_code}: {resp.text[:200]}")
            return ""
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text
    except Exception as e:
        print(f"[GEMINI] Request failed: {e}")
        return ""


def _clean_json_text(text):
    """Remove markdown code fences and clean up for JSON parsing."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def generate_json(prompt, temperature=0.3):
    """Send prompt to Gemini, parse and return JSON (list or dict)."""
    for attempt in range(2):
        text = generate_text(prompt, temperature=temperature)
        if not text:
            if attempt == 0:
                print("[GEMINI] Empty response, retrying...")
                time.sleep(2)
                continue
            return []
        cleaned = _clean_json_text(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"[GEMINI] JSON parse failed, retrying after cleanup... Error: {e}")
                time.sleep(2)
                continue
            print(f"[GEMINI] JSON parse failed after retry. First 300 chars: {cleaned[:300]}")
            return []
    return []
