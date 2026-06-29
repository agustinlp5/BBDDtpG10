from __future__ import annotations

import random
from datetime import date, time, timedelta
from decimal import Decimal
from typing import Any

from .constants import DIAGNOSTICOS, ESPECIALIDADES_QUIRURGICAS
from .models import Medico, Paciente, Turno
from .utils import decimal_money, make_time_slots, random_date_between, weighted_choice

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

    occupied_doctor: set[tuple[str, date, time]] = set()
    occupied_patient: set[tuple[str, date, time]] = set()
    occupied_room: set[tuple[int, date, time]] = set()

    turnos: list[Turno] = []
    attempts = 0
    max_attempts = int(turno_cfg["max_schedule_attempts"])

    def elegir_fecha(estado: str) -> date:
        if estado == "realizado":
            return random_date_between(past_start, past_end)

        if estado == "programado":
            return random_date_between(future_start, future_end)

        # Los cancelados pueden ser pasados o futuros.
        if random.random() < 0.70:
            return random_date_between(past_start, past_end)

        return random_date_between(future_start, future_end)

    def elegir_diagnostico(especialidad: str) -> str:
        if especialidad == "Cardiologia":
            return random.choice(["hipertension", "arritmia", "dolor toracico", "control cardiologico"])

        if especialidad == "Traumatologia":
            return random.choice(["fractura", "dolor lumbar", "esguince", "control postural"])

        if especialidad == "Pediatria":
            return random.choice(["control pediatrico", "gripe", "alergia", "bronquitis"])

        if especialidad == "Ginecologia":
            return random.choice(["control ginecologico", "embarazo", "dolor abdominal"])

        return random.choice(DIAGNOSTICOS)

    while len(turnos) < n_turnos:
        attempts += 1

        if attempts > max_attempts:
            raise RuntimeError(
                "No se pudieron generar suficientes turnos sin solapamientos. "
                "Aumentar cantidad de medicos/consultorios, ampliar rango de fechas o subir max_schedule_attempts."
            )

        estado = weighted_choice(states)
        fecha_turno = elegir_fecha(estado)
        hora_turno = random.choice(slots)

        consultorios_disponibles = [
            numero
            for numero in range(1, n_consultorios + 1)
            if (numero, fecha_turno, hora_turno) not in occupied_room
        ]

        if not consultorios_disponibles:
            continue

        medicos_disponibles = [
            medico
            for medico in medicos
            if (medico.cuil, fecha_turno, hora_turno) not in occupied_doctor
        ]

        if not medicos_disponibles:
            continue

        pacientes_disponibles = [
            paciente
            for paciente in pacientes
            if paciente.fecha_nacimiento <= fecha_turno
            and (paciente.cuil, fecha_turno, hora_turno) not in occupied_patient
        ]

        if not pacientes_disponibles:
            continue

        consultorio = random.choice(consultorios_disponibles)
        medico = random.choice(medicos_disponibles)
        paciente = random.choice(pacientes_disponibles)

        key_doc = (medico.cuil, fecha_turno, hora_turno)
        key_pac = (paciente.cuil, fecha_turno, hora_turno)
        key_room = (consultorio, fecha_turno, hora_turno)

        # Los cancelados no bloquean slots para turnos futuros.
        # Pero tampoco se los deja superponer con turnos no cancelados ya existentes. (trigger)
        if estado != "cancelado":
            occupied_doctor.add(key_doc)
            occupied_patient.add(key_pac)
            occupied_room.add(key_room)

        especialidad = medico.especialidad
        diagnostico = elegir_diagnostico(especialidad)

        costo = decimal_money(turno_cfg["costo_min"], turno_cfg["costo_max"])

        if especialidad in ESPECIALIDADES_QUIRURGICAS:
            costo += decimal_money(5_000, 30_000)

        turnos.append(
            Turno(
                id_turno=len(turnos) + 1,
                diagnostico=diagnostico[:30],
                costo=costo,
                fecha_turno=fecha_turno,
                hora_turno=hora_turno,
                estado=estado,
                cuil_paciente=paciente.cuil,
                cuil_medico=medico.cuil,
                numero_consultorio=consultorio,
            )
        )

    return turnos