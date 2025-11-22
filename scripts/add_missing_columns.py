#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para añadir columnas faltantes en PostgreSQL
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


def add_missing_columns():
    """Añade columnas que faltan en la tabla articulos de PostgreSQL"""

    print("=" * 70)
    print("  AÑADIENDO COLUMNAS FALTANTES A POSTGRESQL")
    print("=" * 70)

    # Configuración
    config = configparser.ConfigParser()
    config_path = PROJECT_ROOT / "config.ini"
    config.read(config_path)

    try:
        import psycopg2
    except ImportError:
        print("\nERROR: psycopg2 no está instalado")
        return False

    # Conectar PostgreSQL
    print("\nConectando a PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=config.get('database', 'HOST'),
        port=config.getint('database', 'PORT'),
        database=config.get('database', 'NAME'),
        user=config.get('database', 'USER'),
        password=config.get('database', 'PASSWORD')
    )

    # Columnas a añadir
    columnas_nuevas = [
        ("unidad_compra", "NUMERIC(10,2) DEFAULT NULL"),
        ("dias_seguridad", "INTEGER DEFAULT 5"),
        ("critico", "SMALLINT DEFAULT 0"),
        ("notas", "TEXT DEFAULT NULL"),
    ]

    print("\nAñadiendo columnas a la tabla 'articulos'...\n")

    with pg_conn.cursor() as cur:
        for nombre_col, definicion in columnas_nuevas:
            try:
                sql = f"ALTER TABLE articulos ADD COLUMN IF NOT EXISTS {nombre_col} {definicion}"
                cur.execute(sql)
                pg_conn.commit()
                print(f"  OK: {nombre_col} ({definicion})")
            except Exception as e:
                pg_conn.rollback()
                print(f"  ERROR en {nombre_col}: {e}")

    # Verificar columnas
    print("\nVerificando columnas finales...")
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'articulos'
            ORDER BY ordinal_position
        """)
        columnas = cur.fetchall()

    print(f"\nTabla 'articulos' tiene {len(columnas)} columnas:")
    for col in columnas:
        print(f"  - {col[0]} ({col[1]})")

    pg_conn.close()

    print("\n" + "=" * 70)
    print("  COLUMNAS AÑADIDAS CORRECTAMENTE")
    print("=" * 70)
    print("\nAhora ejecuta: python scripts/fix_migration.py")

    return True


if __name__ == '__main__':
    try:
        add_missing_columns()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
