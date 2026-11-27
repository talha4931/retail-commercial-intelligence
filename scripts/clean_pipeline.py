# -*- coding: utf-8 -*-
"""
Retail Commercial Intelligence
Clean and audit the UCI Online Retail II workbook.

Expected input:
    data/raw/online_retail_II.xlsx

Outputs:
    data/processed/retail_transactions_clean.csv
    data/processed/audit/*.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# This file lives in <project_root>/scripts/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AUDIT_DIR = PROCESSED_DIR / "audit"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

OLDER_SHEET = "Year 2009-2010"
NEWER_SHEET = "Year 2010-2011"


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input workbook not found: {INPUT_FILE}\n"
            "Download Online Retail II from the UCI repository and place "
            "online_retail_II.xlsx in data/raw/."
        )

    print("=" * 64)
    print("RETAIL COMMERCIAL INTELLIGENCE — CLEANING PIPELINE")
    print("=" * 64)
    print(f"Input: {INPUT_FILE}")

    # ========================================================
    # 2. LOAD AND STANDARDISE DATA
    # ========================================================

    print("\nLoading workbook...")
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)

    frames = []
    for sheet_name, sheet_data in sheets.items():
        sheet_data = sheet_data.copy()
        sheet_data["source_sheet"] = sheet_name
        frames.append(sheet_data)

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "source_row_id", range(1, len(df) + 1))

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    df = df.rename(columns={
        "invoiceno": "invoice",
        "invoicedate": "invoice_date",
        "customerid": "customer_id",
        "stockcode": "stock_code",
        "unitprice": "price",
    })

    required_columns = [
        "invoice", "stock_code", "description", "quantity",
        "invoice_date", "price", "customer_id", "country",
        "source_sheet",
    ]
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    original_row_count = len(df)

    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = (
        df["description"].astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["invoice_date"] = pd.to_datetime(
        df["invoice_date"], errors="coerce"
    )
    df["customer_id"] = pd.to_numeric(
        df["customer_id"], errors="coerce"
    ).astype("Int64")

    # ========================================================
    # 3. IDENTIFY AND REMOVE EXACT DUPLICATES
    # ========================================================

    print("Identifying exact duplicate transaction rows...")
    transaction_fields = [
        c for c in df.columns
        if c not in ["source_sheet", "source_row_id"]
    ]

    df["_duplicate_group"] = (
        df.groupby(
            transaction_fields,
            dropna=False,
            sort=False
        ).ngroup()
    )
    group_sizes = df.groupby("_duplicate_group").size()
    group_sheet_counts = (
        df.groupby("_duplicate_group")["source_sheet"].nunique()
    )

    df["_group_size"] = df["_duplicate_group"].map(group_sizes)
    df["_worksheet_count"] = (
        df["_duplicate_group"].map(group_sheet_counts)
    )
    df["_retention_priority"] = (
        df["source_sheet"].eq(NEWER_SHEET).astype(int)
    )

    # Where identical records overlap across worksheets, retain the
    # newer worksheet's copy. Otherwise retain the earliest source row.
    df = df.sort_values(
        ["_duplicate_group", "_retention_priority", "source_row_id"],
        ascending=[True, False, True],
    )

    duplicate_audit = df[
        df.duplicated(subset=transaction_fields, keep="first")
    ].copy()

    duplicate_audit["removal_reason"] = np.where(
        duplicate_audit["_worksheet_count"] > 1,
        "Cross-worksheet duplicate",
        "Within-worksheet duplicate",
    )

    retained_rows = df.drop_duplicates(
        subset=transaction_fields,
        keep="first",
    )
    retained_sheet_map = (
        retained_rows.set_index("_duplicate_group")["source_sheet"]
    )
    duplicate_audit["retained_source_sheet"] = (
        duplicate_audit["_duplicate_group"].map(retained_sheet_map)
    )

    duplicate_rows_removed = len(duplicate_audit)

    duplicate_audit.drop(
        columns=[
            "_duplicate_group", "_group_size",
            "_worksheet_count", "_retention_priority",
        ],
        errors="ignore",
    ).to_csv(AUDIT_DIR / "duplicate_audit.csv", index=False)

    df = retained_rows.drop(
        columns=[
            "_duplicate_group", "_group_size",
            "_worksheet_count", "_retention_priority",
        ],
        errors="ignore",
    ).copy()

    # ========================================================
    # 4. CALCULATE TRANSACTION VALUE
    # ========================================================

    df["line_value"] = df["quantity"] * df["price"]

    # ========================================================
    # 5. RECOVER ONLY UNAMBIGUOUS MISSING DESCRIPTIONS
    # ========================================================

    print("Recovering unambiguous missing descriptions...")
    description_candidates = (
        df.dropna(subset=["description"])
        .groupby("stock_code")["description"]
        .agg(lambda values: sorted(set(values)))
    )

    unique_description_map = {
        stock_code: candidates[0]
        for stock_code, candidates in description_candidates.items()
        if len(candidates) == 1
    }

    missing_description_rows = df[df["description"].isna()].copy()
    candidate_counts = description_candidates.apply(len)

    missing_description_rows["candidate_count"] = (
        missing_description_rows["stock_code"]
        .map(candidate_counts)
        .fillna(0)
        .astype(int)
    )
    missing_description_rows["recovered_description"] = (
        missing_description_rows["stock_code"].map(unique_description_map)
    )
    missing_description_rows["recovery_status"] = np.select(
        [
            missing_description_rows["candidate_count"].eq(1),
            missing_description_rows["candidate_count"].gt(1),
        ],
        [
            "Recovered: unique candidate",
            "Not recovered: multiple candidates",
        ],
        default="Not recovered: no candidate",
    )
    missing_description_rows.to_csv(
        AUDIT_DIR / "description_recovery_audit.csv",
        index=False,
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

    # ========================================================
    # 6. CLASSIFY DESCRIPTION QUALITY
    # ========================================================

    operational_patterns = (
        r"wrong|wrongly|barcode|wrong code|"
        r"wrongly coded|wrongly marked|wrongly sold"
    )

    df["is_operational_description"] = (
        df["description"].str.contains(
            operational_patterns,
            case=False,
            na=False,
            regex=True,
        )
    )

    df["description_type"] = np.select(
        [
            df["is_description_missing"],
            df["is_operational_description"],
        ],
        ["MISSING", "OPERATIONAL_NOTE"],
        default="PRODUCT_DESCRIPTION",
    )

    description_summary = (
        df.groupby("description_type")
        .agg(
            transaction_lines=("invoice", "size"),
            imputed_descriptions=("description_was_imputed", "sum"),
        )
        .reset_index()
    )
    description_summary.to_csv(
        AUDIT_DIR / "description_classification_summary.csv",
        index=False,
    )

    # ========================================================
    # 7. CLASSIFY TRANSACTIONS
    # ========================================================

    print("Classifying transaction lines...")
    df["is_cancellation"] = df["invoice"].str.startswith(
        "C", na=False
    )
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
        (df["quantity"] > 0) & (df["price"] > 0),
    ]
    categories = [
        "BAD_DEBT_ADJUSTMENT",
        "CANCELLATION",
        "NEGATIVE_QUANTITY_NON_CANCELLATION",
        "ZERO_QUANTITY",
        "ZERO_PRICE",
        "SALE",
    ]
    df["transaction_type"] = np.select(
        conditions, categories, default="OTHER"
    )

    # ========================================================
    # 8. DATA QUALITY AUDIT
    # ========================================================

    original_missing_description_count = len(missing_description_rows)
    missing_description_nonzero_value = int(
        (missing_description_rows["line_value"] != 0).sum()
    )
    imputed_description_count = int(df["description_was_imputed"].sum())

    audit_metrics = [
        ("Original rows", original_row_count),
        ("Final cleaned rows", len(df)),
        ("Duplicate rows removed", duplicate_rows_removed),
        ("Original missing descriptions", original_missing_description_count),
        (
            "Original missing descriptions with non-zero value",
            missing_description_nonzero_value,
        ),
        ("Descriptions imputed", imputed_description_count),
        ("Missing descriptions after recovery", int(df["is_description_missing"].sum())),
        ("Operational descriptions", int(df["is_operational_description"].sum())),
        ("Missing customer IDs", int(df["customer_id"].isna().sum())),
        ("Missing invoice dates", int(df["invoice_date"].isna().sum())),
        ("Missing invoice IDs", int(df["invoice"].isna().sum())),
        ("Cancellation transactions", int((df["transaction_type"] == "CANCELLATION").sum())),
        ("Bad debt adjustments", int((df["transaction_type"] == "BAD_DEBT_ADJUSTMENT").sum())),
        (
            "Negative quantity non-cancellations",
            int((df["transaction_type"] == "NEGATIVE_QUANTITY_NON_CANCELLATION").sum()),
        ),
        ("Zero quantity transactions", int((df["transaction_type"] == "ZERO_QUANTITY").sum())),
        ("Zero-price transactions", int((df["transaction_type"] == "ZERO_PRICE").sum())),
        ("Sale transactions", int((df["transaction_type"] == "SALE").sum())),
        ("Final signed transaction value", round(df["line_value"].sum(), 2)),
    ]

    quality_audit = pd.DataFrame(
        audit_metrics, columns=["metric", "value"]
    )
    quality_audit.to_csv(
        AUDIT_DIR / "data_quality_audit.csv", index=False
    )

    transaction_summary = (
        df.groupby("transaction_type")
        .agg(
            transaction_lines=("invoice", "size"),
            signed_transaction_value=("line_value", "sum"),
        )
        .reset_index()
    )
    transaction_summary.to_csv(
        AUDIT_DIR / "transaction_classification_summary.csv",
        index=False,
    )

    # ========================================================
    # 9. ASSERTIONS AND EXPORT
    # ========================================================

    assert len(df) + duplicate_rows_removed == original_row_count
    assert not df.duplicated(subset=transaction_fields).any()
    assert df["invoice_date"].notna().all()
    assert df["invoice"].notna().all()
    assert missing_description_nonzero_value == 0

    output_file = PROCESSED_DIR / "retail_transactions_clean.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("\nCLEANING COMPLETE")
    print(f"Original rows: {original_row_count:,}")
    print(f"Duplicate rows removed: {duplicate_rows_removed:,}")
    print(f"Final cleaned rows: {len(df):,}")
    print(f"Descriptions imputed: {imputed_description_count:,}")
    print(f"Descriptions still missing: {int(df['is_description_missing'].sum()):,}")
    print(f"Clean dataset: {output_file}")
    print(f"Audit outputs: {AUDIT_DIR}")


if __name__ == "__main__":
    main()
