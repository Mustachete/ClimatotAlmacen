"""
Sistema de Manejo de Errores Centralizado
Este módulo proporciona decoradores y funciones para manejar errores de forma uniforme
"""
import functools
import traceback
from PySide6.QtWidgets import QMessageBox
from src.core.logger import logger, log_error_bd

# ========================================
# DECORADOR PARA FUNCIONES DE BASE DE DATOS
# ========================================

def handle_db_errors(operation_name: str = "operación"):
    """
    Decorador para capturar errores de base de datos automáticamente
    
    Uso:
        @handle_db_errors("crear_articulo")
        def crear_articulo(self, datos):
            # ... código que puede fallar ...
    
    Args:
        operation_name: Nombre de la operación para logs
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Registrar en logs
                module_name = func.__module__.split('.')[-1]
                log_error_bd(module_name, operation_name, e)
                
                # Mostrar mensaje al usuario
                error_msg = str(e)
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                
                QMessageBox.critical(
                    None,
                    "❌ Error de Base de Datos",
                    f"Error al ejecutar {operation_name}:\n\n{error_msg}\n\n"
                    f"Revisa los logs para más detalles."
                )
                
                # Registrar traza completa en logs (nivel DEBUG)
                logger.debug(f"Traza completa del error:\n{traceback.format_exc()}")
                
                return None
        return wrapper
    return decorator

# ========================================
# DECORADOR PARA FUNCIONES GENERALES
# ========================================

def handle_errors(operation_name: str = "operación", show_dialog: bool = True):
    """
    Decorador para capturar errores generales
    
    Args:
        operation_name: Nombre de la operación para logs
        show_dialog: Si True, muestra un diálogo de error al usuario
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Registrar en logs
                module_name = func.__module__.split('.')[-1]
                logger.error(f"ERROR | {module_name} | {operation_name} | {type(e).__name__}: {str(e)}")
                logger.debug(f"Traza completa:\n{traceback.format_exc()}")
                
                # Mostrar mensaje al usuario si está habilitado
                if show_dialog:
                    error_msg = str(e)
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200] + "..."
                    
                    QMessageBox.warning(
                        None,
                        "⚠️ Error",
                        f"Error al ejecutar {operation_name}:\n\n{error_msg}"
                    )
                
                return None
        return wrapper
    return decorator

# ========================================
# FUNCIONES DE AYUDA
# ========================================

def show_error(title: str, message: str, details: str = None):
    """
    Muestra un mensaje de error al usuario y lo registra en logs
    
    Args:
        title: Título del diálogo
        message: Mensaje principal
        details: Detalles adicionales (opcional)
    """
    logger.error(f"ERROR MOSTRADO AL USUARIO | {title} | {message}")
    if details:
        logger.debug(f"Detalles: {details}")
    
    full_message = message
    if details:
        full_message += f"\n\nDetalles:\n{details}"
    
    QMessageBox.critical(None, title, full_message)

def show_warning(title: str, message: str):
    """
    Muestra una advertencia al usuario y la registra en logs
    
    Args:
        title: Título del diálogo
        message: Mensaje de advertencia
    """
    logger.warning(f"ADVERTENCIA MOSTRADA | {title} | {message}")
    QMessageBox.warning(None, title, message)

def show_info(title: str, message: str):
    """
    Muestra un mensaje informativo al usuario y lo registra en logs
    
    Args:
        title: Título del diálogo
        message: Mensaje informativo
    """
    logger.info(f"INFO MOSTRADA | {title} | {message}")
    QMessageBox.information(None, title, message)

# ========================================
# VALIDACIÓN CON LOGGING
# ========================================

def validate_field(field_name: str, value, condition: bool, error_message: str, module: str = "validacion") -> bool:
    """
    Valida un campo y registra si falla
    
    Args:
        field_name: Nombre del campo
        value: Valor a validar
        condition: Condición que debe cumplirse (True = válido)
        error_message: Mensaje si falla la validación
        module: Nombre del módulo para logs
    
    Returns:
        True si válido, False si inválido
    
    Ejemplo:
        if not validate_field("operario", operario_id, operario_id is not None, "Debe seleccionar un operario"):
            return False
    """
    if not condition:
        from src.core.logger import log_validacion
        log_validacion(module, field_name, error_message)
        return False
    return True