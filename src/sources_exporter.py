"""
Sources exporter — generates a CSV of all sources from sources.json.
Run automatically after each crawl so the CSV stays in sync with the JSON.
Output: docs/quellen.csv
"""

import csv
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def export_sources(sources_path: Path, output_path: Path):
    with open(sources_path, encoding="utf-8") as f:
        sources = json.load(f)

    # Sort by active (active first) then category then name
    sources_sorted = sorted(
        sources,
        key=lambda s: (0 if s.get("active", True) else 1, s.get("category", ""), s["name"])
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Name", "URL", "Kategorie", "Typ", "Sprache", "Aktiv", "Notizen"
        ])
        writer.writeheader()
        for s in sources_sorted:
            writer.writerow({
                "Name":      s.get("name", ""),
                "URL":       s.get("url", ""),
                "Kategorie": s.get("category", ""),
                "Typ":       s.get("type", ""),
                "Sprache":   s.get("language", ""),
                "Aktiv":     "Ja" if s.get("active", True) else "Nein",
                "Notizen":   s.get("notes", ""),
            })

    active = sum(1 for s in sources if s.get("active", True))
    inactive = len(sources) - active
    log.info(f"Sources CSV: {len(sources)} total ({active} aktiv, {inactive} inaktiv) → {output_path}")
