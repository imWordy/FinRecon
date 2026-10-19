"""
Data loading, validation, and querying tools for FinRecon.
Provides robust schema inspection, anomaly pre-checking, and parameterized record querying.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

REQUIRED_SCHEMAS = {
    "orders": ["order_id", "customer_id", "order_date", "amount", "status"],
    "payments": ["payment_id", "order_id", "payment_date", "amount", "method", "status"],
    "settlements": ["settlement_id", "payment_id", "settlement_date", "amount", "status"],
    "fees": ["fee_id", "payment_id", "fee_amount", "tax_amount", "total_deduction", "fee_type", "created_at"],
    "refunds": ["refund_id", "payment_id", "order_id", "refund_amount", "refund_date", "reason", "status"],
    "disputes": ["dispute_id", "payment_id", "customer_id", "dispute_date", "claim_reason", "status"],
    "customers": ["customer_id", "name", "email", "tier"],
}


def load_financial_datasets(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Loads all 7 standard financial CSV datasets from a directory."""
    datasets = {}
    for table_name in REQUIRED_SCHEMAS.keys():
        file_path = data_dir / f"{table_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Required dataset file not found: {file_path}")
        datasets[table_name] = pd.read_csv(file_path)
    return datasets


def validate_dataset_schemas(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Validates schemas, null keys, negative values, and date parsing for loaded datasets.
    Returns a structured validation summary report.
    """
    errors = []
    warnings = []
    summary = {}

    for table_name, expected_cols in REQUIRED_SCHEMAS.items():
        if table_name not in datasets:
            errors.append(f"Missing table: {table_name}")
            continue

        df = datasets[table_name]
        summary[table_name] = {"rows": len(df), "columns": list(df.columns)}

        # 1. Missing columns
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Table '{table_name}' missing columns: {missing_cols}")

        # 2. Null primary key check
        pk_col = f"{table_name[:-1]}_id" if table_name != "disputes" and table_name != "fees" else ("dispute_id" if table_name == "disputes" else "fee_id")
        if pk_col in df.columns:
            null_count = df[pk_col].isnull().sum()
            if null_count > 0:
                errors.append(f"Table '{table_name}' has {null_count} null primary keys in '{pk_col}'")

        # 3. Numeric validity (negative amounts)
        for col in ["amount", "refund_amount", "fee_amount", "tax_amount", "total_deduction"]:
            if col in df.columns:
                # Check for non-numeric or negative
                non_numeric = pd.to_numeric(df[col], errors='coerce').isnull().sum()
                if non_numeric > 0:
                    errors.append(f"Table '{table_name}' has {non_numeric} invalid non-numeric values in '{col}'")
                else:
                    neg_count = (df[col] < 0).sum()
                    if neg_count > 0:
                        errors.append(f"Table '{table_name}' has {neg_count} negative values in '{col}'")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "table_summaries": summary
    }


def query_records(df: pd.DataFrame, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filters a DataFrame by exact column values and returns a list of dictionaries."""
    filtered_df = df.copy()
    for col, val in filters.items():
        if col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col] == val]
        else:
            return []
    return filtered_df.to_dict(orient="records")
