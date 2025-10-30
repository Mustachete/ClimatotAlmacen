"""
Script de prueba del sistema de logging
Ejecutar: python scripts/test_logger.py
"""
import sys
from pathlib import Path

# Agregar la ruta raíz del proyecto al path de Python
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ahora sí podemos importar
from src.core.logger import logger, log_inicio_sesion, log_operacion, log_error_bd

print("🔍 Probando el sistema de logging...")
print("-" * 50)

# Prueba 1: Mensaje simple
logger.info("Esto es una prueba de INFO")
logger.warning("Esto es una prueba de WARNING")
logger.error("Esto es una prueba de ERROR")

# Prueba 2: Funciones de ayuda
log_inicio_sesion("admin", "PC-ALMACEN")
log_operacion("pedidos", "crear", "admin", "Pedido #123 creado con 5 artículos")

# Prueba 3: Simular un error de BD
try:
    # Esto va a fallar adrede
    resultado = 10 / 0
except Exception as e:
    log_error_bd("movimientos", "insertar", e)

print("-" * 50)
print("✅ Pruebas completadas")
print("📁 Revisa el archivo: logs/climatot.log")