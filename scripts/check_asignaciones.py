"""
Script simple para verificar asignaciones en la base de datos
"""
import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent.parent / "db" / "almacen.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("VERIFICACION DE ASIGNACIONES DE FURGONETAS")
print("=" * 60)

# Verificar si existe la tabla
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='furgonetas_asignaciones'")
if cursor.fetchone():
    print("\n[OK] Tabla furgonetas_asignaciones existe")

    # Ver estructura
    cursor.execute("PRAGMA table_info(furgonetas_asignaciones)")
    print("\nEstructura:")
    for col in cursor.fetchall():
        print(f"  {col['name']}: {col['type']}")

    # Ver contenido
    cursor.execute("SELECT * FROM furgonetas_asignaciones")
    asignaciones = cursor.fetchall()
    print(f"\nRegistros: {len(asignaciones)}")

    for a in asignaciones:
        print(f"  ID: {a['id']}")
        print(f"    Furgoneta ID: {a['furgoneta_id']}")
        print(f"    Operario: {a['operario']}")
        print(f"    Desde: {a['desde']}")
        print(f"    Hasta: {a['hasta']}")
        print()
else:
    print("\n[ERROR] Tabla furgonetas_asignaciones NO existe")

# Probar la consulta corregida
print("\n" + "=" * 60)
print("PRUEBA DE CONSULTA CORREGIDA")
print("=" * 60)

operario_nombre = "Antonio Rodríguez"
fecha_hoy = date.today().strftime("%Y-%m-%d")

sql = """
    SELECT f.id AS furgoneta_id,
           CASE WHEN f.numero IS NOT NULL
                THEN 'Furgoneta ' || f.numero || ' - ' || f.matricula
                ELSE f.matricula
           END AS furgoneta_nombre
    FROM furgonetas_asignaciones fa
    JOIN furgonetas f ON fa.furgoneta_id = f.id
    WHERE fa.operario = ?
      AND fa.desde <= ?
      AND (fa.hasta IS NULL OR fa.hasta >= ?)
    ORDER BY fa.desde DESC
    LIMIT 1
"""

cursor.execute(sql, (operario_nombre, fecha_hoy, fecha_hoy))
resultado = cursor.fetchone()

if resultado:
    print(f"\n[OK] Furgoneta encontrada para '{operario_nombre}':")
    print(f"  ID: {resultado['furgoneta_id']}")
    print(f"  Nombre: {resultado['furgoneta_nombre']}")
else:
    print(f"\n[INFO] No se encontró asignación para '{operario_nombre}' en {fecha_hoy}")

conn.close()
print("\n" + "=" * 60)
