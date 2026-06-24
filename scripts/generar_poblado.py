#!/usr/bin/env python3
"""
Generador de poblado para el TP de Introduccion a Bases de Datos.
Dominio: consultorio / sistema de turnos medicos.

Este script genera dos archivos:
  - sql/02_populado_datos.sql
  - sql/03_validaciones_populado.sql

Disenado para respetar las restricciones del script "sql/01_creacion_de_tablas.sql":
  - PK/FK entre persona, medico, paciente, turno y tablas dependientes.
  - CHECK constraints de genero, grupo sanguineo, estado, ala, gravedad, etc.
  - Trigger de medicos mayores de edad.
  - Trigger de turnos realizados en el pasado y programados en el futuro.
  - Trigger de no solapamiento de consultorio, medico y paciente en ventanas de 30 minutos.
  - Trigger de fechas de operacion/estudio posteriores o iguales al turno.
  - Trigger de exactamente un cirujano principal por operacion.

Uso recomendado desde la raiz del repo:

    source .venv/bin/activate
    python scripts/generar_poblado.py --config config/poblado_config.json

Luego cargar en PostgreSQL desde pgAdmin o psql:

    sql/02_populado_datos.sql
    sql/03_validaciones_populado.sql
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from faker import Faker
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Falta instalar Faker. Ejecutar: pip install -r requirements.txt"
    ) from exc


# -----------------------------
# Configuracion y constantes
# -----------------------------

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

RIESGOS = [
    "diabetes",
    "obesidad",
    "embarazo",
    "enfermedad cardiaca",
    "enfermedad respiratoria",
    "inmunocomprometido",
    "mayor de edad",
]

OBRAS_SOCIALES_BASE = [
    "OSDE",
    "Swiss Medical",
    "Galeno",
    "Medife",
    "Omint",
    "Avalian",
    "Sancor Salud",
    "Luis Pasteur",
    "Hospital Italiano",
    "IOMA",
    "PAMI",
    "OSUTHGRA",
    "OSECAC",
    "OSPE",
    "UP",
    "Particular",
    "Jerarquicos",
    "Federada Salud",
]

ESPECIALIDADES = [
    "Clinica medica",
    "Cardiologia",
    "Pediatria",
    "Traumatologia",
    "Ginecologia",
    "Dermatologia",
    "Neurologia",
    "Cirugia general",
    "Oftalmologia",
    "Psiquiatria",
    "Endocrinologia",
    "Neumonologia",
    "Gastroenterologia",
    "Otorrinolaringologia",
]

ESPECIALIDADES_QUIRURGICAS = {
    "Cirugia general",
    "Traumatologia",
    "Ginecologia",
    "Oftalmologia",
    "Otorrinolaringologia",
}

DIAGNOSTICOS = [
    "control general",
    "hipertension",
    "dolor abdominal",
    "cefalea",
    "gripe",
    "bronquitis",
    "fractura",
    "dermatitis",
    "arritmia",
    "diabetes",
    "ansiedad",
    "dolor lumbar",
    "alergia",
    "asma",
    "gastritis",
    "embarazo",
]

MEDICAMENTOS_BASE = [
    "Paracetamol",
    "Ibuprofeno",
    "Amoxicilina",
    "Metformina",
    "Losartan",
    "Enalapril",
    "Atorvastatina",
    "Omeprazol",
    "Salbutamol",
    "Loratadina",
    "Sertralina",
    "Clonazepam",
    "Insulina NPH",
    "Azitromicina",
    "Diclofenac",
    "Aspirina",
    "Levotiroxina",
    "Prednisona",
    "Furosemida",
    "Amlodipina",
    "Cetirizina",
    "Cefalexina",
    "Fluoxetina",
    "Pantoprazol",
    "Tramadol",
    "Dexametasona",
    "Budesonida",
    "Warfarina",
    "Ranitidina",
    "Domperidona",
]

EFECTOS_BASE = [
    "nauseas",
    "mareos",
    "somnolencia",
    "cefalea",
    "diarrea",
    "constipacion",
    "erupcion cutanea",
    "dolor abdominal",
    "vomitos",
    "vision borrosa",
    "palpitaciones",
    "hipotension",
    "hipertension",
    "insomnio",
    "sequedad bucal",
    "temblores",
    "dolor muscular",
    "fatiga",
    "aumento de peso",
    "perdida de apetito",
    "reaccion alergica",
    "edema",
    "tos seca",
    "sangrado",
    "confusion",
    "urticaria",
    "fotosensibilidad",
    "acidez",
    "hipoglucemia",
    "retencion de liquidos",
    "calambres",
    "ansiedad",
    "irritabilidad",
    "dolor toracico",
    "disnea",
    "fiebre",
    "rinorrea",
    "debilidad",
    "alteracion del gusto",
    "prurito",
    "bradicardia",
    "taquicardia",
    "convulsiones",
    "hepatotoxicidad",
    "nefrotoxicidad",
]

ESTUDIOS_BASE = [
    "Hemograma completo",
    "Radiografia de torax",
    "Electrocardiograma",
    "Ecografia abdominal",
    "Resonancia magnetica",
    "Tomografia computada",
    "Perfil lipidico",
    "Glucemia",
    "Prueba de esfuerzo",
    "Espirometria",
    "Analisis de orina",
    "Ecocardiograma",
    "Endoscopia",
    "Colonoscopia",
    "Audiometria",
    "Fondo de ojo",
]

OPERACIONES_BASE = [
    "Apendicectomia",
    "Colecistectomia",
    "Artroscopia de rodilla",
    "Cesarea",
    "Hernioplastia",
    "Biopsia quirurgica",
    "Cirugia de cataratas",
    "Reduccion de fractura",
    "Amigdalectomia",
    "Laparoscopia exploratoria",
    "Cirugia dermatologica",
    "Colocacion de stent",
]

ROLES_MEDICOS = [
    "ayudante de cirugia",
    "instrumentista",
    "anestesiólogo",
]


# -----------------------------
# Modelos simples para datos en memoria
# -----------------------------

@dataclass(frozen=True)
class Persona:
    cuil: str
    nombre: str
    apellido: str
    mail: str | None
    telefono: str | None
    fecha_nacimiento: date


@dataclass(frozen=True)
class Medico:
    cuil: str
    salario: Decimal
    cuil_supervisor: str | None
    especialidad: str


@dataclass(frozen=True)
class Paciente:
    cuil: str
    genero: str
    grupo_sanguineo: str
    id_obra: int
    fecha_nacimiento: date


@dataclass(frozen=True)
class Turno:
    id_turno: int
    diagnostico: str
    costo: Decimal
    fecha_turno: date
    hora_turno: time
    estado: str
    cuil_paciente: str
    cuil_medico: str
    numero_consultorio: int


@dataclass(frozen=True)
class Operacion:
    id_operacion: int
    nombre_operacion: str
    complejidad: str
    fecha_operacion: date
    id_turno: int


# -----------------------------
# Utilidades generales
# -----------------------------

def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_CONFIG
    with path.open("r", encoding="utf-8") as f:
        override = json.load(f)
    return deep_merge(DEFAULT_CONFIG, override)


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


# -----------------------------
# Generacion de entidades
# -----------------------------

def generate_personas_medicos_pacientes(
    fake: Faker,
    cfg: dict[str, Any],
    today: date,
) -> tuple[list[Persona], list[Medico], list[Paciente]]:
    counts = cfg["counts"]
    distributions = cfg["distributions"]
    n_medicos = int(counts["medico"])
    n_pacientes = int(counts["paciente"])
    n_obras = int(counts["obra_social"])

    used_cuils: set[str] = set()
    personas: list[Persona] = []
    medicos: list[Medico] = []
    pacientes: list[Paciente] = []

    # Medicos: edades 28-70 para cumplir holgadamente mayoria de edad.
    medico_cuils: list[str] = []
    for idx in range(1, n_medicos + 1):
        nombre = fake.first_name()
        apellido = fake.last_name()
        cuil = generate_unique_cuil(used_cuils)
        fecha_nacimiento = years_ago(28, 70, today)
        persona = Persona(
            cuil=cuil,
            nombre=nombre,
            apellido=apellido,
            mail=safe_email(nombre, apellido, idx),
            telefono=phone_argentina(),
            fecha_nacimiento=fecha_nacimiento,
        )
        personas.append(persona)
        medico_cuils.append(cuil)

    # Primero 20% sin supervisor. El resto supervisado por alguno ya creado.
    senior_count = max(1, int(n_medicos * 0.20))
    for idx, cuil in enumerate(medico_cuils, start=1):
        supervisor = None if idx <= senior_count else random.choice(medico_cuils[: max(1, idx - 1)])
        especialidad = random.choice(ESPECIALIDADES)
        base_salary = decimal_money(900_000, 3_500_000)
        if especialidad in ESPECIALIDADES_QUIRURGICAS:
            base_salary += Decimal(random.randint(200_000, 800_000))
        medicos.append(
            Medico(
                cuil=cuil,
                salario=base_salary.quantize(Decimal("0.01")),
                cuil_supervisor=supervisor,
                especialidad=especialidad,
            )
        )

    # Pacientes: nacidos entre 1928 y hace 3 anios para evitar turnos historicos antes del nacimiento.
    for idx in range(1, n_pacientes + 1):
        genero = weighted_choice(distributions["genero"])
        nombre = fake.first_name()
        apellido = fake.last_name()
        cuil = generate_unique_cuil(used_cuils, genero=genero)
        fecha_nacimiento = years_ago(3, 96, today)
        personas.append(
            Persona(
                cuil=cuil,
                nombre=nombre,
                apellido=apellido,
                mail=safe_email(nombre, apellido, n_medicos + idx),
                telefono=phone_argentina() if random.random() < 0.92 else None,
                fecha_nacimiento=fecha_nacimiento,
            )
        )
        pacientes.append(
            Paciente(
                cuil=cuil,
                genero=genero,
                grupo_sanguineo=weighted_choice(distributions["grupo_sanguineo"]),
                id_obra=random.randint(1, n_obras),
                fecha_nacimiento=fecha_nacimiento,
            )
        )

    return personas, medicos, pacientes


def generate_turnos(
    cfg: dict[str, Any],
    pacientes: list[Paciente],
    medicos: list[Medico],
    today: date,
) -> list[Turno]:
    n_turnos = int(cfg["counts"]["turno"])
    n_consultorios = int(cfg["counts"]["consultorio"])
    turno_cfg = cfg["turno"]
    states = turno_cfg["estado_weights"]
    slots = make_time_slots(
        int(turno_cfg["work_start_hour"]),
        int(turno_cfg["work_end_hour"]),
        int(turno_cfg["duration_minutes"]),
    )

    past_start = today - timedelta(days=int(turno_cfg["past_days"]))
    past_end = today - timedelta(days=1)
    future_start = today + timedelta(days=1)
    future_end = today + timedelta(days=int(turno_cfg["future_days"]))

    medicos_by_cuil = {m.cuil: m for m in medicos}
    pacientes_by_cuil = {p.cuil: p for p in pacientes}

    occupied_doctor: set[tuple[str, date, time]] = set()
    occupied_patient: set[tuple[str, date, time]] = set()
    occupied_room: set[tuple[int, date, time]] = set()

    turnos: list[Turno] = []
    attempts = 0
    max_attempts = int(turno_cfg["max_schedule_attempts"])

    while len(turnos) < n_turnos:
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError(
                "No se pudieron generar suficientes turnos sin solapamientos. "
                "Aumentar cantidad de medicos/consultorios, ampliar rango de fechas o subir max_schedule_attempts."
            )

        estado = weighted_choice(states)
        if estado == "realizado":
            fecha_turno = random_date_between(past_start, past_end)
        elif estado == "programado":
            fecha_turno = random_date_between(future_start, future_end)
        else:
            # Cancelados pueden ser historicos o futuros.
            if random.random() < 0.70:
                fecha_turno = random_date_between(past_start, past_end)
            else:
                fecha_turno = random_date_between(future_start, future_end)

        hora_turno = random.choice(slots)
        medico = random.choice(medicos)
        paciente = random.choice(pacientes)
        consultorio = random.randint(1, n_consultorios)

        # Fecha posterior al nacimiento de ambos. En la practica siempre se cumple por los rangos elegidos.
        if fecha_turno < pacientes_by_cuil[paciente.cuil].fecha_nacimiento:
            continue

        # El trigger compara cualquier NEW turno contra turnos existentes no cancelados.
        # Por eso incluso un turno cancelado nuevo no puede superponerse con un turno
        # ya insertado que sea programado o realizado. Sin embargo, los turnos cancelados
        # no quedan bloqueando slots para turnos posteriores, porque el trigger filtra
        # t.estado <> 'cancelado' sobre los registros existentes.
        key_doc = (medico.cuil, fecha_turno, hora_turno)
        key_pac = (paciente.cuil, fecha_turno, hora_turno)
        key_room = (consultorio, fecha_turno, hora_turno)

        if key_doc in occupied_doctor or key_pac in occupied_patient or key_room in occupied_room:
            continue

        if estado != "cancelado":
            occupied_doctor.add(key_doc)
            occupied_patient.add(key_pac)
            occupied_room.add(key_room)

        especialidad = medicos_by_cuil[medico.cuil].especialidad
        if especialidad == "Cardiologia":
            diagnostico = random.choice(["hipertension", "arritmia", "dolor toracico", "control cardiologico"])
        elif especialidad == "Traumatologia":
            diagnostico = random.choice(["fractura", "dolor lumbar", "esguince", "control postural"])
        elif especialidad == "Pediatria":
            diagnostico = random.choice(["control pediatrico", "gripe", "alergia", "bronquitis"])
        elif especialidad == "Ginecologia":
            diagnostico = random.choice(["control ginecologico", "embarazo", "dolor abdominal"])
        else:
            diagnostico = random.choice(DIAGNOSTICOS)

        base_cost = decimal_money(turno_cfg["costo_min"], turno_cfg["costo_max"])
        if especialidad in ESPECIALIDADES_QUIRURGICAS:
            base_cost += Decimal(random.randint(5_000, 30_000))

        turnos.append(
            Turno(
                id_turno=len(turnos) + 1,
                diagnostico=diagnostico[:30],
                costo=base_cost.quantize(Decimal("0.01")),
                fecha_turno=fecha_turno,
                hora_turno=hora_turno,
                estado=estado,
                cuil_paciente=paciente.cuil,
                cuil_medico=medico.cuil,
                numero_consultorio=consultorio,
            )
        )

    return turnos


def generate_paciente_riesgo(pacientes: list[Paciente], today: date) -> list[tuple[str, int]]:
    riesgo_id = {name: idx for idx, name in enumerate(RIESGOS, start=1)}
    rows: set[tuple[str, int]] = set()

    for paciente in pacientes:
        age = (today - paciente.fecha_nacimiento).days // 365

        if age >= 18 and random.random() < 0.48:
            rows.add((paciente.cuil, riesgo_id["mayor de edad"]))
        if random.random() < 0.12:
            rows.add((paciente.cuil, riesgo_id["diabetes"]))
        if random.random() < 0.18:
            rows.add((paciente.cuil, riesgo_id["obesidad"]))
        if random.random() < 0.10:
            rows.add((paciente.cuil, riesgo_id["enfermedad cardiaca"]))
        if random.random() < 0.09:
            rows.add((paciente.cuil, riesgo_id["enfermedad respiratoria"]))
        if random.random() < 0.04:
            rows.add((paciente.cuil, riesgo_id["inmunocomprometido"]))
        if paciente.genero == "mujer" and 15 <= age <= 50 and random.random() < 0.05:
            rows.add((paciente.cuil, riesgo_id["embarazo"]))

    return sorted(rows)


def generate_catalog_name_rows(base: list[str], count: int, prefix: str) -> list[str]:
    names = list(base)
    i = 1
    while len(names) < count:
        names.append(f"{prefix} {i}")
        i += 1
    return names[:count]


def generate_medicamento_efecto(n_medicamentos: int, n_efectos: int) -> list[tuple[int, int]]:
    rows: set[tuple[int, int]] = set()
    for med_id in range(1, n_medicamentos + 1):
        effects_for_med = random.randint(1, min(5, n_efectos))
        for efecto_id in random.sample(range(1, n_efectos + 1), effects_for_med):
            rows.add((efecto_id, med_id))
    return sorted(rows)


def generate_turno_medicamento(turnos: list[Turno], n_medicamentos: int) -> list[tuple[int, int]]:
    rows: set[tuple[int, int]] = set()
    for turno in turnos:
        if turno.estado == "cancelado":
            continue
        probability = 0.58 if turno.estado == "realizado" else 0.22
        if random.random() < probability:
            meds_count = random.choices([1, 2, 3], weights=[0.68, 0.25, 0.07], k=1)[0]
            for med_id in random.sample(range(1, n_medicamentos + 1), meds_count):
                rows.add((turno.id_turno, med_id))
    return sorted(rows)


def generate_estudios(turnos: list[Turno], count: int, today: date) -> list[tuple[str, date, int]]:
    eligible = [t for t in turnos if t.estado != "cancelado"]
    rows: list[tuple[str, date, int]] = []
    for turno in random.sample(eligible, k=min(count, len(eligible))):
        delay_days = random.randint(0, 45)
        fecha_estudio = turno.fecha_turno + timedelta(days=delay_days)
        rows.append((random.choice(ESTUDIOS_BASE), fecha_estudio, turno.id_turno))
    return rows


def generate_operaciones(turnos: list[Turno], count: int, cfg: dict[str, Any]) -> list[Operacion]:
    # Mayormente turnos realizados; si no alcanza, se toman no cancelados.
    realized = [t for t in turnos if t.estado == "realizado"]
    fallback = [t for t in turnos if t.estado != "cancelado"]
    source = realized if len(realized) >= count else fallback
    chosen = random.sample(source, k=min(count, len(source)))

    operaciones: list[Operacion] = []
    for idx, turno in enumerate(chosen, start=1):
        delay_days = random.randint(0, 60)
        operaciones.append(
            Operacion(
                id_operacion=idx,
                nombre_operacion=random.choice(OPERACIONES_BASE),
                complejidad=weighted_choice(cfg["distributions"]["complejidad"]),
                fecha_operacion=turno.fecha_turno + timedelta(days=delay_days),
                id_turno=turno.id_turno,
            )
        )
    return operaciones


def generate_medico_operacion(
    operaciones: list[Operacion],
    turnos_by_id: dict[int, Turno],
    medicos: list[Medico],
) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    """
    Retorna dos listas: primero cirujanos principales, luego roles secundarios.
    Se escriben en ese orden para satisfacer el trigger de cirujano principal.
    """
    surgical_medicos = [m for m in medicos if m.especialidad in ESPECIALIDADES_QUIRURGICAS]
    if not surgical_medicos:
        surgical_medicos = medicos

    principals: list[tuple[str, int, str]] = []
    secondaries: list[tuple[str, int, str]] = []

    for op in operaciones:
        turno = turnos_by_id[op.id_turno]
        # Los pacientes y medicos fueron generados en conjuntos distintos; igualmente excluimos al paciente.
        eligible_principals = [m for m in surgical_medicos if m.cuil != turno.cuil_paciente]
        principal = random.choice(eligible_principals)
        principals.append((principal.cuil, op.id_operacion, "cirujano principal"))

        already = {principal.cuil}
        team_size = random.choices([1, 2, 3], weights=[0.30, 0.50, 0.20], k=1)[0]
        eligible = [m for m in medicos if m.cuil not in already and m.cuil != turno.cuil_paciente]
        for med in random.sample(eligible, k=min(team_size, len(eligible))):
            already.add(med.cuil)
            secondaries.append((med.cuil, op.id_operacion, random.choice(ROLES_MEDICOS)))

    return principals, secondaries


# -----------------------------
# Escritura de archivos SQL
# -----------------------------

def write_population_sql(
    cfg: dict[str, Any],
    personas: list[Persona],
    medicos: list[Medico],
    pacientes: list[Paciente],
    turnos: list[Turno],
    operaciones: list[Operacion],
    today: date,
    output_path: Path,
) -> None:
    chunk_size = int(cfg["chunk_size"])
    counts = cfg["counts"]
    distributions = cfg["distributions"]

    obras = generate_catalog_name_rows(OBRAS_SOCIALES_BASE, int(counts["obra_social"]), "Obra Social")
    medicamentos = generate_catalog_name_rows(MEDICAMENTOS_BASE, int(counts["medicamento"]), "Medicamento")
    efectos = generate_catalog_name_rows(EFECTOS_BASE, int(counts["efecto_secundario"]), "Efecto")

    paciente_riesgo = generate_paciente_riesgo(pacientes, today)
    medicamento_efecto = generate_medicamento_efecto(len(medicamentos), len(efectos))
    estudios = generate_estudios(turnos, int(counts["estudio"]), today)
    turno_medicamento = generate_turno_medicamento(turnos, len(medicamentos))
    turnos_by_id = {t.id_turno: t for t in turnos}
    med_op_principals, med_op_secondaries = generate_medico_operacion(operaciones, turnos_by_id, medicos)

    with output_path.open("w", encoding="utf-8") as out:
        out.write("-- Script generado automaticamente por scripts/generar_poblado.py\n")
        out.write(f"-- Fecha de generacion: {datetime.now().isoformat(timespec='seconds')}\n")
        out.write("-- Ejecutar despues de sql/01_creacion_de_tablas.sql\n\n")
        out.write("BEGIN;\n\n")

        if cfg.get("truncate_before_insert", True):
            out.write("-- Limpieza para permitir reejecucion del poblado sin duplicados.\n")
            out.write(
                "TRUNCATE TABLE "
                "medico_operacion, turno_medicamento, medicamento_efecto, "
                "operacion, estudio, efecto_secundario, medicamento, turno, "
                "consultorio, paciente_riesgo, riesgo, paciente, obra_social, medico, persona "
                "RESTART IDENTITY CASCADE;\n\n"
            )

        out.write("-- 1. Catalogo de obras sociales\n")
        write_insert(out, "obra_social", ["nombre_obra"], [(name[:30],) for name in obras], chunk_size)

        out.write("-- 2. Catalogo fijo de riesgos\n")
        write_insert(out, "riesgo", ["nombre_riesgo"], [(name,) for name in RIESGOS], chunk_size)

        out.write("-- 3. Consultorios\n")
        consultorio_rows = [
            (
                numero,
                1 + ((numero - 1) // 10),
                weighted_choice(distributions["ala"]),
            )
            for numero in range(1, int(counts["consultorio"]) + 1)
        ]
        write_insert(out, "consultorio", ["numero_consultorio", "piso", "ala"], consultorio_rows, chunk_size)

        out.write("-- 4. Personas: incluye medicos y pacientes\n")
        write_insert(
            out,
            "persona",
            ["cuil", "nombre", "apellido", "mail", "telefono", "fecha_nacimiento"],
            [(p.cuil, p.nombre, p.apellido, p.mail, p.telefono, p.fecha_nacimiento) for p in personas],
            chunk_size,
        )

        out.write("-- 5. Medicos: primero se insertan senior sin supervisor, luego supervisados\n")
        senior_rows = [
            (m.cuil, m.salario, m.cuil_supervisor, m.especialidad)
            for m in medicos
            if m.cuil_supervisor is None
        ]
        supervised_rows = [
            (m.cuil, m.salario, m.cuil_supervisor, m.especialidad)
            for m in medicos
            if m.cuil_supervisor is not None
        ]
        write_insert(out, "medico", ["cuil", "salario", "cuil_supervisor", "especialidad"], senior_rows, chunk_size)
        write_insert(out, "medico", ["cuil", "salario", "cuil_supervisor", "especialidad"], supervised_rows, chunk_size)

        out.write("-- 6. Pacientes\n")
        write_insert(
            out,
            "paciente",
            ["cuil", "genero", "grupo_sanguineo", "id_obra"],
            [(p.cuil, p.genero, p.grupo_sanguineo, p.id_obra) for p in pacientes],
            chunk_size,
        )

        out.write("-- 7. Riesgos por paciente\n")
        write_insert(out, "paciente_riesgo", ["cuil_paciente", "id_riesgo"], paciente_riesgo, chunk_size)

        out.write("-- 8. Turnos sin solapamiento de medico/paciente/consultorio\n")
        write_insert(
            out,
            "turno",
            [
                "diagnostico",
                "costo",
                "fecha_turno",
                "hora_turno",
                "estado",
                "cuil_paciente",
                "cuil_medico",
                "numero_consultorio",
            ],
            [
                (
                    t.diagnostico,
                    t.costo,
                    t.fecha_turno,
                    t.hora_turno,
                    t.estado,
                    t.cuil_paciente,
                    t.cuil_medico,
                    t.numero_consultorio,
                )
                for t in turnos
            ],
            chunk_size,
        )

        out.write("-- 9. Medicamentos\n")
        write_insert(
            out,
            "medicamento",
            ["nombre_medicamento"],
            [(name,) for name in medicamentos],
            chunk_size,
        )

        out.write("-- 10. Efectos secundarios\n")
        write_insert(
            out,
            "efecto_secundario",
            ["nombre_efecto", "gravedad"],
            [(name, weighted_choice(distributions["gravedad"])) for name in efectos],
            chunk_size,
        )

        out.write("-- 11. Relacion medicamento-efecto\n")
        write_insert(out, "medicamento_efecto", ["id_efecto", "id_medicamento"], medicamento_efecto, chunk_size)

        out.write("-- 12. Estudios derivados de turnos\n")
        write_insert(out, "estudio", ["nombre_estudio", "fecha_estudio", "id_turno"], estudios, chunk_size)

        out.write("-- 13. Operaciones derivadas de turnos, con fecha >= fecha_turno\n")
        write_insert(
            out,
            "operacion",
            ["nombre_operacion", "complejidad", "fecha_operacion", "id_turno"],
            [(op.nombre_operacion, op.complejidad, op.fecha_operacion, op.id_turno) for op in operaciones],
            chunk_size,
        )

        out.write("-- 14. Medicamentos recetados en turnos\n")
        write_insert(out, "turno_medicamento", ["id_turno", "id_medicamento"], turno_medicamento, chunk_size)

        out.write("-- 15. Equipos medicos por operacion: se insertan primero los cirujanos principales\n")
        write_insert(out, "medico_operacion", ["cuil", "id_operacion", "rol_medico"], med_op_principals, chunk_size)
        write_insert(out, "medico_operacion", ["cuil", "id_operacion", "rol_medico"], med_op_secondaries, chunk_size)

        out.write("COMMIT;\n")


def write_validations_sql(output_path: Path) -> None:
    output_path.write_text(
        """-- Validaciones del poblado de datos
-- Ejecutar luego de sql/02_populado_datos.sql

-- 1. Cantidad de registros por tabla
SELECT 'persona' AS tabla, COUNT(*) AS cantidad FROM persona
UNION ALL SELECT 'medico', COUNT(*) FROM medico
UNION ALL SELECT 'obra_social', COUNT(*) FROM obra_social
UNION ALL SELECT 'paciente', COUNT(*) FROM paciente
UNION ALL SELECT 'riesgo', COUNT(*) FROM riesgo
UNION ALL SELECT 'paciente_riesgo', COUNT(*) FROM paciente_riesgo
UNION ALL SELECT 'consultorio', COUNT(*) FROM consultorio
UNION ALL SELECT 'turno', COUNT(*) FROM turno
UNION ALL SELECT 'operacion', COUNT(*) FROM operacion
UNION ALL SELECT 'estudio', COUNT(*) FROM estudio
UNION ALL SELECT 'medicamento', COUNT(*) FROM medicamento
UNION ALL SELECT 'efecto_secundario', COUNT(*) FROM efecto_secundario
UNION ALL SELECT 'turno_medicamento', COUNT(*) FROM turno_medicamento
UNION ALL SELECT 'medicamento_efecto', COUNT(*) FROM medicamento_efecto
UNION ALL SELECT 'medico_operacion', COUNT(*) FROM medico_operacion
ORDER BY tabla;

-- 2. Distribucion de estados de turno
SELECT
    estado,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM turno
GROUP BY estado
ORDER BY cantidad DESC;

-- 3. Estadisticos numericos para costo de turno
SELECT
    COUNT(*) AS cantidad,
    MIN(costo) AS minimo,
    ROUND(AVG(costo), 2) AS promedio,
    MAX(costo) AS maximo,
    ROUND(STDDEV(costo), 2) AS desvio_estandar,
    SUM(CASE WHEN costo = 0 THEN 1 ELSE 0 END) AS cantidad_ceros,
    SUM(CASE WHEN costo < 0 THEN 1 ELSE 0 END) AS cantidad_negativos
FROM turno;

-- 4. Estadisticos numericos para salario medico
SELECT
    COUNT(*) AS cantidad,
    MIN(salario) AS minimo,
    ROUND(AVG(salario), 2) AS promedio,
    MAX(salario) AS maximo,
    ROUND(STDDEV(salario), 2) AS desvio_estandar,
    SUM(CASE WHEN salario = 0 THEN 1 ELSE 0 END) AS cantidad_ceros,
    SUM(CASE WHEN salario < 0 THEN 1 ELSE 0 END) AS cantidad_negativos
FROM medico;

-- 5. Distribucion de pacientes por genero y grupo sanguineo
SELECT
    genero,
    grupo_sanguineo,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM paciente
GROUP BY genero, grupo_sanguineo
ORDER BY cantidad DESC;

-- 6. Top 10 obras sociales por cantidad de pacientes
SELECT
    os.nombre_obra,
    COUNT(*) AS cantidad_pacientes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM paciente p
JOIN obra_social os ON os.id_obra = p.id_obra
GROUP BY os.nombre_obra
ORDER BY cantidad_pacientes DESC
LIMIT 10;

-- 7. Turnos por especialidad medica
SELECT
    m.especialidad,
    COUNT(*) AS cantidad_turnos,
    ROUND(AVG(t.costo), 2) AS costo_promedio
FROM turno t
JOIN medico m ON m.cuil = t.cuil_medico
GROUP BY m.especialidad
ORDER BY cantidad_turnos DESC;

-- 8. Validacion: programados futuros y realizados pasados. Debe devolver 0.
SELECT COUNT(*) AS turnos_con_estado_temporal_invalido
FROM turno
WHERE (estado = 'programado' AND (fecha_turno < CURRENT_DATE OR (fecha_turno = CURRENT_DATE AND hora_turno < CURRENT_TIME)))
   OR (estado = 'realizado' AND (fecha_turno > CURRENT_DATE OR (fecha_turno = CURRENT_DATE AND hora_turno > CURRENT_TIME)));

-- 9. Validacion: turnos antes del nacimiento de medico o paciente. Debe devolver 0.
SELECT COUNT(*) AS turnos_antes_de_nacimiento
FROM turno t
JOIN persona pm ON pm.cuil = t.cuil_medico
JOIN persona pp ON pp.cuil = t.cuil_paciente
WHERE t.fecha_turno < pm.fecha_nacimiento
   OR t.fecha_turno < pp.fecha_nacimiento;

-- 10. Validacion: solapamiento de consultorio en turnos no cancelados. Debe devolver 0.
SELECT COUNT(*) AS solapamientos_consultorio
FROM turno t1
JOIN turno t2 ON t1.id_turno < t2.id_turno
              AND t1.numero_consultorio = t2.numero_consultorio
              AND t1.fecha_turno = t2.fecha_turno
              AND t1.estado <> 'cancelado'
              AND t2.estado <> 'cancelado'
              AND t1.hora_turno < (t2.hora_turno + INTERVAL '30 minutes')
              AND (t1.hora_turno + INTERVAL '30 minutes') > t2.hora_turno;

-- 11. Validacion: solapamiento de medico/paciente en turnos no cancelados. Debe devolver 0.
SELECT COUNT(*) AS solapamientos_persona
FROM turno t1
JOIN turno t2 ON t1.id_turno < t2.id_turno
              AND t1.fecha_turno = t2.fecha_turno
              AND t1.estado <> 'cancelado'
              AND t2.estado <> 'cancelado'
              AND (t1.cuil_medico = t2.cuil_medico OR t1.cuil_paciente = t2.cuil_paciente)
              AND t1.hora_turno < (t2.hora_turno + INTERVAL '30 minutes')
              AND (t1.hora_turno + INTERVAL '30 minutes') > t2.hora_turno;

-- 12. Validacion: operaciones y estudios posteriores al turno. Debe devolver 0 en ambos campos.
SELECT
    SUM(CASE WHEN o.fecha_operacion < t.fecha_turno THEN 1 ELSE 0 END) AS operaciones_invalidas,
    (
        SELECT SUM(CASE WHEN e.fecha_estudio < t2.fecha_turno THEN 1 ELSE 0 END)
        FROM estudio e
        JOIN turno t2 ON t2.id_turno = e.id_turno
    ) AS estudios_invalidos
FROM operacion o
JOIN turno t ON t.id_turno = o.id_turno;

-- 13. Validacion: cada operacion tiene exactamente un cirujano principal. Debe devolver 0 filas.
SELECT
    o.id_operacion,
    COUNT(*) FILTER (WHERE mo.rol_medico = 'cirujano principal') AS cantidad_cirujanos_principales
FROM operacion o
LEFT JOIN medico_operacion mo ON mo.id_operacion = o.id_operacion
GROUP BY o.id_operacion
HAVING COUNT(*) FILTER (WHERE mo.rol_medico = 'cirujano principal') <> 1;

-- 14. Validacion: medicos mayores de edad. Debe devolver 0.
SELECT COUNT(*) AS medicos_menores_de_edad
FROM medico m
JOIN persona p ON p.cuil = m.cuil
WHERE p.fecha_nacimiento > CURRENT_DATE - INTERVAL '18 years';

-- 15. Distribucion de riesgos
SELECT
    r.nombre_riesgo,
    COUNT(pr.cuil_paciente) AS cantidad_pacientes,
    ROUND(COUNT(pr.cuil_paciente) * 100.0 / NULLIF((SELECT COUNT(*) FROM paciente), 0), 2) AS porcentaje_sobre_pacientes
FROM riesgo r
LEFT JOIN paciente_riesgo pr ON pr.id_riesgo = r.id_riesgo
GROUP BY r.nombre_riesgo
ORDER BY cantidad_pacientes DESC;
""",
        encoding="utf-8",
    )


# -----------------------------
# Main
# -----------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera script SQL de poblado para el TP de IBD.")
    parser.add_argument("--config", type=Path, default=None, help="Ruta a config JSON. Default: configuracion interna.")
    parser.add_argument("--today", type=str, default=None, help="Fecha base YYYY-MM-DD. Default: fecha actual.")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    seed = int(cfg["seed"])
    random.seed(seed)

    fake = Faker(cfg.get("locale", "es_AR"))
    Faker.seed(seed)

    today = date.fromisoformat(args.today) if args.today else date.today()

    output_sql = Path(cfg["output_sql"])
    output_validations = Path(cfg["output_validations_sql"])
    ensure_dirs(output_sql, output_validations)

    print("Generando personas, medicos y pacientes...")
    personas, medicos, pacientes = generate_personas_medicos_pacientes(fake, cfg, today)

    print("Generando turnos sin solapamientos...")
    turnos = generate_turnos(cfg, pacientes, medicos, today)

    print("Generando operaciones...")
    operaciones = generate_operaciones(turnos, int(cfg["counts"]["operacion"]), cfg)

    print(f"Escribiendo {output_sql}...")
    write_population_sql(cfg, personas, medicos, pacientes, turnos, operaciones, today, output_sql)

    print(f"Escribiendo {output_validations}...")
    write_validations_sql(output_validations)

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
