#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recrear tabla historial_operaciones sin FK incorrecta
"""
import sqlite3
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

def fix_table():
    db_path = Path(__file__).parent.parent / "db" / "almacen.db"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    try:
        print("🔧 Recreando tabla historial_operaciones...")

        # 1. Respaldar datos existentes
        cur.execute("SELECT * FROM historial_operaciones")
        datos_backup = cur.fetchall()
        print(f"   Respaldados {len(datos_backup)} registros")

        # 2. Eliminar tabla antigua
        cur.execute("DROP TABLE IF EXISTS historial_operaciones")
        print("   ✓ Tabla antigua eliminada")

        # 3. Crear nueva tabla SIN foreign key a usuarios
        cur.execute("""
            CREATE TABLE historial_operaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT NOT NULL,
                tipo_operacion TEXT NOT NULL,
                articulo_id INTEGER NOT NULL,
                articulo_nombre TEXT NOT NULL,
                cantidad REAL NOT NULL,
                u_medida TEXT,
                fecha_hora TEXT NOT NULL,
                datos_adicionales TEXT,
                FOREIGN KEY (articulo_id) REFERENCES articulos(id)
            )
        """)
        print("   ✓ Nueva tabla creada (usuario_id es TEXT, sin FK a usuarios)")

        # 4. Crear índices
        cur.execute("""
            CREATE INDEX idx_historial_usuario_fecha
            ON historial_operaciones(usuario_id, fecha_hora DESC)
        """)
        cur.execute("""
            CREATE INDEX idx_historial_tipo
            ON historial_operaciones(tipo_operacion, usuario_id, fecha_hora DESC)
        """)
        print("   ✓ Índices creados")

        # 5. Restaurar datos
        if datos_backup:
            cur.executemany("""
                INSERT INTO historial_operaciones
                (id, usuario_id, tipo_operacion, articulo_id, articulo_nombre, cantidad, u_medida, fecha_hora, datos_adicionales)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, datos_backup)
            print(f"   ✓ Restaurados {len(datos_backup)} registros")

        con.commit()
        print("\n✅ Tabla historial_operaciones recreada correctamente")

    except Exception as e:
        con.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        con.close()

if __name__ == "__main__":
    fix_table()
