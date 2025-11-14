#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las asignaciones de furgonetas a operarios
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import fetch_all, fetch_one
from src.services.furgonetas_service import (
    asignar_furgoneta_a_operario,
    obtener_furgoneta_operario,
    listar_asignaciones_operario
)

print("=" * 80)
print("TEST DE ASIGNACIONES FURGONETA-OPERARIO")
print("=" * 80)

# 1. Obtener primer operario
operario = fetch_one("SELECT id, nombre FROM operarios LIMIT 1")
if not operario:
    print("ERROR: No hay operarios en el sistema")
    sys.exit(1)

operario_id = operario['id']
operario_nombre = operario['nombre']
print(f"\n1. Operario de prueba:")
print(f"   ID: {operario_id}")
print(f"   Nombre: {operario_nombre}")

# 2. Obtener primera furgoneta
furgoneta = fetch_one("SELECT id, nombre FROM almacenes WHERE tipo = 'furgoneta' LIMIT 1")
if not furgoneta:
    print("ERROR: No hay furgonetas en el sistema")
    sys.exit(1)

furgoneta_id = furgoneta['id']
furgoneta_nombre = furgoneta['nombre']
print(f"\n2. Furgoneta de prueba:")
print(f"   ID: {furgoneta_id}")
print(f"   Nombre: {furgoneta_nombre}")

# 3. Crear asignación
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
turno = 'completo'

print(f"\n3. Asignando furgoneta...")
print(f"   Operario: {operario_nombre} (ID: {operario_id})")
print(f"   Furgoneta: {furgoneta_nombre} (ID: {furgoneta_id})")
print(f"   Fecha: {fecha_hoy}")
print(f"   Turno: {turno}")

try:
    resultado = asignar_furgoneta_a_operario(operario_id, furgoneta_id, fecha_hoy, turno)
    print(f"\n   Resultado: {resultado}")

    if resultado:
        print("   ✅ Asignación exitosa")
    else:
        print("   ❌ La función devolvió False")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar en base de datos directamente
print(f"\n4. Verificando en BD (consulta directa):")
asig = fetch_one("""
    SELECT * FROM asignaciones_furgoneta
    WHERE operario_id = ? AND fecha = ? AND turno = ?
""", (operario_id, fecha_hoy, turno))

if asig:
    print(f"   ✅ Registro encontrado:")
    print(f"      Operario ID: {asig['operario_id']}")
    print(f"      Furgoneta ID: {asig['furgoneta_id']}")
    print(f"      Fecha: {asig['fecha']}")
    print(f"      Turno: {asig['turno']}")
else:
    print(f"   ❌ NO SE ENCONTRÓ registro en BD")

# 5. Obtener usando función del servicio
print(f"\n5. Consultando usando servicio:")
furg_asignada = obtener_furgoneta_operario(operario_id, fecha_hoy, turno)

if furg_asignada:
    print(f"   ✅ Furgoneta asignada:")
    print(f"      ID: {furg_asignada.get('furgoneta_id')}")
    print(f"      Nombre: {furg_asignada.get('furgoneta_nombre')}")
else:
    print(f"   ❌ No se obtuvo furgoneta asignada")

# 6. Listar todas las asignaciones del operario
print(f"\n6. Todas las asignaciones del operario:")
asignaciones = listar_asignaciones_operario(operario_id)

if asignaciones:
    print(f"   Total: {len(asignaciones)}")
    for i, asig in enumerate(asignaciones[:5]):  # Primeras 5
        print(f"\n   [{i+1}] Fecha: {asig['fecha']}, Turno: {asig['turno']}")
        print(f"       Furgoneta: {asig['furgoneta_nombre']} (ID: {asig['furgoneta_id']})")
else:
    print(f"   ❌ No hay asignaciones registradas")

print("\n" + "=" * 80)
print("FIN DEL TEST")
print("=" * 80)
