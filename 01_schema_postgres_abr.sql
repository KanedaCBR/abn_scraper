-- =========================================================
-- ABR INGESTION SCHEMA (KISS, INSERT-ONLY)
-- =========================================================

CREATE TABLE abn_entity (
    abn                     CHAR(11) PRIMARY KEY,
    entity_name             TEXT,
    entity_type             TEXT,
    first_active_date       DATE,
    abn_last_updated_date   DATE,
    record_extracted_date   DATE,
    source_document_id      UUID NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT now()
);

-- -------------------------
-- INGESTION / PROVENANCE
-- -------------------------
CREATE TABLE abn_document_registry (
    document_id     UUID PRIMARY KEY,
    filename        TEXT NOT NULL,
    file_hash_sha256 CHAR(64) UNIQUE NOT NULL,
    document_type   TEXT CHECK (document_type IN ('CURRENT','HISTORICAL')),
    ingested_at     TIMESTAMPTZ,
    ingestion_status TEXT CHECK (ingestion_status IN ('SUCCESS','FAILED')),
    error_message   TEXT
);

-- -------------------------
-- STATUS HISTORY
-- -------------------------
CREATE TABLE abn_status_history (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    status          TEXT,
    from_date       DATE,
    to_date         DATE NULL,
    is_current      BOOLEAN NOT NULL,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- ENTITY NAME HISTORY
-- -------------------------
CREATE TABLE abn_name_history (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    entity_name     TEXT,
    from_date       DATE,
    to_date         DATE NULL,
    is_current      BOOLEAN NOT NULL,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- BUSINESS LOCATION HISTORY
-- -------------------------
CREATE TABLE abn_location_history (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    state           CHAR(3),
    postcode        CHAR(4),
    from_date       DATE,
    to_date         DATE NULL,
    is_current      BOOLEAN NOT NULL,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- BUSINESS NAMES
-- -------------------------
CREATE TABLE abn_business_name (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    business_name   TEXT,
    from_date       DATE,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- TRADING NAMES
-- -------------------------
CREATE TABLE abn_trading_name (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    trading_name    TEXT,
    from_date       DATE,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- GST HISTORY
-- -------------------------
CREATE TABLE abn_gst_history (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    gst_status      TEXT,
    from_date       DATE,
    to_date         DATE NULL,
    is_current      BOOLEAN NOT NULL,
    source_document_id UUID NOT NULL
);

-- -------------------------
-- ASIC REGISTRATION
-- -------------------------
CREATE TABLE abn_asic_registration (
    id              BIGSERIAL PRIMARY KEY,
    abn             CHAR(11) REFERENCES abn_entity(abn),
    asic_number     TEXT,
    asic_type       TEXT,
    source_document_id UUID NOT NULL
);
