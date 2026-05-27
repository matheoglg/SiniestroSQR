# src/sql/load_csv_to_sqlite.py
"""Utility to load CSV files into a SQLite database.

Usage (from repository root)::

    python -m src.sql.load_csv_to_sqlite \
        --csv data/raw/siniestros.csv data/raw/polizas.csv \
        --db fraudia.db

The script will:
1️⃣ Create (or replace) the SQLite file.
2️⃣ Load each CSV as a table whose name is derived from the filename (without extension).
3️⃣ Infer dtypes via pandas and store them as appropriate SQLite types.
4️⃣ Create basic indexes on primary‑key‑like columns for faster joins.

This provides a quick way to run SQL queries (see ``sql/queries.sql``) against the
synthetic data generated for the HackIAthon challenge.
"""

import argparse
import pathlib
import sqlite3
import pandas as pd

def load_csv_to_sqlite(csv_paths: list[pathlib.Path], db_path: pathlib.Path):
    """Load each CSV into ``db_path``.

    Parameters
    ----------
    csv_paths: list[Path]
        Paths to CSV files.
    db_path: Path
        Destination SQLite file (will be overwritten if it exists).
    """
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        for csv_path in csv_paths:
            table_name = csv_path.stem  # filename without extension
            print(f"⏳ Loading {csv_path} → table '{table_name}'")
            df = pd.read_csv(csv_path)
            # Let pandas infer types; ``to_sql`` will map them to SQLite types.
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            # Create a simple index if a column looks like an identifier.
            possible_id_cols = [c for c in df.columns if c.lower().endswith("id")]
            for col in possible_id_cols:
                idx_name = f"idx_{table_name}_{col}"
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col});")
        conn.commit()
        print(f"✅ Database written to {db_path}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Load CSVs into SQLite")
    parser.add_argument(
        "--csv",
        nargs="+",
        type=pathlib.Path,
        required=True,
        help="One or more CSV files to import",
    )
    parser.add_argument(
        "--db",
        type=pathlib.Path,
        default=pathlib.Path("fraudia.db"),
        help="SQLite database file (will be overwritten)",
    )
    args = parser.parse_args()
    load_csv_to_sqlite(args.csv, args.db)

if __name__ == "__main__":
    main()
