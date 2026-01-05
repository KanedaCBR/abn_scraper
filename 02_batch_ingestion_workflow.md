\# ABR Batch Ingestion Workflow



\## Trigger

Manual execution of batch script.



\## Steps

1\. Scan `/downloads` for PDF files matching naming convention:

&nbsp;  - ABNCurrent\_details\_\*.pdf

&nbsp;  - ABNHistorical\_details\_\*.pdf



2\. For each file:

&nbsp;  - Compute SHA-256 hash

&nbsp;  - Check `abn\_document\_registry`

&nbsp;    - If hash exists → SKIP

&nbsp;    - Else continue



3\. Identify document type from filename.



4\. Parse PDF:

&nbsp;  - Extract structured fields only.

&nbsp;  - Normalize dates.

&nbsp;  - Convert `(current)` → to\_date = NULL, is\_current = true



5\. Insert rows (INSERT ONLY):

&nbsp;  - abn\_document\_registry (SUCCESS or FAILED)

&nbsp;  - abn\_entity (if not yet present)

&nbsp;  - attribute tables



6\. On parse failure:

&nbsp;  - Insert FAILED row in `abn\_document\_registry`

&nbsp;  - Log error message

&nbsp;  - Continue to next document



\## Guarantees

\- No updates

\- No deletes

\- No partial rollback across documents

\- Document-level idempotency only



