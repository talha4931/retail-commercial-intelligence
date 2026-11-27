# Power BI report

The Power BI report is developed from CSV exports of the SQLite star schema because the working environment does not have the required SQLite connector/ODBC driver available.

## Model tables

- `fact_sales`
- `dim_date`
- `dim_customer`
- `dim_product`
- `dim_country`
- `dim_transaction_type`

Create active one-to-many relationships from each dimension to `fact_sales`, using the matching surrogate key. Use single-direction filtering from dimensions to the fact table.

## Reporting principles

- Sales measures must filter `dim_transaction_type[transaction_type]` to SALE.
- Keep cancellation value separate from sales revenue.
- Exclude operational stock codes M, DOT and POST from merchandise product rankings.
- Exclude customer key 0 from identifiable-customer metrics.
- Sort month names by month number and use year-month for chronological monthly charts.
- Treat December 2011 as a partial month ending 9 December.

The Power BI report file is not yet committed. Add the finished `.pbix` once the report is final and has been checked for private or local data paths.