from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# RETAIL COMMERCIAL INTELLIGENCE
# CLEANING PIPELINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AUDIT_DIR = PROJECT_ROOT / "outputs" / "data_quality"

OLDER_SHEET = "Year 2009-2010"
NEWER_SHEET = "Year 2010-2011"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def load_workbook(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Download Online Retail II from the UCI Machine Learning Repository "
            "and place online_retail_II.xlsx in data/raw/."
        )

    sheets = pd.read_excel(path, sheet_name=None)
    frames = []

    for sheet_name, sheet_data in sheets.items():
        sheet_data = sheet_data.copy()
        sheet_data["source_sheet"] = sheet_name
        frames.append(sheet_data)

    if not frames:
        raise ValueError("No worksheets were found in the workbook.")

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "source_row_id", range(1, len(df) + 1))

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    return df.rename(columns={
        "invoiceno": "invoice",
        "invoicedate": "invoice_date",
        "customerid": "customer_id",
        "stockcode": "stock_code",
        "unitprice": "price"
    })


def validate_and_standardise(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "invoice", "stock_code", "description", "quantity",
        "invoice_date", "price", "customer_id", "country", "source_sheet"
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()

    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = (
        df["description"].astype("string")
        .str.strip()
        .str.replace(r"\\s+", " ", regex=True)
    )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["customer_id"] = pd.to_numeric(
        df["customer_id"], errors="coerce"
    ).astype("Int64")

    if df["invoice"].isna().any() or df["invoice_date"].isna().any():
        raise ValueError("Invoice identifiers and invoice dates must be present.")

    return df


def remove_duplicates(df: pd.DataFrame):
    transaction_fields = [
        column for column in df.columns
        if column not in ["source_sheet", "source_row_id"]
    ]

    df = df.copy()
    df["_duplicate_group"] = df.groupby(
        transaction_fields, dropna=False, sort=False
    ).ngroup()

    group_sheet_counts = (
        df.groupby("_duplicate_group")["source_sheet"].nunique()
    )
    df["_worksheet_count"] = df["_duplicate_group"].map(group_sheet_counts)
    df["_retention_priority"] = (
        df["source_sheet"].eq(NEWER_SHEET).astype(int)
    )

    df = df.sort_values(
        ["_duplicate_group", "_retention_priority", "source_row_id"],
        ascending=[True, False, True]
    )

    duplicate_audit = df[
        df.duplicated(subset=transaction_fields, keep="first")
    ].copy()

    duplicate_audit["removal_reason"] = np.where(
        duplicate_audit["_worksheet_count"] > 1,
        "Cross-worksheet duplicate",
        "Within-worksheet duplicate"
    )

    retained = df.drop_duplicates(
        subset=transaction_fields, keep="first"
    ).copy()

    retained_sheet_map = retained.set_index(
        "_duplicate_group"
    )["source_sheet"]

    duplicate_audit["retained_source_sheet"] = (
        duplicate_audit["_duplicate_group"].map(retained_sheet_map)
    )

    removed_count = len(duplicate_audit)

    duplicate_audit.drop(
        columns=[
            "_duplicate_group", "_worksheet_count", "_retention_priority"
        ],
        errors="ignore"
    ).to_csv(AUDIT_DIR / "duplicate_audit.csv", index=False)

    retained = retained.drop(
        columns=["_duplicate_group", "_worksheet_count", "_retention_priority"]
    )

    if retained.duplicated(subset=transaction_fields).any():
        raise AssertionError("Exact duplicate transactions remain.")

    return retained, removed_count


def recover_descriptions(df: pd.DataFrame):
    df = df.copy()
    df["line_value"] = df["quantity"] * df["price"]

    description_candidates = (
        df.dropna(subset=["description"])
        .groupby("stock_code")["description"]
        .agg(lambda values: sorted(set(values.astype(str))))
    )

    unique_description_map = {
        stock_code: candidates[0]
        for stock_code, candidates in description_candidates.items()
        if len(candidates) == 1
    }

    missing_rows = df[df["description"].isna()].copy()
    candidate_counts = description_candidates.apply(len)

    missing_rows["candidate_count"] = (
        missing_rows["stock_code"].map(candidate_counts).fillna(0).astype(int)
    )
    missing_rows["recovered_description"] = (
        missing_rows["stock_code"].map(unique_description_map)
    )
    missing_rows["recovery_status"] = np.select(
        [
            missing_rows["candidate_count"].eq(1),
            missing_rows["candidate_count"].gt(1)
        ],
        [
            "Recovered: unique candidate",
            "Not recovered: multiple candidates"
        ],
        default="Not recovered: no candidate"
    )

    df["description_was_missing"] = df["description"].isna()
    df["description_was_imputed"] = (
        df["description"].isna()
        & df["stock_code"].isin(unique_description_map)
    )
    df["description"] = df["description"].fillna(
        df["stock_code"].map(unique_description_map)
    )
    df["is_description_missing"] = df["description"].isna()

    missing_rows.to_csv(
        AUDIT_DIR / "description_recovery_audit.csv", index=False
    )

    return df


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    operational_patterns = (
        r"wrong|wrongly|barcode|wrong code|"
        r"wrongly coded|wrongly marked|wrongly sold"
    )

    df["is_operational_description"] = df["description"].str.contains(
        operational_patterns, case=False, na=False, regex=True
    )

    df["description_type"] = np.select(
        [
            df["is_description_missing"],
            df["is_operational_description"]
        ],
        ["MISSING", "OPERATIONAL_NOTE"],
        default="PRODUCT_DESCRIPTION"
    )

    df["is_cancellation"] = df["invoice"].str.startswith("C", na=False)
    df["is_bad_debt_adjustment"] = df["price"] < 0
    df["is_negative_quantity"] = df["quantity"] < 0
    df["is_zero_quantity"] = df["quantity"] == 0
    df["is_zero_price"] = df["price"] == 0

    conditions = [
        df["is_bad_debt_adjustment"],
        df["is_cancellation"],
        df["is_negative_quantity"],
        df["is_zero_quantity"],
        df["is_zero_price"],
        (df["quantity"] > 0) & (df["price"] > 0)
    ]
    categories = [
        "BAD_DEBT_ADJUSTMENT",
        "CANCELLATION",
        "NEGATIVE_QUANTITY_NON_CANCELLATION",
        "ZERO_QUANTITY",
        "ZERO_PRICE",
        "SALE"
    ]
    df["transaction_type"] = np.select(
        conditions, categories, default="OTHER"
    )

    return df


def export_audits(df: pd.DataFrame, original_rows: int, duplicates_removed: int):
    missing_description_rows = df["description_was_missing"]
    missing_nonzero_value = int(
        (df.loc[missing_description_rows, "line_value"] != 0).sum()
    )

    audit_metrics = [
        ("Original rows", original_rows),
        ("Final cleaned rows", len(df)),
        ("Duplicate rows removed", duplicates_removed),
        ("Original missing descriptions", int(missing_description_rows.sum())),
        ("Descriptions imputed", int(df["description_was_imputed"].sum())),
        ("Missing descriptions after recovery", int(df["is_description_missing"].sum())),
        ("Missing descriptions with non-zero line value", missing_nonzero_value),
        ("Operational descriptions", int(df["is_operational_description"].sum())),
        ("Missing customer IDs", int(df["customer_id"].isna().sum())),
        ("Missing invoice dates", int(df["invoice_date"].isna().sum())),
        ("Missing invoice IDs", int(df["invoice"].isna().sum())),
        ("Cancellation transactions", int((df["transaction_type"] == "CANCELLATION").sum())),
        ("Bad debt adjustments", int((df["transaction_type"] == "BAD_DEBT_ADJUSTMENT").sum())),
        ("Negative quantity non-cancellations", int((df["transaction_type"] == "NEGATIVE_QUANTITY_NON_CANCELLATION").sum())),
        ("Zero-price transactions", int((df["transaction_type"] == "ZERO_PRICE").sum())),
        ("Sale transactions", int((df["transaction_type"] == "SALE").sum())),
        ("Final signed transaction value", round(df["line_value"].sum(), 2))
    ]

    pd.DataFrame(
        audit_metrics, columns=["metric", "value"]
    ).to_csv(AUDIT_DIR / "data_quality_audit.csv", index=False)

    df.groupby("transaction_type").agg(
        transaction_lines=("invoice", "size"),
        signed_transaction_value=("line_value", "sum")
    ).reset_index().to_csv(
        AUDIT_DIR / "transaction_classification_summary.csv", index=False
    )

    df.groupby("description_type").agg(
        transaction_lines=("invoice", "size"),
        imputed_descriptions=("description_was_imputed", "sum")
    ).reset_index().to_csv(
        AUDIT_DIR / "description_classification_summary.csv", index=False
    )

    if missing_nonzero_value != 0:
        raise AssertionError(
            "Missing descriptions with non-zero transaction value were found; "
            "review before accepting the cleaning output."
        )


def main():
    print("Loading Online Retail II...")
    df = load_workbook(INPUT_FILE)
    original_rows = len(df)

    print("Standardising fields...")
    df = validate_and_standardise(df)

    print("Removing exact duplicates...")
    df, duplicates_removed = remove_duplicates(df)

    print("Recovering unambiguous descriptions...")
    df = recover_descriptions(df)

    print("Classifying descriptions and transaction types...")
    df = classify_records(df)

    print("Validating and exporting audit files...")
    if len(df) + duplicates_removed != original_rows:
        raise AssertionError("Original and cleaned row counts do not reconcile.")

    if df.duplicated(
        subset=[c for c in df.columns if c not in ["source_sheet", "source_row_id"]]
    ).any():
        raise AssertionError("Exact duplicates remain after cleaning.")

    export_audits(df, original_rows, duplicates_removed)

    output_file = PROCESSED_DIR / "retail_transactions_clean.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("\nCLEANING COMPLETE")
    print(f"Original rows: {original_rows:,}")
    print(f"Duplicates removed: {duplicates_removed:,}")
    print(f"Final rows: {len(df):,}")
    print(f"Clean dataset: {output_file}")
    print(f"Audit outputs: {AUDIT_DIR}")


if __name__ == "__main__":
    main()
