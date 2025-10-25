PRAGMA foreign_keys=ON;

-- ========================================
-- USUARIOS Y SESIONES
-- ========================================
CREATE TABLE IF NOT EXISTS usuarios(
  usuario     TEXT PRIMARY KEY,
  pass_hash   TEXT NOT NULL,
  rol         TEXT NOT NULL DEFAULT 'almacen',
  activo      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sesiones(
  usuario         TEXT NOT NULL,
  inicio_utc      INTEGER NOT NULL,
  ultimo_ping_utc INTEGER NOT NULL,
  hostname        TEXT NOT NULL,
  PRIMARY KEY(usuario, hostname)
);

-- ========================================
-- MAESTROS: PROVEEDORES, OPERARIOS, ETC.
-- ========================================
CREATE TABLE IF NOT EXISTS proveedores(
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre   TEXT UNIQUE NOT NULL,
  telefono TEXT,
  contacto TEXT,
  email    TEXT,
  notas    TEXT
);

CREATE TABLE IF NOT EXISTS operarios(
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre       TEXT UNIQUE NOT NULL,
  rol_operario TEXT NOT NULL DEFAULT 'ayudante',
  activo       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS familias(
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS ubicaciones(
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT UNIQUE NOT NULL
);

-- ========================================
-- ALMACENES Y FURGONETAS
-- ========================================
CREATE TABLE IF NOT EXISTS almacenes(
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre  TEXT UNIQUE NOT NULL,
  tipo    TEXT DEFAULT 'almacen'
);

-- ========================================
-- ARTÍCULOS
-- ========================================
CREATE TABLE IF NOT EXISTS articulos(
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  ean                 TEXT UNIQUE,
  ref_proveedor       TEXT,
  nombre              TEXT NOT NULL,
  palabras_clave      TEXT,
  u_medida            TEXT DEFAULT 'unidad',
  min_alerta          REAL DEFAULT 0,
  ubicacion_id        INTEGER,
  proveedor_id        INTEGER,
  familia_id          INTEGER,
  marca               TEXT,
  coste               REAL DEFAULT 0,
  pvp_sin             REAL DEFAULT 0,
  iva                 REAL DEFAULT 21,
  activo              INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY(ubicacion_id)  REFERENCES ubicaciones(id),
  FOREIGN KEY(proveedor_id)  REFERENCES proveedores(id),
  FOREIGN KEY(familia_id)    REFERENCES familias(id)
);

-- ========================================
-- MOVIMIENTOS
-- ========================================
CREATE TABLE IF NOT EXISTS movimientos(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha       TEXT NOT NULL,
  tipo        TEXT NOT NULL CHECK(tipo IN ('ENTRADA','TRASPASO','IMPUTACION','PERDIDA','DEVOLUCION')),
  origen_id   INTEGER,
  destino_id  INTEGER,
  articulo_id INTEGER NOT NULL,
  cantidad    REAL NOT NULL,
  coste_unit  REAL,
  motivo      TEXT,
  ot          TEXT,
  operario_id INTEGER,
  responsable TEXT,
  albaran     TEXT,
  FOREIGN KEY(origen_id)   REFERENCES almacenes(id),
  FOREIGN KEY(destino_id)  REFERENCES almacenes(id),
  FOREIGN KEY(articulo_id) REFERENCES articulos(id),
  FOREIGN KEY(operario_id) REFERENCES operarios(id)
);

-- ========================================
-- ALBARANES
-- ========================================
CREATE TABLE IF NOT EXISTS albaranes(
  albaran      TEXT PRIMARY KEY,
  proveedor_id INTEGER,
  fecha        TEXT NOT NULL,
  FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
);

-- ========================================
-- ASIGNACIONES FURGONETA-OPERARIO
-- ========================================
CREATE TABLE IF NOT EXISTS asignaciones_furgoneta(
  operario_id   INTEGER NOT NULL,
  fecha         TEXT NOT NULL,
  furgoneta_id  INTEGER NOT NULL,
  PRIMARY KEY (operario_id, fecha),
  FOREIGN KEY(operario_id)   REFERENCES operarios(id),
  FOREIGN KEY(furgoneta_id)  REFERENCES almacenes(id)
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
CREATE INDEX IF NOT EXISTS idx_articulos_palabras ON articulos(palabras_clave);

-- ========================================
-- INVENTARIOS FÍSICOS
-- ========================================
CREATE TABLE IF NOT EXISTS inventarios(
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha        TEXT NOT NULL,
  responsable  TEXT NOT NULL,
  almacen_id   INTEGER,
  observaciones TEXT,
  estado       TEXT NOT NULL DEFAULT 'EN_PROCESO' CHECK(estado IN ('EN_PROCESO','FINALIZADO')),
  fecha_cierre TEXT,
  FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
);

CREATE TABLE IF NOT EXISTS inventario_detalle(
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  inventario_id   INTEGER NOT NULL,
  articulo_id     INTEGER NOT NULL,
  stock_teorico   REAL NOT NULL DEFAULT 0,
  stock_contado   REAL NOT NULL DEFAULT 0,
  diferencia      REAL NOT NULL DEFAULT 0,
  FOREIGN KEY(inventario_id) REFERENCES inventarios(id) ON DELETE CASCADE,
  FOREIGN KEY(articulo_id) REFERENCES articulos(id)
);

-- Índices para inventarios
CREATE INDEX IF NOT EXISTS idx_inventarios_fecha ON inventarios(fecha);
CREATE INDEX IF NOT EXISTS idx_inventarios_almacen ON inventarios(almacen_id);
CREATE INDEX IF NOT EXISTS idx_inventario_detalle_inv ON inventario_detalle(inventario_id);
CREATE INDEX IF NOT EXISTS idx_inventario_detalle_art ON inventario_detalle(articulo_id);
