#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir las secuencias de PostgreSQL
"""
import sys
import os
from pathlib import Path

# Configurar UTF-8 para la salida en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import configparser


def fix_sequences():
    """Corrige todas las secuencias de PostgreSQL"""

    print("Corrigiendo secuencias de PostgreSQL...")

    config = configparser.ConfigParser()
    config.read(PROJECT_ROOT / "config.ini")

    import psycopg2
    pg_conn = psycopg2.connect(
        host=config.get('database', 'HOST'),
        port=config.getint('database', 'PORT'),
        database=config.get('database', 'NAME'),
        user=config.get('database', 'USER'),
        password=config.get('database', 'PASSWORD')
    )

    # Obtener todas las tablas con columna 'id'
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = 'id'
        """)
        tablas = [row[0] for row in cur.fetchall()]

    print(f"\nActualizando {len(tablas)} secuencias...\n")

    with pg_conn.cursor() as cur:
        for tabla in tablas:
            try:
                # Obtener nombre de la secuencia
                cur.execute(f"SELECT pg_get_serial_sequence('{tabla}', 'id')")
                result = cur.fetchone()

                if result and result[0]:
                    seq_name = result[0]

                    # Obtener máximo ID actual
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {tabla}")
                    max_id = cur.fetchone()[0]

                    # Actualizar secuencia
                    cur.execute(f"SELECT setval('{seq_name}', {max_id}, true)")
                    pg_conn.commit()

                    # Verificar
                    cur.execute(f"SELECT nextval('{seq_name}')")
                    next_val = cur.fetchone()[0]
                    cur.execute(f"SELECT setval('{seq_name}', {next_val - 1}, true)")  # Revertir el nextval
                    pg_conn.commit()

                    print(f"  OK: {tabla:30} max_id={max_id:6} -> next={next_val}")

            except Exception as e:
                pg_conn.rollback()
                print(f"  ERROR: {tabla:30} {e}")

    pg_conn.close()
    print("\nSecuencias corregidas!")


if __name__ == '__main__':
    fix_sequences()
