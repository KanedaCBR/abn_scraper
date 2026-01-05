import os
import hashlib
import logging
import argparse
from pathlib import Path
from abr_db_manager import ABRDatabaseManager
from abr_parsers import ABRPDFParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger("abr_batch_ingest")

def compute_sha256(filepath):
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class ABRIngestionWorkflow:
    def __init__(self, db_manager, downloads_dir):
        self.db = db_manager
        self.downloads_dir = Path(downloads_dir)

    def run(self, initialize_db=False):
        if initialize_db:
            self.db.initialize_schema("01_schema_postgres_abr.sql")

        LOG.info(f"Scanning directory: {self.downloads_dir}")
        pdf_files = list(self.downloads_dir.glob("ABN*.pdf"))
        LOG.info(f"Found {len(pdf_files)} ABR PDF files.")

        stats = {"success": 0, "failed": 0, "skipped": 0}

        for pdf_path in pdf_files:
            try:
                self.process_file(pdf_path, stats)
            except Exception as e:
                LOG.error(f"Critical error processing {pdf_path}: {e}")
                stats["failed"] += 1

        LOG.info(f"Ingestion complete. Success: {stats['success']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")

    def process_file(self, pdf_path, stats):
        filename = pdf_path.name
        file_hash = compute_sha256(pdf_path)

        # 1. Idempotency Check
        existing = self.db.get_document_by_hash(file_hash)
        if existing:
            LOG.info(f"Skipping {filename} (hash already exists with status {existing[1]})")
            stats["skipped"] += 1
            return

        # 2. Identify Type
        doc_type = "CURRENT" if "Current_details" in filename else "HISTORICAL"
        
        # 3. Register Document (Initial FAILED status)
        doc_id = self.db.register_document(filename, file_hash, doc_type)

        try:
            # 4. Parse PDF
            parser = ABRPDFParser(pdf_path, doc_id)
            data = parser.parse()

            # 5. Insert Data
            # Start transaction or atomic inserts
            self.db.upsert_entity(data['entity'])
            
            abn = data['entity']['abn']
            
            # History tables
            for table in [
                ('abn_status_history', data.get('status_history', [])),
                ('abn_name_history', data.get('name_history', [])),
                ('abn_location_history', data.get('location_history', [])),
                ('abn_gst_history', data.get('gst_history', [])),
                ('abn_business_name', data.get('business_names', [])),
                ('abn_trading_name', data.get('trading_names', [])),
                ('abn_asic_registration', data.get('asic_registration', []))
            ]:
                table_name, records = table
                if records:
                    # Ensure ABN is in every record (some parsers might skip it in nested objects)
                    for r in records: r['abn'] = abn
                    self.db.insert_history_records(table_name, records)

            # 6. Mark Success
            self.db.update_document_status(doc_id, "SUCCESS")
            LOG.info(f"Successfully ingested {filename}")
            stats["success"] += 1

        except Exception as e:
            LOG.error(f"Failed to ingest {filename}: {e}")
            self.db.update_document_status(doc_id, "FAILED", str(e))
            stats["failed"] += 1

def main():
    parser = argparse.ArgumentParser(description="ABR PDF Batch Ingestion")
    parser.add_argument("--dir", default="downloads", help="Directory containing ABR PDFs")
    parser.add_argument("--init", action="store_true", help="Initialize database schema")
    args = parser.parse_args()

    # Re-checking DB environment variables via manager
    db = ABRDatabaseManager()
    workflow = ABRIngestionWorkflow(db, args.dir)
    workflow.run(initialize_db=args.init)

if __name__ == "__main__":
    main()
