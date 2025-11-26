-- ========================================
-- SCHEMA POSTGRESQL COMPLETO - Generado automáticamente
-- ========================================

-- Tabla: albaranes
CREATE TABLE IF NOT EXISTS albaranes (
  albaran TEXT,
  proveedor_id INTEGER,
  fecha TEXT NOT NULL,
  PRIMARY KEY (albaran)
);

-- Tabla: almacenes
CREATE TABLE IF NOT EXISTS almacenes (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  tipo TEXT DEFAULT 'almacen'
);

-- Tabla: articulos
CREATE TABLE IF NOT EXISTS articulos (
  id SERIAL PRIMARY KEY,
  ean TEXT,
  ref_proveedor TEXT,
  nombre TEXT NOT NULL,
  palabras_clave TEXT,
  u_medida TEXT DEFAULT 'unidad',
  min_alerta NUMERIC(10,2) DEFAULT 0,
  ubicacion_id INTEGER,
  proveedor_id INTEGER,
  familia_id INTEGER,
  marca TEXT,
  coste NUMERIC(10,2) DEFAULT 0,
  pvp_sin NUMERIC(10,2) DEFAULT 0,
  iva NUMERIC(10,2) DEFAULT 21,
  activo INTEGER NOT NULL DEFAULT 1,
  unidad_compra NUMERIC(10,2) DEFAULT NULL,
  dias_seguridad INTEGER DEFAULT 5,
  critico SMALLINT DEFAULT 0,
  notas TEXT DEFAULT NULL
);

-- Tabla: asignaciones_furgoneta
CREATE TABLE IF NOT EXISTS asignaciones_furgoneta (
  operario_id INTEGER NOT NULL,
  fecha TEXT NOT NULL,
  turno TEXT NOT NULL DEFAULT 'completo',
  furgoneta_id INTEGER NOT NULL,
  PRIMARY KEY (operario_id, fecha, turno)
);

-- Tabla: config_backups
CREATE TABLE IF NOT EXISTS config_backups (
  id SERIAL PRIMARY KEY,
  max_backups INTEGER NOT NULL DEFAULT 20,
  permitir_multiples_diarios INTEGER NOT NULL DEFAULT 1,
  backup_auto_inicio INTEGER NOT NULL DEFAULT 0,
  backup_auto_cierre INTEGER NOT NULL DEFAULT 0,
  retencion_dias INTEGER DEFAULT NULL,
  ruta_backups TEXT DEFAULT NULL,
  ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: config_notificaciones
CREATE TABLE IF NOT EXISTS config_notificaciones (
  usuario TEXT NOT NULL,
  tipo_notificacion TEXT NOT NULL,
  activa INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (usuario, tipo_notificacion)
);

-- Tabla: familias
CREATE TABLE IF NOT EXISTS familias (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL
);

-- Tabla: furgonetas
CREATE TABLE IF NOT EXISTS furgonetas (
  id SERIAL PRIMARY KEY,
  matricula TEXT NOT NULL,
  marca TEXT,
  modelo TEXT,
  anio INTEGER,
  activa INTEGER NOT NULL DEFAULT 1,
  notas TEXT,
  numero INTEGER
);

-- Tabla: furgonetas_asignaciones
CREATE TABLE IF NOT EXISTS furgonetas_asignaciones (
  id SERIAL PRIMARY KEY,
  furgoneta_id INTEGER NOT NULL,
  operario TEXT NOT NULL,
  desde TEXT NOT NULL,
  hasta TEXT,
  notas TEXT
);

-- Tabla: historial_operaciones
CREATE TABLE IF NOT EXISTS historial_operaciones (
  id SERIAL PRIMARY KEY,
  usuario_id TEXT NOT NULL,
  tipo_operacion TEXT NOT NULL,
  articulo_id INTEGER NOT NULL,
  articulo_nombre TEXT NOT NULL,
  cantidad NUMERIC(10,2) NOT NULL,
  u_medida TEXT,
  fecha_hora TEXT NOT NULL,
  datos_adicionales TEXT
);

-- Tabla: inventario_detalle
CREATE TABLE IF NOT EXISTS inventario_detalle (
  id SERIAL PRIMARY KEY,
  inventario_id INTEGER NOT NULL,
  articulo_id INTEGER NOT NULL,
  stock_teorico NUMERIC(10,2) NOT NULL DEFAULT 0,
  stock_contado NUMERIC(10,2) NOT NULL DEFAULT 0,
  diferencia NUMERIC(10,2) NOT NULL DEFAULT 0
);

-- Tabla: inventarios
CREATE TABLE IF NOT EXISTS inventarios (
  id SERIAL PRIMARY KEY,
  fecha TEXT NOT NULL,
  responsable TEXT NOT NULL,
  almacen_id INTEGER,
  observaciones TEXT,
  estado TEXT NOT NULL DEFAULT 'EN_PROCESO',
  fecha_cierre TEXT
);

-- Tabla: movimientos
CREATE TABLE IF NOT EXISTS movimientos (
  id SERIAL PRIMARY KEY,
  fecha TEXT NOT NULL,
  tipo TEXT NOT NULL,
  origen_id INTEGER,
  destino_id INTEGER,
  articulo_id INTEGER NOT NULL,
  cantidad NUMERIC(10,2) NOT NULL,
  coste_unit NUMERIC(10,2),
  motivo TEXT,
  ot TEXT,
  operario_id INTEGER,
  responsable TEXT,
  albaran TEXT
);

-- Tabla: notificaciones
CREATE TABLE IF NOT EXISTS notificaciones (
  id SERIAL PRIMARY KEY,
  usuario TEXT NOT NULL,
  tipo TEXT NOT NULL,
  mensaje TEXT NOT NULL,
  fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
  datos_adicionales TEXT
);

-- Tabla: operarios
CREATE TABLE IF NOT EXISTS operarios (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  rol_operario TEXT NOT NULL DEFAULT 'ayudante',
  activo INTEGER NOT NULL DEFAULT 1
);

-- Tabla: proveedores
CREATE TABLE IF NOT EXISTS proveedores (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  telefono TEXT,
  contacto TEXT,
  email TEXT,
  notas TEXT
);

-- Tabla: sesiones
CREATE TABLE IF NOT EXISTS sesiones (
  usuario TEXT NOT NULL,
  inicio_utc INTEGER NOT NULL,
  ultimo_ping_utc INTEGER NOT NULL,
  hostname TEXT NOT NULL,
  PRIMARY KEY (usuario, hostname)
);

-- Tabla: ubicaciones
CREATE TABLE IF NOT EXISTS ubicaciones (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL
);

-- Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
  usuario TEXT,
  pass_hash TEXT NOT NULL,
  rol TEXT NOT NULL DEFAULT 'almacen',
  activo INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (usuario)
);


-- ========================================
-- VISTAS
-- ========================================

-- Vista: vw_furgonetas_estado_actual
CREATE OR REPLACE VIEW vw_furgonetas_estado_actual AS
SELECT f.id AS furgoneta_id,
       f.matricula,
       f.marca,
       f.modelo,
       f.anio,
       f.activa,
       (SELECT a.operario
          FROM furgonetas_asignaciones a
         WHERE a.furgoneta_id = f.id AND a.hasta IS NULL
         ORDER BY a.desde DESC
         LIMIT 1) AS operario_actual,
       (SELECT a.desde
          FROM furgonetas_asignaciones a
         WHERE a.furgoneta_id = f.id AND a.hasta IS NULL
         ORDER BY a.desde DESC
         LIMIT 1) AS desde
  FROM furgonetas f;

-- Vista: vw_stock
CREATE OR REPLACE VIEW vw_stock AS
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

-- Vista: vw_stock_total
CREATE OR REPLACE VIEW vw_stock_total AS
  SELECT articulo_id, SUM(delta) AS stock_total
  FROM vw_stock
  GROUP BY articulo_id;


-- ========================================
-- ÍNDICES
-- ========================================

CREATE INDEX IF NOT EXISTS idx_albaranes_fecha ON albaranes(fecha DESC);

CREATE INDEX IF NOT EXISTS idx_albaranes_prov_fecha ON albaranes(proveedor_id, fecha, albaran);

CREATE INDEX IF NOT EXISTS idx_albaranes_proveedor ON albaranes(proveedor_id);

CREATE INDEX IF NOT EXISTS idx_articulos_activo ON articulos(activo);

CREATE INDEX IF NOT EXISTS idx_articulos_ean ON articulos(ean);

CREATE INDEX IF NOT EXISTS idx_articulos_familia ON articulos(familia_id);

CREATE INDEX IF NOT EXISTS idx_articulos_nombre ON articulos(nombre);

CREATE INDEX IF NOT EXISTS idx_articulos_palabras ON articulos(palabras_clave);

CREATE INDEX IF NOT EXISTS idx_articulos_proveedor ON articulos(proveedor_id);

CREATE INDEX IF NOT EXISTS idx_articulos_ref ON articulos(ref_proveedor);

CREATE INDEX IF NOT EXISTS idx_articulos_ubicacion ON articulos(ubicacion_id);

CREATE INDEX IF NOT EXISTS idx_asig_furgoneta
            ON asignaciones_furgoneta(furgoneta_id)
        ;

CREATE INDEX IF NOT EXISTS idx_asig_operario_fecha
            ON asignaciones_furgoneta(operario_id, fecha DESC)
        ;

CREATE INDEX IF NOT EXISTS idx_config_backups_fecha
ON config_backups(ultima_actualizacion);

CREATE INDEX IF NOT EXISTS idx_furgonetas_asignaciones_actual ON furgonetas_asignaciones(furgoneta_id, hasta);

CREATE INDEX IF NOT EXISTS idx_furgonetas_asignaciones_furgoneta ON furgonetas_asignaciones(furgoneta_id);

CREATE INDEX IF NOT EXISTS idx_historial_tipo
            ON historial_operaciones(tipo_operacion, usuario_id, fecha_hora DESC)
        ;

CREATE INDEX IF NOT EXISTS idx_historial_usuario_fecha
            ON historial_operaciones(usuario_id, fecha_hora DESC)
        ;

CREATE INDEX IF NOT EXISTS idx_inventario_detalle_art ON inventario_detalle(articulo_id);

CREATE INDEX IF NOT EXISTS idx_inventario_detalle_inv ON inventario_detalle(inventario_id);

CREATE INDEX IF NOT EXISTS idx_inventarios_almacen ON inventarios(almacen_id);

CREATE INDEX IF NOT EXISTS idx_inventarios_fecha ON inventarios(fecha);

CREATE INDEX IF NOT EXISTS idx_movimientos_albaran ON movimientos(albaran);

CREATE INDEX IF NOT EXISTS idx_movimientos_articulo ON movimientos(articulo_id);

CREATE INDEX IF NOT EXISTS idx_movimientos_articulo_fecha ON movimientos(articulo_id, fecha DESC);

CREATE INDEX IF NOT EXISTS idx_movimientos_destino ON movimientos(destino_id);

CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha);

CREATE INDEX IF NOT EXISTS idx_movimientos_fecha_tipo ON movimientos(fecha, tipo);

CREATE INDEX IF NOT EXISTS idx_movimientos_operario ON movimientos(operario_id);

CREATE INDEX IF NOT EXISTS idx_movimientos_origen ON movimientos(origen_id);

CREATE INDEX IF NOT EXISTS idx_movimientos_ot ON movimientos(ot);

CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos(tipo);

CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha_creacion);

CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON notificaciones(tipo);

CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario);

