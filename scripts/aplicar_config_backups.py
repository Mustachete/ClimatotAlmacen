"""
Script para aplicar la configuración de backups a la BD
"""
import sys
import sqlite3
from pathlib import Path

# Agregar la ruta raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.db_utils import DB_PATH

def aplicar_config_backups():
    """Aplica el script de configuración de backups"""
    sql_file = ROOT_DIR / "scripts" / "crear_config_backups.sql"

    if not sql_file.exists():
        print(f"No se encontro el archivo SQL: {sql_file}")
        return False

    print(f"Leyendo script: {sql_file}")
    sql_content = sql_file.read_text(encoding='utf-8')

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Ejecutar el script
        cursor.executescript(sql_content)
        conn.commit()

        print("Tabla config_backups creada exitosamente")

        # Mostrar configuración actual
        cursor.execute("SELECT * FROM config_backups")
        config = cursor.fetchone()

        if config:
            print("\nConfiguracion inicial:")
            print(f"  - Max Backups: {config[1]}")
            print(f"  - Multiples Diarios: {'Si' if config[2] else 'No'}")
            print(f"  - Auto Inicio: {'Si' if config[3] else 'No'}")
            print(f"  - Auto Cierre: {'Si' if config[4] else 'No'}")
            print(f"  - Retencion Dias: {config[5] if config[5] else 'Sin limite'}")
            print(f"  - Ruta: {config[6] if config[6] else 'Por defecto'}")

        conn.close()
        return True

    except Exception as e:
        print(f"Error al aplicar configuracion: {e}")
        return False

if __name__ == "__main__":
    print("Aplicando configuracion de backups...")
    print(f"Base de datos: {DB_PATH}")
    print("-" * 50)

    if aplicar_config_backups():
        print("\nConfiguracion aplicada correctamente")
    else:
        print("\nError al aplicar configuracion")
