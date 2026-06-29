from __future__ import annotations

import random
from datetime import date, time, timedelta
from decimal import Decimal

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