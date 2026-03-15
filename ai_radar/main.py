import sys
import os
import io

# Fix Windows console encoding for emoji output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure ai_radar directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # This triggers env var validation
from utils import get_today_iso
from agents import collector, github_radar, hf_radar, analyzer, publisher, brief_writer


def main():
    print(f"[MAIN] 🧠 AI Radar starting — {get_today_iso()}")
    print(f"[MAIN] DRY_RUN: {config.DRY_RUN}")

    # Layer A + D: Official blogs + Tavily web
    web_signals = collector.run()
    print(f"[MAIN] Web signals: {len(web_signals)}")

    # Layer B: GitHub Radar
    github_signals = github_radar.run()
    print(f"[MAIN] GitHub signals: {len(github_signals)}")

    # Layer C: Hugging Face Radar
    hf_signals = hf_radar.run()
    print(f"[MAIN] HF signals: {len(hf_signals)}")

    # Merge all signals
    all_signals = web_signals + github_signals + hf_signals
    print(f"[MAIN] Total raw signals: {len(all_signals)}")

    # Entity resolution + classification + scoring
    analyzed = analyzer.run(all_signals)
    print(f"[MAIN] Stats: {analyzed['stats']}")
    print(
        f"[MAIN] Breakdown — models:{len(analyzed['models'])} "
        f"tools:{len(analyzed['tools'])} research:{len(analyzed['research'])} "
        f"signals:{len(analyzed['signals'])} oss:{len(analyzed['github_repos'])} "
        f"hf:{len(analyzed['hf_models'])} opps:{len(analyzed['opportunities'])} "
        f"alerts:{len(analyzed['alerts'])}"
    )

    # Write to all 9 Notion databases
    publish_stats = publisher.run(analyzed)
    print(f"[MAIN] Publish stats: {publish_stats}")

    # Daily AI Brief
    brief_writer.run(analyzed, publish_stats)
    print("[MAIN] Daily brief complete")

    print("[MAIN] ✅ Run complete.")


if __name__ == "__main__":
    main()
