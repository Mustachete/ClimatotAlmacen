"""
Script para probar la asignación de furgonetas
"""
import sys
from pathlib import Path
from datetime import date

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.repos.movimientos_repo import get_furgoneta_asignada, get_operarios_activos
from src.repos.furgonetas_repo import ensure_schema, list_furgonetas, estado_actual
from src.services.furgonetas_service import reasignar_furgoneta

print("=" * 70)
print("PRUEBA DE ASIGNACION DE FURGONETAS")
print("=" * 70)

# Asegurar que el schema existe
ensure_schema()

print("\n1. OPERARIOS ACTIVOS:")
print("-" * 70)
operarios = get_operarios_activos()
for op in operarios:
    print(f"  ID: {op['id']} - Nombre: {op['nombre']} - Rol: {op.get('rol_operario', 'N/A')}")

print("\n2. FURGONETAS DISPONIBLES:")
print("-" * 70)
furgonetas = list_furgonetas(include_inactive=False)
for f in furgonetas:
    numero = f.get('numero', 'N/A')
    matricula = f.get('matricula', 'N/A')
    print(f"  ID: {f['id']} - Número: {numero} - Matrícula: {matricula}")

print("\n3. ESTADO ACTUAL DE ASIGNACIONES:")
print("-" * 70)
estado = estado_actual()
if estado:
    for e in estado:
        furg_id = e.get('furgoneta_id', 'N/A')
        matricula = e.get('matricula', 'N/A')
        numero = e.get('numero', 'N/A')
        operario = e.get('operario_actual', 'Sin asignar')
        desde = e.get('desde', 'N/A')
        print(f"  Furgoneta {numero} ({matricula}): {operario} (desde {desde})")
else:
    print("  No hay asignaciones registradas")

print("\n4. PRUEBA DE CONSULTA get_furgoneta_asignada:")
print("-" * 70)
if operarios:
    operario_id = operarios[0]['id']
    operario_nombre = operarios[0]['nombre']
    fecha_hoy = date.today().strftime("%Y-%m-%d")

    print(f"  Buscando furgoneta para operario ID={operario_id} ({operario_nombre}) en fecha {fecha_hoy}")

    resultado = get_furgoneta_asignada(operario_id, fecha_hoy)

    if resultado:
        print(f"  ✓ ENCONTRADA: {resultado['furgoneta_nombre']} (ID: {resultado['furgoneta_id']})")
    else:
        print(f"  ✗ No se encontró asignación para este operario en esta fecha")
else:
    print("  No hay operarios para probar")

print("\n5. PRUEBA DE TODOS LOS OPERARIOS:")
print("-" * 70)
fecha_hoy = date.today().strftime("%Y-%m-%d")
for op in operarios:
    resultado = get_furgoneta_asignada(op['id'], fecha_hoy)
    if resultado:
        print(f"  ✓ {op['nombre']}: {resultado['furgoneta_nombre']}")
    else:
        print(f"  ✗ {op['nombre']}: Sin furgoneta asignada")

print("\n" + "=" * 70)
print("PRUEBA COMPLETADA")
print("=" * 70)
