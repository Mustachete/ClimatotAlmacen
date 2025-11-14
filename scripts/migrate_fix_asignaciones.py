#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración: Añadir campo 'turno' a asignaciones_furgoneta y limpiar sistema viejo.

IMPORTANTE: Ejecutar una sola vez.
"""

import sqlite3
import sys
import io
from pathlib import Path

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import DB_PATH
from src.core.logger import logger


def main():
    print("=" * 60)
    print("MIGRACION: Añadir campo 'turno' a asignaciones_furgoneta")
    print("=" * 60)
    print()

    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()

        print("1. Verificando estructura actual...")

        # Verificar si ya existe el campo turno
        cur.execute("PRAGMA table_info(asignaciones_furgoneta)")
        columnas = {row[1] for row in cur.fetchall()}

        if 'turno' in columnas:
            print("   El campo 'turno' ya existe. Migracion no necesaria.")
            con.close()
            return 0

        print("   Campo 'turno' no existe. Aplicando migracion...")
        print()

        # Crear nueva tabla con el campo turno
        print("2. Creando tabla temporal con nuevo esquema...")
        cur.execute("""
            CREATE TABLE asignaciones_furgoneta_new(
                operario_id   INTEGER NOT NULL,
                fecha         TEXT NOT NULL,
                turno         TEXT NOT NULL DEFAULT 'completo' CHECK(turno IN ('manana', 'tarde', 'completo')),
                furgoneta_id  INTEGER NOT NULL,
                PRIMARY KEY (operario_id, fecha, turno),
                FOREIGN KEY(operario_id)   REFERENCES operarios(id),
                FOREIGN KEY(furgoneta_id)  REFERENCES almacenes(id)
            )
        """)
        print("   Tabla temporal creada.")

        # Copiar datos existentes (si los hay)
        print("3. Copiando datos existentes...")
        cur.execute("""
            INSERT INTO asignaciones_furgoneta_new (operario_id, fecha, turno, furgoneta_id)
            SELECT operario_id, fecha, 'completo', furgoneta_id
            FROM asignaciones_furgoneta
        """)
        filas_copiadas = cur.rowcount
        print(f"   {filas_copiadas} registro(s) copiados.")

        # Eliminar tabla vieja
        print("4. Eliminando tabla antigua...")
        cur.execute("DROP TABLE asignaciones_furgoneta")

        # Renombrar tabla nueva
        print("5. Renombrando tabla nueva...")
        cur.execute("ALTER TABLE asignaciones_furgoneta_new RENAME TO asignaciones_furgoneta")

        # Crear índices
        print("6. Creando índices...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_asig_operario_fecha
            ON asignaciones_furgoneta(operario_id, fecha DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_asig_furgoneta
            ON asignaciones_furgoneta(furgoneta_id)
        """)

        # Commit
        con.commit()
        con.close()

        print()
        print("=" * 60)
        print("MIGRACION COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print()
        print("Cambios aplicados:")
        print("  - Añadido campo 'turno' con valores: manana, tarde, completo")
        print("  - PRIMARY KEY actualizada: (operario_id, fecha, turno)")
        print(f"  - {filas_copiadas} registro(s) migrados con turno='completo'")
        print("  - Índices creados para optimizar búsquedas")
        print()
        logger.info("Migración asignaciones_furgoneta completada")

    except Exception as e:
        logger.exception(f"Error en migración: {e}")
        print()
        print(f"ERROR: {e}")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
