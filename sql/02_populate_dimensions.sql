-- ============================================================
-- RETAIL COMMERCIAL INTELLIGENCE
-- STEP 2: POPULATE DIMENSION TABLES
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. DATE DIMENSION
INSERT OR IGNORE INTO dim_date (
    date_key, full_date, year, quarter, month, month_name,
    year_month, day_of_month, day_name, day_of_week
)
SELECT DISTINCT
    CAST(strftime('%Y%m%d', invoice_date) AS INTEGER),
    date(invoice_date),
    CAST(strftime('%Y', invoice_date) AS INTEGER),
    ((CAST(strftime('%m', invoice_date) AS INTEGER) - 1) / 3) + 1,
    CAST(strftime('%m', invoice_date) AS INTEGER),
    CASE strftime('%m', invoice_date)
        WHEN '01' THEN 'January'
        WHEN '02' THEN 'February'
        WHEN '03' THEN 'March'
        WHEN '04' THEN 'April'
        WHEN '05' THEN 'May'
        WHEN '06' THEN 'June'
        WHEN '07' THEN 'July'
        WHEN '08' THEN 'August'
        WHEN '09' THEN 'September'
        WHEN '10' THEN 'October'
        WHEN '11' THEN 'November'
        WHEN '12' THEN 'December'
    END,
    strftime('%Y-%m', invoice_date),
    CAST(strftime('%d', invoice_date) AS INTEGER),
    CASE strftime('%w', invoice_date)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END,
    CAST(strftime('%w', invoice_date) AS INTEGER)
FROM fact_transactions
WHERE invoice_date IS NOT NULL;

-- 2. CUSTOMER DIMENSION
INSERT OR IGNORE INTO dim_customer (customer_id)
SELECT DISTINCT customer_id
FROM fact_transactions
WHERE customer_id IS NOT NULL;

-- 3. PRODUCT DIMENSION
-- Prefer genuine product descriptions; within each type, prefer
-- the most frequently observed description for the stock code.
WITH description_ranked AS (
    SELECT
        stock_code,
        description,
        description_type,
        COUNT(*) AS frequency,
        ROW_NUMBER() OVER (
            PARTITION BY stock_code
            ORDER BY
                CASE description_type
                    WHEN 'PRODUCT_DESCRIPTION' THEN 1
                    WHEN 'OPERATIONAL_NOTE' THEN 2
                    ELSE 3
                END,
                COUNT(*) DESC,
                description
        ) AS rn
    FROM fact_transactions
    WHERE stock_code IS NOT NULL
      AND description IS NOT NULL
    GROUP BY stock_code, description, description_type
)
INSERT OR IGNORE INTO dim_product (
    stock_code, description, description_type
)
SELECT stock_code, description, description_type
FROM description_ranked
WHERE rn = 1;

-- Include stock codes with no available description.
INSERT OR IGNORE INTO dim_product (
    stock_code, description, description_type
)
SELECT DISTINCT stock_code, NULL, 'MISSING'
FROM fact_transactions
WHERE stock_code IS NOT NULL
  AND stock_code NOT IN (SELECT stock_code FROM dim_product);

-- 4. COUNTRY DIMENSION
INSERT OR IGNORE INTO dim_country (country_name)
SELECT DISTINCT TRIM(country)
FROM fact_transactions
WHERE country IS NOT NULL
  AND TRIM(country) <> '';

-- Unknown country member for referential integrity.
INSERT OR IGNORE INTO dim_country (country_key, country_name)
VALUES (0, 'Unknown');

-- 5. TRANSACTION TYPE DIMENSION
INSERT OR IGNORE INTO dim_transaction_type (transaction_type)
SELECT DISTINCT transaction_type
FROM fact_transactions
WHERE transaction_type IS NOT NULL;

-- DIMENSION COUNTS
SELECT 'dim_date' AS dimension, COUNT(*) AS records FROM dim_date
UNION ALL
SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'dim_country', COUNT(*) FROM dim_country
UNION ALL
SELECT 'dim_transaction_type', COUNT(*) FROM dim_transaction_type;
