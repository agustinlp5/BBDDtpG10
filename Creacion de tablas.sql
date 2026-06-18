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
DROP TABLE IF EXISTS turno_medicamento CASCADE;

CREATE TABLE medico (
 	legajo VARCHAR(20) PRIMARY KEY,
 	nombre VARCHAR(100) NOT NULL,
	apellido VARCHAR(100) NOT NULL,
	dni CHAR(8) NOT NULL,
	mail VARCHAR(100),
	telefono VARCHAR(20),
	salario DECIMAL(10,2) CHECK (salario >= 0), --usamos decimal en vez de float porque no queremos errores, como mucho llega a 8 cifras y 2 decimales (10 millones)
	fecha_nacimiento DATE CHECK (fecha_nacimiento <= CURRENT_DATE - INTERVAL '18 years'), --cuidado con el check, solo se ejecuta en la creacion
	especialidad VARCHAR(100) NOT NULL,
	legajo_supervisor VARCHAR(20),
	FOREIGN KEY (legajo_supervisor) REFERENCES medico(legajo),
	CHECK (legajo <> legajo_supervisor)
);

CREATE TABLE obra_social (
	id_obra  SERIAL PRIMARY KEY, -- SERIAL crea id sin tener que aclararlo
	nombre_obra VARCHAR(30) NOT NULL
);

CREATE TABLE paciente(
	id_paciente SERIAL PRIMARY KEY,
 	nombre VARCHAR(100) NOT NULL,
	apellido VARCHAR(100) NOT NULL,
	dni CHAR(8) NOT NULL,
	mail VARCHAR(100),
	telefono VARCHAR(20),
	fecha_nacimiento DATE CHECK (fecha_nacimiento <= CURRENT_DATE),
	genero VARCHAR(10) CHECK (genero in('hombre','mujer')),
	grupo_sanguineo VARCHAR(10) CHECK (grupo_sanguineo in('A+','A-','B+','B-','AB+','AB-','O+','O-')),
	riesgo VARCHAR(30) CHECK(riesgo in('diabetes','obesidad','embarazo','enfermedad cardiaca','enfermedad respiratoria','inmunocomprometido','mayor de edad')),
	id_obra INTEGER,
	FOREIGN KEY (id_obra) REFERENCES obra_social(id_obra)
);

CREATE TABLE consultorio (
	numero_consultorio INTEGER PRIMARY KEY,
	piso INT,
	ala VARCHAR(5) CHECK (ala IN ('este','centro','oeste'))
);

CREATE TABLE turno (
	id_turno SERIAL PRIMARY KEY,
	diagnostico VARCHAR (30),
	costo DECIMAL(8,2)CHECK (costo >= 0),
	fecha DATE NOT NULL,
	hora TIME NOT NULL,
	estado VARCHAR(20) CHECK (estado in ('programado', 'realizado', 'cancelado')),
	id_paciente INTEGER NOT NULL,
	legajo VARCHAR(20) NOT NULL,
	numero_consultorio INTEGER NOT NULL,
	FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
	FOREIGN KEY (legajo) REFERENCES medico(legajo),
	FOREIGN KEY (numero_consultorio) REFERENCES consultorio(numero_consultorio)
);

CREATE TABLE operacion(
	id_operacion SERIAL PRIMARY KEY,
	nombre_operacion VARCHAR(100) NOT NULL,
	complejidad VARCHAR(10) CHECK (complejidad IN ('alta','media','baja')),
	fecha DATE NOT NULL,
	id_turno INTEGER NOT NULL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE estudio(
	id_estudio SERIAL PRIMARY KEY,
	nombre_estudio VARCHAR(100),
	fecha DATE NOT NULL,
	id_turno INTEGER NOT NULL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);
	
CREATE TABLE medicamento(
	id_medicamento SERIAL PRIMARY KEY,
	nombre_medicamento VARCHAR(100),
	id_turno INTEGER NOT NULL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE efecto_secundario(
	id_efecto SERIAL PRIMARY KEY,
	nombre_efecto VARCHAR(100) NOT NULL UNIQUE,
	gravedad VARCHAR(30) CHECK (gravedad IN ('alta','media','baja'))
);

CREATE TABLE turno_medicamento (
	id_turno INTEGER,
	id_medicamento INTEGER,
	-- dosis VARCHAR(20) NOT NULL, --necesito poder aclarar gramos, miligramos, etc
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
	FOREIGN KEY (id_medicamento) REFERENCES medicamento(id_medicamento),
	PRIMARY KEY (id_turno, id_medicamento)
);

CREATE TABLE medicamento_efecto (
	id_efecto INTEGER,
	id_medicamento INTEGER,
	FOREIGN KEY (id_efecto) REFERENCES efecto_secundario(id_efecto),
	FOREIGN KEY (id_medicamento) REFERENCES medicamento(id_medicamento),
	PRIMARY KEY (id_efecto, id_medicamento)
);

CREATE TABLE medico_operacion(
	legajo VARCHAR(20),
	id_operacion INTEGER NOT NULL,
	rol_medico VARCHAR(20) CHECK (rol_medico in ('cirujano principal', 'ayudante de cirugia', 'instrumentista','anestesiólogo')) NOT NULL,
	FOREIGN KEY (legajo) REFERENCES medico(legajo),
	FOREIGN KEY (id_operacion) REFERENCES operacion(id_operacion),
	PRIMARY KEY (legajo, id_operacion)
);
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_fecha_turno()
RETURNS TRIGGER AS $$
DECLARE
    fecha_nac_med DATE;
	fecha_nac_pac DATE;
BEGIN
    SELECT fecha_nacimiento
    INTO fecha_nac_med -- tomo el resultado del SELECT y lo guardo en una variable
    FROM medico med
    WHERE med.legajo = NEW.legajo;
	   
	SELECT fecha_nacimiento
    INTO fecha_nac_pac-- tomo el resultado del SELECT y lo guardo en una variable
    FROM paciente pac
    WHERE pac.id_paciente = NEW.id_paciente;

    IF NEW.fecha < fecha_nac_med THEN
        RAISE EXCEPTION 'El turno no puede ser anterior al nacimiento del médico';
	
	ELSIF NEW.fecha < fecha_nac_pac THEN
		RAISE EXCEPTION 'El turno no puede ser anterior al nacimiento del paciente';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_turno_fecha
BEFORE INSERT OR UPDATE ON turno
FOR EACH ROW
EXECUTE FUNCTION validar_fecha_turno();

-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_cirujano_principal()
RETURNS TRIGGER AS $$
DECLARE
    cantidad INTEGER;
    op INTEGER;
BEGIN

    -- detectar la operación afectada
    op := COALESCE(NEW.id_operacion, OLD.id_operacion); -- NEW.id_operacion si no es null, si no OLD.id_operacion

    -- contar cirujanos principales en esa operación
    SELECT COUNT(*)
    INTO cantidad
    FROM medico_operacion
    WHERE id_operacion = op
      AND rol_medico = 'cirujano principal';

    -- si después del cambio queda en 0 → error
    IF cantidad = 0 THEN
        RAISE EXCEPTION 'La operación % debe tener al menos un cirujano principal', op;
	ELSIF cantidad > 1 THEN
		RAISE EXCEPTION 'La operación % debe tener un único cirujano principal', op;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cirujano_principal
AFTER INSERT OR UPDATE OR DELETE ON medico_operacion
FOR EACH ROW
EXECUTE FUNCTION validar_cirujano_principal();

-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_fecha_post_turno()
RETURNS TRIGGER AS $$
DECLARE
    fecha_turno DATE;
BEGIN
    SELECT fecha
    INTO fecha_turno -- tomo el resultado del SELECT y lo guardo en una variable
    FROM turno turno
    WHERE turno.id_turno = NEW.id_turno;

    IF NEW.fecha < fecha_turno THEN
        RAISE EXCEPTION 'La fecha no puede ser anterior al turno que la receto';
	END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_operacion_post_turno
BEFORE INSERT OR UPDATE ON operacion
FOR EACH ROW
EXECUTE FUNCTION validar_fecha_post_turno();

CREATE TRIGGER trg_validar_estudio_post_turno
BEFORE INSERT OR UPDATE ON estudio
FOR EACH ROW
EXECUTE FUNCTION validar_fecha_post_turno();
-------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION validar_estado_turno()
RETURNS TRIGGER AS $$
BEGIN

    IF NEW.estado = 'programado' AND (NEW.fecha < CURRENT_DATE OR (NEW.fecha = CURRENT_DATE AND NEW.hora < CURRENT_TIME)) THEN
        RAISE EXCEPTION 'Un turno programado debe ser posterior a hoy';

    ELSIF NEW.estado = 'realizado' AND (NEW.fecha > CURRENT_DATE OR (NEW.fecha = CURRENT_DATE AND NEW.hora > CURRENT_TIME)) THEN
        RAISE EXCEPTION 'Un turno realizado debe ser anterior a hoy';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validar_estado_turno
BEFORE INSERT OR UPDATE ON turno
FOR EACH ROW
EXECUTE FUNCTION validar_estado_turno();
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_solapamiento()
RETURNS TRIGGER AS $$
DECLARE
    conflicto INT;
BEGIN

    SELECT COUNT(*)
    INTO conflicto
    FROM turno t
    WHERE t.numero_consultorio = NEW.numero_consultorio
      AND t.fecha = NEW.fecha
      AND t.id_turno <> NEW.id_turno
      AND (NEW.hora < (t.hora + INTERVAL '30 minutes') AND (NEW.hora + interval '30 minutes') > t.hora);

    IF conflicto > 0 THEN
        RAISE EXCEPTION 'El consultorio ya está ocupado en ese horario';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_no_solapamiento
BEFORE INSERT OR UPDATE ON turno
FOR EACH ROW
EXECUTE FUNCTION validar_solapamiento();
