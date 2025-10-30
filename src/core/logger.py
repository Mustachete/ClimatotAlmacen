"""
Sistema de Logging Centralizado para ClimatotAlmacen
Este módulo configura el logging de toda la aplicación
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ========================================
# CONFIGURACIÓN DEL LOGGER
# ========================================

# Crear carpeta de logs si no existe
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Archivo principal de logs
LOG_FILE = LOG_DIR / "climatot.log"

# Crear el logger principal
logger = logging.getLogger("ClimatotAlmacen")
logger.setLevel(logging.DEBUG)  # Captura TODO (desde DEBUG hasta CRITICAL)

# Evitar duplicados si ya está configurado
if not logger.handlers:
    
    # ========================================
    # HANDLER 1: Archivo rotativo
    # ========================================
    # Rotación: 10MB máximo, mantiene 20 archivos históricos
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=20,              # 20 archivos de respaldo
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formato para archivo: incluye TODO el detalle
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # ========================================
    # HANDLER 2: Consola (solo errores)
    # ========================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Solo warnings y errores en consola
    
    # Formato para consola: más simple
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# ========================================
# FUNCIONES DE AYUDA
# ========================================

def log_inicio_sesion(usuario: str, hostname: str):
    """Registra el inicio de sesión de un usuario"""
    logger.info(f"INICIO_SESION | Usuario: {usuario} | Host: {hostname}")

def log_fin_sesion(usuario: str, hostname: str):
    """Registra el cierre de sesión de un usuario"""
    logger.info(f"FIN_SESION | Usuario: {usuario} | Host: {hostname}")

def log_operacion(modulo: str, operacion: str, usuario: str, detalles: str = ""):
    """
    Registra una operación general
    
    Args:
        modulo: Nombre del módulo (ej: "pedidos", "movimientos")
        operacion: Acción realizada (ej: "crear", "modificar", "eliminar")
        usuario: Usuario que realiza la acción
        detalles: Información adicional
    """
    mensaje = f"{modulo.upper()} | {operacion} | Usuario: {usuario}"
    if detalles:
        mensaje += f" | {detalles}"
    logger.info(mensaje)

def log_error_bd(modulo: str, operacion: str, error: Exception):
    """
    Registra un error de base de datos
    
    Args:
        modulo: Módulo donde ocurrió el error
        operacion: Operación que falló
        error: Excepción capturada
    """
    logger.error(f"ERROR_BD | {modulo} | {operacion} | {type(error).__name__}: {str(error)}")

def log_validacion(modulo: str, campo: str, mensaje: str):
    """
    Registra un error de validación
    
    Args:
        modulo: Módulo donde ocurrió
        campo: Campo que falló la validación
        mensaje: Mensaje de error
    """
    logger.warning(f"VALIDACION | {modulo} | {campo} | {mensaje}")

# ========================================
# MENSAJE DE INICIO
# ========================================
logger.info("=" * 80)
logger.info(f"Sistema de logging inicializado | Archivo: {LOG_FILE}")
logger.info("=" * 80)