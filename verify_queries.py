import os
import psycopg2

def run_verification_queries():
    conn_params = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "database": os.getenv("PGDATABASE", "postgres"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", "password")
    }
    
    conn = psycopg2.connect(**conn_params)
    
    queries = [
        ("Row counts per table", """
            SELECT 'abn_entity' as table, count(*) FROM abn_entity
            UNION ALL SELECT 'abn_document_registry', count(*) FROM abn_document_registry
            UNION ALL SELECT 'abn_status_history', count(*) FROM abn_status_history
            UNION ALL SELECT 'abn_name_history', count(*) FROM abn_name_history
            UNION ALL SELECT 'abn_location_history', count(*) FROM abn_location_history
            UNION ALL SELECT 'abn_business_name', count(*) FROM abn_business_name
            UNION ALL SELECT 'abn_trading_name', count(*) FROM abn_trading_name
            UNION ALL SELECT 'abn_gst_history', count(*) FROM abn_gst_history
            UNION ALL SELECT 'abn_asic_registration', count(*) FROM abn_asic_registration
        """),
        ("Top 5 entities by name", "SELECT abn, entity_name FROM abn_entity LIMIT 5"),
        ("Entities with most location changes", """
            SELECT abn, COUNT(*) as changes 
            FROM abn_location_history 
            GROUP BY abn 
            HAVING COUNT(*) > 1 
            ORDER BY changes DESC LIMIT 5
        """),
        ("Document Registry Status Summary", "SELECT ingestion_status, count(*) FROM abn_document_registry GROUP BY ingestion_status")
    ]
    
    for title, sql in queries:
        print(f"\n--- {title} ---")
        with conn.cursor() as cur:
            cur.execute(sql)
            colnames = [desc[0] for desc in cur.description]
            print(" | ".join(colnames))
            print("-" * 40)
            for row in cur.fetchall():
                print(" | ".join(str(val) for val in row))
    
    conn.close()

if __name__ == "__main__":
    try:
        run_verification_queries()
    except Exception as e:
        print(f"Verification failed: {e}")
