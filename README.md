# Arbeitsplatzsuche-43 🗂️

A weekly aggregator of job postings from research institutions, think tanks, NGOs, and policy organizations — inspired by [Paper Picnic](https://paper-picnic.com/).

## How it works

Every Friday at 2 AM UTC, a GitHub Actions workflow:
1. Crawls ~185 active sources listed in `parameters/sources.json`
2. Filters noise via multi-layer blocklist (non-research roles, admin jobs, etc.)
3. Deduplicates against previously seen jobs (`memory/job_ids.csv`)
4. Writes `output/jobs.json` and generates RSS feeds in `docs/`
5. Commits and pushes everything back to the repository

## RSS Feeds

Feeds are published to GitHub Pages and update every Friday. Subscribe in any RSS reader (Feedly, Inoreader, NetNewsWire, etc.).

| Feed | URL |
|------|-----|
| Alle Jobs | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-all.xml` |
| Forschung & Wissenschaft | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-research.xml` |
| Think Tanks & Stiftungen | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-thinktank.xml` |
| NGOs & Zivilgesellschaft | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-ngo.xml` |
| Öffentlicher Sektor & Int. Organisationen | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-government.xml` |
| Parteien & politische Institutionen | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-party.xml` |
| Aggregatoren | `https://cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/feed-aggregator.xml` |

> **Note:** Feeds are served via jsDelivr CDN (free, no GitHub Pages required). jsDelivr may cache feeds for up to 24h after a new crawl run.

## Project Structure

```
Arbeitsplatzsuche-43/
├── .github/
│   └── workflows/
│       └── crawl.yml              # GitHub Actions (crawl + commit, runs Fridays 2AM UTC)
├── main.py                        # Crawler orchestrator
├── requirements.txt
├── parameters/
│   └── sources.json               # ← Add/disable sources here (~270 entries)
├── src/
│   ├── scrapers/
│   │   ├── static_scraper.py      # Plain HTML pages (requests + BeautifulSoup)
│   │   ├── playwright_scraper.py  # JS-rendered pages (headless Chromium)
│   │   ├── ats_scraper.py         # ATS platforms (Personio, eArcu, Workday, etc.)
│   │   └── aggregator.py          # Job board aggregators (RSS, OTT, soziopolis, etc.)
│   ├── data_processor.py          # Deduplication, title cleaning & blocklist filtering
│   ├── classifier.py              # GPT-4o-mini relevance filter (optional)
│   ├── json_renderer.py           # Writes output/jobs.json
│   └── rss_renderer.py            # Generates per-category Atom feeds in docs/
├── memory/
│   └── job_ids.csv                # Seen job IDs — 6 columns: id, url, title, category, institution, date_seen
├── output/
│   └── jobs.json                  # Weekly output → fed to website
└── docs/                          # GitHub Pages source
    ├── index.html                 # Job board website
    ├── feeds.html                 # RSS feed index with subscription links
    ├── feed-all.xml               # Atom feed — all jobs
    ├── feed-research.xml          # Atom feed — Research / Academia
    ├── feed-thinktank.xml         # Atom feed — Think Tanks & Stiftungen
    ├── feed-ngo.xml               # Atom feed — NGOs
    ├── feed-government.xml        # Atom feed — Government & Int. Orgs
    ├── feed-party.xml             # Atom feed — Political Party
    └── feed-aggregator.xml        # Atom feed — Aggregator sources
```

## Adding a new source

Add one entry to `parameters/sources.json`:

```json
{
  "name": "Example Institute – Jobs",
  "url": "https://www.example.org/careers/",
  "type": "static",
  "job_list_selector": ".job-item",
  "title_selector": "h3 a",
  "category": "Think Tank",
  "language": "de",
  "active": true,
  "notes": "Optional notes about this source"
}
```

**Source types:**
- `static` — plain HTML, fetched with requests
- `dynamic` — JS-rendered, fetched with Playwright (slower, use sparingly)
- `ats` — ATS platform (Personio, eArcu, Phenom, Recruitee, Workday)
- `aggregator` — special handling for RSS feeds, soziopolis, OTT, etc.

**Categories** (used for RSS feed routing):
- `Research / Academia` · `Research Institute`
- `Think Tank` · `Think Tank / Policy` · `Foundation / Think Tank`
- `NGO / Civil Society` · `NGO / Human Rights` · `NGO / Association`
- `Government / Public Sector` · `International Organization`
- `Political Party`
- `Aggregator`

## Setup

### 1. RSS Feeds via jsDelivr
Feeds are served automatically via `cdn.jsdelivr.net/gh/Sw3azy/Arbeitsplatzsuche-43@main/docs/`. No GitHub Pages setup needed. Note that jsDelivr CDN may cache files for up to 24 hours after a new crawl run.

### 2. GitHub Actions (automated weekly crawl)
The workflow in `.github/workflows/crawl.yml` runs automatically every Friday at 2 AM UTC. It requires write permissions to commit back to the repo — make sure **Settings → Actions → General → Workflow permissions** is set to "Read and write permissions".

### 3. Optional: GPT classifier
Go to **Settings → Secrets and variables → Actions** and add:
- `OPENAI_API_KEY` — for GPT-4o-mini classification
- Set `USE_CLASSIFIER=true` in the workflow env to enable

### Local development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium --with-deps
python main.py
```

## Memory file

`memory/job_ids.csv` has 6 columns: `id, url, title, category, institution, date_seen`. If you get a column mismatch error, delete the file — it will be recreated on the next run.

## License

MIT
