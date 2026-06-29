from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal


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
