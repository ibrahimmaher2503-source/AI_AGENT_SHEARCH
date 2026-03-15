"""Smoke test for AI Radar — validates imports, env vars, and utility functions."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["AI_RADAR_SKIP_VALIDATION"] = "1"

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS ✓ {name}")
        passed += 1
    else:
        print(f"  FAIL ✗ {name}")
        failed += 1


def test_env_vars():
    print("\n[SMOKE] Checking environment variables...")
    required = [
        "GEMINI_API_KEY", "NOTION_API_KEY", "TAVILY_API_KEY",
        "NOTION_DB_MODELS", "NOTION_DB_TOOLS", "NOTION_DB_RESEARCH",
        "NOTION_DB_SIGNALS", "NOTION_DB_OPPORTUNITIES", "NOTION_DB_BRIEFS",
        "NOTION_DB_OSS_RADAR", "NOTION_DB_HF_RADAR", "NOTION_DB_ALERTS",
        "NOTION_PARENT_PAGE_ID",
    ]
    for var in required:
        val = os.environ.get(var, "")
        if val:
            check(f"ENV {var}", True)
        else:
            print(f"  WARN ⚠ {var} not set (required for production)")


def test_imports():
    print("\n[SMOKE] Checking module imports...")
    modules = [
        "utils", "sources", "prompts",
        "agents.collector", "agents.github_radar", "agents.hf_radar",
        "agents.analyzer", "agents.publisher", "agents.brief_writer",
    ]
    for mod in modules:
        try:
            __import__(mod)
            check(f"import {mod}", True)
        except Exception as e:
            check(f"import {mod} ({e})", False)


def test_utils():
    print("\n[SMOKE] Checking utility functions...")
    from utils import (get_today_iso, extract_domain, normalize_url,
                       score_to_rating, title_similarity, normalize_company,
                       calculate_radar_score, assign_alert_level)

    # get_today_iso
    today = get_today_iso()
    check("get_today_iso() returns valid date", len(today) == 10 and today[4] == "-")

    # extract_domain
    domain = extract_domain("https://openai.com/blog")
    check('extract_domain("https://openai.com/blog") == "openai.com"', domain == "openai.com")

    # normalize_url
    norm = normalize_url("https://example.com/?utm_source=twitter")
    check("normalize_url strips tracking params", "utm_source" not in norm)

    # score_to_rating
    rating = score_to_rating(85)
    check('score_to_rating(85) == "⭐⭐⭐⭐⭐"', rating == "⭐⭐⭐⭐⭐")

    # title_similarity
    sim = title_similarity("a b c d e f", "a b c d e g")
    check("title_similarity with 5 shared words", sim == True)

    # normalize_company
    comp = normalize_company("openai")
    check('normalize_company("openai") == "OpenAI"', comp == "OpenAI")

    # calculate_radar_score
    score = calculate_radar_score({
        "novelty_score": 80, "credibility_score": 90,
        "execution_value": 70, "dev_value": 60, "agency_value": 50
    })
    check("calculate_radar_score returns valid float", isinstance(score, float) and 0 <= score <= 100)

    # assign_alert_level
    level = assign_alert_level({"radar_score": 82, "source_priority": "high"})
    check('assign_alert_level(radar_score=82) == "P1"', level == "P1")

    level2 = assign_alert_level({"radar_score": 60, "source_priority": "medium"})
    check('assign_alert_level(radar_score=60) == "P2"', level2 == "P2")

    level3 = assign_alert_level({"radar_score": 35, "source_priority": "low"})
    check('assign_alert_level(radar_score=35) == "P3"', level3 == "P3")


def main():
    print("[SMOKE] 🧪 AI Radar Smoke Test")
    test_env_vars()
    test_imports()
    test_utils()

    print(f"\n[SMOKE] Results: {passed} passed, {failed} failed")
    if failed > 0:
        print("[SMOKE] ❌ Some checks failed")
        sys.exit(1)
    else:
        print("[SMOKE] ✅ All checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
