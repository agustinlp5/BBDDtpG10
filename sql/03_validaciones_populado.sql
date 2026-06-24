-- Validaciones del poblado de datos
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
