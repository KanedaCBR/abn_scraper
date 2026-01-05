from pypdf import PdfReader
import os

def sample_pdf(filepath):
    print(f"\n--- SAMPLING: {os.path.basename(filepath)} ---")
    reader = PdfReader(filepath)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Print search results for specific markers
    markers = [
        "Current details for ABN",
        "Historical details for ABN",
        "ABN details",
        "Entity name",
        "ABN status",
        "Entity type",
        "Goods & Services Tax (GST)",
        "Main business location",
        "Business name(s)",
        "Trading name(s)",
        "ASIC registration",
        "Record extracted",
        "ABN last updated"
    ]
    
    print("--- HEADERS FOUND ---")
    lines = full_text.split('\n')
    for line in lines[:20]:
        print(line.strip())
    
    print("--- MARKER CHECKS ---")
    for marker in markers:
        if marker.lower() in full_text.lower():
            print(f"FOUND: {marker}")
        else:
            print(f"NOT FOUND: {marker}")
    
    print("--- END SAMPLING ---\n")

if __name__ == "__main__":
    current_file = r"c:\Users\peter\API\abn_scraper\downloads\ABNCurrent_details_11009413629_PETRO_GEOCONSULTANTS_PTY_LTD.pdf"
    historical_file = r"c:\Users\peter\API\abn_scraper\downloads\ABNHistorical_details_11009413629_PETRO_GEOCONSULTANTS_PTY_LTD.pdf"
    
    if os.path.exists(current_file):
        sample_pdf(current_file)
    if os.path.exists(historical_file):
        sample_pdf(historical_file)
