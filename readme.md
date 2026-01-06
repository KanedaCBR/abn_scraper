# ABN Scraper & Browser

Python system for scraping, ingesting, and visualizing Australian Business Register (ABR) data.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start PostgreSQL (localhost:5432, db: postgres, user: postgres, pass: password)

# 3. Ingest PDFs
python abr_ingest_batch.py --dir downloads --init

# 4. Launch UI
streamlit run streamlit_app.py
```

## System Components

| Component | Purpose |
|-----------|---------|
| `abn_pdf_scraper.py` | Scrapes PDFs from ABN Lookup |
| `abr_ingest_batch.py` | Batch PDF ingestion |
| `abr_parsers.py` | PDF parsing (Current + Historical) |
| `streamlit_app.py` | Web UI for browsing data |

## Documentation

- **[SYSTEM_DOCUMENTATION.md](SYSTEM_DOCUMENTATION.md)** - Full architecture, workflows, dataflows
- **[README_ABR_Ingestion_Submodule.md](README_ABR_Ingestion_Submodule.md)** - Ingestion design principles
- **[ARCHITECTURAL_NOTES.md](ARCHITECTURAL_NOTES.md)** - Scraper architecture
- **[03_parser_rules_abr.md](03_parser_rules_abr.md)** - PDF parsing rules

## Features

- **Scraper**: Pagination (200 results), Current + Historical PDFs, ASIC link collection
- **Ingestion**: SHA-256 idempotency, insert-only, full audit trail
- **UI**: Dashboard, Search, Entity Detail, Analytics, Map View
- **Analysis**: Location history, status changes, GST registrations, trading names

## Docker Usage

```bash
# Update search term in docker.yaml
docker compose -f docker.yaml up --build
```

## Compliance

Respect ABN Lookup's robots.txt and terms of use.
