#!/usr/bin/env python3
"""
Entry point para generar:
  - sql/02_populado_datos.sql
  - sql/03_validaciones_populado.sql

La lógica está en poblado/.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from faker import Faker
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Falta instalar Faker. Ejecutar: pip install -r requirements.txt") from exc

from poblado.config import load_config, resolve_reference_date
from poblado.generator import generate_operaciones, generate_personas_medicos_pacientes
from poblado.scheduler import generate_turnos
from poblado.sql_writer import write_population_sql
from poblado.utils import ensure_dirs
from poblado.validation_writer import write_validations_sql


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera script SQL de poblado para el TP de IBD.")
    parser.add_argument("--config", type=Path, default=None, help="Ruta a config JSON. Default: configuracion interna.")
    parser.add_argument(
        "--reference-date",
        "--today",
        dest="reference_date",
        type=str,
        default=None,
        help="Fecha logica base YYYY-MM-DD. Prioridad: CLI > config.reference_date > fecha actual.",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    reference_date = resolve_reference_date(cfg, args.reference_date)

    seed = int(cfg["seed"])
    random.seed(seed)

    fake = Faker(cfg.get("locale", "es_AR"))
    Faker.seed(seed)

    output_sql = Path(cfg["output_sql"])
    output_validations = Path(cfg["output_validations_sql"])
    ensure_dirs(output_sql, output_validations)

    print(f"Fecha logica de referencia: {reference_date.isoformat()}")

    print("Generando personas, medicos y pacientes...")
    personas, medicos, pacientes = generate_personas_medicos_pacientes(fake, cfg, reference_date)

    print("Generando turnos sin solapamientos...")
    turnos = generate_turnos(cfg, pacientes, medicos, reference_date)

    print("Generando operaciones...")
    operaciones = generate_operaciones(turnos, int(cfg["counts"]["operacion"]), cfg)

    print(f"Escribiendo {output_sql}...")
    write_population_sql(cfg, personas, medicos, pacientes, turnos, operaciones, reference_date, output_sql)

    print(f"Escribiendo {output_validations}...")
    write_validations_sql(output_validations, reference_date)

    print("Listo.")
    print("Resumen:")
    print(f"  personas: {len(personas)}")
    print(f"  medicos: {len(medicos)}")
    print(f"  pacientes: {len(pacientes)}")
    print(f"  turnos: {len(turnos)}")
    print(f"  operaciones: {len(operaciones)}")
    print(f"  output: {output_sql}")
    print(f"  validaciones: {output_validations}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
