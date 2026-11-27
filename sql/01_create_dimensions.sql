PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name TEXT,
    year_month TEXT,
    day_of_month INTEGER,
    day_name TEXT,
    day_of_week INTEGER
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER UNIQUE
);

INSERT OR IGNORE INTO dim_customer (customer_key, customer_id)
VALUES (0, NULL);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL UNIQUE,
    description TEXT,
    description_type TEXT
);

CREATE TABLE IF NOT EXISTS dim_country (
    country_key INTEGER PRIMARY KEY AUTOINCREMENT,
    country_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_transaction_type (
    transaction_type_key INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT NOT NULL UNIQUE
);
