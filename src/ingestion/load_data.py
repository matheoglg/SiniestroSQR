# src/ingestion/load_data.py
"""Utility to load synthetic CSVs produced by ``scripts/generate_synthetic.py``.

The function returns a pandas.DataFrame ready for further processing.
"""

import os
import pandas as pd

DATA_DIR = os.getenv("DATA_DIR", "data")
RAW_DIR = os.getenv("RAW_DATA_DIR", os.path.join(DATA_DIR, "raw"))


def load_siniestros(csv_name: str = "siniestros.csv") -> pd.DataFrame:
    """Load a CSV file from the ``raw`` data directory.

    Parameters
    ----------
    csv_name: str
        Name of the CSV file (default ``siniestros.csv``).
    """
    path = os.path.join(RAW_DIR, csv_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Synthetic data file not found: {path}")
    df = pd.read_csv(path, parse_dates=["fecha_ocurrencia", "fecha_reporte"], infer_datetime_format=True)
    return df
