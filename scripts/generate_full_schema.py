#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar schema completo de PostgreSQL desde SQLite
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

import sqlite3

def sqlite_to_postgres_type(sqlite_type):
    """Convierte tipos de SQLite a PostgreSQL"""
    sqlite_type = sqlite_type.upper()

    if 'INT' in sqlite_type:
        return 'INTEGER'
    elif 'CHAR' in sqlite_type or 'TEXT' in sqlite_type or 'CLOB' in sqlite_type:
        return 'TEXT'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'NUMERIC(10,2)'
    elif 'BLOB' in sqlite_type:
        return 'BYTEA'
    elif 'BOOL' in sqlite_type:
        return 'SMALLINT'
    else:
        return 'TEXT'  # Default

def generate_postgres_schema():
    """Genera schema completo de PostgreSQL desde SQLite"""

    conn = sqlite3.connect('db/almacen.db')
    cursor = conn.cursor()

    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print("-- ========================================")
    print("-- SCHEMA POSTGRESQL COMPLETO - Generado automáticamente")
    print("-- ========================================\n")

    for table in tables:
        print(f"-- Tabla: {table}")

        # Obtener estructura de la tabla
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        print(f"CREATE TABLE IF NOT EXISTS {table} (")

        col_defs = []
        pk_cols = []

        for col in columns:
            col_id, col_name, col_type, not_null, default_val, is_pk = col

            # Tipo PostgreSQL
            if 'AUTOINCREMENT' in col_type or (is_pk and col_name == 'id'):
                pg_type = 'SERIAL PRIMARY KEY'
                is_pk = 0  # Ya lo manejamos aquí
            else:
                pg_type = sqlite_to_postgres_type(col_type)

            # Construir definición
            col_def = f"  {col_name} {pg_type}"

            # NOT NULL
            if not_null and 'SERIAL' not in pg_type:
                col_def += " NOT NULL"

            # DEFAULT
            if default_val is not None and 'SERIAL' not in pg_type:
                if default_val.lower() in ('null', "'null'"):
                    col_def += " DEFAULT NULL"
                elif default_val.startswith("'"):
                    col_def += f" DEFAULT {default_val}"
                elif default_val.isdigit() or default_val in ('0', '1', 'true', 'false'):
                    col_def += f" DEFAULT {default_val}"
                else:
                    col_def += f" DEFAULT '{default_val}'"

            col_defs.append(col_def)

            if is_pk:
                pk_cols.append(col_name)

        # PRIMARY KEY compuesta
        if pk_cols:
            col_defs.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")

        print(",\n".join(col_defs))
        print(");\n")

    # Obtener vistas
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name")
    views = cursor.fetchall()

    if views:
        print("\n-- ========================================")
        print("-- VISTAS")
        print("-- ========================================\n")
        for view_name, view_sql in views:
            print(f"-- Vista: {view_name}")
            print(view_sql.replace('CREATE VIEW', 'CREATE OR REPLACE VIEW') + ";\n")

    # Índices
    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    indexes = cursor.fetchall()

    if indexes:
        print("\n-- ========================================")
        print("-- ÍNDICES")
        print("-- ========================================\n")
        for idx_name, idx_sql in indexes:
            # Adaptar CREATE INDEX para PostgreSQL
            idx_sql_pg = idx_sql.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
            print(f"{idx_sql_pg};\n")

    conn.close()

if __name__ == '__main__':
    generate_postgres_schema()
