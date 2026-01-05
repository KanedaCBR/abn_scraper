# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-04

### Added

- Docker support: Added `Dockerfile` and `docker.yaml` (Docker Compose) for containerized execution.
- Dependency management: Added `requirements.txt`.
- Enhanced selector support in `abn_pdf_scraper.py` for the ABN Lookup (ABR) website.

### Changed

- Improved tab navigation logic in `abn_pdf_scraper.py` to use specific element IDs (`#HyperlinkAbnHistory`, `#HyperlinkCurrentDetails`).
- Updated `abn_pdf_scraper.py` to identify and collect ASIC registration and historical business name links.
- Implemented a simplified reporting mechanism that saves these links to `ASIC_links_<entity>.txt` to avoid ASIC's CAPTCHA/bot detection.
- Adjusted scraping logic to ensure robust collection across Current and History tabs.
- Updated PDF download detection to include `input.inputpdf` controls.

### Fixed

- Issue where the scraper failed to find the PDF download button on result pages.
- Issue where the scraper could not navigate to the "Historical details" tab.
