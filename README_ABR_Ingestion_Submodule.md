\# ABR Ingestion Submodule



\## Purpose

This submodule ingests Australian Business Register (ABR) PDF outputs

(Current details and Historical details) into PostgreSQL to support

longitudinal and pattern-based analysis such as:



\- state/postcode movement

\- first business registration timing

\- trading name and business name reuse

\- simple phoenix-style pattern detection



The system is intentionally \*\*KISS\*\*, \*\*insert-only\*\*, and \*\*ABR-only\*\*.



---



\## Data Sources

\- ABR “Current details” PDFs

\- ABR “Historical details” PDFs



No non-ABR data is ingested or referenced.



---



\## Core Design Principles

\- \*\*Document-level idempotency\*\*

&nbsp; - A PDF is processed once only (SHA-256 hash).

\- \*\*Insert-only\*\*

&nbsp; - No updates, no deletes.

\- \*\*Exact fidelity\*\*

&nbsp; - Dates and values reflect ABR statements only.

&nbsp; - No inferred or derived dates.

\- \*\*Auditability\*\*

&nbsp; - Every row is traceable to a source document.

\- \*\*KISS\*\*

&nbsp; - Explicit tables per attribute.

&nbsp; - No polymorphic schemas.

&nbsp; - No background daemons.



---



\## Repository Documents (Authoritative)



| File | Purpose |

|----|----|

| `01\_schema\_postgres\_abr.sql` | Final PostgreSQL schema |

| `02\_batch\_ingestion\_workflow.md` | Batch ingestion logic |

| `03\_parser\_rules\_abr.md` | Parser rules mapped to ABR sections |

| `04\_implementation\_plan\_mvp.md` | MVP-first implementation plan |

| `05\_sql\_analysis\_query\_pack.sql` | Analysis \& pattern queries |



If there is any conflict between code and these documents,

\*\*the documents take precedence\*\*.



---



\## Ingestion Overview



1\. Batch job scans `/downloads`

2\. Identifies ABR PDFs by filename

3\. Computes file hash

4\. Skips already-ingested documents

5\. Parses structured data

6\. Inserts rows into PostgreSQL

7\. Logs success or failure



On failure, the job logs and continues.



---



\## Schema Overview



\- `abn\_entity`

\- `abn\_status\_history`

\- `abn\_name\_history`

\- `abn\_location\_history`

\- `abn\_business\_name`

\- `abn\_trading\_name`

\- `abn\_gst\_history`

\- `abn\_asic\_registration`

\- `abn\_document\_registry`



All history tables store:

\- from\_date

\- to\_date (NULL if current)

\- is\_current

\- source\_document\_id



---



\## What This System Does NOT Do

\- No re-ingestion or updates

\- No enrichment (ASIC, ATO, addresses, people)

\- No inference or scoring

\- No real-time monitoring

\- No data correction



Those are deliberate future decisions.



---



\## Intended Use

This database is an \*\*evidence store\*\*, not a conclusions engine.

It supports downstream analysis, visualisation, and legal or forensic review

without altering or interpreting ABR data.



---



\## Definition of Done

\- All ABR PDFs ingested or logged as failures

\- No duplicate documents processed

\- Queries in `05\_sql\_analysis\_query\_pack.sql` run successfully

\- Spot checks match source PDFs exactly



