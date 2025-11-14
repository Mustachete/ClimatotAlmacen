"""
Test simple de get_furgoneta_asignada
"""
import sys
from pathlib import Path
from datetime import date

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.repos.movimientos_repo import get_furgoneta_asignada

print("Test de get_furgoneta_asignada")
print("-" * 50)

# ID 4 es Antonio Rodríguez según vimos antes
operario_id = 4
fecha_hoy = date.today().strftime("%Y-%m-%d")

print(f"Buscando furgoneta para operario ID {operario_id} en fecha {fecha_hoy}")

try:
    resultado = get_furgoneta_asignada(operario_id, fecha_hoy)

    if resultado:
        print(f"\nRESULTADO:")
        print(f"  Furgoneta ID: {resultado['furgoneta_id']}")
        print(f"  Nombre: {resultado['furgoneta_nombre']}")
        print("\n[OK] Funcion funciona correctamente!")
    else:
        print("\n[INFO] No se encontro asignacion (esto puede ser normal si no hay asignacion activa)")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
