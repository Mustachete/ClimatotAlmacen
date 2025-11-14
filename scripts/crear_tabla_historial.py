#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear tabla de historial de operaciones rápidas.
Permite guardar las últimas operaciones de cada usuario para repetirlas.
"""

import sys
import io
from pathlib import Path

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con

def crear_tabla_historial():
    """Crea la tabla de historial de operaciones"""

    print("🔧 Creando tabla de historial de operaciones...")

    try:
        con = get_con()
        cur = con.cursor()

        # Crear tabla de historial
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historial_operaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo_operacion TEXT NOT NULL,  -- 'movimiento', 'imputacion', 'material_perdido', 'devolucion'
                articulo_id INTEGER NOT NULL,
                articulo_nombre TEXT NOT NULL,
                cantidad REAL NOT NULL,
                u_medida TEXT,
                fecha_hora TEXT NOT NULL,  -- ISO 8601
                datos_adicionales TEXT,  -- JSON para info extra (OT, motivo, etc.)
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (articulo_id) REFERENCES articulos(id)
            )
        """)

        # Crear índices para consultas rápidas
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historial_usuario_fecha
            ON historial_operaciones(usuario_id, fecha_hora DESC)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_historial_tipo
            ON historial_operaciones(tipo_operacion, usuario_id, fecha_hora DESC)
        """)

        con.commit()
        con.close()

        print("✅ Tabla 'historial_operaciones' creada exitosamente")
        print("✅ Índices creados para consultas rápidas")
        print("\nEstructura:")
        print("  - id: Identificador único")
        print("  - usuario_id: Usuario que realizó la operación")
        print("  - tipo_operacion: Tipo (movimiento, imputacion, etc.)")
        print("  - articulo_id: ID del artículo")
        print("  - articulo_nombre: Nombre del artículo (para mostrar)")
        print("  - cantidad: Cantidad usada")
        print("  - u_medida: Unidad de medida")
        print("  - fecha_hora: Timestamp de la operación")
        print("  - datos_adicionales: JSON con info extra (OT, motivo, etc.)")

    except Exception as e:
        print(f"❌ Error al crear tabla: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crear_tabla_historial()
