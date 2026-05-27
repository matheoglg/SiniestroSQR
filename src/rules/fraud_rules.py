# src/rules/fraud_rules.py
"""Reglas de negocio para detección de fraude.

- Hard rules (RF‑01 … RF‑07) disparan una clasificación *roja* o *amarilla*
  inmediatamente.
- Soft rules asignan puntaje (0‑40) según la tabla del PDF.

Se asume que cada registro es un ``pandas.Series`` con los nombres de columna
exactamente como aparecen en el CSV generado por ``scripts/generate_synthetic.py``.
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Hard rules (return flag and immediate semáforo)
# ---------------------------------------------------------------------------

def hard_rule_rf01(record) -> Tuple[bool, str]:
    """Cobertura Pérdida Total por Robo → Rojo"""
    return record["cobertura"].lower() == "robo" and record["cobertura"].lower() == "pérdida total", "rojo"

def hard_rule_rf02(record) -> Tuple[bool, str]:
    """Evidencia de falsificación documental → Rojo"""
    # En datos sintéticos usamos la columna documentos_completos (bool)
    # Si es False se considera posible falsificación.
    return not record["documentos_completos"], "rojo"

def hard_rule_rf03(record) -> Tuple[bool, str]:
    """Asegurado/Beneficiario en lista restrictiva → Rojo"""
    # Lista restrictiva ficticia
    restrictiva = {"Taller XYZ", "Clínica ABC"}
    return record["beneficiario"] in restrictiva, "rojo"

def hard_rule_rf04(record) -> Tuple[bool, str]:
    """Dinámica de accidente físicamente imposible → Rojo"""
    # Simulación simple: si la descripción contiene palabras clave de imposibilidad
    impossible_keywords = ["volcadura", "desplome", "levitación"]
    desc = str(record["descripcion"]).lower()
    return any(kw in desc for kw in impossible_keywords), "rojo"

def hard_rule_rf05(record) -> Tuple[bool, str]:
    """Siniestro al borde de la vigencia (<48 h) → Amarillo"""
    days_to_expiry = record["dias_desde_fin_poliza"]
    return days_to_expiry >= 0 and days_to_expiry <= 2, "amarillo"

def hard_rule_rf06(record) -> Tuple[bool, str]:
    """Demora atípica en denuncia de robo (>4 días) → Amarillo"""
    # Aplicable solo a cobertura robo
    if record["cobertura"].lower() != "robo":
        return False, ""
    return record["dias_entre_ocurrencia_reporte"] > 4, "amarillo"

def hard_rule_rf07(record) -> Tuple[bool, str]:
    """Narrativa idéntica (clonada) → Amarillo"""
    # Este cheque se hará a nivel global comparando embeddings, aquí devolvemos False.
    return False, ""

# ---------------------------------------------------------------------------
# Soft rules – tabla de puntaje (0‑40)
# ---------------------------------------------------------------------------
SOFT_RULES = [
    # (column, condition lambda, points)
    ("dias_entre_ocurrencia_reporte", lambda x: x <= 3, 0),
    ("dias_entre_ocurrencia_reporte", lambda x: 4 <= x <= 7, 3),
    ("dias_entre_ocurrencia_reporte", lambda x: x > 7, 5),
    ("dias_desde_fin_poliza", lambda x: x <= 10, 8),
    ("dias_desde_fin_poliza", lambda x: 11 <= x <= 30, 4),
    ("dias_desde_fin_poliza", lambda x: x > 30, 0),
    # Se pueden agregar más reglas según el PDF.
]

def compute_soft_score(record) -> int:
    """Suma los puntos de las reglas blandas que se cumplen."""
    total = 0
    for col, condition, points in SOFT_RULES:
        try:
            if condition(record[col]):
                total += points
        except Exception:
            continue
    return total

# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------
def evaluate_record(record) -> Dict:
    """Evalúa un registro y devuelve:
    {
        "hard_flag": bool,
        "hard_color": "rojo"|"amarillo"|"",
        "soft_score": int,
        "final_color": "rojo"|"amarillo"|"verde"
    }
    """
    # Check hard rules in order
    for fn in [hard_rule_rf01, hard_rule_rf02, hard_rule_rf03, hard_rule_rf04, hard_rule_rf05, hard_rule_rf06, hard_rule_rf07]:
        flag, color = fn(record)
        if flag:
            return {
                "hard_flag": True,
                "hard_color": color,
                "soft_score": 0,
                "final_color": color,
            }
    # No hard rule triggered – compute soft score
    soft = compute_soft_score(record)
    # Map total to semáforo
    if soft <= 10:
        final = "verde"
    elif soft <= 30:
        final = "amarillo"
    else:
        final = "rojo"
    return {
        "hard_flag": False,
        "hard_color": "",
        "soft_score": soft,
        "final_color": final,
    }
