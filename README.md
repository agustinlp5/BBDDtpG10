Requisitos:

- Java 17.0.19
- Docker 29.5.3
- Python 3.12.7


Dependencias Python:

- pandas 2.3.3
- redis 8.0.0 (cliente de Python para Redis)
- pymongo 3.12.0
- dotenv 1.2.2
- pyspark 4.1.2


Servicios:

- PostgreSQL 16 con PostGIS 3.4 (imagen Docker: postgis/postgis:16-3.4)
- Redis 7.2 (imagen Docker: redis:7.2-alpine)
- MongoDB Atlas (servicio en la nube)

Los dockers para PostgreSQL y Redis se utilizan como en clase.
El acceso a mongo es configurada mediante variables de entorno(.env)