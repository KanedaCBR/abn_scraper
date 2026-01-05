from pypdf import PdfReader
import os

def sample_pdf(filepath):
    print(f"\n--- SAMPLING: {os.path.basename(filepath)} ---")
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    print(text)
    print("--- END SAMPLING ---\n")

if __name__ == "__main__":
    current_file = r"c:\Users\peter\API\abn_scraper\downloads\ABNCurrent_details_11009413629_PETRO_GEOCONSULTANTS_PTY_LTD.pdf"
    historical_file = r"c:\Users\peter\API\abn_scraper\downloads\ABNHistorical_details_11009413629_PETRO_GEOCONSULTANTS_PTY_LTD.pdf"
    
    if os.path.exists(current_file):
        sample_pdf(current_file)
    else:
        print(f"File not found: {current_file}")
        
    if os.path.exists(historical_file):
        sample_pdf(historical_file)
    else:
        print(f"File not found: {historical_file}")
