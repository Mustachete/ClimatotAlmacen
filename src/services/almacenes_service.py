"""
Servicio de Almacenes - Lógica de negocio para gestión de almacenes y furgonetas
"""
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from src.repos import almacenes_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """Valida que el nombre del almacén sea válido."""
    if not nombre or not nombre.strip():
        log_validacion("almacenes", "nombre", "Nombre vacío")
        return False, "El nombre del almacén es obligatorio"

    if len(nombre.strip()) < 2:
        log_validacion("almacenes", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 2 caracteres"

    if len(nombre.strip()) > 100:
        log_validacion("almacenes", "nombre", f"Nombre muy largo: {len(nombre)}")
        return False, "El nombre no puede exceder 100 caracteres"

    return True, ""


def validar_tipo(tipo: str) -> Tuple[bool, str]:
    """Valida que el tipo sea válido."""
    tipos_validos = ['almacen', 'furgoneta']
    if tipo not in tipos_validos:
        log_validacion("almacenes", "tipo", f"Tipo inválido: {tipo}")
        return False, f"El tipo debe ser 'almacen' o 'furgoneta'"
    return True, ""


def validar_nombre_unico(nombre: str, almacen_id: Optional[int] = None) -> Tuple[bool, str]:
    """Valida que el nombre del almacén sea único."""
    existente = almacenes_repo.get_by_nombre(nombre)
    if existente:
        if almacen_id and existente['id'] == almacen_id:
            return True, ""
        log_validacion("almacenes", "nombre", f"Nombre duplicado: {nombre}")
        return False, f"Ya existe un almacén con el nombre '{nombre}'"
    return True, ""


def crear_almacen(nombre: str, tipo: str = 'almacen', usuario: str = "admin") -> Tuple[bool, str, Optional[int]]:
    """Crea un nuevo almacén con validaciones."""
    try:
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error, None

        valido, error = validar_tipo(tipo)
        if not valido:
            return False, error, None

        valido, error = validar_nombre_unico(nombre)
        if not valido:
            return False, error, None

        nombre = nombre.strip()
        almacen_id = almacenes_repo.crear_almacen(nombre, tipo)

        log_operacion("almacenes", "crear", usuario, f"Almacén ID: {almacen_id}, Nombre: {nombre}, Tipo: {tipo}")
        logger.info(f"Almacén creado | ID: {almacen_id} | {nombre} ({tipo})")

        return True, f"Almacén '{nombre}' creado correctamente", almacen_id

    except psycopg2.IntegrityError:
        return False, f"Ya existe un almacén con el nombre '{nombre}'", None
    except Exception as e:
        log_error_bd("almacenes", "crear_almacen", e)
        return False, f"Error al crear almacén: {str(e)}", None


def actualizar_almacen(almacen_id: int, nombre: str, tipo: str, usuario: str = "admin") -> Tuple[bool, str]:
    """Actualiza un almacén existente con validaciones."""
    try:
        almacen = almacenes_repo.get_by_id(almacen_id)
        if not almacen:
            return False, f"No se encontró el almacén con ID {almacen_id}"

        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        valido, error = validar_tipo(tipo)
        if not valido:
            return False, error

        valido, error = validar_nombre_unico(nombre, almacen_id)
        if not valido:
            return False, error

        nombre = nombre.strip()
        almacenes_repo.actualizar_almacen(almacen_id, nombre, tipo)

        log_operacion("almacenes", "actualizar", usuario, f"Almacén ID: {almacen_id}, Nombre: {nombre}, Tipo: {tipo}")
        logger.info(f"Almacén actualizado | ID: {almacen_id} | {nombre} ({tipo})")

        return True, f"Almacén '{nombre}' actualizado correctamente"

    except psycopg2.IntegrityError:
        return False, f"Ya existe otro almacén con el nombre '{nombre}'"
    except Exception as e:
        log_error_bd("almacenes", "actualizar_almacen", e)
        return False, f"Error al actualizar almacén: {str(e)}"


def eliminar_almacen(almacen_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """Elimina un almacén."""
    try:
        almacen = almacenes_repo.get_by_id(almacen_id)
        if not almacen:
            return False, f"No se encontró el almacén con ID {almacen_id}"

        nombre = almacen['nombre']

        tiene_movimientos = almacenes_repo.verificar_movimientos(almacen_id)
        if tiene_movimientos:
            return False, (
                f"El almacén '{nombre}' tiene movimientos asociados.\n\n"
                "No se puede eliminar un almacén con movimientos registrados."
            )

        almacenes_repo.eliminar_almacen(almacen_id)

        log_operacion("almacenes", "eliminar", usuario, f"Almacén ID: {almacen_id}, Nombre: {nombre}")
        logger.info(f"Almacén eliminado | ID: {almacen_id} | {nombre}")

        return True, f"Almacén '{nombre}' eliminado correctamente"

    except psycopg2.IntegrityError:
        return False, "El almacén tiene movimientos asociados y no se puede eliminar"
    except Exception as e:
        log_error_bd("almacenes", "eliminar_almacen", e)
        return False, f"Error al eliminar almacén: {str(e)}"


def obtener_almacenes(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtiene lista de todos los almacenes con filtros."""
    try:
        return almacenes_repo.get_todos(filtro_texto=filtro_texto, limit=limit)
    except Exception as e:
        log_error_bd("almacenes", "obtener_almacenes", e)
        return []


def obtener_almacenes_fijos() -> List[Dict[str, Any]]:
    """Obtiene solo los almacenes fijos (tipo='almacen')."""
    try:
        return almacenes_repo.get_almacenes()
    except Exception as e:
        log_error_bd("almacenes", "obtener_almacenes_fijos", e)
        return []


def obtener_furgonetas() -> List[Dict[str, Any]]:
    """Obtiene solo las furgonetas (tipo='furgoneta')."""
    try:
        return almacenes_repo.get_furgonetas()
    except Exception as e:
        log_error_bd("almacenes", "obtener_furgonetas", e)
        return []


def obtener_almacen(almacen_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén específico por ID."""
    try:
        return almacenes_repo.get_by_id(almacen_id)
    except Exception as e:
        log_error_bd("almacenes", "obtener_almacen", e)
        return None


def obtener_almacen_por_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén por su nombre exacto."""
    try:
        return almacenes_repo.get_by_nombre(nombre)
    except Exception as e:
        log_error_bd("almacenes", "obtener_almacen_por_nombre", e)
        return None


def obtener_stock_almacen(almacen_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock actual de un almacén.

    Args:
        almacen_id: ID del almacén

    Returns:
        Lista de artículos con su stock en el almacén
    """
    try:
        return almacenes_repo.get_stock_almacen(almacen_id)
    except Exception as e:
        log_error_bd("almacenes", "obtener_stock_almacen", e)
        return []


def obtener_estadisticas_almacen(almacen_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un almacén.

    Args:
        almacen_id: ID del almacén

    Returns:
        Diccionario con estadísticas del almacén
    """
    try:
        return almacenes_repo.get_estadisticas_almacen(almacen_id)
    except Exception as e:
        log_error_bd("almacenes", "obtener_estadisticas_almacen", e)
        return {}
