# scripts/generate_synthetic.py
"""Generate synthetic insurance claim datasets.

- Uses Faker to create realistic tabular data.
- Calls Gemini 1.5 Flash to generate free-text claim narratives.
- Produces CSV files under data/raw/.
"""

import csv
import os
import os, json, time, math
from pathlib import Path
from datetime import datetime, timedelta
import random
from faker import Faker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

FAKE = Faker("es_ES")
FAKE.seed_instance(42)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def generate_narrative(siniestro_id: int) -> str:
    """Generate synthetic insurance claim narrative using Gemini."""

    prompt = f"""
    You are an insurance claims adjuster.

    Generate a short realistic insurance claim narrative for claim #{siniestro_id}.

    Requirements:
    - Maximum 80 words
    - Professional tone
    - Mention incident, vehicle/property, and parties involved
    - Completely fictional
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )

        if response.text:
            return response.text.strip()

        return "Descripción no disponible."

    except Exception as e:
        print(f"[ERROR] Gemini generation failed for claim {siniestro_id}: {e}")
        return "Descripción generada automáticamente no disponible."


# ---------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------


def generate_siniestros(num_records: int = 5000):
    """Create synthetic insurance claims dataset."""

    fieldnames = [
        "id_siniestro",
        "id_poliza",
        "id_asegurado",
        "ramo",
        "cobertura",
        "fecha_ocurrencia",
        "fecha_reporte",
        "monto_reclamado",
        "monto_estimado",
        "monto_pagado",
        "estado",
        "sucursal",
        "descripcion",
        "documentos_completos",
        "beneficiario",
        "dias_desde_inicio_poliza",
        "dias_desde_fin_poliza",
        "dias_entre_ocurrencia_reporte",
        "historial_siniestros_asegurado",
        "etiqueta_fraude_simulada",
    ]

    rows = []

    for i in range(1, num_records + 1):

        id_poliza = random.randint(1, num_records // 2)
        id_asegurado = random.randint(1, num_records // 3)

        ramo = random.choice([
            "Vehículos",
            "Salud",
            "Vida",
            "Generales",
            "Hogar",
        ])

        cobertura = random.choice([
            "Choque",
            "Robo",
            "Atención médica",
            "Incendio",
            "Daño material",
        ])

        # Policy dates
        policy_start = FAKE.date_between(
            start_date="-5y",
            end_date="-1y",
        )

        policy_end = policy_start + timedelta(
            days=random.randint(180, 720)
        )

        fecha_ocurrencia = FAKE.date_between(
            start_date=policy_start,
            end_date=policy_end,
        )

        fecha_reporte = fecha_ocurrencia + timedelta(
            days=random.randint(0, 30)
        )

        # Amounts
        monto_reclamado = round(random.uniform(500, 15000), 2)

        monto_estimado = round(
            monto_reclamado * random.uniform(0.6, 0.9),
            2,
        )

        monto_pagado = round(
            monto_estimado * random.choice([0, 0.5, 1.0]),
            2,
        )

        estado = random.choice([
            "Reserva",
            "Pago Total",
            "Pago Parcial",
            "Anticipo",
            "Negativa",
            "Cierre Sin Consecuencia",
            "Liquidado",
        ])

        sucursal = random.choice([
            "Quito",
            "Guayaquil",
            "Cuenca",
            "Santo Domingo",
        ])

        descripcion = generate_narrative(i)

        documentos_completos = random.choice(["Sí", "No"])

        beneficiario = random.choice([
            "Taller A",
            "Clínica B",
            "Perito C",
            "Otro",
        ])

        dias_desde_inicio_poliza = (
            fecha_ocurrencia - policy_start
        ).days

        dias_desde_fin_poliza = (
            policy_end - fecha_ocurrencia
        ).days

        dias_entre_ocurrencia_reporte = (
            fecha_reporte - fecha_ocurrencia
        ).days

        historial = random.randint(0, 5)

        fraude = random.choice([0, 1])

        row = {
            "id_siniestro": i,
            "id_poliza": id_poliza,
            "id_asegurado": id_asegurado,
            "ramo": ramo,
            "cobertura": cobertura,
            "fecha_ocurrencia": fecha_ocurrencia.isoformat(),
            "fecha_reporte": fecha_reporte.isoformat(),
            "monto_reclamado": monto_reclamado,
            "monto_estimado": monto_estimado,
            "monto_pagado": monto_pagado,
            "estado": estado,
            "sucursal": sucursal,
            "descripcion": descripcion,
            "documentos_completos": documentos_completos,
            "beneficiario": beneficiario,
            "dias_desde_inicio_poliza": dias_desde_inicio_poliza,
            "dias_desde_fin_poliza": dias_desde_fin_poliza,
            "dias_entre_ocurrencia_reporte": dias_entre_ocurrencia_reporte,
            "historial_siniestros_asegurado": historial,
            "etiqueta_fraude_simulada": fraude,
        }

        rows.append(row)

        if i % 50 == 0:
            print(f"Generated {i}/{num_records} claims...")

    # Save CSV
    out_path = DATA_RAW / "siniestros.csv"

    with out_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nGenerated {len(rows)} records")
    print(f"Saved to: {out_path}")


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    generate_siniestros(num_records=2000)