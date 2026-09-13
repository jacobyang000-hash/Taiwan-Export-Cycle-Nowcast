"""Load MOEA export orders from a manually downloaded Excel file."""

import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def month_name_to_date(year, month_label):
    """Convert year 2001 + 'Jan' -> Timestamp for 2001-01-01."""
    month = MONTH_MAP[str(month_label).strip()]
    return pd.Timestamp(year=int(year), month=month, day=1)


def load_export_orders():
    df = pd.read_excel(RAW / "MOEA_Export_Orders_Raw.xlsx", skiprows=1, header=None)

    # Keep only the first 3 columns — the 4th is blank junk in this file
    df = df.iloc[:, :3]
    df.columns = ["year_raw", "month_raw", "orders_total"]

    # The "blank" year cells are the literal string " ", not NaN.
    # Replace that with real NaN first, so ffill() has something to fill.
    df["year_raw"] = df["year_raw"].replace(r"^\s*$", pd.NA, regex=True)
    df["year_raw"] = df["year_raw"].ffill()

    # Drop the junk footer row — tabs instead of a real month label
    df["month_raw"] = df["month_raw"].astype(str).str.strip()
    df = df[df["month_raw"].isin(MONTH_MAP.keys())]

    df["date"] = df.apply(
        lambda row: month_name_to_date(row["year_raw"], row["month_raw"]), axis=1
    )

    df["orders_total"] = pd.to_numeric(df["orders_total"], errors="coerce")

    tidy = df[["date", "orders_total"]].dropna(subset=["orders_total"])
    tidy = tidy.melt(id_vars="date", var_name="series_id", value_name="value")
    return tidy.sort_values(["series_id", "date"])


if __name__ == "__main__":
    out = load_export_orders()
    print(out.head())
    print(out.tail())
    print(out.shape)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PROCESSED / "moea_eo.parquet", index=False)
    print("saved")