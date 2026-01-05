from playwright.sync_api import sync_playwright
import os

def extract_pdf_text(filepath):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # file:// protocol for local files
        page.goto(f"file://{os.path.abspath(filepath)}")
        # Wait for potential rendering
        page.wait_for_timeout(2000)
        text = page.locator("body").inner_text()
        browser.close()
        return text

if __name__ == "__main__":
    test_file = r"c:\Users\peter\API\abn_scraper\downloads\ABNCurrent_details_11009413629_PETRO_GEOCONSULTANTS_PTY_LTD.pdf"
    print(f"Extracting from: {test_file}")
    content = extract_pdf_text(test_file)
    print("--- CONTENT START ---")
    print(content)
    print("--- CONTENT END ---")
