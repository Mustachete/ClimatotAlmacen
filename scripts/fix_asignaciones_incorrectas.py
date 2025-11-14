#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para limpiar asignaciones incorrectas (almacenes que no son furgonetas)"""

import sys
import io
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("LIMPIEZA: Asignaciones incorrectas (almacenes que no son furgonetas)")
print("=" * 70)
print()

con = get_con()
cur = con.cursor()

# 1. Detectar asignaciones incorrectas
print("1. Detectando asignaciones incorrectas...")
cur.execute("""
    SELECT
        o.nombre as operario_nombre,
        af.fecha,
        af.turno,
        a.nombre as almacen_nombre,
        a.tipo as almacen_tipo
    FROM asignaciones_furgoneta af
    JOIN operarios o ON af.operario_id = o.id
    JOIN almacenes a ON af.furgoneta_id = a.id
    WHERE a.tipo != 'furgoneta'
""")
incorrectas = cur.fetchall()

if not incorrectas:
    print("   ✅ No hay asignaciones incorrectas. Todo OK.")
    con.close()
    sys.exit(0)

print(f"   ⚠️ Encontradas {len(incorrectas)} asignaciones incorrectas:")
for asig in incorrectas:
    print(f"      - {asig[0]} -> {asig[3]} (tipo: {asig[4]}) en {asig[1]} turno {asig[2]}")

print()

# 2. Eliminar asignaciones incorrectas
print("2. Eliminando asignaciones incorrectas...")
cur.execute("""
    DELETE FROM asignaciones_furgoneta
    WHERE furgoneta_id IN (
        SELECT id FROM almacenes WHERE tipo != 'furgoneta'
    )
""")
eliminadas = cur.rowcount
con.commit()

print(f"   ✅ Eliminadas {eliminadas} asignaciones incorrectas")
print()

# 3. Verificar resultado
print("3. Verificando resultado...")
cur.execute("""
    SELECT COUNT(*)
    FROM asignaciones_furgoneta af
    JOIN almacenes a ON af.furgoneta_id = a.id
    WHERE a.tipo != 'furgoneta'
""")
restantes = cur.fetchone()[0]

if restantes == 0:
    print("   ✅ Todas las asignaciones son correctas ahora")
else:
    print(f"   ⚠️ Todavía quedan {restantes} asignaciones incorrectas")

print()
print("=" * 70)
print("LIMPIEZA COMPLETADA")
print("=" * 70)

con.close()
