# SQL workflow

Run these scripts in order in DB Browser for SQLite, after loading the cleaned CSV into the staging table `fact_transactions`.

1. `01_create_dimensions.sql` — create the five dimension tables and the unknown customer member.
2. `02_populate_dimensions.sql` — populate date, customer, product, country and transaction-type dimensions.
3. `03_create_fact_sales.sql` — create and populate the analytical fact table.
4. `04_reconciliation.sql` — compare source and fact row counts, signed values, transaction classifications and foreign-key integrity.

## Prerequisites

- The cleaned transaction CSV produced by the Python cleaning pipeline.
- A SQLite database containing a staging table named `fact_transactions` with the columns referenced by the scripts.
- SQLite window-function support for the product-description ranking query.

## Important implementation notes

- Enable foreign keys for each SQLite connection using `PRAGMA foreign_keys = ON;`.
- The fact table is at transaction-line grain and retains `source_row_id` as its primary key.
- Missing customer IDs map to the unknown customer member (key 0); missing country values map to the unknown country member (key 0).
- The date dimension stores month names as text and month numbers separately for chronological sorting in Power BI.
- Re-running the fact-table script drops and recreates `fact_sales`. Do not run it against a production database without understanding that effect.

## Validation

The reconciliation script should show matching source and fact row counts and signed values. `PRAGMA foreign_key_check` should return no rows. Record actual outputs from the database run; do not treat the presence of validation queries as proof that they passed.
