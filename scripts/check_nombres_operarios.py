"""
Comparar nombres de operarios en ambas tablas
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "almacen.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("NOMBRES EN TABLA OPERARIOS:")
print("-" * 50)
cursor.execute("SELECT id, nombre FROM operarios ORDER BY id")
operarios = cursor.fetchall()
for op in operarios:
    # Usar repr para mostrar el string exacto
    print(f"ID {op['id']:2d}: {repr(op['nombre'])}")

print("\n\nNOMBRES EN TABLA FURGONETAS_ASIGNACIONES:")
print("-" * 50)
cursor.execute("SELECT DISTINCT operario FROM furgonetas_asignaciones ORDER BY operario")
asignaciones = cursor.fetchall()
for a in asignaciones:
    print(f"  {repr(a['operario'])}")

print("\n\nCOMPARACION:")
print("-" * 50)
cursor.execute("SELECT DISTINCT fa.operario FROM furgonetas_asignaciones fa")
nombres_asignados = {row['operario'] for row in cursor.fetchall()}

cursor.execute("SELECT nombre FROM operarios")
nombres_operarios = {row['nombre'] for row in cursor.fetchall()}

print(f"\nNombres en asignaciones que NO estan en operarios:")
for nombre in nombres_asignados:
    if nombre not in nombres_operarios:
        print(f"  - {repr(nombre)}")

print(f"\nNombres en operarios:")
for nombre in nombres_operarios:
    print(f"  - {repr(nombre)}")

conn.close()
