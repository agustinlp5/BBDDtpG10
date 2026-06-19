# BBDDtpG10
Trabajo práctico BBDD

## To Do List:

1.1:
- Agregar lo que haya que agregar al DER para hacer el resto del tp
- Informe DER y consigna.
- Completar decisiones de diseño.
- Informe decisiones de diseño.
- Informe Restricciones.

1.2:
- Informe
- Implementar Restricciones. X

1.3:
- Informe
- Poblar base.
- Validar consistencia.

2.1:
- Informe
- 2 consultas de ventana: X
    - Descripción de la pregunta.
    - Justificación de usar ventana.
    - Informar resultado.

2.2:
- Informe
- Funciones estadisticas:
    - C1.
    - C2.
    - C3.
    - Consulta con CTE.

2.3:
- Hacer EXPLAIN / EXPLAIN ANALYZE a una consulta *COMPLEJA*.
- Analizar plan de ejecución.
- Proponer mejora (indices/ cambiar consulta).
- Comparar y explicar diferencias.

3.1:
- Informe
- 3 procesos con MapReduce:
    - Describir pregunta.
    - Explicitar Map.
    - Explicitar Reduce.
    - Mostrar resultados.

4.1.1: 
- Informe
- 3 tipos de datos que almacenar como clave-valor simples/hashes:
    - Código de carga de datos.
    - Consultas de valores específicos.
    - Actualizar y verificar un campo.
    - Explicar por qué Redis es mejor que PostgreSQL en este caso.

4.1.2:
- Informe
- Escenario donde lista de Redis es adecuada:
    - Creación y carga de datos.
    - Consultas .
    - Gestión (agregar, recuperar y eliminar datos).
    - Simulación del flujo completo.

4.1.3:
- Informe
- 3 claves con TTL distinto:
    - Justificar tiempo elegido.
    - Verificador de tiempo restante.
    - Mensajes que simulen el sistema.

4.2:
- Informe
- Elegir mongo en la nube o en Docker y documentar pasos de config, string de conexión, y problemas.

4.2.1:
- Informe
- Dos colecciones de docs:
    - Decisiones de diseño (preguntas).

4.2.2:
- Informe
- Insercion de documentos.
- Consultas con filtros en diferentes campos.
- Proyecciones.
- Actualización.
- Eliminación condicional.

4.2.3:
- Informe
- 2 pipelines de agregacion:
    - Explicar cada etapa (al menos 3) y que transformación realiza.
- Reflexion comparativa PostgreSQL, SparkSQL y MongoDB

Entrega:
- Archivo README para reproducir el entorno

### Decisiones de diseño:

- El genero de los pacientes es el asignado al nacer.
- Cada médico trabaja en una única especialidad en particular (por más de que pueda tener más de una).
- Solo se atienden pacientes que tengan CUIL.
- Habría que agregar más?


### Restricciones (pendientes):

- No puede utilizarse un consultorio para dos turnos al mismo tiempo (se asume que cada turno dura 30 minutos). X
- La fecha de nacimiento de un paciente no puede superar la fecha actual. X  
- Los médicos tienen una fecha de nacimiento tal que tienen más de 18 años. X
- Un paciente o un médico no pueden tener un turno antes de nacer. X
- Todas las operaciones deben tener un único "cirujano principal". X
- Los turnos y operaciones deben ocurrir después que el turno que lo solicitó. X
- Los sueldos de los médicos y los costos de la consulta no pueden ser negativos. X
- Un medico no puede supervisarse a si mismo. X
- La supervisión tiene forma de arbol?. 
- Si un turno es programado, su fecha es posterior a la actual, si es cancelado nada, si es realizado debe ser previa a la actual. X
- Un medico solo tiene un rol en cada operación. (ya esta cumplida al no hacer que rol forme parte de la clave de medico_operacion). X
- Un medico no puede operarse a si mismo. X
- Un medico o paciente no puede tener dos turnos al mismo tiempo. X

### Posibles funciones ventana

- Ranking de médicos que hicieron más operaciones para darle un bonus (parece fácil de hacer con group by).
- De cada paciente se quiere saber el primer y útlimo turno.
- Ranking de quienes fueron los clientes que más costos tuvieron en sus consultas.
- Cuantos dias pasaron desde la ultima consulta del cliente. X

Ya tenía hecho esto:

- Para cada turno que tuvo un paciente, mostrar la fecha de su turno anterior y los días que hubo de diferencia.
- Ranking de médicos más solicitados de cada especialidad, según la cantidad de turnos atendidos.
- Ranking de médicos que recetaron la mayor cantidad de medicamentos con efectos secundarios de gravedad alta.

Podría agregar el de primer y último turno de cada paciente.

### Posibles TTL:

- Sesión de una persona en la página web del hospital
- Sesión del médico en la computadora de un consultorio
- Reserva temporal de un turno:
