#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la migración y volver a intentar las tablas que fallaron
"""
import sys
import os
from pathlib import Path

# Configurar UTF-8 para la salida en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Añadir raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
import configparser


def fix_migration():
    """Corrige la migración reintentando las tablas que fallaron"""

    print("=" * 70)
    print("  CORRECCIÓN DE MIGRACIÓN")
    print("=" * 70)

    # Configuración
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / "config.ini"

    if not config_path.exists():
        print("\nERROR: No se encontró config.ini")
        return False

    config.read(config_path)

    # Ruta SQLite
    sqlite_db_path = PROJECT_ROOT / "db" / "almacen.db"
    if not sqlite_db_path.exists():
        print(f"\nERROR: No se encontró SQLite: {sqlite_db_path}")
        return False

    # Verificar psycopg2
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        print("\nERROR: psycopg2 no está instalado")
        return False

    # Conectar SQLite
    print("\nConectando a SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row

    # Conectar PostgreSQL
    print("Conectando a PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=config.get('database', 'HOST'),
        port=config.getint('database', 'PORT'),
        database=config.get('database', 'NAME'),
        user=config.get('database', 'USER'),
        password=config.get('database', 'PASSWORD')
    )

    # Tablas que fallaron (en orden de dependencias)
    tablas_problema = [
        'articulos',       # Debe ir primero (otros dependen de ella)
        'movimientos',     # Depende de articulos
        'inventario_detalle',  # Depende de articulos
    ]

    print("\nRe-intentando tablas que fallaron...\n")

    for tabla in tablas_problema:
        print(f"Procesando: {tabla}")

        # Limpiar tabla en PostgreSQL primero
        try:
            with pg_conn.cursor() as cur:
                cur.execute(f"DELETE FROM {tabla}")
                pg_conn.commit()
                print(f"  - Tabla limpiada")
        except Exception as e:
            print(f"  - Error limpiando: {e}")
            pg_conn.rollback()

        # Leer datos de SQLite
        try:
            cursor_sqlite = sqlite_conn.execute(f"SELECT * FROM {tabla}")
            rows = cursor_sqlite.fetchall()

            if not rows:
                print(f"  - Tabla vacía en SQLite")
                continue

            columnas = [desc[0] for desc in cursor_sqlite.description]
            print(f"  - {len(rows)} registros en SQLite")
            print(f"  - Columnas: {', '.join(columnas)}")

        except Exception as e:
            print(f"  - ERROR leyendo SQLite: {e}")
            continue

        # Insertar uno por uno para ver errores específicos
        errores = []
        exitos = 0

        with pg_conn.cursor() as cur_pg:
            placeholders = ', '.join(['%s'] * len(columnas))
            cols = ', '.join(columnas)
            insert_sql = f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})"

            for idx, row in enumerate(rows):
                try:
                    # Convertir row a tupla
                    valores = tuple(row)
                    cur_pg.execute(insert_sql, valores)
                    pg_conn.commit()
                    exitos += 1

                except Exception as e:
                    pg_conn.rollback()
                    # Guardar información del error
                    error_info = {
                        'fila': idx + 1,
                        'error': str(e),
                        'datos': dict(zip(columnas, row))
                    }
                    errores.append(error_info)

                    # Mostrar primeros 3 errores
                    if len(errores) <= 3:
                        print(f"\n  ERROR en fila {idx + 1}:")
                        print(f"    {e}")
                        print(f"    Datos: {dict(zip(columnas, row))}")

        if exitos > 0:
            print(f"  OK: {exitos} registros insertados")

        if errores:
            print(f"  FALLOS: {len(errores)} registros con errores")

            # Analizar tipos de errores
            tipos_error = {}
            for err in errores:
                error_msg = err['error']
                # Extraer tipo de error
                if 'foreign key' in error_msg.lower():
                    tipo = 'Foreign Key Violation'
                elif 'unique' in error_msg.lower():
                    tipo = 'Unique Constraint'
                elif 'not null' in error_msg.lower():
                    tipo = 'NOT NULL Violation'
                else:
                    tipo = 'Otro'

                if tipo not in tipos_error:
                    tipos_error[tipo] = []
                tipos_error[tipo].append(err)

            print(f"\n  Resumen de errores:")
            for tipo, errs in tipos_error.items():
                print(f"    - {tipo}: {len(errs)} casos")
                if tipo == 'Foreign Key Violation' and len(errs) > 0:
                    # Mostrar ejemplo
                    ejemplo = errs[0]
                    print(f"      Ejemplo (fila {ejemplo['fila']}): {ejemplo['error'][:100]}")

        print()

    # Actualizar secuencias
    print("Actualizando secuencias...")
    with pg_conn.cursor() as cur:
        for tabla in tablas_problema:
            try:
                cur.execute(f"SELECT pg_get_serial_sequence('{tabla}', 'id')")
                result = cur.fetchone()

                if result and result[0]:
                    seq_name = result[0]
                    cur.execute(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {tabla}), 1), true)")
                    pg_conn.commit()
                    print(f"  OK: {tabla}")
            except Exception as e:
                pass

    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 70)
    print("  CORRECCIÓN COMPLETADA")
    print("=" * 70)
    print("\nAhora ejecuta: python scripts/test_postgres_migration.py")

    return True


if __name__ == '__main__':
    try:
        fix_migration()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
