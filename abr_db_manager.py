import os
import psycopg2
from psycopg2.extras import execute_values
import logging
import uuid
from datetime import datetime

LOG = logging.getLogger("abr_ingestion")

class ABRDatabaseManager:
    def __init__(self):
        self.conn_params = {
            "host": os.getenv("PGHOST", "localhost"),
            "port": os.getenv("PGPORT", "5432"),
            "database": os.getenv("PGDATABASE", "postgres"),
            "user": os.getenv("PGUSER", "postgres"),
            "password": os.getenv("PGPASSWORD", "password")
        }
        self.conn = None

    def connect(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
        return self.conn

    def initialize_schema(self, schema_file_path):
        """Executes the DDL to initialize the schema."""
        LOG.info(f"Initializing schema from {schema_file_path}")
        with open(schema_file_path, 'r') as f:
            sql = f.read()
        
        with self.connect().cursor() as cur:
            cur.execute(sql)
        LOG.info("Schema initialization complete.")

    def get_document_by_hash(self, file_hash):
        """Checks if a document with the given hash already exists."""
        with self.connect().cursor() as cur:
            cur.execute("SELECT document_id, ingestion_status FROM abn_document_registry WHERE file_hash_sha256 = %s", (file_hash,))
            return cur.fetchone()

    def register_document(self, filename, file_hash, doc_type):
        """Creates a new record in the document registry."""
        doc_id = str(uuid.uuid4())
        with self.connect().cursor() as cur:
            cur.execute("""
                INSERT INTO abn_document_registry (document_id, filename, file_hash_sha256, document_type, ingestion_status)
                VALUES (%s, %s, %s, %s, 'FAILED')
            """, (doc_id, filename, file_hash, doc_type))
        return doc_id

    def update_document_status(self, doc_id, status, error_message=None):
        """Updates the status and ingest time of a document."""
        with self.connect().cursor() as cur:
            cur.execute("""
                UPDATE abn_document_registry
                SET ingestion_status = %s, error_message = %s, ingested_at = %s
                WHERE document_id = %s
            """, (status, error_message, datetime.now(), doc_id))

    def upsert_entity(self, entity_data):
        """Inserts or updates (using manual check per insert-only logic) an entity record."""
        # Note: abn_entity has abn as PRIMARY KEY. 
        # Requirement is "Insert-only", but we need the base entity record to exist for foreign keys.
        # We check if it exists first.
        with self.connect().cursor() as cur:
            cur.execute("SELECT abn FROM abn_entity WHERE abn = %s", (entity_data['abn'],))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO abn_entity (
                        abn, entity_name, entity_type, first_active_date, 
                        abn_last_updated_date, record_extracted_date, source_document_id
                    ) VALUES (%(abn)s, %(entity_name)s, %(entity_type)s, %(first_active_date)s, 
                              %(abn_last_updated_date)s, %(record_extracted_date)s, %(source_document_id)s)
                """, entity_data)

    def insert_history_records(self, table_name, records):
        """Generic function to insert history records into attribute tables."""
        if not records:
            return
        
        columns = records[0].keys()
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s"
        values = [[r[col] for col in columns] for r in records]
        
        with self.connect().cursor() as cur:
            execute_values(cur, query, values)

if __name__ == "__main__":
    # Test initialization
    logging.basicConfig(level=logging.INFO)
    db = ABRDatabaseManager()
    # Assuming the user sets the PG env vars, we could run initialize_schema here if needed.
    # db.initialize_schema("01_schema_postgres_abr.sql")
    print("DB Manager ready.")
