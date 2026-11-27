# Retail Commercial Intelligence

**A transaction-level retail analytics project using Python, SQLite and Power BI.**

## Business question

Is the retailer generating durable revenue, or is reported performance vulnerable to customer concentration, weak repeat purchasing, product dependence and cancellations?

The project treats revenue growth as only one part of commercial performance. It examines the customers, orders, products, markets and operational patterns that sit underneath reported sales.

## Project overview

This project uses the **Online Retail II** dataset from the UCI Machine Learning Repository. It contains transactions from a UK-registered, non-store online retailer between December 2009 and December 2011.

The workflow is designed to be reproducible:

1. **Python — data preparation:** standardise fields, audit exact duplicates, resolve unambiguous missing descriptions, classify transaction types and export quality checks.
2. **SQLite — data modelling:** load the cleaned transaction data into a staging table, create a star schema and validate the analytical fact table.
3. **SQL — commercial analysis:** investigate revenue trends, customer behaviour, product and order concentration, geography and cancellations.
4. **Power BI — reporting:** communicate the commercial findings through an executive overview and supporting customer, product, market and operational views.

## Main commercial findings

- Total sales revenue is **£20.48m** across **40,077 orders**, with an average order value of **£510.92**.
- November 2011 new-customer revenue was **53.3% lower year on year**, while returning-customer revenue was **6.0% higher**.
- The project's rule-based segmentation identified **449 high-value inactive customers** with at least five orders, at least £1,000 historical revenue and no purchase for at least 91 days. Their historic revenue was approximately **£1.76m**; this is not a forecast of recoverable revenue.
- The top 100 identifiable customers account for **37.55% of identifiable-customer revenue**.
- The UK accounts for **85.51% of merchandise revenue**. International growth is uneven and, in some markets, highly concentrated among a small number of customers.
- Cancellation value is approximately **£1.46m**, but includes unusual bulk and non-merchandise adjustments. It should not be read as a confirmed lost-sales rate.

More detail and caveats are in [the commercial findings](docs/commercial_findings.md).

## Technology

- Python: pandas, NumPy, openpyxl
- Database: SQLite
- SQL: dimensional modelling, joins, aggregation and validation
- Visualisation: Microsoft Power BI

## Repository structure

```text
retail-commercial-intelligence/
├── data/
│   ├── raw/                 # Place the source workbook here (not committed)
│   └── processed/           # Generated cleaned data (not committed)
├── docs/
│   ├── commercial_findings.md
│   └── data_dictionary.md
├── outputs/                 # Generated audit files (not committed)
├── powerbi/                 # Power BI report and guidance
├── scripts/
│   └── 01_clean_data.py
├── sql/
│   ├── 01_create_dimensions.sql
│   ├── 02_populate_dimensions.sql
│   ├── 03_create_fact_sales.sql
│   ├── 04_reconciliation.sql
│   └── README.md
├── .gitignore
└── requirements.txt
```

## Run the Python cleaning pipeline

### 1. Clone the repository

```bash
git clone https://github.com/talha4931/retail-commercial-intelligence.git
cd retail-commercial-intelligence
```

### 2. Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Obtain the source dataset

Download **Online Retail II** from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii).

Place the workbook at:

```text
data/raw/online_retail_II.xlsx
```

The source data is not included in this repository. The dataset is provided by UCI under **CC BY 4.0**; retain appropriate attribution when reusing it.

### 5. Run the cleaning pipeline

```bash
python scripts/01_clean_data.py
```

The script writes:

- `data/processed/retail_transactions_clean.csv`
- `outputs/data_quality/data_quality_audit.csv`
- `outputs/data_quality/duplicate_audit.csv`
- `outputs/data_quality/description_recovery_audit.csv`
- `outputs/data_quality/transaction_classification_summary.csv`
- `outputs/data_quality/description_classification_summary.csv`

These generated files are excluded from version control.

## SQLite workflow

After creating the staging table `fact_transactions` from the cleaned CSV, run the SQL scripts in order:

1. `sql/01_create_dimensions.sql`
2. `sql/02_populate_dimensions.sql`
3. `sql/03_create_fact_sales.sql`
4. `sql/04_reconciliation.sql)

See [the SQL workflow guide](sql/README.md) for prerequisites and validation expectations.

## Data model

The analytical model is a star schema with one transaction-line fact table and five dimensions:

- `fact_sales`
- `dim_date`
- `dim_customer`
- `dim_product`
- `dim_country`
- `dim_transaction_type`

See [the data dictionary](docs/data_dictionary.md) for field definitions and classification rules.

## Analytical scope and limitations

The project analyses sales revenue, order behaviour, customer activity, product concentration, geography and cancellations. It does **not** calculate profit or gross margin because product cost data is not available.

Other limitations:
- Some transactions have no customer identifier. They remain in overall sales but are excluded from identified-customer measures.
- Cancellation value includes non-merchandise and unusual bulk adjustments.
- Customer segments use project-defined thresholds, not industry standards.
- The final month, December 2011, is partial and ends on 9 December.
- The dataset does not provide marketing spend, acquisition channels, inventory availability or cancellation reasons. Causal conclusions and investment-return claims are therefore outside scope.

## Author

Talha Hassan Saleem

