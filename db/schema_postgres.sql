-- ========================================
-- SCHEMA POSTGRESQL - Sistema Climatot Almacén
-- ========================================
-- Conversión desde SQLite a PostgreSQL
-- Cambios principales:
--   - INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
--   - TEXT → VARCHAR o TEXT según necesidad
--   - REAL → NUMERIC para precisión decimal
--   - INTEGER (booleans) → SMALLINT (se mantiene para compatibilidad)
--   - date('now') → CURRENT_DATE
--   - datetime('now') → NOW()
-- ========================================

-- ========================================
-- USUARIOS Y SESIONES
-- ========================================
CREATE TABLE IF NOT EXISTS usuarios(
  usuario     VARCHAR(100) PRIMARY KEY,
  pass_hash   VARCHAR(255) NOT NULL,
  rol         VARCHAR(50) NOT NULL DEFAULT 'almacen',
  activo      SMALLINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sesiones(
  usuario         VARCHAR(100) NOT NULL,
  inicio_utc      BIGINT NOT NULL,
  ultimo_ping_utc BIGINT NOT NULL,
  hostname        VARCHAR(255) NOT NULL,
  PRIMARY KEY(usuario, hostname)
);

-- ========================================
-- MAESTROS: PROVEEDORES, OPERARIOS, ETC.
-- ========================================
CREATE TABLE IF NOT EXISTS proveedores(
  id       SERIAL PRIMARY KEY,
  nombre   VARCHAR(255) UNIQUE NOT NULL,
  telefono VARCHAR(50),
  contacto VARCHAR(255),
  email    VARCHAR(255),
  notas    TEXT
);

CREATE TABLE IF NOT EXISTS operarios(
  id           SERIAL PRIMARY KEY,
  nombre       VARCHAR(255) UNIQUE NOT NULL,
  rol_operario VARCHAR(50) NOT NULL DEFAULT 'ayudante',
  activo       SMALLINT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS familias(
  id     SERIAL PRIMARY KEY,
  nombre VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS ubicaciones(
  id     SERIAL PRIMARY KEY,
  nombre VARCHAR(255) UNIQUE NOT NULL
);

-- ========================================
-- ALMACENES Y FURGONETAS
-- ========================================
CREATE TABLE IF NOT EXISTS almacenes(
  id      SERIAL PRIMARY KEY,
  nombre  VARCHAR(255) UNIQUE NOT NULL,
  tipo    VARCHAR(50) DEFAULT 'almacen'
);

-- ========================================
-- ARTÍCULOS
-- ========================================
CREATE TABLE IF NOT EXISTS articulos(
  id                  SERIAL PRIMARY KEY,
  ean                 VARCHAR(50) UNIQUE,
  ref_proveedor       VARCHAR(100),
  nombre              VARCHAR(500) NOT NULL,
  palabras_clave      TEXT,
  u_medida            VARCHAR(50) DEFAULT 'unidad',
  min_alerta          NUMERIC(10,2) DEFAULT 0,
  ubicacion_id        INTEGER,
  proveedor_id        INTEGER,
  familia_id          INTEGER,
  marca               VARCHAR(255),
  coste               NUMERIC(10,2) DEFAULT 0,
  pvp_sin             NUMERIC(10,2) DEFAULT 0,
  iva                 NUMERIC(5,2) DEFAULT 21,
  activo              SMALLINT NOT NULL DEFAULT 1,
  FOREIGN KEY(ubicacion_id)  REFERENCES ubicaciones(id),
  FOREIGN KEY(proveedor_id)  REFERENCES proveedores(id),
  FOREIGN KEY(familia_id)    REFERENCES familias(id)
);

-- ========================================
-- MOVIMIENTOS
-- ========================================
CREATE TABLE IF NOT EXISTS movimientos(
  id          SERIAL PRIMARY KEY,
  fecha       DATE NOT NULL,
  tipo        VARCHAR(20) NOT NULL CHECK(tipo IN ('ENTRADA','TRASPASO','IMPUTACION','PERDIDA','DEVOLUCION')),
  origen_id   INTEGER,
  destino_id  INTEGER,
  articulo_id INTEGER NOT NULL,
  cantidad    NUMERIC(10,2) NOT NULL,
  coste_unit  NUMERIC(10,2),
  motivo      TEXT,
  ot          VARCHAR(100),
  operario_id INTEGER,
  responsable VARCHAR(100),
  albaran     VARCHAR(100),
  FOREIGN KEY(origen_id)   REFERENCES almacenes(id),
  FOREIGN KEY(destino_id)  REFERENCES almacenes(id),
  FOREIGN KEY(articulo_id) REFERENCES articulos(id),
  FOREIGN KEY(operario_id) REFERENCES operarios(id)
);

-- ========================================
-- ALBARANES
-- ========================================
CREATE TABLE IF NOT EXISTS albaranes(
  albaran      VARCHAR(100) PRIMARY KEY,
  proveedor_id INTEGER,
  fecha        DATE NOT NULL,
  FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
);

-- ========================================
-- ASIGNACIONES FURGONETA-OPERARIO
-- ========================================
CREATE TABLE IF NOT EXISTS asignaciones_furgoneta(
  operario_id   INTEGER NOT NULL,
  fecha         DATE NOT NULL,
  turno         VARCHAR(20),
  furgoneta_id  INTEGER NOT NULL,
  PRIMARY KEY (fecha, turno, furgoneta_id),
  FOREIGN KEY(operario_id)   REFERENCES operarios(id),
  FOREIGN KEY(furgoneta_id)  REFERENCES almacenes(id)
);

-- ========================================
-- INVENTARIOS FÍSICOS
-- ========================================
CREATE TABLE IF NOT EXISTS inventarios(
  id           SERIAL PRIMARY KEY,
  fecha        DATE NOT NULL,
  responsable  VARCHAR(100) NOT NULL,
  almacen_id   INTEGER,
  observaciones TEXT,
  estado       VARCHAR(20) NOT NULL DEFAULT 'EN_PROCESO' CHECK(estado IN ('EN_PROCESO','FINALIZADO')),
  fecha_cierre DATE,
  FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
);

CREATE TABLE IF NOT EXISTS inventario_detalle(
  id              SERIAL PRIMARY KEY,
  inventario_id   INTEGER NOT NULL,
  articulo_id     INTEGER NOT NULL,
  stock_teorico   NUMERIC(10,2) NOT NULL DEFAULT 0,
  stock_contado   NUMERIC(10,2) NOT NULL DEFAULT 0,
  diferencia      NUMERIC(10,2) NOT NULL DEFAULT 0,
  FOREIGN KEY(inventario_id) REFERENCES inventarios(id) ON DELETE CASCADE,
  FOREIGN KEY(articulo_id) REFERENCES articulos(id)
);

-- ========================================
-- TABLAS ADICIONALES (NOTIFICACIONES, HISTORIAL, ETC.)
-- ========================================
-- Añadir aquí otras tablas si existen en tu SQLite
-- Por ejemplo: notificaciones, historial, furgonetas, etc.

CREATE TABLE IF NOT EXISTS furgonetas(
  id          SERIAL PRIMARY KEY,
  matricula   VARCHAR(20) UNIQUE NOT NULL,
  nombre      VARCHAR(255),
  almacen_id  INTEGER,
  activa      SMALLINT NOT NULL DEFAULT 1,
  FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
);

CREATE TABLE IF NOT EXISTS notificaciones(
  id          SERIAL PRIMARY KEY,
  usuario     VARCHAR(100) NOT NULL,
  tipo        VARCHAR(50) NOT NULL,
  titulo      VARCHAR(255) NOT NULL,
  mensaje     TEXT,
  leido       SMALLINT NOT NULL DEFAULT 0,
  fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
  FOREIGN KEY(usuario) REFERENCES usuarios(usuario)
);

CREATE TABLE IF NOT EXISTS historial(
  id          SERIAL PRIMARY KEY,
  fecha       TIMESTAMP NOT NULL DEFAULT NOW(),
  usuario     VARCHAR(100),
  accion      VARCHAR(50) NOT NULL,
  tabla       VARCHAR(100),
  registro_id INTEGER,
  detalles    TEXT
);

-- ========================================
-- VISTAS PARA STOCK
-- ========================================
DROP VIEW IF EXISTS vw_stock;
CREATE VIEW vw_stock AS
  SELECT destino_id AS almacen_id, articulo_id, SUM(cantidad) AS delta
  FROM movimientos
  WHERE tipo IN ('ENTRADA','TRASPASO')
  GROUP BY destino_id, articulo_id
  UNION ALL
  SELECT origen_id AS almacen_id, articulo_id, SUM(-cantidad) AS delta
  FROM movimientos
  WHERE tipo IN ('IMPUTACION','PERDIDA','DEVOLUCION','TRASPASO')
    AND origen_id IS NOT NULL
  GROUP BY origen_id, articulo_id;

DROP VIEW IF EXISTS vw_stock_total;
CREATE VIEW vw_stock_total AS
  SELECT articulo_id, SUM(delta) AS stock_total
  FROM vw_stock
  GROUP BY articulo_id;

-- ========================================
-- ÍNDICES
-- ========================================
CREATE INDEX IF NOT EXISTS idx_movimientos_articulo ON movimientos(articulo_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos(tipo);
CREATE INDEX IF NOT EXISTS idx_movimientos_ot ON movimientos(ot);
CREATE INDEX IF NOT EXISTS idx_movimientos_operario ON movimientos(operario_id);
CREATE INDEX IF NOT EXISTS idx_articulos_nombre ON articulos(nombre);
CREATE INDEX IF NOT EXISTS idx_articulos_ean ON articulos(ean);
CREATE INDEX IF NOT EXISTS idx_articulos_ref ON articulos(ref_proveedor);
CREATE INDEX IF NOT EXISTS idx_articulos_palabras ON articulos USING GIN(to_tsvector('spanish', palabras_clave));

-- Índices para inventarios
CREATE INDEX IF NOT EXISTS idx_inventarios_fecha ON inventarios(fecha);
CREATE INDEX IF NOT EXISTS idx_inventarios_almacen ON inventarios(almacen_id);
CREATE INDEX IF NOT EXISTS idx_inventario_detalle_inv ON inventario_detalle(inventario_id);
CREATE INDEX IF NOT EXISTS idx_inventario_detalle_art ON inventario_detalle(articulo_id);

-- Índices para notificaciones
CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario);
CREATE INDEX IF NOT EXISTS idx_notificaciones_leido ON notificaciones(leido);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha_creacion);

-- Índices para historial
CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial(fecha);
CREATE INDEX IF NOT EXISTS idx_historial_usuario ON historial(usuario);
CREATE INDEX IF NOT EXISTS idx_historial_tabla ON historial(tabla);

-- ========================================
-- COMENTARIOS SOBRE LA MIGRACIÓN
-- ========================================
-- NOTAS:
-- 1. Las fechas en SQLite se guardaban como TEXT (ISO8601: 'YYYY-MM-DD')
--    En PostgreSQL usamos DATE que es compatible
--
-- 2. Los timestamps (sesiones.inicio_utc) se guardaban como INTEGER (Unix epoch)
--    Se mantienen como BIGINT para compatibilidad
--    Si prefieres, puedes cambiarlos a TIMESTAMP y convertir en la migración
--
-- 3. Los booleans (activo, leido) se mantienen como SMALLINT (0/1)
--    para máxima compatibilidad con el código existente
--    PostgreSQL soporta BOOLEAN nativo si quieres cambiarlo
--
-- 4. NUMERIC(10,2) para precios y cantidades da precisión decimal
--    vs REAL en SQLite que es floating point
--
-- 5. El índice GIN en palabras_clave permite búsqueda full-text en español
--    Si no quieres full-text search, usa un índice normal:
--    CREATE INDEX idx_articulos_palabras ON articulos(palabras_clave);
--
-- 6. Si tu aplicación tiene más tablas (furgonetas, historial, etc.)
--    añádelas siguiendo el mismo patrón de conversión
