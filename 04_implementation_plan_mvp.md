\# Implementation Plan (MVP First)



\## Phase 1 — Foundations

\- Create PostgreSQL schema

\- Create document registry

\- Create DB connection module



\## Phase 2 — Minimal Vertical Slice

\- Batch runner script

\- Hash + skip logic

\- Current-details PDF parser

\- Insert abn\_entity + status + location



\## Phase 3 — Expand Coverage

\- Business names parser

\- Trading names parser

\- GST history parser



\## Phase 4 — Historical PDFs

\- Historical name parser

\- Historical location parser

\- Historical status parser



\## Phase 5 — Hardening

\- Error handling + logging

\- Failure capture in registry

\- Spot-check against PDFs



\## Out of Scope

\- Updates

\- Re-ingestion

\- Watchers

\- Non-ABR data



