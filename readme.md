# ABN Lookup PDF scraper (Playwright)

Python scraper using Playwright to search the ABN Lookup site, navigate pagination, and extract both PDFs and ASIC registry links.

## Features

- **Pagination Support**: Automatically navigates through result pages (capturing up to 200 matches).
- **Tab Navigation**: Downloads both "Current" and "Historical" status PDFs for each entity.
- **ASIC Link Collection**: Scrapes ASIC registration and Business Name links into a summary text file (bypassing the need to solve CAPTCHAs for automated ASIC downloads).
- **Descriptive Naming**: Organizes downloads using the format `Content_ABN_EntityName.pdf` or `ASIC_links_EntityName_ABN.txt`.
- **Dockerized**: Fully containerized to ensure consistent browser environments.

## Usage (Docker)

The easiest way to run the scraper is via Docker Compose:

1. Update the search term in `docker.yaml`:

    ```yaml
    command: ["T Do", "--max-results", "20", "--headless"]
    ```

2. Launch the container:

    ```bash
    docker compose -f docker.yaml up --build
    ```

3. Check the `downloads/` directory for results.

## Configuration

See `ARCHITECTURAL_NOTES.md` for technical deep-dives and extension paths.

## Compliance Note

Respect the site's robots.txt and terms of use. This script is designed for transparency and reliability with conservative delays.
