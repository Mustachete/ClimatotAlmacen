#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicialización de base de datos PostgreSQL
Crea las tablas, vistas e índices en PostgreSQL
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

import configparser

def init_postgres_database():
    """Inicializa la base de datos PostgreSQL con el esquema"""

    print("=" * 60)
    print("  INICIALIZACIÓN DE BASE DE DATOS POSTGRESQL")
    print("=" * 60)

    # Leer configuración
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / "config.ini"

    if not config_path.exists():
        print("\n❌ ERROR: No se encontró config.ini")
        print("   Crea el archivo config.ini con los datos de conexión:")
        print("""
[database]
ENGINE = postgres
HOST = localhost
PORT = 5432
NAME = climatot_almacen_dev
USER = climatot
PASSWORD = tu_password
        """)
        return False

    config.read(config_path)

    # Verificar que sea PostgreSQL
    engine = config.get('database', 'ENGINE', fallback='sqlite').lower()
    if engine not in ('postgres', 'postgresql'):
        print(f"\n❌ ERROR: config.ini tiene ENGINE={engine}")
        print("   Debe ser 'postgres' para este script")
        return False

    # Mostrar configuración
    print(f"\n📋 Configuración:")
    print(f"   Host: {config.get('database', 'HOST')}")
    print(f"   Puerto: {config.get('database', 'PORT')}")
    print(f"   Base de datos: {config.get('database', 'NAME')}")
    print(f"   Usuario: {config.get('database', 'USER')}")

    # Verificar psycopg2
    try:
        import psycopg2
    except ImportError:
        print("\n❌ ERROR: psycopg2 no está instalado")
        print("   Ejecuta: pip install psycopg2-binary")
        return False

    # Verificar que existe schema_postgres.sql
    schema_path = PROJECT_ROOT / "db" / "schema_postgres.sql"
    if not schema_path.exists():
        print(f"\n❌ ERROR: No se encontró {schema_path}")
        return False

    print(f"\n📄 Schema encontrado: {schema_path.name}")

    # Conectar a PostgreSQL
    print("\n🔌 Conectando a PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=config.get('database', 'HOST'),
            port=config.getint('database', 'PORT'),
            database=config.get('database', 'NAME'),
            user=config.get('database', 'USER'),
            password=config.get('database', 'PASSWORD')
        )
        print("✅ Conexión establecida")
    except psycopg2.OperationalError as e:
        print(f"\n❌ ERROR de conexión:")
        print(f"   {e}")
        print("\n💡 Verifica que:")
        print("   1. PostgreSQL esté instalado y corriendo")
        print("   2. La base de datos exista (CREATE DATABASE climatot_almacen_dev;)")
        print("   3. El usuario tenga permisos (GRANT ALL PRIVILEGES...)")
        print("   4. Las credenciales en config.ini sean correctas")
        return False
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
        return False

    # Verificar si ya hay tablas
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tabla_count = cur.fetchone()[0]

    if tabla_count > 0:
        print(f"\n⚠️  ADVERTENCIA: La base de datos ya tiene {tabla_count} tablas")
        respuesta = input("   ¿Continuar de todas formas? (s/N): ").strip().lower()
        if respuesta != 's':
            print("\n❌ Operación cancelada por el usuario")
            conn.close()
            return False

    # Leer y ejecutar schema
    print("\n📝 Leyendo schema...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    print("⚙️  Ejecutando schema SQL...")
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()

        print("✅ Schema ejecutado correctamente")
    except Exception as e:
        print(f"\n❌ ERROR al ejecutar schema: {e}")
        conn.rollback()
        conn.close()
        return False

    # Verificar tablas creadas
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tablas = [row[0] for row in cur.fetchall()]

    print(f"\n✅ {len(tablas)} tablas creadas:")
    for tabla in tablas:
        print(f"   • {tabla}")

    # Verificar vistas
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        vistas = [row[0] for row in cur.fetchall()]

    if vistas:
        print(f"\n✅ {len(vistas)} vistas creadas:")
        for vista in vistas:
            print(f"   • {vista}")

    # Verificar índices
    with conn.cursor() as cur:
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey'
            ORDER BY indexname
        """)
        indices = [row[0] for row in cur.fetchall()]

    if indices:
        print(f"\n✅ {len(indices)} índices creados:")
        for indice in indices:
            print(f"   • {indice}")

    conn.close()

    print("\n" + "=" * 60)
    print("  ✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("=" * 60)
    print("\n💡 Próximos pasos:")
    print("   1. Ejecutar: python scripts/migrate_sqlite_to_postgres.py")
    print("      (para migrar datos desde SQLite)")
    print("   2. Ejecutar: python scripts/test_postgres_migration.py")
    print("      (para validar la migración)")
    print("   3. Ejecutar: python app.py")
    print("      (para probar la aplicación con PostgreSQL)\n")

    return True


if __name__ == '__main__':
    try:
        success = init_postgres_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
