#!/usr/bin/env python3
"""
ABN Lookup PDF scraper using Playwright.

Behavior:
 - Navigate to https://abr.business.gov.au/
 - Run a search
 - Iterate through results (max_results)
 - For each result:
    - open the details page
    - click two tabs (first two tabs by default, or tabs matched by selectors)
    - on each tab, locate a "download pdf" button/link and download the file

Adjust selectors if the live site has different structure.
"""

import argparse
import os
import re
import time
import random
import logging
from pathlib import Path
from typing import List, Optional

from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError

LOG = logging.getLogger("abn_scraper")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_URL = "https://abr.business.gov.au/"

# Configurable conservative delays
MIN_DELAY = 1.0
MAX_DELAY = 3.0

def random_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def find_search_input(page: Page) -> Optional[Locator]:
    """Try a list of likely selectors to find the search input on the ABN Lookup home page."""
    candidates = [
        'input[type="search"]',
        'input[name="SearchQuery"]',
        'input[name="search"]',
        'input[id*="search"]',
        'input[placeholder*="ABN"]',
        'input[placeholder*="Name"]',
        'input'
    ]
    for sel in candidates:
        try:
            input_el = page.locator(sel)
            if input_el.count() > 0:
                LOG.debug("Found search input with selector: %s", sel)
                return input_el.first
        except PlaywrightTimeoutError:
            continue
    return None

def find_result_links(page: Page, max_total: int = 200) -> List[str]:
    """Collect candidate result detail URLs from all available result pages.

    Iterates through pagination (up to max_total) and returns a deduplicated list of absolute URLs.
    """
    all_links = []
    current_page_num = 1

    while len(all_links) < max_total:
        LOG.info("Collecting links from results page %d", current_page_num)
        
        # Wait for the main results table specifically
        try:
            page.wait_for_selector(".search-results-table, table", timeout=10000)
        except PlaywrightTimeoutError:
            LOG.warning("Timeout waiting for result table on page %d", current_page_num)
            break

        # Narrowly target links within the table rows
        candidates = page.locator(".search-results-table a, table tr td a")
        count = candidates.count()
        LOG.debug("Found %d targeted anchors on page %d", count, current_page_num)
        
        anchors = []
        for i in range(count):
            try:
                a = candidates.nth(i)
                href = a.get_attribute("href") or ""
                # ABR specific URL pattern for details
                if href and ("/Details/" in href or "/ABN/" in href):
                    if href.startswith("/"):
                        full_url = "https://abr.business.gov.au" + href
                    else:
                        full_url = href if href.startswith("http") else page.url.rsplit("/", 1)[0] + "/" + href
                    anchors.append(full_url)
            except Exception:
                continue

        # Deduplicate while preserving order
        for u in anchors:
            if u not in all_links:
                all_links.append(u)
        
        if len(all_links) >= max_total:
            LOG.info("Reached maximum result limit of %d", max_total)
            break

        # Try to find next page link
        next_page = current_page_num + 1
        # Selector for the next page number link (1-indexed text)
        next_selector = f".pagination a:has-text('{next_page}'), .pagination li a:text('{next_page}')"
        try:
            next_btn = page.locator(next_selector)
            if next_btn.count() > 0:
                LOG.info("Navigating to results page %d", next_page)
                next_btn.first.click()
                current_page_num = next_page
                # Wait for table or links to be present on new page
                page.wait_for_load_state("networkidle")
                random_delay()
            else:
                LOG.info("No more result pages found after page %d", current_page_num)
                break
        except Exception as e:
            LOG.debug("Error checking for next page: %s", e)
            break

    LOG.info("Collected %d unique result links in total", len(all_links))
    return all_links[:max_total]

def sanitize_filename(s: str) -> str:
    s = re.sub(r"[\\/*?<>:|\"']", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    if not s:
        s = "download"
    return s[:200]

def download_from_tab(page: Page, output_dir: Path, custom_filename: str, pdf_selector_candidates: List[str]) -> Optional[Path]:
    """Click the download PDF control on the current tab and save the download to output_dir.

    Returns path to saved file or None if not found.
    """
    for sel in pdf_selector_candidates:
        try:
            elems = page.locator(sel)
            if elems.count() == 0:
                continue
            # Try first matching element
            el = elems.first
            try:
                with page.expect_download(timeout=20000) as download_info:
                    el.click()
                download = download_info.value
                target = output_dir / custom_filename
                download.save_as(str(target))
                LOG.info("Saved download: %s", target)
                return target
            except PlaywrightTimeoutError:
                LOG.debug("Clicking selector %s didn't trigger download within timeout", sel)
                # maybe the download link opens a new window or triggers a navigation to a PDF
                # try to handle a navigation that returns a PDF
                try:
                    with page.expect_navigation(wait_until="networkidle", timeout=8000):
                        el.click()
                    # If the navigation landed on a PDF, we might be able to get it via response
                    # (Playwright sync API doesn't easily fetch last response content here)
                except PlaywrightTimeoutError:
                    LOG.debug("Click didn't navigate either for selector %s", sel)
                    continue
        except Exception as e:
            LOG.debug("Error trying pdf selector %s: %s", sel, e)
    LOG.warning("No PDF control found on tab '%s' for '%s'", tab_name, company_name)
    return None

def click_tab_by_index_or_name(page: Page, tab_index: int) -> Optional[str]:
    """Click a tab on a details page specifically for ABR structure."""
    abr_ids = ["#HyperlinkCurrentDetails", "#HyperlinkAbnHistory"]
    if tab_index < len(abr_ids):
        try:
            target = page.locator(abr_ids[tab_index])
            if target.count() > 0:
                name = target.inner_text().strip()
                target.click()
                return name
        except Exception:
            pass
    return None

def find_asic_links(page: Page) -> List[str]:
    """Find all unique ASIC registry search links on the current page."""
    links = []
    # General ASIC search link pattern
    candidates = page.locator("a[href*='connectonline.asic.gov.au/RegistrySearch']")
    for i in range(candidates.count()):
        href = candidates.nth(i).get_attribute("href")
        if href:
            links.append(href)
    return list(set(links))

# Note: process_asic_link was removed to avoid CAPTCHA complexity on ASIC site.
# Links are now collected and saved to a text file in process_result.

def process_result(page: Page, url: str, output_dir: Path, pdf_selector_candidates: List[str], tabs_to_click: int = 2):
    """Reuse existing page object to process an ABN result."""
    LOG.info("Opening result page: %s", url)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except PlaywrightTimeoutError:
        LOG.warning("Timeout loading %s; trying again", url)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        LOG.error("Failed to load %s: %s", url, e)
        return

    # Extract real entity name (legal name) to use in filenames
    legal_name = ""
    abn_clean = ""
    try:
        # Prioritize span[itemprop="legalName"]
        legal_name_el = page.locator('span[itemprop="legalName"]').first
        if legal_name_el.count() > 0:
            legal_name = legal_name_el.inner_text().strip()
        
        # Extract ABN for uniqueness and clarity
        abn_match = re.search(r"abn=(\d+)", url)
        if abn_match:
            abn_clean = abn_match.group(1)
            
        # If legal name not found, try H1 or title
        if not legal_name:
            h1 = page.locator("h1").first
            if h1.count() > 0:
                legal_name = h1.inner_text().strip()
            else:
                legal_name = page.title() or "entity"
    except Exception:
        legal_name = "entity"

    legal_name_sanitized = sanitize_filename(legal_name)
    # The user wants entity name at the end of the filename
    # We'll use a descriptive base (e.g. ABNCurrentDetails_123) and append _Name
    
    # identify tabs and iterate
    asic_links = set()
    for tab_index in range(tabs_to_click):
        random_delay()
        tab_name = click_tab_by_index_or_name(page, tab_index)
        if not tab_name:
            # no tab at that index; attempt to click elements that look like a tab panel label
            LOG.debug("No tab found at index %d; continuing", tab_index)
            # Default to descriptive names for common indices if tab name can't be scraped
            if tab_index == 0:
                tab_name = "Current_details"
            elif tab_index == 1:
                tab_name = "Historical_details"
            else:
                tab_name = f"tab{tab_index+1}"

        # Give content time to load
        try:
            page.wait_for_timeout(2000) # Increased for stability
        except Exception:
            pass

        # Collect ASIC links from this tab
        links_on_tab = find_asic_links(page)
        asic_links.update(links_on_tab)
        if links_on_tab:
            LOG.info("Found %d ASIC links on tab '%s'", len(links_on_tab), tab_name)

        # Build refined filename: Content_ABN_EntityName.pdf
        tab_name_clean = sanitize_filename(tab_name)
        file_base = f"ABN{tab_name_clean}_{abn_clean}" if abn_clean else f"{tab_name_clean}"
        custom_filename = f"{file_base}_{legal_name_sanitized}.pdf"

        LOG.info("Attempting download on tab '%s' for '%s'", tab_name, legal_name)
        saved = download_from_tab(page, output_dir, custom_filename, pdf_selector_candidates)
        # ... rest of the existing download logic remains in context ...
        if not saved:
            # ... (existing fallback logic)
            try:
                pdf_anchors = page.locator("a[href$='.pdf'], a[href*='.pdf?']")
                if pdf_anchors.count() > 0:
                    # ... (existing code for pdf_anchors)
                    href = pdf_anchors.first.get_attribute("href")
                    if href:
                        if href.startswith("/"):
                            href = "https://abr.business.gov.au" + href
                        LOG.info("Found direct PDF link; downloading from %s", href)
                        with page.expect_download(timeout=20000) as download_info:
                            page.evaluate("url => window.open(url, '_blank')", href)
                        download = download_info.value
                        target = output_dir / custom_filename
                        download.save_as(str(target))
                        LOG.info("Saved download: %s", target)
            except Exception as e:
                LOG.debug("Alternative PDF download attempt failed: %s", e)

    # Now process any collected ASIC links
    if asic_links:
        LOG.info("Found %d unique ASIC/Business Name links for '%s' (ABN: %s)", len(asic_links), legal_name, abn_clean)
        links_file = output_dir / f"ASIC_links_{legal_name_sanitized}_{abn_clean}.txt"
        try:
            with open(links_file, "w", encoding="utf-8") as f:
                f.write(f"Entity: {legal_name}\n")
                f.write(f"ABN: {abn_clean}\n")
                f.write("="*40 + "\n")
                f.write("ASIC/Business Name links:\n")
                for asic_url in sorted(asic_links):
                    f.write(f"{asic_url}\n")
            LOG.info("Saved ASIC links to: %s", links_file)
        except Exception as e:
            LOG.error("Error writing ASIC links file: %s", e)

def main():
    parser = argparse.ArgumentParser(description="ABN Lookup PDF scraper (Playwright)")
    parser.add_argument("search", nargs="+", help="One or more search terms (names or ABNs)")
    parser.add_argument("--max-results", type=int, default=10, help="Max results to process per search term")
    parser.add_argument("--out", default="downloads", help="Output directory to save PDFs")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (default: headful for debugging)")
    parser.add_argument("--tabs", type=int, default=2, help="Number of tabs to click/download on each details page")
    args = parser.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    # Optimized selectors for ABR site
    pdf_selector_candidates = [
        "input.inputpdf",
        "input[value='Pdf']",
        "a[href*='Download']"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(accept_downloads=True, user_agent="Mozilla/5.0 (compatible; ABN-PDF-scraper/1.0)")
        page = context.new_page()

        for term in args.search:
            LOG.info("=== Starting search for: '%s' ===", term)
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            random_delay()

            input_el = find_search_input(page)
            if not input_el:
                LOG.error("Unable to find search input for '%s'. Skipping.", term)
                continue

            LOG.info("Typing search term: %s", term)
            try:
                # Clear and fill
                input_el.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                input_el.fill(term)
                random_delay()
                input_el.press("Enter")
            except Exception:
                try:
                    btn = page.get_by_role("button", name=re.compile("Search", re.I))
                    if btn.count() > 0:
                        btn.first.click()
                    else:
                        raise Exception("Search button not found")
                except Exception as e:
                    LOG.error("Couldn't submit search form for '%s': %s", term, e)
                    continue

            random_delay()
            result_links = find_result_links(page, max_total=args.max_results)
            if not result_links:
                LOG.warning("No result links found for '%s'.", term)
                continue

            to_process = result_links[: args.max_results]
            LOG.info("Processing %d results for '%s'", len(to_process), term)
            for idx, url in enumerate(to_process, start=1):
                LOG.info("[%s] Processing result %d/%d: %s", term, idx, len(to_process), url)
                try:
                    process_result(page, url, outdir, pdf_selector_candidates, tabs_to_click=args.tabs)
                except Exception as e:
                    LOG.exception("Error processing %s: %s", url, e)
                random_delay()

        LOG.info("Finished all searches. PDFs saved to: %s", outdir.resolve())
        browser.close()

if __name__ == "__main__":
    main()