# BBDDtpG10
Trabajo práctico BBDD

## To Do List:

1.1:
- Agregar lo que haya que agregar al DER para hacer el resto del tp (tal vez no hace falta)

- Informe DER y consigna.
- Informe decisiones de diseño. X
- Informe Restricciones. X

1.2:
- Informe
- Implementar Restricciones. X

1.3:
- Informe
- Poblar base.
- Validar consistencia.

2.1: X
- ventanas: tal vez pusimos consultas de más? (no c si la 3 aporta mucho)

2.2:
- Informe
- Funciones estadisticas:
    - C1.
    - C2.
    - C3.
    - Consulta con CTE. X

2.3:
- Hacer EXPLAIN / EXPLAIN ANALYZE a una consulta *COMPLEJA*.
- Analizar plan de ejecución.
- Proponer mejora (indices/ cambiar consulta).
- Comparar y explicar diferencias.

3.1:
- Informe X
- 3 procesos con MapReduce: X
    - Describir pregunta. X
    - Explicitar Map. X
    - Explicitar Reduce. X
    - Mostrar resultados.
- explicar transformaciones lazy X

4.1.1: 
- Informe X
- 3 tipos de datos que almacenar como clave-valor simples/hashes: 2/3
    - Código de carga de datos. X
    - Consultas de valores específicos. X
    - Actualizar y verificar un campo. X
    - Explicar por qué Redis es mejor que PostgreSQL en este caso. X

4.1.2:
- Informe X
- Escenario donde lista de Redis es adecuada: X
    - Creación y carga de datos. X
    - Consultas. X
    - Gestión (agregar, recuperar y eliminar datos). X
    - Simulación del flujo completo. X

4.1.3:
- Informe X
- 3 claves con TTL distinto: X
    - Justificar tiempo elegido. X
    - Verificador de tiempo restante. X
    - Mensajes que simulen el sistema. X 

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



### Clave valor / hashes REDIS:

- HASH perfil de un paciente: clave es cuil, datos(genero, nombre, apellido, riesgos?) en un hash
- Estado actual de un turno (como el estado puede cambiar entre programado y cancelado, un medico o paciente puede querer saber el estado de su turno multiples veces)
- la sesion del usuario en la pagina web... pero desp lo ponemos en ttl

### Colas de REDIS:

- Cada consultorio tiene una lista de los pacientes que tienen un turno en ese consultorio, las lista contiene los cuils de forma que se hace un pop del primer elemento de la lista y luego se obtiene la informacion de ese paciente, y asi el médico por ejemplo puede llamar al siguiente paciente.

### Posibles TTL:

- Sesión de una persona en la página web del hospital  X
- Sesión del médico en la computadora de un consultorio X
- Reserva temporal de un turno (5-10 minutos) X


### MONGO:

- Como en los documentos quiero cosas opcionales, podría poner turnos, donde en el caso de turnos programados o cancelados, datos como el diagnostico son nulls (por lo que se pueden no poner) mientras que si aparecen en turnos ya realizados.
