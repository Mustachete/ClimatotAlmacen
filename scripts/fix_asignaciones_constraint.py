#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la constraint de la tabla asignaciones_furgoneta.
Asegura que exista el PRIMARY KEY correcto para que funcione ON CONFLICT.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.db_utils import execute_query, fetch_one
from src.core.logger import logger


def fix_asignaciones_constraint():
    """
    Corrige la constraint PRIMARY KEY de asignaciones_furgoneta.
    """
    try:
        print("=" * 60)
        print("FIX: Constraint de asignaciones_furgoneta")
        print("=" * 60)

        # Verificar si existe la constraint correcta
        print("\n1. Verificando constraint actual...")
        check_sql = """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'asignaciones_furgoneta'
              AND constraint_type = 'PRIMARY KEY'
        """

        result = fetch_one(check_sql)

        if result:
            print(f"   [OK] PRIMARY KEY encontrada: {result['constraint_name']}")

            # Verificar las columnas de la constraint
            check_columns_sql = """
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = 'asignaciones_furgoneta'
                  AND constraint_name = %s
                ORDER BY ordinal_position
            """

            from src.core.db_utils import fetch_all
            columns = fetch_all(check_columns_sql, (result['constraint_name'],))
            column_names = [col['column_name'] for col in columns]

            print(f"   Columnas en PK: {', '.join(column_names)}")

            # Verificar si las columnas son las correctas
            expected_columns = ['fecha', 'turno', 'furgoneta_id']
            if column_names == expected_columns:
                print("   [OK] La constraint es correcta!")
                print("\n" + "=" * 60)
                print("No se requieren cambios.")
                print("=" * 60)
                return

            print(f"   [ERROR] Las columnas no coinciden. Se esperaba: {expected_columns}")
            print("\n2. Eliminando constraint incorrecta...")
            execute_query(f"ALTER TABLE asignaciones_furgoneta DROP CONSTRAINT {result['constraint_name']}")
            print("   [OK] Constraint eliminada")
        else:
            print("   [ERROR] No se encontró PRIMARY KEY")

        print("\n3. Creando la constraint correcta...")

        # Primero, eliminar registros duplicados si existen
        print("   Eliminando posibles duplicados...")
        deduplicate_sql = """
            DELETE FROM asignaciones_furgoneta a
            USING asignaciones_furgoneta b
            WHERE a.ctid < b.ctid
              AND a.fecha = b.fecha
              AND a.turno = b.turno
              AND a.furgoneta_id = b.furgoneta_id
        """
        execute_query(deduplicate_sql)
        print("   [OK] Duplicados eliminados (si existían)")

        # Crear el PRIMARY KEY correcto
        create_pk_sql = """
            ALTER TABLE asignaciones_furgoneta
            ADD PRIMARY KEY (fecha, turno, furgoneta_id)
        """
        execute_query(create_pk_sql)
        print("   [OK] PRIMARY KEY creado correctamente")

        print("\n4. Verificando la nueva constraint...")
        result = fetch_one(check_sql)
        if result:
            print(f"   [OK] PRIMARY KEY confirmada: {result['constraint_name']}")

        print("\n" + "=" * 60)
        print("[OK] CORRECCIÓN COMPLETADA CON ÉXITO")
        print("=" * 60)

    except Exception as e:
        logger.exception(f"Error al corregir constraint: {e}")
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    fix_asignaciones_constraint()
