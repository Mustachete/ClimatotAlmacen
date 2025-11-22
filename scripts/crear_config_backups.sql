-- Script para crear tabla de configuración de backups
-- Fecha: 2025-11-18

-- Crear tabla de configuración de backups
CREATE TABLE IF NOT EXISTS config_backups (
    id INTEGER PRIMARY KEY CHECK(id = 1),  -- Solo permitir una fila
    max_backups INTEGER NOT NULL DEFAULT 20,  -- Número máximo de backups a mantener
    permitir_multiples_diarios INTEGER NOT NULL DEFAULT 1,  -- 0=No, 1=Sí
    backup_auto_inicio INTEGER NOT NULL DEFAULT 0,  -- 0=No, 1=Sí
    backup_auto_cierre INTEGER NOT NULL DEFAULT 0,  -- 0=No, 1=Sí
    retencion_dias INTEGER DEFAULT NULL,  -- NULL = no limitar por días, sino por número
    ruta_backups TEXT DEFAULT NULL,  -- NULL = usar ruta por defecto (db/backups)
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuración por defecto
INSERT INTO config_backups (
    id,
    max_backups,
    permitir_multiples_diarios,
    backup_auto_inicio,
    backup_auto_cierre,
    retencion_dias,
    ruta_backups
) VALUES (
    1,
    20,
    1,  -- Permitir múltiples backups diarios por defecto
    0,
    0,
    NULL,
    NULL
);

-- Crear índice en fecha de última actualización
CREATE INDEX IF NOT EXISTS idx_config_backups_fecha
ON config_backups(ultima_actualizacion);

-- Mostrar configuración inicial
SELECT
    max_backups as 'Max Backups',
    CASE permitir_multiples_diarios
        WHEN 1 THEN 'Sí'
        ELSE 'No'
    END as 'Múltiples Diarios',
    CASE backup_auto_inicio
        WHEN 1 THEN 'Sí'
        ELSE 'No'
    END as 'Auto Inicio',
    CASE backup_auto_cierre
        WHEN 1 THEN 'Sí'
        ELSE 'No'
    END as 'Auto Cierre',
    COALESCE(retencion_dias, 'Sin límite') as 'Retención (días)',
    COALESCE(ruta_backups, 'Ruta por defecto') as 'Ubicación'
FROM config_backups;
