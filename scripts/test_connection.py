#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba de conexión a PostgreSQL
Verifica que puedes conectar antes de migrar
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


def test_connection():
    """Prueba la conexión a PostgreSQL"""

    print("=" * 60)
    print("  TEST DE CONEXIÓN POSTGRESQL")
    print("=" * 60)

    # Leer configuración
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / "config.ini"

    if not config_path.exists():
        print("\n❌ ERROR: No se encontró config.ini")
        print("\n💡 Crea el archivo config.ini en la raíz del proyecto:")
        print("""
[database]
ENGINE = postgres
HOST = localhost
PORT = 5432
NAME = climatot_almacen_dev
USER = climatot
PASSWORD = Eduard90
        """)
        return False

    config.read(config_path)

    # Mostrar configuración
    print(f"\n📋 Configuración leída de config.ini:")
    print(f"   ENGINE: {config.get('database', 'ENGINE', fallback='(no definido)')}")
    print(f"   HOST: {config.get('database', 'HOST', fallback='(no definido)')}")
    print(f"   PORT: {config.get('database', 'PORT', fallback='(no definido)')}")
    print(f"   NAME: {config.get('database', 'NAME', fallback='(no definido)')}")
    print(f"   USER: {config.get('database', 'USER', fallback='(no definido)')}")
    print(f"   PASSWORD: {'*' * len(config.get('database', 'PASSWORD', fallback=''))}")

    # Verificar psycopg2
    print("\n🔍 Verificando psycopg2...")
    try:
        import psycopg2
        print(f"✅ psycopg2 instalado (versión: {psycopg2.__version__})")
    except ImportError:
        print("❌ psycopg2 NO está instalado")
        print("\n💡 Instálalo con: pip install psycopg2-binary")
        return False

    # Intentar conexión
    print("\n🔌 Intentando conectar a PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=config.get('database', 'HOST'),
            port=config.getint('database', 'PORT'),
            database=config.get('database', 'NAME'),
            user=config.get('database', 'USER'),
            password=config.get('database', 'PASSWORD')
        )

        print("✅ CONEXIÓN EXITOSA")

        # Obtener información del servidor
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\n📊 Información del servidor:")
            print(f"   {version[:60]}...")

            # Contar tablas
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            table_count = cur.fetchone()[0]
            print(f"\n📄 Tablas en la base de datos: {table_count}")

            if table_count > 0:
                # Listar tablas
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tablas = [row[0] for row in cur.fetchall()]
                print("   Tablas existentes:")
                for tabla in tablas[:10]:  # Mostrar máximo 10
                    print(f"   • {tabla}")
                if len(tablas) > 10:
                    print(f"   ... y {len(tablas) - 10} más")

        conn.close()

        print("\n" + "=" * 60)
        print("  ✅ TODO OK - PUEDES CONTINUAR CON LA MIGRACIÓN")
        print("=" * 60)

        if table_count == 0:
            print("\n💡 Próximo paso:")
            print("   python scripts/init_postgres.py")
        else:
            print("\n⚠️  La base de datos ya tiene tablas")
            print("   Si quieres reiniciar, elimina las tablas primero o crea una BD nueva")

        return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ ERROR DE CONEXIÓN:")
        print(f"   {e}")
        print("\n💡 Posibles causas:")
        print("   1. PostgreSQL no está instalado o no está corriendo")
        print("      - En Windows: Abre 'Servicios' y busca 'postgresql'")
        print("      - Debe estar en estado 'En ejecución'")
        print("\n   2. La base de datos no existe")
        print("      - Abre pgAdmin o psql y ejecuta:")
        print("        CREATE DATABASE climatot_almacen_dev;")
        print("\n   3. El usuario no existe o no tiene permisos")
        print("      - Ejecuta:")
        print("        CREATE USER climatot WITH PASSWORD 'Eduard90';")
        print("        GRANT ALL PRIVILEGES ON DATABASE climatot_almacen_dev TO climatot;")
        print("\n   4. Credenciales incorrectas en config.ini")
        print("      - Verifica usuario y password")
        return False

    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        return False


if __name__ == '__main__':
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
