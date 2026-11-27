-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- STEP 4: FINAL FACT TABLE RECONCILIATION
-- Run after 03_create_fact_sales.sql
-- ============================================================

-- 1. Compare source and analytical row counts and signed values.
SELECT
    'Source' AS dataset,
    COUNT(*) AS transaction_lines,
    ROUND(SUM(line_value), 2) AS signed_value
FROM fact_transactions
UNION ALL
SELECT
    'Analytical Fact',
    COUNT(*),
    ROUND(SUM(line_value), 2)
FROM fact_sales;

-- 2. Check duplicate source row IDs in the fact table.
SELECT COUNT(*) AS duplicate_source_ids
FROM (
    SELECT source_row_id
    FROM fact_sales
    GROUP BY source_row_id
    HAVING COUNT(*) > 1
);

-- 3. Check foreign-key integrity (no rows should be returned).
PRAGMA foreign_key_check;

-- 4. Compare transaction classification counts and signed values.
SELECT
    transaction_type,
    COUNT(*) AS transaction_lines,
    ROUND(SUM(line_value), 2) AS signed_value
FROM fact_transactions
GROUP BY transaction_type
ORDER BY transaction_type;

SELECT
    tt.transaction_type,
    COUNT(*) AS transaction_lines,
    ROUND(SUM(fs.line_value), 2) AS signed_value
FROM fact_sales fs
JOIN dim_transaction_type tt
    ON fs.transaction_type_key = tt.transaction_type_key
GROUP BY tt.transaction_type
ORDER BY tt.transaction_type;
