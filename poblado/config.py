from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "seed": 20260624,
    "locale": "es_AR",
    "output_sql": "sql/02_populado_datos.sql",
    "output_validations_sql": "sql/03_validaciones_populado.sql",
    "chunk_size": 800,
    "truncate_before_insert": True,
    "counts": {
        "obra_social": 16,
        "consultorio": 42,
        "medico": 160,
        "paciente": 5000,
        "turno": 10000,
        "medicamento": 120,
        "efecto_secundario": 45,
        "estudio": 2500,
        "operacion": 900,
    },
    "turno": {
        "duration_minutes": 30,
        "work_start_hour": 8,
        "work_end_hour": 18,
        "past_days": 1095,
        "future_days": 180,
        "estado_weights": {"realizado": 0.65, "programado": 0.20, "cancelado": 0.15},
        "costo_min": 5000,
        "costo_max": 75000,
        "max_schedule_attempts": 300000,
    },
    "distributions": {
        "genero": {"hombre": 0.49, "mujer": 0.51},
        "grupo_sanguineo": {
            "O+": 0.36,
            "A+": 0.31,
            "B+": 0.10,
            "AB+": 0.04,
            "O-": 0.07,
            "A-": 0.07,
            "B-": 0.03,
            "AB-": 0.02,
        },
        "ala": {"este": 0.34, "centro": 0.32, "oeste": 0.34},
        "complejidad": {"baja": 0.50, "media": 0.35, "alta": 0.15},
        "gravedad": {"baja": 0.55, "media": 0.32, "alta": 0.13},
    },
}


# Fecha lógica por defecto para que el dataset sea estable aunque se ejecute otro día.
DEFAULT_CONFIG["reference_date"] = "2026-06-24"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Combina dos diccionarios recursivamente sin modificar el original."""
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path | None) -> dict[str, Any]:
    """Carga configuración desde JSON y la mezcla con DEFAULT_CONFIG."""
    if path is None:
        return deepcopy(DEFAULT_CONFIG)

    with path.open("r", encoding="utf-8") as f:
        override = json.load(f)

    return deep_merge(DEFAULT_CONFIG, override)


def resolve_reference_date(cfg: dict[str, Any], cli_reference_date: str | None = None) -> date:
    """
    Resuelve la fecha lógica usada para generar datos.

    Prioridad:
      1. --reference-date / --today
      2. config["reference_date"]
      3. date.today()
    """
    reference_date_str = cli_reference_date or cfg.get("reference_date")

    if reference_date_str:
        reference_date = date.fromisoformat(reference_date_str)
    else:
        reference_date = date.today()

    cfg["reference_date"] = reference_date.isoformat()
    return reference_date
