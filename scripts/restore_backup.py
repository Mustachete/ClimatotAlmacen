"""
Script para restaurar un backup
Uso: python scripts/restore_backup.py
"""
import sys
from pathlib import Path

# Agregar la ruta raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backup_db import listar_backups, restaurar_backup, BACKUP_DIR

print("📋 Backups disponibles:")
backups = listar_backups()

for i, (nombre, fecha, tamanio) in enumerate(backups, 1):
    print(f"{i}. {nombre} - {fecha.strftime('%Y-%m-%d %H:%M:%S')} - {tamanio:.2f} MB")

if not backups:
    print("❌ No hay backups disponibles")
    exit()

try:
    opcion = int(input("\n¿Qué backup deseas restaurar? (número): "))
    if 1 <= opcion <= len(backups):
        backup_seleccionado = BACKUP_DIR / backups[opcion - 1][0]
        
        confirmacion = input(f"\n⚠️  ¿Estás seguro de restaurar {backups[opcion - 1][0]}? (SI/NO): ")
        if confirmacion.upper() == "SI":
            if restaurar_backup(backup_seleccionado):
                print("✅ Backup restaurado exitosamente")
            else:
                print("❌ Error al restaurar backup")
        else:
            print("❌ Operación cancelada")
    else:
        print("❌ Opción inválida")
except ValueError:
    print("❌ Debes introducir un número")