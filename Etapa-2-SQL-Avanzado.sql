-- Etapa 2: SQL Avanzado --

-- 2.1 Funciones de ventana --

-- 1 --

SELECT pa.cuil,
	   pe.nombre,
	   pe.apellido,
	   pa.genero,
	   pe.fecha_nacimiento,
	   pe.mail,
	   t.id_turno,
       t.diagnostico,
       t.fecha_turno,
	   LAG(t.fecha_turno) OVER (PARTITION BY t.cuil_paciente ORDER BY t.cuil_paciente, t.fecha_turno) AS fecha_turno_anterior,
	   t.fecha_turno -  LAG(t.fecha_turno) OVER (PARTITION BY t.cuil_paciente ORDER BY t.cuil_paciente, t.fecha_turno) AS dias_desde_turno_anterior
FROM paciente pa
JOIN persona pe ON pa.cuil = pe.cuil
JOIN turno t ON t.cuil_paciente = pa.cuil


-- 2 --

WITH turnos_por_medico AS (
SELECT m.cuil,
	   m.especialidad,
	   COUNT(t.id_turno) AS cant_turnos
FROM medico m
JOIN turno t ON m.cuil = t.cuil_medico
GROUP BY(m.cuil, m.especialidad)
)

SELECT especialidad,
       p.cuil,
	   p.nombre,
	   p.apellido,
	   p.mail,
	   cant_turnos,
	   RANK() OVER (PARTITION BY especialidad ORDER BY cant_turnos DESC) AS ranking
FROM turnos_por_medico t
JOIN persona p ON t.cuil = p.cuil
ORDER BY especialidad, ranking


-- 3 --

SELECT DISTINCT pa.cuil,
    			pe.nombre,
    			pe.apellido,
    			pe.telefono,
    			pa.genero,
    			FIRST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno) AS primer_turno,
    			LAST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS ultimo_turno
FROM paciente pa
JOIN persona pe ON pe.cuil = pa.cuil
JOIN turno t ON t.cuil_paciente = pa.cuil
ORDER BY pa.cuil


-- 2.2 Funciones estadísticas --

-- C1 --

SELECT 'id_turno' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(id_turno) AS cant_no_nulls,
	   ROUND(COUNT(id_turno) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT id_turno) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'costo' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(costo) AS cant_no_nulls,
	   ROUND(COUNT(costo) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT costo) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'fecha_turno' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(fecha_turno) AS cant_no_nulls,
	   ROUND(COUNT(fecha_turno) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT fecha_turno) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'hora_turno' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(hora_turno) AS cant_no_nulls,
	   ROUND(COUNT(hora_turno) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT hora_turno) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'estado' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(estado) AS cant_no_nulls,
	   ROUND(COUNT(estado) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT estado) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'diagnostico' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(diagnostico) AS cant_no_nulls,
	   ROUND(COUNT(diagnostico) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT diagnostico) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'numero_consultorio' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(numero_consultorio) AS cant_no_nulls,
	   ROUND(COUNT(numero_consultorio) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT numero_consultorio) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'cuil_paciente' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(cuil_paciente) AS cant_no_nulls,
	   ROUND(COUNT(cuil_paciente) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT cuil_paciente) AS cant_valores_diferentes
FROM turno

UNION ALL

SELECT 'cuil_medico' AS columna,
	   COUNT(*) AS cant_filas,
	   COUNT(cuil_medico) AS cant_no_nulls,
	   ROUND(COUNT(cuil_medico) * 100.0 / COUNT(*), 2) || '%' AS porcentaje_no_nulos,
	   COUNT(DISTINCT cuil_medico) AS cant_valores_diferentes
FROM turno


-- C2 --

WITH cuartiles AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY costo) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY costo) AS q3
    FROM turno
)

SELECT 'costo' AS columna,
	   ROUND(STDDEV_POP(costo), 2) AS desvio_estandar,
	   ROUND(MIN(costo), 2) AS minimo,
	   ROUND((PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY costo))::numeric, 2) AS p05,
	   ROUND(c.q1::numeric, 2) AS q1,
	   ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY costo))::numeric, 2) AS mediana,
	   ROUND(AVG(costo), 2) AS promedio,
	   ROUND(c.q3::numeric, 2) AS q3,
	   ROUND((PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY costo))::numeric, 2) AS p95,
	   ROUND(MAX(costo), 2) AS maximo,
	   SUM(CASE WHEN costo = 0 THEN 1 ELSE 0 END) AS cant_ceros,
	   ROUND(COUNT(*) FILTER (WHERE costo = 0) * 100.0 / COUNT(*), 2) AS porcentaje_ceros,
	   SUM(CASE WHEN costo < 0 THEN 1 ELSE 0 END) AS cant_negativos,
	   ROUND(COUNT(*) FILTER (WHERE costo < 0) * 100.0 / COUNT(*), 2) AS porcentaje_negativos,
	   COUNT(*) FILTER (
       WHERE costo < c.q1 - 1.5 * (c.q3 - c.q1)
           OR costo > c.q3 + 1.5 * (c.q3 - c.q1)
       ) AS cant_outliers
FROM turno
CROSS JOIN cuartiles c
GROUP BY c.q1, c.q3


-- C3 --

WITH frecuencias_estado AS (
	SELECT estado AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY estado
),

frecuencias_cuil_paciente AS (
	SELECT cuil_paciente AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY cuil_paciente
),

frecuencias_diagnostico AS (
	SELECT diagnostico AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY diagnostico
),

frecuencias_cuil_medico AS (
	SELECT cuil_medico AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY cuil_medico
),

frecuencias_fecha_turno AS (
	SELECT fecha_turno AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY fecha_turno
),

frecuencias_hora_turno AS (
	SELECT hora_turno AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY hora_turno
),

frecuencias_numero_consultorio AS (
	SELECT numero_consultorio AS valor, COUNT(*) AS frecuencia, RANK() OVER (ORDER BY COUNT(*) DESC) AS ranking
	FROM turno
	GROUP BY numero_consultorio
),

total AS (
	SELECT COUNT(*) AS total_filas
	FROM turno
)

(
SELECT 'estado' AS columna,
	   valor,
	   frecuencia,
	   ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
	   ranking
FROM frecuencias_estado
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'estado' AS columna,
	   'otros' AS valor,
	   SUM(frecuencia) AS frecuencia,
	   ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
	   11 AS ranking
FROM frecuencias_estado
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'diagnostico' AS columna,
       valor,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_diagnostico
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'diagnostico' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_diagnostico
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'numero_consultorio' AS columna,
       valor::text,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_numero_consultorio
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'numero_consultorio' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_numero_consultorio
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'fecha_turno' AS columna,
       valor::text,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_fecha_turno
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'fecha_turno' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_fecha_turno
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'hora_turno' AS columna,
       valor::text,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_hora_turno
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'hora_turno' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_hora_turno
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'cuil_paciente' AS columna,
       valor::text,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_cuil_paciente
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'cuil_paciente' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_cuil_paciente
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

UNION ALL

(
SELECT 'cuil_medico' AS columna,
       valor::text,
       frecuencia,
       ROUND(frecuencia * 100.0 / total_filas, 2) AS porcentaje,
       ranking
FROM frecuencias_cuil_medico
CROSS JOIN total
WHERE ranking <= 10

UNION ALL

SELECT 'cuil_medico' AS columna,
       'otros' AS valor,
       SUM(frecuencia) AS frecuencia,
       ROUND(SUM(frecuencia) * 100.0 / MAX(total_filas), 2) AS porcentaje,
       11 AS ranking
FROM frecuencias_cuil_medico
CROSS JOIN total
WHERE ranking > 10
HAVING COUNT(*) > 0
)

ORDER BY columna, ranking


-- 2.3 Análisis de performance --

-- EXPLAIN --

EXPLAIN(
SELECT DISTINCT pa.cuil,
    			pe.nombre,
    			pe.apellido,
    			pe.telefono,
    			pa.genero,
    			FIRST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno) AS primer_turno,
    			LAST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS ultimo_turno
FROM paciente pa
JOIN persona pe ON pe.cuil = pa.cuil
JOIN turno t ON t.cuil_paciente = pa.cuil
ORDER BY pa.cuil
)

-- EXPLAIN ANALYZE --

EXPLAIN ANALYZE(
SELECT DISTINCT pa.cuil,
    			pe.nombre,
    			pe.apellido,
    			pe.telefono,
    			pa.genero,
    			FIRST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno) AS primer_turno,
    			LAST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS ultimo_turno
FROM paciente pa
JOIN persona pe ON pe.cuil = pa.cuil
JOIN turno t ON t.cuil_paciente = pa.cuil
ORDER BY pa.cuil
)

-- Crear índice --
CREATE INDEX idx_turno_paciente_fecha
ON turno(cuil_paciente, fecha_turno);

-- Este índice podría ya estar creado al haber definido cuil como PK en paciente
CREATE INDEX idx_paciente_cuil
ON paciente(cuil);

-- Este índice podría ya estar creado al haber definido cuil como PK en persona
CREATE INDEX idx_persona_cuil
ON persona(cuil);


-- Ejecutar EXPLAIN nuevamente --

EXPLAIN(
SELECT DISTINCT pa.cuil,
    			pe.nombre,
    			pe.apellido,
    			pe.telefono,
    			pa.genero,
    			FIRST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno) AS primer_turno,
    			LAST_VALUE(t.fecha_turno) OVER (PARTITION BY pa.cuil ORDER BY t.fecha_turno ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS ultimo_turno
FROM paciente pa
JOIN persona pe ON pe.cuil = pa.cuil
JOIN turno t ON t.cuil_paciente = pa.cuil
ORDER BY pa.cuil
)

-- Borrar índices --
DROP INDEX idx_turno_paciente_fecha;
DROP INDEX idx_paciente_cuil;
DROP INDEX idx_persona_cuil;
