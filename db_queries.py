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

# High-level entity category mapping SQL CASE expression
# Note: % escaped as %% to avoid conflicts with psycopg2 parameter formatting
HIGH_LEVEL_CATEGORY_SQL = """
    CASE 
        WHEN entity_type ILIKE '%%individual%%' OR entity_type ILIKE '%%sole trader%%' THEN 'Individual / Sole Trader'
        WHEN entity_type ILIKE '%%partnership%%' THEN 'Partnership'
        WHEN entity_type ILIKE '%%trust%%' THEN 'Trust'
        WHEN entity_type ILIKE '%%company%%' OR entity_type ILIKE '%%pty%%' OR entity_type ILIKE '%%ltd%%' THEN 'Company'
        WHEN entity_type ILIKE '%%super%%' OR entity_type ILIKE '%%fund%%' THEN 'Superannuation Fund'
        ELSE 'Other'
    END
"""

def map_to_high_level_category(entity_type):
    """Map detailed entity type to high-level category (Python version)."""
    if not entity_type:
        return 'Other'
    et = entity_type.lower()
    if 'individual' in et or 'sole trader' in et:
        return 'Individual / Sole Trader'
    if 'partnership' in et:
        return 'Partnership'
    if 'trust' in et:
        return 'Trust'
    if 'company' in et or 'pty' in et or 'ltd' in et:
        return 'Company'
    if 'super' in et or 'fund' in et:
        return 'Superannuation Fund'
    return 'Other'

def get_postcodes_by_state(state=None):
    """Get postcodes, optionally filtered by state."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if state:
                cur.execute("""
                    SELECT DISTINCT postcode 
                    FROM abn_location_history 
                    WHERE postcode IS NOT NULL AND state = %s
                    ORDER BY postcode
                """, (state,))
            else:
                cur.execute("""
                    SELECT DISTINCT postcode 
                    FROM abn_location_history 
                    WHERE postcode IS NOT NULL 
                    ORDER BY postcode
                """)
            return [row[0] for row in cur.fetchall()]


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
            
            # Entity types distribution (HIGH-LEVEL categories for dashboard)
            cur.execute(f"""
                SELECT {HIGH_LEVEL_CATEGORY_SQL} as entity_type, COUNT(*) as count 
                FROM abn_entity 
                GROUP BY {HIGH_LEVEL_CATEGORY_SQL}
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

def get_postcodes():
    """Get list of unique postcodes."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT postcode FROM abn_location_history WHERE postcode IS NOT NULL ORDER BY postcode")
            return [row[0] for row in cur.fetchall()]

def get_analytics_data_filtered(state=None, postcode=None, entity_type=None, use_high_level_category=False):
    """Get filtered data for analytics charts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            analytics = {}
            
            # Build filter conditions
            conditions = []
            params = []
            
            if state:
                conditions.append("l.state = %s")
                params.append(state)
            if postcode:
                conditions.append("l.postcode = %s")
                params.append(postcode)
            if entity_type:
                # Support filtering by high-level category or detailed type
                if entity_type in ['Individual / Sole Trader', 'Partnership', 'Trust', 'Company', 'Superannuation Fund', 'Other']:
                    conditions.append(f"{HIGH_LEVEL_CATEGORY_SQL} = %s")
                else:
                    conditions.append("e.entity_type = %s")
                params.append(entity_type)
            
            where_clause = "WHERE l.is_current = true"
            if conditions:
                where_clause += " AND " + " AND ".join(conditions)
            
            # Filtered entity count
            cur.execute(f"""
                SELECT COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
            """, params)
            analytics['filtered_count'] = cur.fetchone()['count']
            
            # Entity types - HIGH-LEVEL categories
            cur.execute(f"""
                SELECT {HIGH_LEVEL_CATEGORY_SQL} as entity_type, COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                GROUP BY {HIGH_LEVEL_CATEGORY_SQL}
                ORDER BY count DESC
            """, params)
            analytics['entity_types_high_level'] = [dict(row) for row in cur.fetchall()]
            
            # Entity types - DETAILED categories
            cur.execute(f"""
                SELECT e.entity_type, COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                GROUP BY e.entity_type
                ORDER BY count DESC
            """, params)
            analytics['entity_types_detailed'] = [dict(row) for row in cur.fetchall()]
            
            # State distribution
            cur.execute(f"""
                SELECT l.state, COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                GROUP BY l.state
                ORDER BY count DESC
            """, params)
            analytics['state_distribution'] = [dict(row) for row in cur.fetchall()]
            
            # Postcode distribution (for when state is selected)
            cur.execute(f"""
                SELECT l.postcode, COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                AND l.postcode IS NOT NULL
                GROUP BY l.postcode
                ORDER BY count DESC
                LIMIT 20
            """, params)
            analytics['postcode_distribution'] = [dict(row) for row in cur.fetchall()]
            
            # Registrations by year
            cur.execute(f"""
                SELECT EXTRACT(YEAR FROM e.first_active_date)::int as year, COUNT(DISTINCT e.abn) as count
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                AND e.first_active_date IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM e.first_active_date)
                ORDER BY year
            """, params)
            analytics['by_year'] = [dict(row) for row in cur.fetchall()]
            
            return analytics

def get_map_data(state=None, postcode=None, entity_type=None):
    """Get entity data for map view with state/postcode coordinates."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = ["l.is_current = true"]
            params = []
            
            if state:
                conditions.append("l.state = %s")
                params.append(state)
            if postcode:
                conditions.append("l.postcode = %s")
                params.append(postcode)
            if entity_type:
                # Support filtering by high-level category or detailed type
                if entity_type in ['Individual / Sole Trader', 'Partnership', 'Trust', 'Company', 'Superannuation Fund', 'Other']:
                    conditions.append(f"{HIGH_LEVEL_CATEGORY_SQL} = %s")
                else:
                    conditions.append("e.entity_type = %s")
                params.append(entity_type)
            
            where_clause = "WHERE " + " AND ".join(conditions)
            
            cur.execute(f"""
                SELECT 
                    e.abn,
                    e.entity_name,
                    e.entity_type,
                    l.state,
                    l.postcode
                FROM abn_entity e
                JOIN abn_location_history l ON e.abn = l.abn
                {where_clause}
                ORDER BY l.state, l.postcode, e.entity_name
            """, params)
            
            return [dict(row) for row in cur.fetchall()]

