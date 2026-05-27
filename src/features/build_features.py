# src/features/build_features.py
"""Feature engineering for the fraud detection prototype.

* Derives temporal and relational features from the raw synthetic CSV.
* Generates sentence embeddings for the claim ``descripcion`` column using
  ``sentence-transformers``.
* Returns a ``pandas.DataFrame`` ready for model training.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer

# Paths (can be overridden via env vars)
DATA_DIR = os.getenv("DATA_DIR", "data")
RAW_DIR = os.getenv("RAW_DATA_DIR", os.path.join(DATA_DIR, "raw"))
PROC_DIR = os.getenv("PROCESSED_DATA_DIR", os.path.join(DATA_DIR, "processed"))

# Ensure processed folder exists
Path(PROC_DIR).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper: temporal features
# ---------------------------------------------------------------------------
def _temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Ensure dates are datetime objects
    df["fecha_ocurrencia"] = pd.to_datetime(df["fecha_ocurrencia"], errors="coerce")
    df["fecha_reporte"] = pd.to_datetime(df["fecha_reporte"], errors="coerce")
    # Days between occurrence and report
    df["dias_entre_ocurrencia_reporte"] = (
        df["fecha_reporte"] - df["fecha_ocurrencia"]).dt.days
    # Age of policy at the time of claim (already present, but keep for safety)
    df["dias_desde_inicio_poliza"] = pd.to_numeric(df["dias_desde_inicio_poliza"], errors="coerce")
    df["dias_desde_fin_poliza"] = pd.to_numeric(df["dias_desde_fin_poliza"], errors="coerce")
    return df

# ---------------------------------------------------------------------------
# Helper: numeric feature scaling / simple aggregates
# ---------------------------------------------------------------------------
def _numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Ratio of claimed amount to estimated amount (avoid division by zero)
    df["ratio_monto"] = df["monto_reclamado"] / df["monto_estimado"].replace(0, np.nan)
    df["ratio_monto"] = df["ratio_monto"].fillna(0)
    # Frequency of claims for the same insured (historical count)
    df["freq_asegurado"] = df.groupby("id_asegurado")["id_siniestro"].transform("count")
    # Frequency of claims for same provider (beneficiario)
    df["freq_beneficiario"] = df.groupby("beneficiario")["id_siniestro"].transform("count")
    return df

# ---------------------------------------------------------------------------
# Helper: text embeddings for the free‑text description
# ---------------------------------------------------------------------------
def _embedding_features(df: pd.DataFrame, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> pd.DataFrame:
    df = df.copy()
    model = SentenceTransformer(model_name)
    # Compute embeddings – we store them as a list of floats (could be persisted as .npy)
    embeddings = model.encode(df["descripcion"].astype(str).tolist(), show_progress_bar=False)
    # Expand to separate columns (e.g., embed_0 … embed_383 for MiniLM-L6-v2 which has 384 dims)
    embed_dim = embeddings.shape[1]
    embed_cols = [f"embed_{i}" for i in range(embed_dim)]
    embed_df = pd.DataFrame(embeddings, columns=embed_cols)
    df = pd.concat([df.reset_index(drop=True), embed_df], axis=1)
    return df

# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def build_features(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Run the full feature engineering pipeline.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw data (as returned by ``src.ingestion.load_data.load_siniestros``).
    save : bool, default True
        If True, the processed dataframe is written to ``data/processed`` as
        ``features.csv``.
    """
    # 1️⃣ Temporal features
    df = _temporal_features(df)
    # 2️⃣ Numeric / aggregate features
    df = _numeric_features(df)
    # 3️⃣ Text embeddings (NLP)
    df = _embedding_features(df)

    if save:
        out_path = Path(PROC_DIR) / "features.csv"
        df.to_csv(out_path, index=False)
        print(f"Features saved to {out_path}")
    return df

# ---------------------------------------------------------------------------
# If executed as a script (useful for quick local testing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from src.ingestion.load_data import load_siniestros
    raw_df = load_siniestros()
    build_features(raw_df)
