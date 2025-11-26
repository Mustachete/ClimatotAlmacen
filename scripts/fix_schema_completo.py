#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir completamente el schema de PostgreSQL.
Añade todas las constraints faltantes (PKs y FKs).
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.db_utils import execute_query, fetch_one
from src.core.logger import logger


def fix_historial_pk():
    """Añade PRIMARY KEY a la tabla historial o la crea si no existe"""
    print("\n1. Verificando tabla historial...")
    try:
        # Verificar si la tabla existe
        sql_check_table = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'historial'
        """
        table_exists = fetch_one(sql_check_table)

        if not table_exists:
            print("   [INFO] Tabla historial no existe, creándola...")
            create_table_sql = """
                CREATE TABLE historial(
                  id          SERIAL PRIMARY KEY,
                  fecha       TIMESTAMP NOT NULL DEFAULT NOW(),
                  usuario     VARCHAR(100),
                  accion      VARCHAR(50) NOT NULL,
                  tabla       VARCHAR(100),
                  registro_id INTEGER,
                  detalles    TEXT
                )
            """
            execute_query(create_table_sql)
            print("   [OK] Tabla historial creada con PRIMARY KEY")
            return

        # Verificar si ya existe PK
        sql_check = """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'historial'
              AND constraint_type = 'PRIMARY KEY'
        """
        result = fetch_one(sql_check)

        if result:
            print("   [OK] Ya existe PRIMARY KEY")
            return

        # Añadir PK
        execute_query("ALTER TABLE historial ADD PRIMARY KEY (id)")
        print("   [OK] PRIMARY KEY añadida")

    except Exception as e:
        print(f"   [ERROR] {e}")
        raise


def fix_foreign_keys():
    """Añade todas las FOREIGN KEYS faltantes"""
    print("\n2. Añadiendo FOREIGN KEYS...")

    # Definir todas las FKs que deben existir
    foreign_keys = [
        # Tabla, columna, tabla_referenciada, columna_referenciada
        ('articulos', 'ubicacion_id', 'ubicaciones', 'id'),
        ('articulos', 'proveedor_id', 'proveedores', 'id'),
        ('articulos', 'familia_id', 'familias', 'id'),
        ('movimientos', 'origen_id', 'almacenes', 'id'),
        ('movimientos', 'destino_id', 'almacenes', 'id'),
        ('movimientos', 'articulo_id', 'articulos', 'id'),
        ('movimientos', 'operario_id', 'operarios', 'id'),
        ('albaranes', 'proveedor_id', 'proveedores', 'id'),
        ('asignaciones_furgoneta', 'operario_id', 'operarios', 'id'),
        ('asignaciones_furgoneta', 'furgoneta_id', 'almacenes', 'id'),
        ('inventarios', 'almacen_id', 'almacenes', 'id'),
        ('inventario_detalle', 'inventario_id', 'inventarios', 'id'),
        ('inventario_detalle', 'articulo_id', 'articulos', 'id'),
        ('furgonetas', 'almacen_id', 'almacenes', 'id'),
        ('notificaciones', 'usuario', 'usuarios', 'usuario'),
    ]

    for tabla, columna, tabla_ref, columna_ref in foreign_keys:
        try:
            # Verificar si ya existe
            sql_check = """
                SELECT tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = %s
                  AND kcu.column_name = %s
            """
            result = fetch_one(sql_check, (tabla, columna))

            if result:
                print(f"   [SKIP] {tabla}.{columna} (ya existe)")
                continue

            # Nombre de la constraint
            fk_name = f"fk_{tabla}_{columna}"

            # Crear FK
            sql_fk = f"""
                ALTER TABLE {tabla}
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY ({columna})
                REFERENCES {tabla_ref}({columna_ref})
            """

            # Para inventario_detalle.inventario_id, añadir ON DELETE CASCADE
            if tabla == 'inventario_detalle' and columna == 'inventario_id':
                sql_fk += " ON DELETE CASCADE"

            execute_query(sql_fk)
            print(f"   [OK] {tabla}.{columna} -> {tabla_ref}.{columna_ref}")

        except Exception as e:
            print(f"   [ERROR] {tabla}.{columna}: {e}")
            # Continuar con las demás, no fallar todo


def verificar_correcciones():
    """Verifica que las correcciones se aplicaron correctamente"""
    print("\n3. Verificando correcciones...")

    errores = 0

    # Verificar PK de historial
    sql_check_pk = """
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'historial'
          AND constraint_type = 'PRIMARY KEY'
    """
    result = fetch_one(sql_check_pk)
    if result:
        print("   [OK] historial.id PRIMARY KEY")
    else:
        print("   [ERROR] historial.id PRIMARY KEY no existe")
        errores += 1

    # Verificar algunas FKs críticas
    fks_criticas = [
        ('articulos', 'proveedor_id'),
        ('movimientos', 'articulo_id'),
        ('asignaciones_furgoneta', 'operario_id'),
    ]

    for tabla, columna in fks_criticas:
        sql_check_fk = """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = %s
              AND kcu.column_name = %s
        """
        result = fetch_one(sql_check_fk, (tabla, columna))
        if result:
            print(f"   [OK] {tabla}.{columna} FK")
        else:
            print(f"   [ERROR] {tabla}.{columna} FK no existe")
            errores += 1

    return errores


def main():
    """Ejecuta todas las correcciones"""
    print("=" * 60)
    print("CORRECCIÓN COMPLETA DE SCHEMA POSTGRESQL")
    print("=" * 60)

    try:
        # 1. Corregir PK de historial
        fix_historial_pk()

        # 2. Añadir todas las FKs
        fix_foreign_keys()

        # 3. Verificar
        errores = verificar_correcciones()

        print("\n" + "=" * 60)
        if errores == 0:
            print("[OK] CORRECCIÓN COMPLETADA CON ÉXITO")
        else:
            print(f"[WARNING] Completado con {errores} errores")
        print("=" * 60)

        print("\nRecomendación: Ejecutar verificar_schema_postgres.py para confirmar.")

    except Exception as e:
        logger.exception(f"Error en corrección: {e}")
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
