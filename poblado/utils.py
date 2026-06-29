from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Sequence

def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def weighted_choice(weight_map: dict[str, float]) -> str:
    keys = list(weight_map.keys())
    weights = list(weight_map.values())
    return random.choices(keys, weights=weights, k=1)[0]


def decimal_money(min_value: float | int, max_value: float | int) -> Decimal:
    value = random.uniform(float(min_value), float(max_value))
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def random_date_between(start: date, end: date) -> date:
    if end < start:
        raise ValueError(f"Rango de fechas invalido: {start} > {end}")
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def years_ago(min_years: int, max_years: int, today: date) -> date:
    """Devuelve fecha de nacimiento entre min_years y max_years de edad."""
    max_birth = today - timedelta(days=365 * min_years)
    min_birth = today - timedelta(days=365 * max_years)
    return random_date_between(min_birth, max_birth)


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    if isinstance(value, date) and not isinstance(value, datetime):
        return f"'{value.isoformat()}'"
    if isinstance(value, time):
        return f"'{value.strftime('%H:%M:%S')}'"
    text = str(value).replace("'", "''")
    return f"'{text}'"


def row_sql(values: Sequence[Any]) -> str:
    return "(" + ", ".join(sql_literal(v) for v in values) + ")"


def write_insert(
    out,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    chunk_size: int,
) -> None:
    if not rows:
        return
    col_sql = ", ".join(columns)
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        out.write(f"INSERT INTO {table} ({col_sql}) VALUES\n")
        out.write(",\n".join(row_sql(row) for row in chunk))
        out.write(";\n\n")


def generate_unique_cuil(used: set[str], genero: str | None = None) -> str:
    """Genera CUIL de 11 digitos. No calcula digito verificador real, solo formato valido."""
    if genero == "hombre":
        prefixes = ["20", "23"]
    elif genero == "mujer":
        prefixes = ["27", "23"]
    else:
        prefixes = ["20", "23", "27", "30"]

    while True:
        prefix = random.choice(prefixes)
        dni = random.randint(10_000_000, 49_999_999)
        check_digit = random.randint(0, 9)
        cuil = f"{prefix}{dni:08d}{check_digit}"
        if cuil not in used:
            used.add(cuil)
            return cuil


def phone_argentina() -> str:
    return f"+54 11 {random.randint(2000, 9999)}-{random.randint(1000, 9999)}"


def safe_email(nombre: str, apellido: str, seq: int) -> str:
    def normalize(s: str) -> str:
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
            "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "Ñ": "n",
        }
        for a, b in replacements.items():
            s = s.replace(a, b)
        return "".join(ch.lower() for ch in s if ch.isalnum())

    return f"{normalize(nombre)}.{normalize(apellido)}.{seq}@mail.com"[:100]


def make_time_slots(start_hour: int, end_hour: int, duration_minutes: int) -> list[time]:
    slots: list[time] = []
    current = datetime.combine(date.today(), time(start_hour, 0))
    end = datetime.combine(date.today(), time(end_hour, 0))
    step = timedelta(minutes=duration_minutes)
    while current < end:
        slots.append(current.time())
        current += step
    return slots