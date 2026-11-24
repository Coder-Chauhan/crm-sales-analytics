"""
Load the CRM CSVs into a SQLite database and run every analysis query in sql/.
Each query's result is printed and saved to outputs/<query_name>.csv.

Usage:  python scripts/run_analysis.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, SQL, OUT = ROOT / "data", ROOT / "sql", ROOT / "outputs"
DB = ROOT / "crm.db"
TABLES = ["users", "accounts", "leads", "opportunities", "opportunity_history", "activities"]


def build_db() -> sqlite3.Connection:
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript((SQL / "00_schema.sql").read_text())
    for t in TABLES:
        # keep_default_na=False so text like "NA" is never read as missing; only empty cells are NULL
        df = pd.read_csv(DATA / f"{t}.csv", keep_default_na=False, na_values=[""])
        df.to_sql(t, con, if_exists="append", index=False)
        print(f"loaded {t:<20} {len(df):>6} rows")
    return con


def run_queries(con: sqlite3.Connection) -> None:
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 160, "display.max_columns", 20)
    for f in sorted(SQL.glob("[0-9][0-9]_*.sql")):
        if f.name.startswith("00_"):
            continue
        df = pd.read_sql_query(f.read_text(), con)
        df.to_csv(OUT / f"{f.stem}.csv", index=False)
        print(f"\n=== {f.stem} ({len(df)} rows) ===")
        print(df.head(12).to_string(index=False))


if __name__ == "__main__":
    connection = build_db()
    run_queries(connection)
    connection.close()
