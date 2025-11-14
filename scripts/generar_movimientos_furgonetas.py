#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar movimientos de furgonetas basándose en asignaciones existentes.
"""
import sys
import io
import random
from pathlib import Path
from datetime import datetime

# Configurar encoding UTF-8 para la salida
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import execute_query, fetch_all, fetch_one

print("=" * 60)
print("GENERANDO MOVIMIENTOS PARA FURGONETAS")
print("=" * 60)

# Obtener almacén principal
almacen = fetch_one("SELECT id FROM almacenes WHERE tipo = 'almacen' LIMIT 1")
if not almacen:
    print("ERROR: No se encontro almacen principal")
    sys.exit(1)

almacen_id = almacen['id']
print(f"\nAlmacen Principal ID: {almacen_id}")

# Obtener artículos
articulos = fetch_all("SELECT id, u_medida FROM articulos WHERE activo = 1 LIMIT 100")
articulos_ids = [a['id'] for a in articulos]
print(f"Articulos disponibles: {len(articulos_ids)}")

# Obtener asignaciones desde 27/10/2024
asignaciones = fetch_all("""
    SELECT * FROM asignaciones_furgoneta
    WHERE fecha >= '2024-10-27'
    ORDER BY fecha
""")
print(f"Asignaciones encontradas: {len(asignaciones)}")

if len(asignaciones) == 0:
    print("ERROR: No hay asignaciones para generar movimientos")
    sys.exit(1)

entregas = 0
imputaciones = 0
devoluciones = 0

print("\nGenerando movimientos...")

# Procesar cada asignación
for asig in asignaciones:
    fecha = asig['fecha']
    furgoneta_id = asig['furgoneta_id']
    operario_id = asig['operario_id']

    # 1. ENTREGA diaria (almacen -> furgoneta)
    # Cada día, entregar 2-4 artículos diferentes
    num_arts = random.randint(2, 4)
    arts_entregar = random.sample(articulos_ids, min(num_arts, len(articulos_ids)))

    for art_id in arts_entregar:
        articulo = next((a for a in articulos if a['id'] == art_id), None)
        if articulo:
            # Cantidad según tipo
            if articulo['u_medida'] in ['kg', 'metro']:
                cantidad = random.randint(2, 10)
            elif articulo['u_medida'] == 'rollo':
                cantidad = random.randint(1, 3)
            else:
                cantidad = random.randint(5, 20)

            try:
                execute_query("""
                    INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id)
                    VALUES (?, 'TRASPASO', ?, ?, ?, ?, ?)
                """, (fecha, art_id, cantidad, almacen_id, furgoneta_id, operario_id))
                entregas += 1
            except Exception as e:
                print(f"Error entrega: {e}")
                pass

    # 2. IMPUTACION (30% de probabilidad)
    if random.random() < 0.3:
        art_id = random.choice(articulos_ids)
        articulo = next((a for a in articulos if a['id'] == art_id), None)
        if articulo:
            if articulo['u_medida'] in ['kg', 'metro']:
                cantidad = random.uniform(0.5, 5.0)
            elif articulo['u_medida'] == 'rollo':
                cantidad = random.uniform(0.1, 1.0)
            else:
                cantidad = random.randint(1, 5)

            ot = f"OT{random.randint(1000, 9999)}"

            try:
                execute_query("""
                    INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id, ot)
                    VALUES (?, 'IMPUTACION', ?, ?, ?, NULL, ?, ?)
                """, (fecha, art_id, cantidad, furgoneta_id, operario_id, ot))
                imputaciones += 1
            except Exception as e:
                print(f"Error imputacion: {e}")
                pass

    # 3. DEVOLUCION (10% de probabilidad)
    if random.random() < 0.1:
        art_id = random.choice(articulos_ids)
        articulo = next((a for a in articulos if a['id'] == art_id), None)
        if articulo:
            if articulo['u_medida'] in ['kg', 'metro']:
                cantidad = random.uniform(1.0, 5.0)
            elif articulo['u_medida'] == 'rollo':
                cantidad = 1.0
            else:
                cantidad = random.randint(1, 10)

            try:
                execute_query("""
                    INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id)
                    VALUES (?, 'DEVOLUCION', ?, ?, ?, ?, ?)
                """, (fecha, art_id, cantidad, furgoneta_id, almacen_id, operario_id))
                devoluciones += 1
            except Exception as e:
                print(f"Error devolucion: {e}")
                pass

print("\n" + "=" * 60)
print("PROCESO COMPLETADO")
print("=" * 60)
print(f"\nMovimientos generados:")
print(f"  - Entregas (almacen -> furgoneta): {entregas}")
print(f"  - Imputaciones (furgoneta -> OT): {imputaciones}")
print(f"  - Devoluciones (furgoneta -> almacen): {devoluciones}")
print(f"  TOTAL: {entregas + imputaciones + devoluciones}")
print("\nAhora puedes generar informes de furgonetas!\n")
