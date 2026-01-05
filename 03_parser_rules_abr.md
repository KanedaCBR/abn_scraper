\# ABR PDF Parsing Rules



\## Global

\- Single-page PDFs

\- Text-extractable

\- Header-based parsing only



---



\## CURRENT DETAILS PDF



\### Header

\- "Current details for ABN"

\- Extract:

&nbsp; - ABN

&nbsp; - Record extracted date

&nbsp; - ABN last updated date



\### ABN Details Section

\- Entity name → abn\_entity.entity\_name

\- ABN status "Active from" → 

&nbsp; - abn\_status\_history

&nbsp; - abn\_entity.first\_active\_date

\- Entity type → abn\_entity.entity\_type

\- GST status → abn\_gst\_history

\- Main business location → abn\_location\_history (is\_current = true)



\### Business name(s)

\- Each row → abn\_business\_name



\### Trading name(s)

\- Each row → abn\_trading\_name



---



\## HISTORICAL DETAILS PDF



\### Header

\- "Historical details for ABN"



\### Entity name history

\- Rows with From / To

\- `(current)` → to\_date NULL + is\_current true



\### ABN status history

\- Same handling as entity name history



\### Main business location history

\- State + postcode

\- From / To preserved exactly



\### GST history

\- If "No current or historical GST registrations":

&nbsp; - Single row with gst\_status = 'NONE'



\### ASIC registration

\- Store number + inferred type (ACN/ARBN/etc.)



