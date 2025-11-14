"""
Servicio de Ubicaciones - Lógica de negocio para gestión de ubicaciones del almacén
"""
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from src.repos import ubicaciones_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """Valida que el nombre de la ubicación sea válido."""
    if not nombre or not nombre.strip():
        log_validacion("ubicaciones", "nombre", "Nombre vacío")
        return False, "El nombre de la ubicación es obligatorio"

    if len(nombre.strip()) < 1:
        log_validacion("ubicaciones", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 1 carácter"

    if len(nombre.strip()) > 100:
        log_validacion("ubicaciones", "nombre", f"Nombre muy largo: {len(nombre)}")
        return False, "El nombre no puede exceder 100 caracteres"

    return True, ""


def validar_nombre_unico(nombre: str, ubicacion_id: Optional[int] = None) -> Tuple[bool, str]:
    """Valida que el nombre de la ubicación sea único."""
    existente = ubicaciones_repo.get_by_nombre(nombre)
    if existente:
        if ubicacion_id and existente['id'] == ubicacion_id:
            return True, ""
        log_validacion("ubicaciones", "nombre", f"Nombre duplicado: {nombre}")
        return False, f"Ya existe una ubicación con el nombre '{nombre}'"
    return True, ""


def crear_ubicacion(nombre: str, usuario: str = "admin") -> Tuple[bool, str, Optional[int]]:
    """Crea una nueva ubicación con validaciones."""
    try:
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error, None

        valido, error = validar_nombre_unico(nombre)
        if not valido:
            return False, error, None

        nombre = nombre.strip()
        ubicacion_id = ubicaciones_repo.crear_ubicacion(nombre)

        log_operacion("ubicaciones", "crear", usuario, f"Ubicación ID: {ubicacion_id}, Nombre: {nombre}")
        logger.info(f"Ubicación creada | ID: {ubicacion_id} | {nombre}")

        return True, f"Ubicación '{nombre}' creada correctamente", ubicacion_id

    except sqlite3.IntegrityError:
        return False, f"Ya existe una ubicación con el nombre '{nombre}'", None
    except Exception as e:
        log_error_bd("ubicaciones", "crear_ubicacion", e)
        return False, f"Error al crear ubicación: {str(e)}", None


def actualizar_ubicacion(ubicacion_id: int, nombre: str, usuario: str = "admin") -> Tuple[bool, str]:
    """Actualiza una ubicación existente con validaciones."""
    try:
        ubicacion = ubicaciones_repo.get_by_id(ubicacion_id)
        if not ubicacion:
            return False, f"No se encontró la ubicación con ID {ubicacion_id}"

        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        valido, error = validar_nombre_unico(nombre, ubicacion_id)
        if not valido:
            return False, error

        nombre = nombre.strip()
        ubicaciones_repo.actualizar_ubicacion(ubicacion_id, nombre)

        log_operacion("ubicaciones", "actualizar", usuario, f"Ubicación ID: {ubicacion_id}, Nombre: {nombre}")
        logger.info(f"Ubicación actualizada | ID: {ubicacion_id} | {nombre}")

        return True, f"Ubicación '{nombre}' actualizada correctamente"

    except sqlite3.IntegrityError:
        return False, f"Ya existe otra ubicación con el nombre '{nombre}'"
    except Exception as e:
        log_error_bd("ubicaciones", "actualizar_ubicacion", e)
        return False, f"Error al actualizar ubicación: {str(e)}"


def eliminar_ubicacion(ubicacion_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """Elimina una ubicación."""
    try:
        ubicacion = ubicaciones_repo.get_by_id(ubicacion_id)
        if not ubicacion:
            return False, f"No se encontró la ubicación con ID {ubicacion_id}"

        nombre = ubicacion['nombre']

        tiene_articulos = ubicaciones_repo.verificar_articulos(ubicacion_id)
        if tiene_articulos:
            return False, (
                f"La ubicación '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar una ubicación que está siendo usada."
            )

        ubicaciones_repo.eliminar_ubicacion(ubicacion_id)

        log_operacion("ubicaciones", "eliminar", usuario, f"Ubicación ID: {ubicacion_id}, Nombre: {nombre}")
        logger.info(f"Ubicación eliminada | ID: {ubicacion_id} | {nombre}")

        return True, f"Ubicación '{nombre}' eliminada correctamente"

    except sqlite3.IntegrityError:
        return False, "La ubicación tiene artículos asociados y no se puede eliminar"
    except Exception as e:
        log_error_bd("ubicaciones", "eliminar_ubicacion", e)
        return False, f"Error al eliminar ubicación: {str(e)}"


def obtener_ubicaciones(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtiene lista de ubicaciones con filtros."""
    try:
        return ubicaciones_repo.get_todos(filtro_texto=filtro_texto, limit=limit)
    except Exception as e:
        log_error_bd("ubicaciones", "obtener_ubicaciones", e)
        return []


def obtener_ubicacion(ubicacion_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una ubicación específica por ID."""
    try:
        return ubicaciones_repo.get_by_id(ubicacion_id)
    except Exception as e:
        log_error_bd("ubicaciones", "obtener_ubicacion", e)
        return None
