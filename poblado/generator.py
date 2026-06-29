from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from faker import Faker


from .constants import (
    ESPECIALIDADES,
    ESPECIALIDADES_QUIRURGICAS,
    ESTUDIOS_BASE,
    OPERACIONES_BASE,
    RIESGOS,
    ROLES_MEDICOS,
)
from .models import Medico, Operacion, Paciente, Persona, Turno
from .utils import (
    decimal_money,
    generate_unique_cuil,
    phone_argentina,
    safe_email,
    weighted_choice,
    years_ago,
)

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
        salary = decimal_money(900_000, 3_500_000)
        if especialidad in ESPECIALIDADES_QUIRURGICAS:
            salary += decimal_money(200_000, 800_000)
        medicos.append(
            Medico(
                cuil=cuil,
                salario=salary,
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