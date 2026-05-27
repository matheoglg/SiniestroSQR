# src/explainability/explain_score.py
"""Explainability utilities for the fraud detector.

- `combine_scores` merges rule‑based points and the ML model risk score.
- `generate_explanation` calls Gemini (flash) to produce a concise, human‑readable
  explanation of why a claim received a particular colour (green/yellow/red).

The function is deliberately lightweight – it receives a dictionary with the
relevant fields, builds a prompt, and returns the LLM response.
"""
import os
from typing import Dict, Any
from google.generativeai import GenerativeModel

# Initialise Gemini model (Flash) – gemini‑1.5‑flash‑001 is the default.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")
model = GenerativeModel(MODEL_NAME)


def combine_scores(rule_score: int, ml_score: float) -> int:
    """Combine rule‑based points (0‑40) with ML anomaly score (0‑60).
    The final risk score ranges 0‑100.
    """
    # Normalise the ML score to 0‑60 (assuming IsolationForest/XGBoost output 0‑1)
    ml_norm = int(ml_score * 60)
    total = min(rule_score + ml_norm, 100)
    return total


def _build_prompt(claim: Dict[str, Any], rule_score: int, ml_score: float, total_score: int) -> str:
    """Compose a prompt for Gemini that explains the reasoning.
    The prompt includes:
    * key fields of the claim (date, amount, provider, etc.)
    * which hard/soft rules fired (passed in the claim dict under `triggered_rules`)
    * the ML model confidence (probability of fraud)
    """
    triggered = ", ".join(claim.get("triggered_rules", [])) or "none"
    return (
        f"Explain why this insurance claim received a risk score of {total_score}/100.\n"
        f"Claim details: id={claim.get('id_siniestro')}, policy={claim.get('id_poliza')}, amount={claim.get('monto_reclamado')}, date={claim.get('fecha_ocurrencia')}.\n"
        f"Rule‑based points: {rule_score} (triggered: {triggered}).\n"
        f"Machine‑learning anomaly probability: {ml_score:.2%}.\n"
        "Provide a short bullet‑point summary and a concise natural‑language explanation."
    )


def generate_explanation(claim: Dict[str, Any], rule_score: int, ml_score: float) -> str:
    """Return a Gemini‑generated explanation for a claim.

    Parameters
    ----------
    claim: dict
        Dictionary with claim fields and a ``triggered_rules`` list.
    rule_score: int
        Points from the rule engine (0‑40).
    ml_score: float
        Anomaly probability from the ML model (0‑1).
    """
    total = combine_scores(rule_score, ml_score)
    prompt = _build_prompt(claim, rule_score, ml_score, total)
    response = model.generate_content(prompt)
    return response.text

__all__ = ["combine_scores", "generate_explanation"]
