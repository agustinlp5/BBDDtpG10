DROP TABLE IF EXISTS persona CASCADE;
DROP TABLE IF EXISTS medico CASCADE;
DROP TABLE IF EXISTS obra_social CASCADE;
DROP TABLE IF EXISTS paciente CASCADE;
DROP TABLE IF EXISTS riesgo CASCADE;
DROP TABLE IF EXISTS paciente_riesgo CASCADE;
DROP TABLE IF EXISTS consultorio CASCADE;
DROP TABLE IF EXISTS turno CASCADE;
DROP TABLE IF EXISTS operacion CASCADE;
DROP TABLE IF EXISTS estudio CASCADE;
DROP TABLE IF EXISTS medicamento CASCADE;
DROP TABLE IF EXISTS efecto_secundario CASCADE;
DROP TABLE IF EXISTS turno_medicamento CASCADE;
DROP TABLE IF EXISTS medicamento_efecto CASCADE;
DROP TABLE IF EXISTS medico_operacion CASCADE;


CREATE TABLE persona (
	cuil CHAR(11) PRIMARY KEY,
	nombre VARCHAR(100) NOT NULL,
	apellido VARCHAR(100) NOT NULL,
	mail VARCHAR(100),
	telefono VARCHAR(20),
	fecha_nacimiento DATE CHECK (fecha_nacimiento <= CURRENT_DATE)
	);

CREATE TABLE medico (
	cuil CHAR(11) PRIMARY KEY,
	salario DECIMAL(10,2) CHECK (salario >= 0),
	cuil_supervisor CHAR(11),
	especialidad VARCHAR(100) NOT NULL,
	FOREIGN KEY (cuil) REFERENCES persona(cuil),
	FOREIGN KEY (cuil_supervisor) REFERENCES medico(cuil),
	CHECK (cuil <> cuil_supervisor)
);

CREATE TABLE obra_social (
	id_obra  SERIAL PRIMARY KEY, -- SERIAL crea id sin tener que aclararlo
	nombre_obra VARCHAR(30) NOT NULL
);

CREATE TABLE paciente(
	cuil CHAR(11) PRIMARY KEY,
	genero VARCHAR(10) CHECK (genero in('hombre','mujer')),
	grupo_sanguineo VARCHAR(10) CHECK (grupo_sanguineo in('A+','A-','B+','B-','AB+','AB-','O+','O-')),
	id_obra INTEGER,
	FOREIGN KEY (cuil) REFERENCES persona(cuil),
	FOREIGN KEY (id_obra) REFERENCES obra_social(id_obra)
);

CREATE TABLE riesgo(
	id_riesgo SERIAL PRIMARY KEY,
	nombre_riesgo VARCHAR(30) CHECK(nombre_riesgo in('diabetes','obesidad','embarazo','enfermedad cardiaca','enfermedad respiratoria','inmunocomprometido','mayor de edad'))
);

CREATE TABLE paciente_riesgo(
	cuil_paciente CHAR(11),
	id_riesgo INTEGER,
	FOREIGN KEY (cuil_paciente) REFERENCES paciente(cuil),
	FOREIGN KEY (id_riesgo) REFERENCES riesgo(id_riesgo),
	PRIMARY KEY(cuil_paciente,id_riesgo)
);

CREATE TABLE consultorio (
	numero_consultorio INTEGER PRIMARY KEY,
	piso INTEGER,
	ala VARCHAR(5) CHECK (ala IN ('este','centro','oeste'))
);

CREATE TABLE turno (
	id_turno SERIAL PRIMARY KEY,
	diagnostico VARCHAR (30),
	costo DECIMAL(8,2)CHECK (costo >= 0),
	fecha_turno DATE NOT NULL,
	hora_turno TIME NOT NULL,
	estado VARCHAR(20) CHECK (estado in ('programado', 'realizado', 'cancelado')),
	cuil_paciente CHAR(11) NOT NULL,
	cuil_medico CHAR(11) NOT NULL,
	numero_consultorio INTEGER NOT NULL,
	FOREIGN KEY (cuil_paciente) REFERENCES paciente(cuil),
	FOREIGN KEY (cuil_medico) REFERENCES medico(cuil),
	FOREIGN KEY (numero_consultorio) REFERENCES consultorio(numero_consultorio)
);

CREATE TABLE operacion(
	id_operacion SERIAL PRIMARY KEY,
	nombre_operacion VARCHAR(100) NOT NULL,
	complejidad VARCHAR(10) CHECK (complejidad IN ('alta','media','baja')),
	fecha_operacion DATE NOT NULL,
	id_turno INTEGER UNIQUE NOT NULL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE estudio(
	id_estudio SERIAL PRIMARY KEY,
	nombre_estudio VARCHAR(100),
	fecha_estudio DATE NOT NULL,
	id_turno INTEGER NOT NULL,
	FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);
	
CREATE TABLE medicamento(
	id_medicamento SERIAL PRIMARY KEY,
	nombre_medicamento VARCHAR(100)
);

CREATE TABLE efecto_secundario(
	id_efecto SERIAL PRIMARY KEY,
	nombre_efecto VARCHAR(100) NOT NULL UNIQUE,
	gravedad VARCHAR(30) CHECK (gravedad IN ('alta','media','baja'))
);

CREATE TABLE turno_medicamento (
	id_turno INTEGER,
	id_medicamento INTEGER,
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
	cuil CHAR(11),
	id_operacion INTEGER NOT NULL,
	rol_medico VARCHAR(20) CHECK (rol_medico in ('cirujano principal', 'ayudante de cirugia', 'instrumentista','anestesiólogo')) NOT NULL,
	FOREIGN KEY (cuil) REFERENCES medico(cuil),
	FOREIGN KEY (id_operacion) REFERENCES operacion(id_operacion),
	PRIMARY KEY (cuil, id_operacion)
);
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_fecha_turno()
RETURNS TRIGGER AS $$
DECLARE
    fecha_nac_med DATE;
	fecha_nac_pac DATE;
BEGIN
    SELECT fecha_nacimiento
    INTO fecha_nac_med
    FROM persona per
    WHERE per.cuil = NEW.cuil_medico;
	   
	SELECT fecha_nacimiento
    INTO fecha_nac_pac
    FROM persona per
    WHERE per.cuil = NEW.cuil_paciente;

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
CREATE OR REPLACE FUNCTION validar_medicos_mayores()
RETURNS TRIGGER AS $$
DECLARE
    fecha_nac_med DATE;
BEGIN
    SELECT fecha_nacimiento
    INTO fecha_nac_med
    FROM persona per
    WHERE per.cuil = NEW.cuil;

    IF fecha_nac_med > CURRENT_DATE - INTERVAL '18 years' THEN
        RAISE EXCEPTION 'El médico debe ser mayor de edad';

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_medicos_mayores
BEFORE INSERT OR UPDATE ON medico
FOR EACH ROW
EXECUTE FUNCTION validar_medicos_mayores();
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_operacion_mismo()
RETURNS TRIGGER AS $$
DECLARE
	id_pac CHAR(11);
BEGIN	
	SELECT tu.cuil_paciente
	INTO id_pac
	FROM operacion op
	JOIN turno tu ON op.id_turno = tu.id_turno
	WHERE op.id_operacion = NEW.id_operacion;

	IF id_pac = NEW.cuil THEN
		RAISE EXCEPTION 'Un medico no puede operarse a si mismo';
	END IF;
	
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_operacion_mismo
BEFORE INSERT OR UPDATE ON medico_operacion
FOR EACH ROW
EXECUTE FUNCTION validar_operacion_mismo();
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

CREATE OR REPLACE FUNCTION validar_fecha_operacion_post_turno()
RETURNS TRIGGER AS $$
DECLARE
    fecha_t DATE;
BEGIN
    SELECT fecha_turno
    INTO fecha_t -- tomo el resultado del SELECT y lo guardo en una variable
    FROM turno turno
    WHERE turno.id_turno = NEW.id_turno;

    IF NEW.fecha_operacion < fecha_t THEN
        RAISE EXCEPTION 'La fecha no puede ser anterior al turno que la receto';
	END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_operacion_post_turno
BEFORE INSERT OR UPDATE ON operacion
FOR EACH ROW
EXECUTE FUNCTION validar_fecha_operacion_post_turno();
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_fecha_estudio_post_turno()
RETURNS TRIGGER AS $$
DECLARE
    fecha_t DATE;
BEGIN
    SELECT fecha_turno
    INTO fecha_t -- tomo el resultado del SELECT y lo guardo en una variable
    FROM turno turno
    WHERE turno.id_turno = NEW.id_turno;

    IF NEW.fecha_estudio< fecha_t THEN
        RAISE EXCEPTION 'La fecha no puede ser anterior al turno que la receto';
	END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_validar_estudio_post_turno
BEFORE INSERT OR UPDATE ON estudio
FOR EACH ROW
EXECUTE FUNCTION validar_fecha_estudio_post_turno();
-------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION validar_estado_turno()
RETURNS TRIGGER AS $$
BEGIN

    IF NEW.estado = 'programado' AND (NEW.fecha_turno < CURRENT_DATE OR (NEW.fecha_turno = CURRENT_DATE AND NEW.hora_turno < CURRENT_TIME)) THEN
        RAISE EXCEPTION 'Un turno programado debe ser posterior a hoy';

    ELSIF NEW.estado = 'realizado' AND (NEW.fecha > CURRENT_DATE OR (NEW.fecha_turno = CURRENT_DATE AND NEW.hora_turno > CURRENT_TIME)) THEN
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

CREATE OR REPLACE FUNCTION validar_solapamiento_consultorio()
RETURNS TRIGGER AS $$
DECLARE
    conflicto INT;
BEGIN

    SELECT COUNT(*)
    INTO conflicto
    FROM turno t
    WHERE t.numero_consultorio = NEW.numero_consultorio
      AND t.fecha_turno = NEW.fecha_turno
      AND t.id_turno <> NEW.id_turno
	  AND t.estado <> 'cancelado'	
      AND (NEW.hora_turno < (t.hora_turno + INTERVAL '30 minutes') AND (NEW.hora_turno + INTERVAL '30 minutes') > t.hora_turno);

    IF conflicto > 0 THEN
        RAISE EXCEPTION 'El consultorio ya está ocupado en ese horario';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_no_solapamiento_consultorio
BEFORE INSERT OR UPDATE ON turno
FOR EACH ROW
EXECUTE FUNCTION validar_solapamiento_consultorio();

-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validar_solapamiento_persona()
RETURNS TRIGGER AS $$
DECLARE
    conflicto INT;
BEGIN

    SELECT COUNT(*)
    INTO conflicto
    FROM turno t
    WHERE (t.cuil_paciente = NEW.cuil_paciente OR t.cuil_medico = NEW.cuil_medico)
      AND t.fecha_turno = NEW.fecha_turno
      AND t.id_turno <> NEW.id_turno
	  AND t.estado <> 'cancelado'
      AND (NEW.hora_turno < (t.hora_turno + INTERVAL '30 minutes') AND (NEW.hora_turno + INTERVAL '30 minutes') > t.hora_turno);

    IF conflicto > 0 THEN
        RAISE EXCEPTION 'El medico o el paciente ya tienen un turno en ese horario';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_no_solapamiento_persona
BEFORE INSERT OR UPDATE ON turno
FOR EACH ROW
EXECUTE FUNCTION validar_solapamiento_persona();

