"""
Servicio de Familias - Lógica de negocio para gestión de familias de artículos
"""
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from src.repos import familias_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """Valida que el nombre de la familia sea válido."""
    if not nombre or not nombre.strip():
        log_validacion("familias", "nombre", "Nombre vacío")
        return False, "El nombre de la familia es obligatorio"

    if len(nombre.strip()) < 2:
        log_validacion("familias", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 2 caracteres"

    if len(nombre.strip()) > 100:
        log_validacion("familias", "nombre", f"Nombre muy largo: {len(nombre)}")
        return False, "El nombre no puede exceder 100 caracteres"

    return True, ""


def validar_nombre_unico(nombre: str, familia_id: Optional[int] = None) -> Tuple[bool, str]:
    """Valida que el nombre de la familia sea único."""
    existente = familias_repo.get_by_nombre(nombre)
    if existente:
        if familia_id and existente['id'] == familia_id:
            return True, ""
        log_validacion("familias", "nombre", f"Nombre duplicado: {nombre}")
        return False, f"Ya existe una familia con el nombre '{nombre}'"
    return True, ""


def crear_familia(nombre: str, usuario: str = "admin") -> Tuple[bool, str, Optional[int]]:
    """Crea una nueva familia con validaciones."""
    try:
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error, None

        valido, error = validar_nombre_unico(nombre)
        if not valido:
            return False, error, None

        nombre = nombre.strip()
        familia_id = familias_repo.crear_familia(nombre)

        log_operacion("familias", "crear", usuario, f"Familia ID: {familia_id}, Nombre: {nombre}")
        logger.info(f"Familia creada | ID: {familia_id} | {nombre}")

        return True, f"Familia '{nombre}' creada correctamente", familia_id

    except sqlite3.IntegrityError:
        return False, f"Ya existe una familia con el nombre '{nombre}'", None
    except Exception as e:
        log_error_bd("familias", "crear_familia", e)
        return False, f"Error al crear familia: {str(e)}", None


def actualizar_familia(familia_id: int, nombre: str, usuario: str = "admin") -> Tuple[bool, str]:
    """Actualiza una familia existente con validaciones."""
    try:
        familia = familias_repo.get_by_id(familia_id)
        if not familia:
            return False, f"No se encontró la familia con ID {familia_id}"

        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        valido, error = validar_nombre_unico(nombre, familia_id)
        if not valido:
            return False, error

        nombre = nombre.strip()
        familias_repo.actualizar_familia(familia_id, nombre)

        log_operacion("familias", "actualizar", usuario, f"Familia ID: {familia_id}, Nombre: {nombre}")
        logger.info(f"Familia actualizada | ID: {familia_id} | {nombre}")

        return True, f"Familia '{nombre}' actualizada correctamente"

    except sqlite3.IntegrityError:
        return False, f"Ya existe otra familia con el nombre '{nombre}'"
    except Exception as e:
        log_error_bd("familias", "actualizar_familia", e)
        return False, f"Error al actualizar familia: {str(e)}"


def eliminar_familia(familia_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """Elimina una familia."""
    try:
        familia = familias_repo.get_by_id(familia_id)
        if not familia:
            return False, f"No se encontró la familia con ID {familia_id}"

        nombre = familia['nombre']

        tiene_articulos = familias_repo.verificar_articulos(familia_id)
        if tiene_articulos:
            return False, (
                f"La familia '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar una familia que está siendo usada."
            )

        familias_repo.eliminar_familia(familia_id)

        log_operacion("familias", "eliminar", usuario, f"Familia ID: {familia_id}, Nombre: {nombre}")
        logger.info(f"Familia eliminada | ID: {familia_id} | {nombre}")

        return True, f"Familia '{nombre}' eliminada correctamente"

    except sqlite3.IntegrityError:
        return False, "La familia tiene artículos asociados y no se puede eliminar"
    except Exception as e:
        log_error_bd("familias", "eliminar_familia", e)
        return False, f"Error al eliminar familia: {str(e)}"


def obtener_familias(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtiene lista de familias con filtros."""
    try:
        return familias_repo.get_todos(filtro_texto=filtro_texto, limit=limit)
    except Exception as e:
        log_error_bd("familias", "obtener_familias", e)
        return []


def obtener_familia(familia_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una familia específica por ID."""
    try:
        return familias_repo.get_by_id(familia_id)
    except Exception as e:
        log_error_bd("familias", "obtener_familia", e)
        return None
