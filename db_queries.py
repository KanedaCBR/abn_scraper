"""Database query functions for Streamlit ABN Browser UI."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Database connection configuration
DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "database": os.getenv("PGDATABASE", "postgres"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "password")
}

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def get_dashboard_stats():
    """Get summary statistics for the dashboard."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            stats = {}
            
            # Total entities
            cur.execute("SELECT COUNT(*) as count FROM abn_entity")
            stats['total_entities'] = cur.fetchone()['count']
            
            # Total documents
            cur.execute("SELECT COUNT(*) as count FROM abn_document_registry")
            stats['total_documents'] = cur.fetchone()['count']
            
            # Success rate
            cur.execute("""
                SELECT ingestion_status, COUNT(*) as count 
                FROM abn_document_registry 
                GROUP BY ingestion_status
            """)
            stats['document_status'] = {row['ingestion_status']: row['count'] for row in cur.fetchall()}
            
            # Entity types distribution
            cur.execute("""
                SELECT entity_type, COUNT(*) as count 
                FROM abn_entity 
                GROUP BY entity_type 
                ORDER BY count DESC
            """)
            stats['entity_types'] = [dict(row) for row in cur.fetchall()]
            
            # State distribution
            cur.execute("""
                SELECT state, COUNT(*) as count 
                FROM abn_location_history 
                WHERE is_current = true 
                GROUP BY state 
                ORDER BY count DESC
            """)
            stats['state_distribution'] = [dict(row) for row in cur.fetchall()]
            
            # GST summary
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN is_current THEN 1 ELSE 0 END) as current_gst,
                    COUNT(*) as total_gst
                FROM abn_gst_history
            """)
            gst = cur.fetchone()
            stats['gst_current'] = gst['current_gst'] or 0
            stats['gst_total'] = gst['total_gst'] or 0
            
            return stats

def search_entities(query="", entity_type=None, state=None, limit=50, offset=0):
    """Search entities by name, trading name, or business name."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = []
            params = []
            
            if query:
                conditions.append("""
                    (e.entity_name ILIKE %s 
                     OR e.abn LIKE %s
                     OR EXISTS (SELECT 1 FROM abn_trading_name t WHERE t.abn = e.abn AND t.trading_name ILIKE %s)
                     OR EXISTS (SELECT 1 FROM abn_business_name b WHERE b.abn = e.abn AND b.business_name ILIKE %s))
                """)
                search_term = f"%{query}%"
                params.extend([search_term, f"%{query}%", search_term, search_term])
            
            if entity_type:
                conditions.append("e.entity_type = %s")
                params.append(entity_type)
            
            if state:
                conditions.append("""
                    EXISTS (SELECT 1 FROM abn_location_history l 
                            WHERE l.abn = e.abn AND l.is_current = true AND l.state = %s)
                """)
                params.append(state)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM abn_entity e {where_clause}"
            cur.execute(count_query, params)
            total = cur.fetchone()['count']
            
            # Get results
            query_sql = f"""
                SELECT 
                    e.abn, 
                    e.entity_name, 
                    e.entity_type, 
                    e.first_active_date,
                    l.state,
                    l.postcode
                FROM abn_entity e
                LEFT JOIN abn_location_history l ON e.abn = l.abn AND l.is_current = true
                {where_clause}
                ORDER BY e.entity_name
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cur.execute(query_sql, params)
            
            return {
                'total': total,
                'results': [dict(row) for row in cur.fetchall()]
            }

def get_entity_detail(abn):
    """Get complete entity profile with all related data."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            result = {}
            
            # Main entity
            cur.execute("SELECT * FROM abn_entity WHERE abn = %s", (abn,))
            entity = cur.fetchone()
            if not entity:
                return None
            result['entity'] = dict(entity)
            
            # Status history
            cur.execute("""
                SELECT status, from_date, to_date, is_current 
                FROM abn_status_history 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['status_history'] = [dict(row) for row in cur.fetchall()]
            
            # Name history
            cur.execute("""
                SELECT entity_name, from_date, to_date, is_current 
                FROM abn_name_history 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['name_history'] = [dict(row) for row in cur.fetchall()]
            
            # Location history
            cur.execute("""
                SELECT state, postcode, from_date, to_date, is_current 
                FROM abn_location_history 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['location_history'] = [dict(row) for row in cur.fetchall()]
            
            # Business names
            cur.execute("""
                SELECT business_name, from_date 
                FROM abn_business_name 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['business_names'] = [dict(row) for row in cur.fetchall()]
            
            # Trading names
            cur.execute("""
                SELECT trading_name, from_date 
                FROM abn_trading_name 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['trading_names'] = [dict(row) for row in cur.fetchall()]
            
            # GST history
            cur.execute("""
                SELECT gst_status, from_date, to_date, is_current 
                FROM abn_gst_history 
                WHERE abn = %s ORDER BY from_date DESC
            """, (abn,))
            result['gst_history'] = [dict(row) for row in cur.fetchall()]
            
            # ASIC registration
            cur.execute("""
                SELECT asic_number, asic_type 
                FROM abn_asic_registration 
                WHERE abn = %s
            """, (abn,))
            result['asic_registration'] = [dict(row) for row in cur.fetchall()]
            
            return result

def get_entity_types():
    """Get list of unique entity types."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT entity_type FROM abn_entity ORDER BY entity_type")
            return [row[0] for row in cur.fetchall()]

def get_states():
    """Get list of unique states."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT state FROM abn_location_history WHERE state IS NOT NULL ORDER BY state")
            return [row[0] for row in cur.fetchall()]

def get_analytics_data():
    """Get data for analytics charts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            analytics = {}
            
            # Registrations by year
            cur.execute("""
                SELECT EXTRACT(YEAR FROM first_active_date)::int as year, COUNT(*) as count
                FROM abn_entity 
                WHERE first_active_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM first_active_date)
                ORDER BY year
            """)
            analytics['by_year'] = [dict(row) for row in cur.fetchall()]
            
            # Trading name reuse
            cur.execute("""
                SELECT trading_name, COUNT(DISTINCT abn) as abn_count
                FROM abn_trading_name
                GROUP BY trading_name
                HAVING COUNT(DISTINCT abn) > 1
                ORDER BY abn_count DESC
                LIMIT 10
            """)
            analytics['trading_name_reuse'] = [dict(row) for row in cur.fetchall()]
            
            # Entities with most location changes
            cur.execute("""
                SELECT e.abn, e.entity_name, COUNT(*) as location_changes
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                GROUP BY e.abn, e.entity_name
                HAVING COUNT(*) > 1
                ORDER BY location_changes DESC
                LIMIT 10
            """)
            analytics['location_changes'] = [dict(row) for row in cur.fetchall()]
            
            return analytics
