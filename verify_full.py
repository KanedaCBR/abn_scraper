#!/usr/bin/env python3
"""Comprehensive verification script for ABR database ingestion."""
import os
import psycopg2

def run_full_verification():
    conn_params = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "database": os.getenv("PGDATABASE", "postgres"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", "password")
    }
    
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    print("=" * 60)
    print("ABR DATABASE VERIFICATION REPORT")
    print("=" * 60)
    
    # 1. Row counts per table
    print("\n--- TABLE ROW COUNTS ---")
    tables = [
        'abn_entity', 'abn_document_registry', 'abn_status_history',
        'abn_name_history', 'abn_location_history', 'abn_business_name',
        'abn_trading_name', 'abn_gst_history', 'abn_asic_registration'
    ]
    for table in tables:
        cur.execute(f"SELECT count(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count}")
    
    # 2. Document registry status summary
    print("\n--- DOCUMENT REGISTRY STATUS ---")
    cur.execute("SELECT ingestion_status, count(*) FROM abn_document_registry GROUP BY ingestion_status")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # 3. Sample entities
    print("\n--- SAMPLE ENTITIES (Top 5) ---")
    cur.execute("SELECT abn, entity_name, entity_type FROM abn_entity LIMIT 5")
    for row in cur.fetchall():
        print(f"  ABN: {row[0]} | Name: {row[1][:40]}... | Type: {row[2]}")
    
    # 4. Entities with multiple location changes
    print("\n--- ENTITIES WITH LOCATION CHANGES ---")
    cur.execute("""
        SELECT abn, COUNT(*) as changes 
        FROM abn_location_history 
        GROUP BY abn 
        HAVING COUNT(*) > 1 
        ORDER BY changes DESC LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  ABN: {row[0]} | Changes: {row[1]}")
    
    # 5. Trading name reuse check
    print("\n--- TRADING NAME REUSE (Same name, multiple ABNs) ---")
    cur.execute("""
        SELECT trading_name, COUNT(DISTINCT abn) AS abn_count
        FROM abn_trading_name
        GROUP BY trading_name
        HAVING COUNT(DISTINCT abn) > 1
        ORDER BY abn_count DESC
        LIMIT 5
    """)
    results = cur.fetchall()
    if results:
        for row in results:
            print(f"  '{row[0][:40]}': used by {row[1]} ABNs")
    else:
        print("  (No trading name reuse detected)")
    
    # 6. GST status summary
    print("\n--- GST STATUS SUMMARY ---")
    cur.execute("""
        SELECT is_current, count(*) 
        FROM abn_gst_history 
        GROUP BY is_current
    """)
    for row in cur.fetchall():
        status = "Current" if row[0] else "Historical"
        print(f"  {status}: {row[1]}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    try:
        run_full_verification()
    except Exception as e:
        print(f"Verification failed: {e}")
