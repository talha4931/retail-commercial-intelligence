# Data dictionary

## Source fields

| Field | Meaning | Notes |
|---|---|---|
| Invoice | Invoice identifier | Identifiers beginning with C are cancellation invoices |
| StockCode | Product or stock identifier | Includes non-merchandise operational codes |
| Description | Item description | Missing values are only recovered when a stock code has one unambiguous description |
| Quantity | Number of units on the line | Negative and zero values are retained and classified |
| InvoiceDate | Date and time of transaction | Used to create the date dimension |
| Price | Unit price | Negative values are classified as bad-debt adjustments in this project |
| CustomerID | Customer identifier | Missing values are retained as unidentified customer transactions |
| Country | Customer country field | UK-registered retailer; country is not necessarily customer residence |

## Cleaned transaction fields

| Field | Meaning |
|---|---|
| source_row_id | Original row position in the concatenated workbook; retained for traceability |
| source_sheet | Original worksheet name |
| line_value | Quantity multiplied by unit price |
| description_was_missing | Description was missing before recovery |
| description_was_imputed | Description was recovered from an unambiguous stock-code mapping |
| is_description_missing | Description remains missing after recovery |
| is_operational_description | Description appears to be an operational note rather than a product name |
| description_type | PRODUCT_DESCRIPTION, OPERATIONAL_NOTE or MISSING |
| is_cancellation | Invoice identifier begins with C |
| is_bad_debt_adjustment | Unit price is negative |
| is_negative_quantity | Quantity is negative |
| is_zero_quantity | Quantity equals zero |
| is_zero_price | Unit price equals zero |
| transaction_type | Mutually exclusive primary transaction classification |

## Transaction classification priority

The cleaning pipeline applies the first matching condition:

1. BAD_DEBT_ADJUSTMENT — negative unit price.
2. CANCELLATION — invoice identifier begins with C.
3. NEGATIVE_QUANTITY_NON_CANCELLATION — negative quantity on a non-cancellation invoice.
4. ZERO_QUANTITY — quantity equals zero.
5. ZERO_PRICE — unit price equals zero.
6. SALE — positive quantity and positive unit price.
7. OTHER — records not matching the above conditions.

The independent diagnostic flags are retained separately from the mutually exclusive transaction_type field.

## Analytical model

The SQLite model uses a transaction-line fact table, `fact_sales`, and five dimensions:

- `dim_date`: calendar attributes including year, quarter, month and year-month.
- `dim_customer`: customer identifiers, including an unknown member with key 0.
- `dim_product`: one representative description per stock code.
- `dim_country`: country names, including an Unknown member with key 0.
- `dim_transaction_type`: mutually exclusive transaction classifications.

The fact table stores dimension keys, invoice, quantity, unit price, line value, source worksheet and diagnostic flags.

## Important interpretation rules

- Missing CustomerID does not mean the transaction did not occur. Such revenue remains in total sales but is excluded from identified-customer metrics.
- Cancellations, bad-debt adjustments, negative-quantity lines and zero-price lines are not ordinary sales.
- The dataset contains no product cost data. Revenue must not be described as profit or gross margin.
- December 2011 is partial, ending on 9 December in this dataset. Avoid direct comparison with complete months without adjusting the period.
- Operational stock codes such as M, DOT and POST should not be treated as ordinary merchandise in product-performance analysis.
