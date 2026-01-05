-- =========================================================
-- ABR ANALYSIS QUERY PACK
-- Purpose: pattern detection & longitudinal analysis
-- =========================================================

-- ---------------------------------------------------------
-- 1. First registration date per ABN
-- ---------------------------------------------------------
SELECT
    abn,
    first_active_date
FROM abn_entity
ORDER BY first_active_date;

-- ---------------------------------------------------------
-- 2. ABNs first registered before a given year (e.g. 2005)
-- ---------------------------------------------------------
SELECT
    abn,
    entity_name,
    first_active_date
FROM abn_entity
WHERE first_active_date < DATE '2005-01-01'
ORDER BY first_active_date;

-- ---------------------------------------------------------
-- 3. Current business location per ABN
-- ---------------------------------------------------------
SELECT
    abn,
    state,
    postcode
FROM abn_location_history
WHERE is_current = true;

-- ---------------------------------------------------------
-- 4. State-to-state movement (any time)
-- ---------------------------------------------------------
SELECT DISTINCT
    l1.abn,
    l1.state AS from_state,
    l2.state AS to_state
FROM abn_location_history l1
JOIN abn_location_history l2
  ON l1.abn = l2.abn
 AND l1.state <> l2.state;

-- ---------------------------------------------------------
-- 5. Postcode movement timeline for a given ABN
-- ---------------------------------------------------------
SELECT
    abn,
    state,
    postcode,
    from_date,
    to_date,
    is_current
FROM abn_location_history
WHERE abn = '99125524457'
ORDER BY from_date;

-- ---------------------------------------------------------
-- 6. ABNs that changed postcode more than once
-- ---------------------------------------------------------
SELECT
    abn,
    COUNT(DISTINCT postcode) AS postcode_count
FROM abn_location_history
GROUP BY abn
HAVING COUNT(DISTINCT postcode) > 1
ORDER BY postcode_count DESC;

-- ---------------------------------------------------------
-- 7. Trading name reuse across multiple ABNs
-- ---------------------------------------------------------
SELECT
    trading_name,
    COUNT(DISTINCT abn) AS abn_count
FROM abn_trading_name
GROUP BY trading_name
HAVING COUNT(DISTINCT abn) > 1
ORDER BY abn_count DESC;

-- ---------------------------------------------------------
-- 8. Business name reuse across multiple ABNs
-- ---------------------------------------------------------
SELECT
    business_name,
    COUNT(DISTINCT abn) AS abn_count
FROM abn_business_name
GROUP BY business_name
HAVING COUNT(DISTINCT abn) > 1
ORDER BY abn_count DESC;

-- ---------------------------------------------------------
-- 9. ABNs with multiple entity name changes
-- ---------------------------------------------------------
SELECT
    abn,
    COUNT(*) AS name_versions
FROM abn_name_history
GROUP BY abn
HAVING COUNT(*) > 1
ORDER BY name_versions DESC;

-- ---------------------------------------------------------
-- 10. Potential phoenix-style movement heuristic
--     (simple, non-inferential)
-- ---------------------------------------------------------
SELECT
    e.abn,
    e.entity_name,
    COUNT(DISTINCT l.state) AS states_used,
    COUNT(DISTINCT l.postcode) AS postcodes_used
FROM abn_entity e
JOIN abn_location_history l
  ON e.abn = l.abn
GROUP BY e.abn, e.entity_name
HAVING COUNT(DISTINCT l.postcode) >= 2
ORDER BY postcodes_used DESC;

-- ---------------------------------------------------------
-- 11. ABNs with GST ever registered, now not current
-- ---------------------------------------------------------
SELECT DISTINCT
    abn
FROM abn_gst_history
WHERE gst_status ILIKE '%Registered%'
  AND is_current = false;

-- ---------------------------------------------------------
-- 12. Full longitudinal profile for one ABN
-- ---------------------------------------------------------
-- Location history
SELECT * FROM abn_location_history
WHERE abn = '99125524457'
ORDER BY from_date;

-- Name history
SELECT * FROM abn_name_history
WHERE abn = '99125524457'
ORDER BY from_date;

-- Business names
SELECT * FROM abn_business_name
WHERE abn = '99125524457'
ORDER BY from_date;

-- Trading names
SELECT * FROM abn_trading_name
WHERE abn = '99125524457'
ORDER BY from_date;
