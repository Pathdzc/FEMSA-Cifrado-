# Modelo de datos del proyecto (SQLite)
-- Ver explicación en docs/modelo_datos.md
PRAGMA foreign_keys = ON;

#CARGAS: un registro cada vez que se sube un archivo
CREATE TABLE IF NOT EXISTS cargas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_carga     TEXT    NOT NULL,  # fecha y hora de la carga (AAAA-MM-DD HH:MM:SS)
    nombre_archivo  TEXT    NOT NULL,  #solo el nombre, no la ruta
    hash_archivo    TEXT    NOT NULL,  #SHA-256 del archivo original
    total_filas     INTEGER NOT NULL,
    hash_anterior   TEXT,               --hash de la carga anterior (historial encadenado)
    hash_carga      TEXT               --hash de esta carga
);

#EQUIPOS: los datos TAL COMO VINIERON en cada carga.
#Es la evidencia: nunca se modifica, solo se agregan registros.
#Todo es texto para guardar los valores exactamente como llegaron.
CREATE TABLE IF NOT EXISTS equipos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    carga_id              INTEGER NOT NULL REFERENCES cargas(id),
    equipo_id             TEXT,
    usuario_id            TEXT,
    pais                  TEXT,
    region                TEXT,
    sistema_operativo     TEXT,
    version_so            TEXT,
    estado_tpm            TEXT,
    encryption_readiness  TEXT,
    estado_cifrado        TEXT,
    detalle_cifrado       TEXT,   #columna original: "Tecnología de cifrado State"
    estado_cumplimiento   TEXT,
    categoria_equipo      TEXT,
    clase_equipo          TEXT,
    perfil_privilegio     TEXT,
    antiguedad_meses      TEXT,
    banda_antiguedad      TEXT,
    estado_cuenta         TEXT,
    mes_ultimo_logon      TEXT,
    banda_recencia        TEXT,
    estado_hardware       TEXT,
    tipo_red              TEXT,
    fuente_datos          TEXT,
    en_mdm                TEXT,
    en_ad                 TEXT,
    en_macos              TEXT
);

#RESULTADOS: cada regla evaluada sobre cada equipo
#Se guardan TODAS las evaluaciones, no solo las fallas:
--así se demuestra que se revisó el 100% de los equipos.
CREATE TABLE IF NOT EXISTS resultados (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    carga_id     INTEGER NOT NULL REFERENCES cargas(id),
    equipo_ref   INTEGER NOT NULL REFERENCES equipos(id),
    regla        TEXT    NOT NULL,   #nombre de la regla evaluada
    cumple       TEXT    NOT NULL,   --Sí / No/ Sin información
    detalle      TEXT,               --por qué cumple o no cumple
    severidad    TEXT                --Alta / Media / Baja (solo si no cumple)
);

#REPORTES: cada PDF generado
CREATE TABLE IF NOT EXISTS reportes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    carga_id          INTEGER NOT NULL REFERENCES cargas(id),
    fecha_generacion  TEXT    NOT NULL,
    alcance           TEXT    NOT NULL,   -- país o "Todos"
    hash_pdf          TEXT    NOT NULL,   -- SHA-256 del PDF
    firma             TEXT    NOT NULL    -- firma digital del hash
);

# Índices para que las consultas por carga sean rápidas
CREATE INDEX IF NOT EXISTS idx_equipos_carga    ON equipos(carga_id);
CREATE INDEX IF NOT EXISTS idx_resultados_carga ON resultados(carga_id);
