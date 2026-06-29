# BBDDtpG10

Trabajo Práctico grupal de **Introducción a Bases de Datos**.

## Requisitos

- Java 17.0.19
- Docker 29.5.3
- Python 3.12.7

## Dependencias Python

Las dependencias utilizadas en los notebooks y scripts son:

- pandas 2.3.3
- redis 8.0.0
- pymongo 3.12.0
- python-dotenv 1.2.2
- pyspark 4.1.2
- Faker 40.23.0

Para instalar las dependencias necesarias especificamente para el script de poblado de datos:

```bash
pip install -r requirements.txt
```


## Poblado de datos

El poblado de datos se genera mediante el script:

```bash
./scripts/generar_poblado.py
```

El script no requiere argumentos. Por defecto toma la configuración desde:

```text
config/default_config.json
```

A partir de esa configuración genera los archivos SQL.

## PostgreSQL

La conexión a PostgreSQL puede realizarse desde pgAdmin con los datos definidos en `docker-compose.yml`.

En el flujo normal, primero se ejecuta el script de creación de tablas y luego el script de poblado generado:

```text
sql/01_creacion_de_tablas.sql
sql/02_populado_datos.sql
```
