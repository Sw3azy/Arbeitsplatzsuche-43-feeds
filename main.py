"""
Arbeitsplatzsuche-43 — Research Jobs Crawler
Inspired by Paper Picnic (github.com/sumtxt/picnic)

Run: python main.py
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from src.scrapers.static_scraper import scrape_static
from src.scrapers.ats_scraper import scrape_ats
from src.scrapers.aggregator import scrape_aggregator
from src.scrapers.playwright_scraper import scrape_dynamic
from src.data_processor import deduplicate, clean_jobs
from src.classifier import classify_jobs
from src.json_renderer import render_output
from src.rss_renderer import render_rss
from src.sources_exporter import export_sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

SOURCES_PATH = Path("parameters/sources.json")
MEMORY_PATH  = Path("memory/job_ids.csv")
OUTPUT_PATH  = Path("output/jobs.json")
DOCS_PATH    = Path("docs")
SOURCES_PATH = Path("parameters/sources.json")

# Set to False to skip GPT classification (faster, cheaper for testing)
USE_CLASSIFIER = os.getenv("USE_CLASSIFIER", "false").lower() == "true"


def load_sources() -> list[dict]:
    with open(SOURCES_PATH) as f:
        sources = json.load(f)
    active = [s for s in sources if s.get("active", True)]
    log.info(f"Loaded {len(active)} active sources")
    return active


def crawl_source(source: dict) -> list[dict]:
    scraper_type = source.get("type")
    name = source.get("name")
    try:
        if scraper_type == "static":
            return scrape_static(source)
        elif scraper_type == "dynamic":
            return scrape_dynamic(source)
        elif scraper_type == "ats":
            return scrape_ats(source)
        elif scraper_type == "aggregator":
            return scrape_aggregator(source)
        else:
            log.warning(f"Unknown type '{scraper_type}' for {name} — skipping")
            return []
    except Exception as e:
        log.error(f"Failed to crawl {name}: {e}")
        return []


def main():
    log.info("=== Arbeitsplatzsuche-43 crawler starting ===")

    sources = load_sources()
    all_jobs = []

    for source in sources:
        log.info(f"Crawling: {source['name']}")
        jobs = crawl_source(source)
        log.info(f"  → {len(jobs)} jobs found")
        all_jobs.extend(jobs)

    log.info(f"Total raw jobs collected: {len(all_jobs)}")

    # Clean fields
    all_jobs = clean_jobs(all_jobs)

    # Deduplicate against memory
    new_jobs, seen_count = deduplicate(all_jobs, MEMORY_PATH)
    log.info(f"New jobs after deduplication: {len(new_jobs)} ({seen_count} already seen)")

    # Optional: classify with GPT-4o-mini
    if USE_CLASSIFIER and new_jobs:
        log.info("Running GPT classifier...")
        new_jobs = classify_jobs(new_jobs)

    # Render output
    render_output(new_jobs, OUTPUT_PATH)
    log.info(f"Output written to {OUTPUT_PATH}")

    # Generate RSS feeds
    updated_iso = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    render_rss(new_jobs, DOCS_PATH, updated_iso)

    # Export sources CSV
    export_sources(SOURCES_PATH, Path("parameters/quellen.csv"))
    log.info("=== Done ===")


if __name__ == "__main__":
    main()
