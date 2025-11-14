"""
Script para verificar la estructura de la base de datos
"""
import sqlite3
import sys
from pathlib import Path

# Ruta a la base de datos
DB_PATH = Path(__file__).parent.parent / "db" / "almacen.db"

print("=" * 60)
print("VERIFICACION DE LA BASE DE DATOS")
print("=" * 60)

if not DB_PATH.exists():
    print(f"\n[ERROR] La base de datos no existe en: {DB_PATH}")
    sys.exit(1)

print(f"\n[OK] Base de datos encontrada en: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener lista de tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tablas = cursor.fetchall()

    print(f"\n[TABLAS] Se encontraron {len(tablas)} tablas:")
    for tabla in tablas:
        print(f"  - {tabla[0]}")

    # Verificar estructura de cada tabla
    print("\n" + "=" * 60)
    print("ESTRUCTURA DE LAS TABLAS")
    print("=" * 60)

    for tabla in tablas:
        nombre_tabla = tabla[0]
        cursor.execute(f"PRAGMA table_info({nombre_tabla});")
        columnas = cursor.fetchall()

        print(f"\n[{nombre_tabla}] - {len(columnas)} columnas:")
        for col in columnas:
            col_id, nombre, tipo, not_null, default, pk = col
            pk_str = " [PK]" if pk else ""
            not_null_str = " NOT NULL" if not_null else ""
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  {col_id}. {nombre}: {tipo}{pk_str}{not_null_str}{default_str}")

    # Contar registros en cada tabla
    print("\n" + "=" * 60)
    print("CONTEO DE REGISTROS")
    print("=" * 60)

    for tabla in tablas:
        nombre_tabla = tabla[0]
        cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla};")
        count = cursor.fetchone()[0]
        print(f"  {nombre_tabla}: {count} registros")

    conn.close()

    print("\n" + "=" * 60)
    print("[OK] VERIFICACION COMPLETADA EXITOSAMENTE")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Error al verificar la base de datos: {e}")
    sys.exit(1)
