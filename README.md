# Retail Commercial Intelligence

An end-to-end commercial analytics project using the UCI Online Retail II dataset, SQLite and Power BI. The project examines whether reported revenue is supported by durable customer behaviour, diversified product demand and sustainable market performance.

## Business question

**Is the retailer generating durable revenue, or is reported performance vulnerable to customer concentration, weak repeat purchasing, product dependence and cancellations?**

The analysis is designed around commercial decisions rather than dashboard metrics alone. It investigates revenue trends, order behaviour, customer retention and concentration, product performance, geographic exposure and cancellations.

## Dashboard

The Power BI report is organised into three pages:

1. **Executive Overview** — revenue, orders, units, average order value, identified customers, cancellation value, monthly trends and country contribution.
2. **Customer & Product Performance** — new versus returning customer revenue, customer segments, product rankings and customer revenue concentration.
3. **Markets & Operational Performance** — monthly sales, international revenue, cancellation value by country and weekday sales patterns.

The final Power BI report (.pbix), PDF export and page screenshots will be added to the dashboard/ directory.

## Data source

- **Dataset:** [Online Retail II — UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Publisher:** UCI Machine Learning Repository
- **Coverage:** December 2009 to 9 December 2011
- **Business context:** UK-based, non-store online retailer
- **Licence:** CC BY 4.0

The original workbook contains two worksheets. The source data is not redistributed in this repository. Download it from the UCI source above and follow the preparation instructions in the project documentation.

## Technology

- Python — source data preparation and quality auditing
- SQLite — relational data storage, transformations and analytical queries
- SQL — data validation and commercial analysis
- Power BI Desktop — data model, DAX measures and interactive reporting

## Analytical workflow

1. **Extract and standardise** the two source worksheets; standardise field names and data types.
2. **Audit duplicates and overlap** across worksheets, retaining the appropriate source copy and preserving row-level traceability.
3. **Recover descriptions conservatively** only where a stock code has one unambiguous description; retain unresolved missing values.
4. **Classify transaction records** into sales, cancellations, bad-debt adjustments and other non-standard transaction types. Keep diagnostic flags separate from the mutually exclusive primary classification.
5. **Build the analytical model** in SQLite using a sales fact table and date, customer, product, country and transaction-type dimensions.
6. **Analyse commercial performance** across revenue, orders, customer behaviour, products, geography and cancellations.
7. **Build the Power BI report** using a star-schema model, DAX measures and a consistent visual theme.

Detailed scripts and documentation will be maintained in sql/ and documentation/.

## Metric definitions and interpretation

- **Sales revenue** is based on records classified as sales; cancellations and bad-debt adjustments are analysed separately.
- **Average order value (AOV)** is sales revenue divided by distinct sales invoices.
- **Identified customers** excludes transactions without a customer ID.
- **Cancellation value** is shown as an operational measure and should not be interpreted as confirmed lost profit.
- Customer segments are rule-based analytical groupings defined for this project, not externally validated industry standards.

## Important limitations

- The dataset contains no product cost data; this project does not calculate gross margin or profitability.
- Missing customer IDs mean some sales cannot be attributed to identified customers.
- The dataset ends on 9 December 2011; December 2011 is a partial month and should not be compared directly with complete months.
- Customer inactivity and cohort measures describe observed behaviour within the available period; they do not establish why a customer stopped purchasing.
- Descriptive patterns are not causal evidence. Market growth does not, by itself, establish the return on additional investment.
- Cancellation values can include unusual operational adjustments and bulk transactions; they require context before being interpreted as product or service failures.

## Repository structure

~~~text
retail-commercial-intelligence/
├── README.md
├── .gitignore
├── data/
│   └── README.md
├── dashboard/
│   ├── screenshots/
│   └── README.md
├── sql/
│   └── README.md
└── documentation/
    └── README.md
~~~

## Reproducing the project

1. Download the Online Retail II workbook from the UCI Machine Learning Repository.
2. Review the data preparation instructions and scripts in this repository.
3. Run the preparation workflow to create the cleaned transaction file.
4. Create and populate the SQLite database using the SQL scripts.
5. Export the analytical tables for Power BI if using the CSV-import workflow.
6. Open the Power BI report in Power BI Desktop and refresh it against the prepared data.

Exact commands, expected outputs and validation checks will be documented alongside the scripts.

## Licence and attribution

The Online Retail II dataset is provided by the UCI Machine Learning Repository under **CC BY 4.0**. Please refer to the [dataset page](https://archive.ics.uci.edu/dataset/502/online+retail+ii) for the original data and attribution details.

Unless otherwise stated in individual files, the original dataset remains subject to its source licence. Project code and documentation are provided under the repository licence once one is added.
