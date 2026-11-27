-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- STEP 3: CREATE AND POPULATE FACT TABLE
-- ============================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_sales;

CREATE TABLE fact_sales (
    source_row_id INTEGER PRIMARY KEY,
    invoice TEXT NOT NULL,
    date_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    country_key INTEGER NOT NULL,
    transaction_type_key INTEGER NOT NULL,
    quantity INTEGER,
    unit_price REAL,
    line_value REAL,
    source_sheet TEXT,
    is_cancellation INTEGER,
    is_bad_debt_adjustment INTEGER,
    is_negative_quantity INTEGER,
    is_zero_price INTEGER,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (country_key) REFERENCES dim_country(country_key),
    FOREIGN KEY (transaction_type_key)
        REFERENCES dim_transaction_type(transaction_type_key)
);

INSERT INTO fact_sales (
    source_row_id, invoice, date_key, customer_key, product_key,
    country_key, transaction_type_key, quantity, unit_price,
    line_value, source_sheet, is_cancellation,
    is_bad_debt_adjustment, is_negative_quantity, is_zero_price
)
SELECT
    t.source_row_id,
    CAST(t.invoice AS TEXT),
    d.date_key,
    COALESCE(c.customer_key, 0),
    p.product_key,
    COALESCE(co.country_key, 0),
    tt.transaction_type_key,
    t.quantity,
    t.price,
    t.line_value,
    t.source_sheet,
    CASE WHEN LOWER(t.is_cancellation) = 'true' THEN 1 ELSE 0 END,
    CASE WHEN LOWER(t.is_bad_debt_adjustment) = 'true' THEN 1 ELSE 0 END,
    CASE WHEN LOWER(t.is_negative_quantity) = 'true' THEN 1 ELSE 0 END,
    CASE WHEN LOWER(t.is_zero_price) = 'true' THEN 1 ELSE 0 END
FROM fact_transactions t
LEFT JOIN dim_date d
    ON d.full_date = DATE(t.invoice_date)
LEFT JOIN dim_customer c
    ON c.customer_id = t.customer_id
LEFT JOIN dim_product p
    ON p.stock_code = t.stock_code
LEFT JOIN dim_country co
    ON co.country_name = TRIM(t.country)
LEFT JOIN dim_transaction_type tt
    ON tt.transaction_type = t.transaction_type;

-- VALIDATION
SELECT COUNT(*) AS fact_sales_rows FROM fact_sales;

SELECT
    (SELECT COUNT(*) FROM fact_transactions) AS source_rows,
    (SELECT COUNT(*) FROM fact_sales) AS fact_rows;

SELECT 'Source' AS dataset, ROUND(SUM(line_value), 2) AS signed_value
FROM fact_transactions
UNION ALL
SELECT 'Fact', ROUND(SUM(line_value), 2)
FROM fact_sales;

PRAGMA foreign_key_check;

SELECT
    SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS missing_date_keys,
    SUM(CASE WHEN customer_key IS NULL THEN 1 ELSE 0 END) AS missing_customer_keys,
    SUM(CASE WHEN product_key IS NULL THEN 1 ELSE 0 END) AS missing_product_keys,
    SUM(CASE WHEN country_key IS NULL THEN 1 ELSE 0 END) AS missing_country_keys,
    SUM(CASE WHEN transaction_type_key IS NULL THEN 1 ELSE 0 END)
        AS missing_transaction_type_keys
FROM fact_sales;
