from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from .constants import (
    EFECTOS_BASE,
    MEDICAMENTOS_BASE,
    OBRAS_SOCIALES_BASE,
    RIESGOS,
)
from .generator import (
    generate_catalog_name_rows,
    generate_estudios,
    generate_medicamento_efecto,
    generate_medico_operacion,
    generate_paciente_riesgo,
    generate_turno_medicamento,
)
from .models import Medico, Operacion, Paciente, Persona, Turno
from .utils import weighted_choice, write_insert

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
        out.write(f"-- Fecha logica de referencia: {today.isoformat()}\n")
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