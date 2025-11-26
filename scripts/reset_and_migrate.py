#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resetear PostgreSQL completamente y migrar desde SQLite
ADVERTENCIA: Esto eliminará todos los datos en PostgreSQL
"""
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import configparser
import sqlite3

def reset_and_migrate():
    """Resetea PostgreSQL y migra desde SQLite"""

    print("=" * 70)
    print("  RESET COMPLETO Y MIGRACIÓN")
    print("=" * 70)
    print("\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos en PostgreSQL")
    respuesta = input("¿Continuar? (escribe 'SI' para confirmar): ")

    if respuesta != 'SI':
        print("\n❌ Operación cancelada")
        return False

    # Configuración
    config = configparser.ConfigParser()
    config.read(PROJECT_ROOT / "config.ini")

    import psycopg2
    from psycopg2.extras import execute_values

    # Conectar PostgreSQL
    print("\n🔌 Conectando a PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=config.get('database', 'HOST'),
        port=config.getint('database', 'PORT'),
        database=config.get('database', 'NAME'),
        user=config.get('database', 'USER'),
        password=config.get('database', 'PASSWORD')
    )

    # PASO 1: Eliminar todas las tablas
    print("\n🗑️  Eliminando todas las tablas existentes...")
    with pg_conn.cursor() as cur:
        # Obtener todas las tablas
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = [row[0] for row in cur.fetchall()]

        # Eliminar vistas primero
        cur.execute("""
            SELECT table_name FROM information_schema.views
            WHERE table_schema = 'public'
        """)
        views = [row[0] for row in cur.fetchall()]

        for view in views:
            print(f"  Eliminando vista: {view}")
            cur.execute(f"DROP VIEW IF EXISTS {view} CASCADE")

        # Eliminar tablas
        for table in tables:
            print(f"  Eliminando tabla: {table}")
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

        pg_conn.commit()

    print("  ✅ Todas las tablas eliminadas")

    # PASO 2: Leer schema generado
    print("\n📄 Leyendo schema completo...")
    schema_path = PROJECT_ROOT / "db" / "schema_postgres_full.sql"

    if not schema_path.exists():
        print(f"  ❌ Error: No se encontró {schema_path}")
        print("  Ejecuta primero: python scripts/generate_full_schema.py > db/schema_postgres_full.sql")
        return False

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # PASO 3: Crear tablas
    print("⚙️  Creando tablas...")
    try:
        with pg_conn.cursor() as cur:
            cur.execute(schema_sql)
            pg_conn.commit()
        print("  ✅ Tablas creadas correctamente")
    except Exception as e:
        print(f"  ❌ Error creando tablas: {e}")
        pg_conn.rollback()
        return False

    # PASO 4: Migrar datos desde SQLite
    print("\n📦 Migrando datos desde SQLite...")

    sqlite_conn = sqlite3.connect(PROJECT_ROOT / "db" / "almacen.db")
    sqlite_conn.row_factory = sqlite3.Row

    # Obtener lista de tablas de SQLite
    cursor = sqlite_conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tablas = [row[0] for row in cursor.fetchall()]

    total_registros = 0

    for tabla in tablas:
        try:
            # Leer datos de SQLite
            cursor_sqlite = sqlite_conn.execute(f"SELECT * FROM {tabla}")
            rows = cursor_sqlite.fetchall()

            if not rows:
                print(f"  ⏭️  {tabla:30} - vacía")
                continue

            columnas = [desc[0] for desc in cursor_sqlite.description]

            # Insertar en PostgreSQL
            with pg_conn.cursor() as cur_pg:
                placeholders = ', '.join(['%s'] * len(columnas))
                cols = ', '.join(columnas)
                insert_sql = f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})"

                # Insertar por lotes
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    data = [tuple(row) for row in batch]
                    execute_values(cur_pg, f"INSERT INTO {tabla} ({cols}) VALUES %s", data)

            pg_conn.commit()
            print(f"  ✅ {tabla:30} - {len(rows):6} registros")
            total_registros += len(rows)

        except Exception as e:
            pg_conn.rollback()
            print(f"  ❌ {tabla:30} - ERROR: {str(e)[:60]}")

    # PASO 5: Actualizar secuencias
    print("\n🔄 Actualizando secuencias...")
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'id'
        """)
        tablas_con_id = [row[0] for row in cur.fetchall()]

        for tabla in tablas_con_id:
            try:
                cur.execute(f"SELECT pg_get_serial_sequence('{tabla}', 'id')")
                result = cur.fetchone()

                if result and result[0]:
                    seq_name = result[0]
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {tabla}")
                    max_id = cur.fetchone()[0]

                    if max_id > 0:
                        cur.execute(f"SELECT setval('{seq_name}', {max_id}, true)")
                        pg_conn.commit()
                        print(f"  ✅ {tabla:30} -> {max_id}")
            except:
                pass

    # Cerrar conexiones
    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 70)
    print("  ✅ RESET Y MIGRACIÓN COMPLETADOS")
    print("=" * 70)
    print(f"\n📊 Total de registros migrados: {total_registros:,}")
    print("\n🚀 Ahora puedes ejecutar: python app.py")

    return True

if __name__ == '__main__':
    try:
        reset_and_migrate()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
