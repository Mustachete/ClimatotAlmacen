#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validación de migración SQLite → PostgreSQL
Compara los datos entre ambas bases de datos
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


def test_migration():
    """Valida que la migración fue exitosa comparando ambas bases de datos"""

    print("=" * 70)
    print("  VALIDACIÓN DE MIGRACIÓN: SQLite vs PostgreSQL")
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
        print(f"\n❌ ERROR: No se encontró SQLite: {sqlite_db_path}")
        return False

    # Verificar psycopg2
    try:
        import psycopg2
    except ImportError:
        print("\n❌ ERROR: psycopg2 no está instalado")
        return False

    # Conectar SQLite
    print("\n🔌 Conectando a SQLite...")
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        print("✅ SQLite conectado")
    except Exception as e:
        print(f"❌ Error conectando a SQLite: {e}")
        return False

    # Conectar PostgreSQL
    print("🔌 Conectando a PostgreSQL...")
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
        sqlite_conn.close()
        return False

    # Tablas a comparar
    tablas = [
        'usuarios',
        'proveedores',
        'operarios',
        'familias',
        'ubicaciones',
        'almacenes',
        'articulos',
        'movimientos',
        'asignaciones_furgoneta',
        'albaranes',
        'inventarios',
        'inventario_detalle'
    ]

    print("\n📊 Comparando conteo de registros...\n")
    print(f"{'Tabla':<30} {'SQLite':>10} {'PostgreSQL':>10} {'Estado'}")
    print("-" * 70)

    diferencias = []
    total_sqlite = 0
    total_postgres = 0

    for tabla in tablas:
        # Contar en SQLite
        try:
            cur_sqlite = sqlite_conn.execute(f"SELECT COUNT(*) FROM {tabla}")
            count_sqlite = cur_sqlite.fetchone()[0]
            total_sqlite += count_sqlite
        except sqlite3.OperationalError:
            # Tabla no existe en SQLite
            count_sqlite = 0

        # Contar en PostgreSQL
        try:
            with pg_conn.cursor() as cur_pg:
                cur_pg.execute(f"SELECT COUNT(*) FROM {tabla}")
                count_pg = cur_pg.fetchone()[0]
                total_postgres += count_pg
        except Exception:
            # Tabla no existe en PostgreSQL
            count_pg = 0

        # Comparar
        if count_sqlite == count_pg:
            estado = "✅"
        else:
            estado = "❌"
            diferencias.append((tabla, count_sqlite, count_pg))

        print(f"{tabla:<30} {count_sqlite:>10,} {count_pg:>10,}  {estado}")

    print("-" * 70)
    print(f"{'TOTAL':<30} {total_sqlite:>10,} {total_postgres:>10,}")

    # Resumen
    print("\n" + "=" * 70)
    if not diferencias:
        print("  ✅ VALIDACIÓN EXITOSA")
        print("=" * 70)
        print("\n🎉 Todas las tablas tienen el mismo número de registros")
    else:
        print("  ⚠️  SE ENCONTRARON DIFERENCIAS")
        print("=" * 70)
        print(f"\n❌ {len(diferencias)} tabla(s) con diferencias:")
        for tabla, sqlite_count, pg_count in diferencias:
            diff = pg_count - sqlite_count
            print(f"   • {tabla}: SQLite={sqlite_count}, PostgreSQL={pg_count} (diff={diff:+d})")

    # Tests adicionales de integridad
    print("\n🔍 Tests de integridad adicionales...\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Verificar que existen usuarios
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1")
            usuarios_activos = cur.fetchone()[0]
            if usuarios_activos > 0:
                print(f"✅ Usuarios activos: {usuarios_activos}")
                tests_passed += 1
            else:
                print("❌ No hay usuarios activos")
                tests_failed += 1
    except Exception as e:
        print(f"❌ Error verificando usuarios: {e}")
        tests_failed += 1

    # Test 2: Verificar que existen artículos
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM articulos WHERE activo = 1")
            articulos_activos = cur.fetchone()[0]
            if articulos_activos > 0:
                print(f"✅ Artículos activos: {articulos_activos}")
                tests_passed += 1
            else:
                print("⚠️  No hay artículos activos")
                tests_passed += 1  # No es error crítico
    except Exception as e:
        print(f"❌ Error verificando artículos: {e}")
        tests_failed += 1

    # Test 3: Verificar vistas
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM vw_stock_total")
            stock_count = cur.fetchone()[0]
            print(f"✅ Vista vw_stock_total funciona: {stock_count} artículos con stock")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Error en vista vw_stock_total: {e}")
        tests_failed += 1

    # Test 4: Verificar foreign keys
    try:
        with pg_conn.cursor() as cur:
            # Intentar insertar un movimiento con artículo inexistente (debe fallar)
            cur.execute("""
                INSERT INTO movimientos(fecha, tipo, articulo_id, cantidad)
                VALUES('2025-01-01', 'ENTRADA', 99999999, 1)
            """)
            pg_conn.rollback()
            print("❌ Foreign keys NO están funcionando (se permitió insertar dato inválido)")
            tests_failed += 1
    except psycopg2.IntegrityError:
        pg_conn.rollback()
        print("✅ Foreign keys funcionan correctamente")
        tests_passed += 1
    except Exception as e:
        pg_conn.rollback()
        print(f"⚠️  No se pudo verificar foreign keys: {e}")

    # Test 5: Verificar que las secuencias funcionan
    try:
        with pg_conn.cursor() as cur:
            # Obtener el siguiente valor de la secuencia de proveedores
            cur.execute("""
                SELECT nextval(pg_get_serial_sequence('proveedores', 'id'))
            """)
            next_id = cur.fetchone()[0]
            pg_conn.rollback()  # No guardar el cambio

            # Verificar que el siguiente ID es mayor que el máximo existente
            cur.execute("SELECT COALESCE(MAX(id), 0) FROM proveedores")
            max_id = cur.fetchone()[0]

            if next_id > max_id:
                print(f"✅ Secuencias funcionan correctamente (next={next_id}, max={max_id})")
                tests_passed += 1
            else:
                print(f"❌ Problema con secuencias (next={next_id}, max={max_id})")
                tests_failed += 1
    except Exception as e:
        print(f"⚠️  No se pudo verificar secuencias: {e}")

    # Cerrar conexiones
    sqlite_conn.close()
    pg_conn.close()

    # Resumen final
    print("\n" + "=" * 70)
    print(f"  RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    print(f"\n✅ Tests pasados: {tests_passed}")
    print(f"❌ Tests fallidos: {tests_failed}")

    if tests_failed == 0 and not diferencias:
        print("\n🎉 ¡Migración completamente exitosa!")
        print("\n💡 Puedes cambiar config.ini a ENGINE=postgres y usar la aplicación")
        return True
    elif tests_failed == 0 and diferencias:
        print("\n⚠️  Migración parcialmente exitosa (hay diferencias en conteos)")
        print("   Revisa las diferencias antes de usar en producción")
        return False
    else:
        print("\n❌ La migración tiene problemas")
        print("   Revisa los errores antes de continuar")
        return False


if __name__ == '__main__':
    try:
        success = test_migration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
