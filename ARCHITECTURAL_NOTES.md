# ABN Scraper Architectural Notes

## Core Design

The scraper is built as a sequential workflow using Playwright's sync API. It prioritizes stability over raw speed to avoid being flagged by registry bot detection.

## Key Logic Components

### Pagination & Collection

- `find_result_links`: Navigates up to 5 pages of ABN Lookup matches. It deduplicates links while preserving relevance order.
- **Limit**: Capped at 200 matches by the ABR website itself.

### Filename & Metadata Strategy

The scraper extracts the legal entity name from `span[itemprop="legalName"]` on the details page. This ensures filenames are descriptive and correlate exactly with the registry's primary record.

### ASIC Link Aggregation

Instead of automated downloads (which are blocked by CAPTCHAs), the scraper:

1. Visits the Current and Historical tabs.
2. Greps for `connectonline.asic.gov.au/RegistrySearch` links.
3. Saves a unique list to `ASIC_links_<Name>_<ABN>.txt`.

## Project Structure

- `abn_pdf_scraper.py`: Main execution script.
- `docker.yaml`: Multi-run configuration for different search terms.
- `Dockerfile`: Playwright-ready container environment.

## Extension Ideas

1. **Proxy Rotation**: If larger batches (>200) are needed, implement proxy rotation in `context` creation.
2. **Resume Logic**: Use a local SQLite database to track processed ABNs and skip them in future runs.
3. **Cloud Storage**: Redirect `downloads/` output to an S3 bucket or similar for persistence.
