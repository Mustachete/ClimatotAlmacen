#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para debuggear asignaciones de furgonetas"""

import sys
import io
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

con = get_con()
cur = con.cursor()

print("=" * 70)
print("DEBUG: ASIGNACIONES DE FURGONETAS")
print("=" * 70)
print()

# 1. Ver estructura de almacenes
print("1. ALMACENES (con tipo):")
print("-" * 70)
cur.execute("""
    SELECT id, nombre, tipo
    FROM almacenes
    ORDER BY tipo, nombre
""")
almacenes = cur.fetchall()
for alm in almacenes:
    print(f"  ID: {alm[0]:3d} | Nombre: {alm[1]:30s} | Tipo: {alm[2]}")

print()

# 2. Ver furgonetas (almacenes tipo='furgoneta')
print("2. FURGONETAS (tipo='furgoneta'):")
print("-" * 70)
cur.execute("""
    SELECT id, nombre
    FROM almacenes
    WHERE tipo = 'furgoneta'
    ORDER BY nombre
""")
furgonetas = cur.fetchall()
if furgonetas:
    for furg in furgonetas:
        print(f"  ID: {furg[0]:3d} | Nombre: {furg[1]}")
else:
    print("  ⚠️ NO HAY FURGONETAS REGISTRADAS (tipo='furgoneta')")

print()

# 3. Ver asignaciones actuales
print("3. ASIGNACIONES ACTUALES:")
print("-" * 70)
cur.execute("""
    SELECT
        af.operario_id,
        o.nombre as operario_nombre,
        af.fecha,
        af.turno,
        af.furgoneta_id,
        a.nombre as furgoneta_nombre,
        a.tipo as almacen_tipo
    FROM asignaciones_furgoneta af
    JOIN operarios o ON af.operario_id = o.id
    JOIN almacenes a ON af.furgoneta_id = a.id
    ORDER BY af.fecha DESC, o.nombre
""")
asignaciones = cur.fetchall()
if asignaciones:
    for asig in asignaciones:
        print(f"  Operario: {asig[1]:20s} (ID:{asig[0]})")
        print(f"    -> Fecha: {asig[2]} | Turno: {asig[3]}")
        print(f"    -> Furgoneta ID: {asig[4]} | Nombre: {asig[5]}")
        print(f"    -> Tipo almacén: {asig[6]}")
        if asig[6] != 'furgoneta':
            print(f"       ⚠️ PROBLEMA: Este almacén NO es tipo 'furgoneta'!")
        print()
else:
    print("  ⚠️ NO HAY ASIGNACIONES REGISTRADAS")

print()

# 4. Verificar asignaciones de HOY
hoy = datetime.now().strftime("%Y-%m-%d")
print(f"4. ASIGNACIONES DE HOY ({hoy}):")
print("-" * 70)
cur.execute("""
    SELECT
        o.nombre as operario_nombre,
        af.turno,
        a.nombre as furgoneta_nombre,
        a.tipo as almacen_tipo
    FROM asignaciones_furgoneta af
    JOIN operarios o ON af.operario_id = o.id
    JOIN almacenes a ON af.furgoneta_id = a.id
    WHERE af.fecha = ?
    ORDER BY o.nombre, af.turno
""", (hoy,))
asignaciones_hoy = cur.fetchall()
if asignaciones_hoy:
    for asig in asignaciones_hoy:
        turno_emoji = {'manana': '🌅', 'tarde': '🌆', 'completo': '🕐'}
        emoji = turno_emoji.get(asig[1], '❓')
        print(f"  {emoji} {asig[0]:20s} -> {asig[2]} (tipo: {asig[3]})")
        if asig[3] != 'furgoneta':
            print(f"     ⚠️ PROBLEMA: Este almacén NO es tipo 'furgoneta'!")
else:
    print(f"  ℹ️ No hay asignaciones para hoy ({hoy})")

print()

# 5. Problema potencial: almacenes asignados que NO son furgonetas
print("5. DIAGNÓSTICO: Asignaciones a almacenes que NO son furgonetas:")
print("-" * 70)
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
    ORDER BY af.fecha DESC
""")
problemas = cur.fetchall()
if problemas:
    print("  ⚠️ ENCONTRADOS PROBLEMAS:")
    for prob in problemas:
        print(f"    Operario: {prob[0]}")
        print(f"    Fecha: {prob[1]} | Turno: {prob[2]}")
        print(f"    Asignado a: {prob[3]} (tipo: {prob[4]}) ❌")
        print()
else:
    print("  ✅ NO HAY PROBLEMAS: Todas las asignaciones apuntan a furgonetas válidas")

print()
print("=" * 70)

con.close()
