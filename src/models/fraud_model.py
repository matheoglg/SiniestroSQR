import os
import joblib
import pandas as pd
from pathlib import Path

from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

# Paths (adjust if needed)
RAW_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
MODEL_DIR = Path(__file__).resolve().parents[3] / "models"

def load_data() -> pd.DataFrame:
    """Load the processed dataset used for training.
    Expected file: `processed/siniestros_processed.csv`.
    """
    csv_path = PROCESSED_DATA_DIR / "siniestros_processed.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Processed data not found at {csv_path}")
    return pd.read_csv(csv_path)

def train_isolation_forest(df: pd.DataFrame, contamination: float = 0.05):
    """Train an IsolationForest on the numeric features.
    Returns the fitted model and the anomaly scores.
    """
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    X = df[numeric_cols]
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(X)
    scores = -model.decision_function(X)  # higher = more anomalous
    return model, scores

def train_xgboost(df: pd.DataFrame, target: str = "etiqueta_fraude_simulada"):
    """Train an XGBoost classifier for the binary fraud label.
    Returns the fitted model.
    """
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in data")
    X = df.drop(columns=[target])
    y = df[target]
    # Simple preprocessing: fill NaNs with median for numeric columns
    X = X.fillna(X.median())
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)
    return model

def save_model(model, model_name: str):
    """Persist a trained model using joblib.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / f"{model_name}.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

def main():
    df = load_data()
    # Train Isolation Forest
    iso_model, iso_scores = train_isolation_forest(df)
    save_model(iso_model, "isolation_forest")
    # Train XGBoost
    xgb_model = train_xgboost(df)
    save_model(xgb_model, "xgboost_fraud")
    # Optionally, store anomaly scores for later use
    scores_path = PROCESSED_DATA_DIR / "iso_scores.csv"
    pd.DataFrame({"id_siniestro": df["id_siniestro"], "anomaly_score": iso_scores}).to_csv(scores_path, index=False)
    print(f"Anomaly scores saved to {scores_path}")

if __name__ == "__main__":
    main()
