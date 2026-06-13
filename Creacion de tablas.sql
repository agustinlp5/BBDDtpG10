DROP TABLE IF EXISTS medico CASCADE;
DROP TABLE IF EXISTS obra_social CASCADE;
DROP TABLE IF EXISTS paciente CASCADE;
DROP TABLE IF EXISTS consultorio CASCADE;
DROP TABLE IF EXISTS turno CASCADE;
DROP TABLE IF EXISTS operacion CASCADE;
DROP TABLE IF EXISTS estudio CASCADE;
DROP TABLE IF EXISTS medicamento CASCADE;
DROP TABLE IF EXISTS efecto_secundario CASCADE;
DROP TABLE IF EXISTS medicamento_efecto CASCADE;
DROP TABLE IF EXISTS medico_operacion CASCADE;

CREATE TABLE medico (
 	legajo VARCHAR(20) PRIMARY KEY,
 	nombre VARCHAR(20),
	apellido VARCHAR(20),
	dni CHAR(8),
	mail VARCHAR(100),
	telefono VARCHAR(20),
	salario DECIMAL(10,2), --usamos decimal en vez de float porque no queremos errores, como mucho llega a 8 cifras y 2 decimales (10 millones)
	fecha_nacimiento DATE,
	especialidad VARCHAR(100),
	legajo_supervisor VARCHAR(20),
	FOREIGN KEY (legajo_supervisor) REFERENCES medico(legajo)
);

CREATE TABLE obra_social (
	id_obra  SERIAL PRIMARY KEY, -- SERIAL crea id sin tener que aclararlo
	nombre_obra VARCHAR(30)
);

CREATE TABLE paciente(
	id_paciente serial PRIMARY KEY,
 	nombre VARCHAR(20),
	apellido VARCHAR(20),
	dni CHAR(8),
	mail VARCHAR(100),
	telefono VARCHAR(20),
	fecha_nacimiento DATE,
	genero VARCHAR(10) CHECK (genero in('hombre','mujer')),
	grupo_sanguineo VARCHAR(10) CHECK (grupo_sanguineo in('A+','A-','B+','B-','AB+','AB-','O+','O-')),
	riesgo VARCHAR(30) CHECK(riesgo in('diabetes','obesidad','embarazo','enfermedad cardiaca','enfermedad respiratoria','inmunocomprometido','mayor de edad')),
	id_obra SERIAL,
	FOREIGN KEY (id_obra) REFERENCES obra_social(id_obra)
);

CREATE TABLE consultorio (
	numero_consultorio INTEGER PRIMARY KEY,
	piso INT,
	ala VARCHAR(5) CHECK (Ala IN ('este','centro','oeste'))
);

CREATE TABLE turno (
	id_turno SERIAL PRIMARY KEY,
	diagnostico VARCHAR (30),
	costo DECIMAL(8,2), --entre 70.000 a 8.000
	fecha DATE,
	hora TIME,
	estado VARCHAR(20) CHECK (estado in ('programado', 'realizado', 'cancelado')),
	id_paciente SERIAL,
	legajo VARCHAR(20),
	FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
	FOREIGN KEY (legajo) REFERENCES medico(legajo)
);

CREATE TABLE operacion(
	id_operacion SERIAL PRIMARY KEY,
	nombre_operacion VARCHAR(100),
	complejidad VARCHAR(10) CHECK (complejidad IN ('alta','media','baja')),
	fecha DATE,
	id_turno SERIAL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE estudio(
	id_estudio SERIAL PRIMARY KEY,
	nombre_estudio VARCHAR(100),
	fecha DATE,
	id_turno SERIAL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);
	
CREATE TABLE medicamento(
	id_medicamento SERIAL PRIMARY KEY,
	nombre_medicamento VARCHAR(100),
	dosis VARCHAR(20), --necesito poder aclarar gramos, miligramos, etc
	id_turno SERIAL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE efecto_secundario(
	id_efecto SERIAL PRIMARY KEY,
	nombre_efecto VARCHAR(100),
	gravedad VARCHAR(30) CHECK (gravedad IN ('alta','media','baja'))
);

CREATE TABLE medicamento_efecto (
	id_efecto SERIAL,
	id_medicamento SERIAL,
	FOREIGN KEY (id_efecto) REFERENCES efecto_secundario(id_efecto),
	FOREIGN KEY (id_medicamento) REFERENCES medicamento(id_medicamento)
);

CREATE TABLE medico_operacion(
	legajo VARCHAR(20),
	id_operacion SERIAL,
	rol_medico VARCHAR(20) CHECK (rol_medico in ('cirujano principal', 'ayudante de cirugia', 'instrumentista','anestesiólogo')),
	FOREIGN KEY (legajo) REFERENCES medico(legajo),
	FOREIGN KEY (id_operacion) REFERENCES operacion(id_operacion)
);

