#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración de datos SQLite a PostgreSQL
Copia todos los datos de la BD SQLite a PostgreSQL
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


def migrate_data():
    """Migra datos de SQLite a PostgreSQL"""

    print("=" * 70)
    print("  MIGRACIÓN DE DATOS: SQLite → PostgreSQL")
    print("=" * 70)

    # Configuración
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / "config.ini"

    if not config_path.exists():
        print("\n❌ ERROR: No se encontró config.ini")
        return False

    config.read(config_path)

    # Ruta SQLite
    sqlite_db_path = PROJECT_ROOT / "db" / "almacen.db"
    if not sqlite_db_path.exists():
        print(f"\n❌ ERROR: No se encontró la base de datos SQLite: {sqlite_db_path}")
        return False

    print(f"\n📁 Base de datos SQLite: {sqlite_db_path}")
    print(f"   Tamaño: {sqlite_db_path.stat().st_size / 1024:.2f} KB")

    # Verificar psycopg2
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        print("\n❌ ERROR: psycopg2 no está instalado")
        print("   Ejecuta: pip install psycopg2-binary")
        return False

    # Conectar SQLite
    print("\n🔌 Conectando a SQLite...")
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        print("✅ SQLite conectado")
    except Exception as e:
        print(f"❌ Error conectando a SQLite: {e}")
        return False

    # Conectar PostgreSQL
    print("\n🔌 Conectando a PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(
            host=config.get('database', 'HOST'),
            port=config.getint('database', 'PORT'),
            database=config.get('database', 'NAME'),
            user=config.get('database', 'USER'),
            password=config.get('database', 'PASSWORD')
        )
        print("✅ PostgreSQL conectado")
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print("\n💡 Asegúrate de haber ejecutado: python scripts/init_postgres.py")
        sqlite_conn.close()
        return False

    # Orden de tablas (respetar foreign keys)
    tablas_orden = [
        'usuarios',
        'sesiones',
        'proveedores',
        'operarios',
        'familias',
        'ubicaciones',
        'almacenes',
        'furgonetas',
        'articulos',
        'movimientos',
        'asignaciones_furgoneta',
        'albaranes',
        'inventarios',
        'inventario_detalle',
        'notificaciones',
        'historial'
    ]

    print("\n📋 Migrando tablas...\n")

    total_registros = 0
    tablas_migradas = 0

    for tabla in tablas_orden:
        # Verificar si la tabla existe en SQLite
        try:
            cursor_check = sqlite_conn.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (tabla,)
            )
            if not cursor_check.fetchone():
                print(f"⏭️  {tabla:30} - No existe en SQLite")
                continue
        except Exception:
            continue

        # Leer datos de SQLite
        try:
            cursor_sqlite = sqlite_conn.execute(f"SELECT * FROM {tabla}")
            rows = cursor_sqlite.fetchall()

            if not rows:
                print(f"⚠️  {tabla:30} - Tabla vacía")
                continue

            # Obtener nombres de columnas
            columnas = [desc[0] for desc in cursor_sqlite.description]

        except Exception as e:
            print(f"❌ {tabla:30} - Error leyendo SQLite: {e}")
            continue

        # Insertar en PostgreSQL
        try:
            with pg_conn.cursor() as cur_pg:
                # Preparar INSERT
                placeholders = ', '.join(['%s'] * len(columnas))
                cols = ', '.join(columnas)
                insert_sql = f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})"

                # Insertar por lotes para mejor rendimiento
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    data = [tuple(row) for row in batch]
                    execute_values(cur_pg, f"INSERT INTO {tabla} ({cols}) VALUES %s", data, template=None)

            pg_conn.commit()
            print(f"✅ {tabla:30} - {len(rows):6} registros migrados")
            total_registros += len(rows)
            tablas_migradas += 1

        except Exception as e:
            pg_conn.rollback()
            print(f"❌ {tabla:30} - Error insertando en PostgreSQL:")
            print(f"   {e}")
            # Intentar insertar fila por fila para identificar problemas
            print(f"   Intentando inserción fila por fila...")
            errores = 0
            exitos = 0
            with pg_conn.cursor() as cur_pg:
                for row in rows:
                    try:
                        cur_pg.execute(insert_sql, tuple(row))
                        pg_conn.commit()
                        exitos += 1
                    except Exception as row_error:
                        pg_conn.rollback()
                        errores += 1
                        if errores <= 3:  # Mostrar solo los primeros 3 errores
                            print(f"      Error en fila: {dict(row)}")
                            print(f"      {row_error}")

            if exitos > 0:
                print(f"   ✅ {exitos} registros insertados correctamente")
                print(f"   ❌ {errores} registros con errores")
                total_registros += exitos
                tablas_migradas += 1

    # Actualizar secuencias de PostgreSQL
    print("\n🔄 Actualizando secuencias (SERIAL)...")
    with pg_conn.cursor() as cur:
        for tabla in tablas_orden:
            try:
                # Obtener nombre de la secuencia
                cur.execute("""
                    SELECT pg_get_serial_sequence(%s, 'id')
                """, (tabla,))
                result = cur.fetchone()

                if result and result[0]:
                    seq_name = result[0]
                    # Actualizar secuencia al máximo id + 1
                    cur.execute(f"""
                        SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {tabla}), 1), true)
                    """, (seq_name,))
                    pg_conn.commit()
                    print(f"   ✅ {tabla}")

            except Exception as e:
                # Algunas tablas no tienen secuencias (ej: sesiones)
                pass

    # Resumen
    print("\n" + "=" * 70)
    print("  ✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\n📊 Estadísticas:")
    print(f"   Tablas migradas: {tablas_migradas}")
    print(f"   Registros totales: {total_registros:,}")

    # Verificar integridad
    print("\n🔍 Verificando integridad...")
    try:
        with pg_conn.cursor() as cur:
            # Contar registros en tablas principales
            cur.execute("SELECT COUNT(*) FROM usuarios")
            usuarios_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM articulos")
            articulos_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM movimientos")
            movimientos_count = cur.fetchone()[0]

        print(f"   Usuarios: {usuarios_count}")
        print(f"   Artículos: {articulos_count}")
        print(f"   Movimientos: {movimientos_count}")

    except Exception as e:
        print(f"   ⚠️  Error verificando integridad: {e}")

    # Cerrar conexiones
    sqlite_conn.close()
    pg_conn.close()

    print("\n💡 Próximos pasos:")
    print("   1. Ejecutar: python scripts/test_postgres_migration.py")
    print("      (para validar que la migración fue correcta)")
    print("   2. Cambiar config.ini ENGINE=postgres si aún no lo has hecho")
    print("   3. Ejecutar: python app.py")
    print("      (para probar la aplicación con PostgreSQL)\n")

    return True


if __name__ == '__main__':
    try:
        success = migrate_data()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
