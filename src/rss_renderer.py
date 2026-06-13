"""
RSS renderer — generates Atom/RSS feeds from jobs.json.

Produces:
  docs/feed.xml            — all jobs
  docs/feed-research.xml   — Research / Academia only
  docs/feed-ngo.xml        — NGO / Civil Society + NGO / Human Rights + NGO / Association
  docs/feed-thinktank.xml  — Think Tank + Think Tank / Policy + Foundation / Think Tank
  docs/feed-government.xml — Government / Public Sector + International Organization
  docs/feed-party.xml      — Political Party
  docs/feeds.html          — landing page listing all feeds
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

log = logging.getLogger(__name__)

BASE_URL = "https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs"

# Map feed slug → (label, set of job categories included)
FEEDS = {
    "all": (
        "Alle Jobs",
        None,  # None = include everything
    ),
    "research": (
        "Forschung & Wissenschaft",
        {"Research / Academia", "Research Institute"},
    ),
    "thinktank": (
        "Think Tanks & Stiftungen",
        {"Think Tank", "Think Tank / Policy", "Foundation / Think Tank"},
    ),
    "ngo": (
        "NGOs & Zivilgesellschaft",
        {"NGO / Civil Society", "NGO / Human Rights", "NGO / Association"},
    ),
    "government": (
        "Öffentlicher Sektor & Int. Organisationen",
        {"Government / Public Sector", "International Organization"},
    ),
    "party": (
        "Parteien & politische Institutionen",
        {"Political Party"},
    ),
    "aggregator": (
        "Aggregatoren (gemischt)",
        {"Aggregator"},
    ),
}


def _atom_feed(title: str, slug: str, jobs: list[dict], updated_iso: str) -> str:
    feed_url = f"{BASE_URL}/feed-{slug}.xml"
    html_url = f"{BASE_URL}/feeds.html"

    entries = []
    for job in jobs:
        job_id = escape(job.get("id") or "")
        job_title = escape(job.get("title") or "Untitled")
        job_url = escape(job.get("url") or "")
        institution = escape(job.get("institution") or "")
        category = escape(job.get("category") or "")
        date_scraped = job.get("date_scraped") or updated_iso
        # Atom requires a valid RFC 3339 datetime
        try:
            dt = datetime.fromisoformat(date_scraped)
            pub_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            pub_date = updated_iso

        summary_parts = []
        if institution:
            summary_parts.append(f"Institution: {institution}")
        if category:
            summary_parts.append(f"Kategorie: {category}")
        if job.get("location"):
            summary_parts.append(f"Ort: {escape(job['location'])}")
        if job.get("deadline"):
            summary_parts.append(f"Bewerbungsschluss: {escape(job['deadline'])}")
        summary = " · ".join(summary_parts) if summary_parts else institution

        entries.append(f"""  <entry>
    <id>{feed_url}#{job_id}</id>
    <title>{job_title}</title>
    <link href="{job_url}" rel="alternate" type="text/html"/>
    <updated>{pub_date}</updated>
    <author><name>{institution}</name></author>
    <summary>{summary}</summary>
    <category term="{category}"/>
  </entry>""")

    entries_xml = "\n".join(entries)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>{feed_url}</id>
  <title>Arbeitsplatzsuche-43 – {escape(title)}</title>
  <subtitle>Wöchentlich aktualisierte Stellenangebote für Politikwissenschaft, Soziologie und verwandte Bereiche</subtitle>
  <link href="{feed_url}" rel="self" type="application/atom+xml"/>
  <link href="{html_url}" rel="alternate" type="text/html"/>
  <updated>{updated_iso}</updated>
  <generator>Arbeitsplatzsuche-43</generator>
{entries_xml}
</feed>
"""


def _feeds_html(feeds_with_counts: list[tuple]) -> str:
    """Simple HTML page listing all feeds with subscription links."""

    rows = []
    for slug, label, count in feeds_with_counts:
        feed_url = f"{BASE_URL}/feed-{slug}.xml"
        feedly_url = f"https://feedly.com/i/subscription/feed/{feed_url}"
        inoreader_url = f"https://www.inoreader.com/?add_feed={feed_url}"
        rows.append(f"""
      <tr>
        <td><strong>{label}</strong><br>
            <small><a href="{feed_url}">{feed_url}</a></small></td>
        <td>{count} Jobs</td>
        <td>
          <a href="{feedly_url}" target="_blank">Feedly</a> ·
          <a href="{inoreader_url}" target="_blank">Inoreader</a> ·
          <a href="{feed_url}" target="_blank">XML</a>
        </td>
      </tr>""")

    rows_html = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arbeitsplatzsuche-43 – RSS Feeds</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #333; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
    p.sub {{ color: #666; margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
    th {{ text-align: left; border-bottom: 2px solid #ddd; padding: 0.5rem 0.75rem; font-size: 0.85rem; color: #666; }}
    td {{ padding: 0.6rem 0.75rem; border-bottom: 1px solid #eee; vertical-align: top; }}
    td small {{ color: #888; font-size: 0.78rem; word-break: break-all; }}
    a {{ color: #2563eb; }}
    .hint {{ margin-top: 1.5rem; padding: 0.75rem 1rem; background: #f5f5f5; border-radius: 6px; font-size: 0.875rem; color: #555; }}
    .guide {{ margin-top: 2.5rem; border-top: 1px solid #e5e5e5; padding-top: 1.5rem; }}
    .guide h2 {{ font-size: 1.1rem; margin-bottom: 0.5rem; }}
    .guide h3 {{ font-size: 0.95rem; margin: 1.25rem 0 0.4rem; color: #444; }}
    .guide p {{ margin: 0.4rem 0; font-size: 0.9rem; color: #555; line-height: 1.6; }}
    .guide ul, .guide ol {{ margin: 0.4rem 0 0.4rem 1.25rem; font-size: 0.9rem; color: #555; line-height: 1.8; }}
    .guide code {{ background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.82rem; }}
    .privacy-note {{ margin-top: 1rem; padding: 0.6rem 0.8rem; background: #f0fdf4; border-radius: 6px; color: #444; }}
    .note {{ margin-top: 0.75rem; padding: 0.6rem 0.8rem; background: #fffbeb; border-radius: 6px; color: #444; border-left: 3px solid #f59e0b; }}
  </style>
</head>
<body>
  <h1>Arbeitsplatzsuche-43 – RSS Feeds</h1>
  <p class="sub">Wöchentlich aktualisierte Stellenangebote für Politikwissenschaft, Soziologie und verwandte Bereiche.<br>
  Feeds werden jeden Freitag gegen 2:00 Uhr UTC aktualisiert.</p>

  <table>
    <thead>
      <tr>
        <th>Feed</th>
        <th>Aktuelle Jobs</th>
        <th>Abonnieren</th>
      </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>

  <div class="hint">
    💡 <strong>Tipp:</strong> Kopiere die XML-URL in jeden beliebigen RSS-Reader
    (Feedly, Inoreader, NetNewsWire, Reeder, FreshRSS, etc.).
    Oder abonniere direkt per Klick auf „Feedly" oder „Inoreader".
  </div>

  <section class="guide">
    <h2>Was ist RSS und wie nutze ich es?</h2>
    <p>RSS ist ein Format, mit dem du Inhalte von Websites automatisch abonnieren kannst —
    ähnlich wie ein Newsletter, aber ohne E-Mail-Adresse und ohne Registrierung.
    Du bekommst neue Stellenangebote direkt in deiner App angezeigt, sobald sie erscheinen.</p>

    <h3>Schritt 1: Einen RSS-Reader installieren</h3>
    <p>Wähle eine App oder einen Dienst:</p>
    <ul>
      <li><strong>Thunderbird</strong> — der bekannte E-Mail-Client kann RSS-Feeds direkt neben deinen E-Mails anzeigen.
      Unter <em>Feeds &amp; News-Feeds → Feed hinzufügen</em> einfach die XML-URL einfügen.</li>
      <li><strong><a href="https://feedly.com" target="_blank">Feedly</a></strong> — kostenlos, im Browser und als App (iOS/Android). Empfehlenswert für Einsteiger.</li>
      <li><strong><a href="https://www.inoreader.com" target="_blank">Inoreader</a></strong> — kostenlos, sehr leistungsfähig, Browser + App.</li>
      <li><strong><a href="https://netnewswire.com" target="_blank">NetNewsWire</a></strong> — kostenlos, nur Mac und iPhone.</li>
      <li><strong><a href="https://freshrss.org" target="_blank">FreshRSS</a></strong> — kostenlos, selbst gehostet, für Technik-Affine.</li>
    </ul>

    <h3>Schritt 2: Einen Feed abonnieren</h3>
    <p>Es gibt zwei einfache Wege:</p>
    <ol>
      <li><strong>Per Klick:</strong> Klicke oben in der Tabelle auf „Feedly" oder „Inoreader" neben dem gewünschten Feed.
      Du wirst direkt zur Abo-Seite weitergeleitet.</li>
      <li><strong>Manuell:</strong> Kopiere die XML-URL des gewünschten Feeds (z.B. <code>…/feed-research.xml</code>)
      und füge sie in deinem RSS-Reader unter „Feed hinzufügen" ein.</li>
    </ol>

    <h3>Schritt 3: Fertig</h3>
    <p>Ab sofort siehst du jeden Freitag neue Stellenangebote direkt in deiner App —
    gefiltert nach den Kategorien, die dich interessieren.
    Keine E-Mails, kein Spam, kein Algorithmus.</p>
    <p class="note">⚠️ <strong>Hinweis:</strong> Die Feed-URLs werden erst nach dem ersten automatischen Crawl-Lauf
    (jeden Freitag gegen 2:00 Uhr UTC) gültig. Wenn du eine Fehlermeldung wie
    „liefert keinen gültigen Feed" siehst, ist der Feed noch nicht generiert worden —
    bitte nach dem nächsten Freitag erneut versuchen.</p>

    <p class="privacy-note">🔒 RSS ist privat: Niemand erfährt, welche Feeds du abonnierst.
    Es gibt keine Anmeldung und keine Weitergabe deiner Daten.</p>
  </section>
</body>
</html>
"""


def render_rss(jobs: list[dict], docs_dir: Path, updated_iso: str):
    """
    Called from main.py after render_output().
    Writes one Atom feed per category group + feeds.html index.
    """
    docs_dir.mkdir(parents=True, exist_ok=True)

    feeds_with_counts = []

    for slug, (label, categories) in FEEDS.items():
        if categories is None:
            feed_jobs = jobs
        else:
            feed_jobs = [j for j in jobs if (j.get("category") or "") in categories]

        xml = _atom_feed(label, slug, feed_jobs, updated_iso)
        out_path = docs_dir / f"feed-{slug}.xml"
        out_path.write_text(xml, encoding="utf-8")
        log.info(f"RSS: wrote {len(feed_jobs)} jobs to {out_path.name}")

        feeds_with_counts.append((slug, label, len(feed_jobs)))

    # Write feeds index page
    html = _feeds_html(feeds_with_counts)
    html_path = docs_dir / "feeds.html"
    html_path.write_text(html, encoding="utf-8")
    log.info(f"RSS: wrote feeds index to {html_path.name}")
