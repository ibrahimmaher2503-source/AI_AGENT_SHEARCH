import sys
import os
import io
import json
import argparse
import logging
import requests

# Fix Windows console encoding for emoji output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure ai_radar directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # This triggers env var validation
from utils import get_today_iso
from agents import collector, github_radar, hf_radar, analyzer, publisher, brief_writer
import github_client

log = logging.getLogger("ai_radar")

# Intermediate files for passing data between separate process invocations
# (e.g. when the workflow runs --layer collect, then --layer analyze as separate steps).
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_BASE_DIR, ".pipeline_data")
SIGNALS_FILE = os.path.join(DATA_DIR, "signals.json")
ANALYZED_FILE = os.path.join(DATA_DIR, "analyzed.json")


def _setup_logging():
    """Configure logging to stdout + daily log file. Called once from main()."""
    log_dir = os.path.join(_BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"radar_{get_today_iso()}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


# ---------------------------------------------------------------------------
# Rate-limit dashboard
# ---------------------------------------------------------------------------
def log_rate_limits():
    """Log remaining GitHub API quotas."""
    log.info("--- Rate Limit Dashboard ---")
    try:
        resp = requests.get(
            "https://api.github.com/rate_limit",
            headers=github_client._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            core = data.get("resources", {}).get("core", {})
            search = data.get("resources", {}).get("search", {})
            log.info(
                f"GitHub Core: {core.get('remaining', '?')}/{core.get('limit', '?')} "
                f"| Search: {search.get('remaining', '?')}/{search.get('limit', '?')}"
            )
        else:
            log.info(f"GitHub rate limit check returned {resp.status_code}")
    except Exception as e:
        log.info(f"GitHub rate limit check failed: {e}")
    log.info("----------------------------")


# ---------------------------------------------------------------------------
# Stage functions
# ---------------------------------------------------------------------------
def stage_collect(persist=True):
    """Layer A+B+C+D: collect all signals, optionally save to disk."""
    log.info("=== Stage: COLLECT ===")

    web_signals = collector.run()
    log.info(f"Web signals: {len(web_signals)}")

    github_signals = github_radar.run()
    log.info(f"GitHub signals: {len(github_signals)}")

    hf_signals = hf_radar.run()
    log.info(f"HF signals: {len(hf_signals)}")

    all_signals = web_signals + github_signals + hf_signals
    log.info(f"Total raw signals: {len(all_signals)}")

    if persist:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SIGNALS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_signals, f, ensure_ascii=False)
        log.info(f"Signals saved to {SIGNALS_FILE}")
    return all_signals


def stage_analyze(all_signals=None, persist=True):
    """Entity resolution + Gemini classification + scoring."""
    log.info("=== Stage: ANALYZE ===")

    if all_signals is None:
        if not os.path.exists(SIGNALS_FILE):
            log.error(f"No signals file found at {SIGNALS_FILE}. Run --layer collect first.")
            sys.exit(1)
        with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
            all_signals = json.load(f)
        log.info(f"Loaded {len(all_signals)} signals from disk")

    analyzed = analyzer.run(all_signals)
    log.info(f"Stats: {analyzed['stats']}")
    log.info(
        f"Breakdown — models:{len(analyzed['models'])} "
        f"tools:{len(analyzed['tools'])} research:{len(analyzed['research'])} "
        f"signals:{len(analyzed['signals'])} oss:{len(analyzed['github_repos'])} "
        f"hf:{len(analyzed['hf_models'])} opps:{len(analyzed['opportunities'])} "
        f"alerts:{len(analyzed['alerts'])}"
    )

    if persist:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ANALYZED_FILE, "w", encoding="utf-8") as f:
            json.dump(analyzed, f, ensure_ascii=False)
        log.info(f"Analyzed data saved to {ANALYZED_FILE}")
    return analyzed


def stage_publish(analyzed=None):
    """Publish to Notion databases + generate daily brief."""
    log.info("=== Stage: PUBLISH ===")

    if analyzed is None:
        if not os.path.exists(ANALYZED_FILE):
            log.error(f"No analyzed file found at {ANALYZED_FILE}. Run --layer analyze first.")
            sys.exit(1)
        with open(ANALYZED_FILE, "r", encoding="utf-8") as f:
            analyzed = json.load(f)
        log.info("Loaded analyzed data from disk")

    publish_stats = publisher.run(analyzed)
    log.info(f"Publish stats: {publish_stats}")

    brief_writer.run(analyzed, publish_stats)
    log.info("Daily brief complete")
    return publish_stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="AI Radar pipeline")
    parser.add_argument(
        "--layer",
        choices=["collect", "analyze", "publish", "weekly", "all"],
        default="all",
        help="Run a specific pipeline stage (default: all)",
    )
    args = parser.parse_args()

    _setup_logging()
    log.info(f"AI Radar starting — {get_today_iso()}")
    log.info(f"DRY_RUN: {config.DRY_RUN} | Layer: {args.layer}")

    if args.layer == "collect":
        stage_collect()
    elif args.layer == "analyze":
        stage_analyze()
    elif args.layer == "publish":
        stage_publish()
    elif args.layer == "weekly":
        from agents import weekly_digest
        log.info("=== Stage: WEEKLY DIGEST ===")
        weekly_digest.run()
    else:
        all_signals = stage_collect(persist=False)
        analyzed = stage_analyze(all_signals, persist=False)
        stage_publish(analyzed)

    if args.layer in ("collect", "all"):
        log_rate_limits()

    log.info("Run complete.")


if __name__ == "__main__":
    main()
