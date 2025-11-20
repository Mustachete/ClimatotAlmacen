-- Script para crear el sistema de notificaciones
-- Ejecutar este script para añadir las tablas necesarias

-- ========================================
-- TABLA DE NOTIFICACIONES
-- ========================================
CREATE TABLE IF NOT EXISTS notificaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    tipo TEXT NOT NULL, -- 'stock_critico', 'stock_bajo', 'inventario_pendiente', etc.
    mensaje TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    datos_adicionales TEXT, -- JSON con info para navegación (ej: {"articulo_id": 123})
    FOREIGN KEY(usuario) REFERENCES usuarios(usuario) ON DELETE CASCADE
);

-- ========================================
-- CONFIGURACIÓN DE NOTIFICACIONES POR USUARIO
-- ========================================
CREATE TABLE IF NOT EXISTS config_notificaciones (
    usuario TEXT NOT NULL,
    tipo_notificacion TEXT NOT NULL,
    activa INTEGER NOT NULL DEFAULT 1, -- 1 = activa, 0 = desactivada
    PRIMARY KEY(usuario, tipo_notificacion),
    FOREIGN KEY(usuario) REFERENCES usuarios(usuario) ON DELETE CASCADE
);

-- ========================================
-- ÍNDICES
-- ========================================
CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON notificaciones(tipo);

-- ========================================
-- CONFIGURACIÓN POR DEFECTO PARA USUARIOS EXISTENTES
-- ========================================
-- Insertar configuración por defecto para el usuario admin
INSERT OR IGNORE INTO config_notificaciones (usuario, tipo_notificacion, activa)
VALUES
    ('admin', 'stock_critico', 1),
    ('admin', 'stock_bajo', 1),
    ('admin', 'inventario_pendiente', 1);

-- Script completado
SELECT 'Sistema de notificaciones creado correctamente' AS resultado;
