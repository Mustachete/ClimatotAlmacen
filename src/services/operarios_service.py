"""
Servicio de Operarios - Lógica de negocio para gestión de operarios/técnicos
"""
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from src.repos import operarios_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


# ========================================
# VALIDACIONES
# ========================================

def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """
    Valida que el nombre del operario sea válido.

    Args:
        nombre: Nombre del operario

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not nombre or not nombre.strip():
        log_validacion("operarios", "nombre", "Nombre vacío")
        return False, "El nombre del operario es obligatorio"

    if len(nombre.strip()) < 3:
        log_validacion("operarios", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 3 caracteres"

    if len(nombre.strip()) > 200:
        log_validacion("operarios", "nombre", f"Nombre muy largo: {len(nombre)} caracteres")
        return False, "El nombre no puede exceder 200 caracteres"

    return True, ""


def validar_nombre_unico(nombre: str, operario_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Valida que el nombre del operario sea único.

    Args:
        nombre: Nombre del operario
        operario_id: ID del operario (para edición, permite el mismo nombre)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    existente = operarios_repo.get_by_nombre(nombre)
    if existente:
        # Si estamos editando y es el mismo operario, está bien
        if operario_id and existente['id'] == operario_id:
            return True, ""
        log_validacion("operarios", "nombre", f"Nombre duplicado: {nombre}")
        return False, f"Ya existe un operario con el nombre '{nombre}'"

    return True, ""


def validar_rol(rol: str) -> Tuple[bool, str]:
    """
    Valida que el rol del operario sea válido.

    Args:
        rol: Rol del operario

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    roles_validos = ["oficial", "ayudante"]

    if not rol or not rol.strip():
        log_validacion("operarios", "rol", "Rol vacío")
        return False, "El rol del operario es obligatorio"

    rol = rol.strip().lower()

    if rol not in roles_validos:
        log_validacion("operarios", "rol", f"Rol inválido: {rol}")
        return False, f"El rol debe ser 'oficial' o 'ayudante', no '{rol}'"

    return True, ""


# ========================================
# OPERACIONES DE OPERARIOS
# ========================================

def crear_operario(
    nombre: str,
    rol_operario: str = "ayudante",
    activo: bool = True,
    usuario: str = "admin"
) -> Tuple[bool, str, Optional[int]]:
    """
    Crea un nuevo operario con validaciones.

    Args:
        nombre: Nombre del operario (obligatorio)
        rol_operario: 'oficial' o 'ayudante'
        activo: Si está activo
        usuario: Usuario que crea el operario

    Returns:
        Tupla (exito, mensaje, operario_id)
    """
    try:
        # Validar nombre
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error, None

        # Validar unicidad del nombre
        valido, error = validar_nombre_unico(nombre)
        if not valido:
            return False, error, None

        # Validar rol
        valido, error = validar_rol(rol_operario)
        if not valido:
            return False, error, None

        # Normalizar campos
        nombre = nombre.strip()
        rol_operario = rol_operario.strip().lower()

        # Crear operario
        operario_id = operarios_repo.crear_operario(
            nombre=nombre,
            rol_operario=rol_operario,
            activo=activo
        )

        # Logging
        rol_texto = "Oficial" if rol_operario == "oficial" else "Ayudante"
        detalles = f"Operario ID: {operario_id}, Nombre: {nombre}, Rol: {rol_texto}"
        log_operacion("operarios", "crear", usuario, detalles)
        logger.info(f"Operario creado | ID: {operario_id} | {nombre} ({rol_texto})")

        return True, f"Operario '{nombre}' creado correctamente como {rol_texto}", operario_id

    except sqlite3.IntegrityError as e:
        mensaje = f"Ya existe un operario con el nombre '{nombre}'"
        log_error_bd("operarios", "crear_operario", e)
        return False, mensaje, None

    except Exception as e:
        log_error_bd("operarios", "crear_operario", e)
        return False, f"Error al crear operario: {str(e)}", None


def actualizar_operario(
    operario_id: int,
    nombre: str,
    rol_operario: str = "ayudante",
    activo: bool = True,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Actualiza un operario existente con validaciones.

    Args:
        operario_id: ID del operario a actualizar
        (resto de parámetros igual que crear_operario)

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que el operario existe
        operario = operarios_repo.get_by_id(operario_id)
        if not operario:
            return False, f"No se encontró el operario con ID {operario_id}"

        # Validar nombre
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        # Validar unicidad del nombre (pasando el ID para permitir el mismo nombre)
        valido, error = validar_nombre_unico(nombre, operario_id)
        if not valido:
            return False, error

        # Validar rol
        valido, error = validar_rol(rol_operario)
        if not valido:
            return False, error

        # Normalizar campos
        nombre = nombre.strip()
        rol_operario = rol_operario.strip().lower()

        # Actualizar operario
        operarios_repo.actualizar_operario(
            operario_id=operario_id,
            nombre=nombre,
            rol_operario=rol_operario,
            activo=activo
        )

        # Logging
        rol_texto = "Oficial" if rol_operario == "oficial" else "Ayudante"
        detalles = f"Operario ID: {operario_id}, Nombre: {nombre}, Rol: {rol_texto}"
        log_operacion("operarios", "actualizar", usuario, detalles)
        logger.info(f"Operario actualizado | ID: {operario_id} | {nombre} ({rol_texto})")

        return True, f"Operario '{nombre}' actualizado correctamente"

    except sqlite3.IntegrityError as e:
        mensaje = f"Ya existe otro operario con el nombre '{nombre}'"
        log_error_bd("operarios", "actualizar_operario", e)
        return False, mensaje

    except Exception as e:
        log_error_bd("operarios", "actualizar_operario", e)
        return False, f"Error al actualizar operario: {str(e)}"


def eliminar_operario(
    operario_id: int,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Elimina un operario.

    Args:
        operario_id: ID del operario
        usuario: Usuario que elimina

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que existe
        operario = operarios_repo.get_by_id(operario_id)
        if not operario:
            return False, f"No se encontró el operario con ID {operario_id}"

        nombre = operario['nombre']

        # Verificar si tiene movimientos
        tiene_movimientos = operarios_repo.verificar_movimientos(operario_id)
        if tiene_movimientos:
            return False, (
                f"El operario '{nombre}' tiene movimientos o asignaciones asociadas.\n\n"
                "En lugar de eliminarlo, puede marcarlo como 'Inactivo' editándolo."
            )

        # Eliminar
        operarios_repo.eliminar_operario(operario_id)

        # Logging
        detalles = f"Operario ID: {operario_id}, Nombre: {nombre}"
        log_operacion("operarios", "eliminar", usuario, detalles)
        logger.info(f"Operario eliminado | ID: {operario_id} | {nombre}")

        return True, f"Operario '{nombre}' eliminado correctamente"

    except sqlite3.IntegrityError:
        # Por si acaso la verificación previa no funcionó
        return False, (
            f"El operario tiene movimientos o asignaciones asociadas.\n\n"
            "En lugar de eliminarlo, puede marcarlo como 'Inactivo'."
        )

    except Exception as e:
        log_error_bd("operarios", "eliminar_operario", e)
        return False, f"Error al eliminar operario: {str(e)}"


def activar_operario(operario_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """
    Activa un operario.

    Args:
        operario_id: ID del operario
        usuario: Usuario que activa

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        operario = operarios_repo.get_by_id(operario_id)
        if not operario:
            return False, f"No se encontró el operario con ID {operario_id}"

        operarios_repo.activar_desactivar_operario(operario_id, True)

        detalles = f"Operario ID: {operario_id}, Nombre: {operario['nombre']}"
        log_operacion("operarios", "activar", usuario, detalles)

        return True, f"Operario '{operario['nombre']}' activado"

    except Exception as e:
        log_error_bd("operarios", "activar_operario", e)
        return False, f"Error al activar operario: {str(e)}"


def desactivar_operario(operario_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """
    Desactiva un operario.

    Args:
        operario_id: ID del operario
        usuario: Usuario que desactiva

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        operario = operarios_repo.get_by_id(operario_id)
        if not operario:
            return False, f"No se encontró el operario con ID {operario_id}"

        operarios_repo.activar_desactivar_operario(operario_id, False)

        detalles = f"Operario ID: {operario_id}, Nombre: {operario['nombre']}"
        log_operacion("operarios", "desactivar", usuario, detalles)

        return True, f"Operario '{operario['nombre']}' desactivado"

    except Exception as e:
        log_error_bd("operarios", "desactivar_operario", e)
        return False, f"Error al desactivar operario: {str(e)}"


# ========================================
# CONSULTAS Y REPORTES
# ========================================

def obtener_operarios(
    filtro_texto: Optional[str] = None,
    solo_rol: Optional[str] = None,
    solo_activos: Optional[bool] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de operarios con filtros.

    Args:
        filtro_texto: Búsqueda por nombre
        solo_rol: Filtrar por rol ('oficial' o 'ayudante')
        solo_activos: Si True solo activos, si False solo inactivos, si None todos
        limit: Límite de resultados

    Returns:
        Lista de operarios
    """
    try:
        return operarios_repo.get_todos(
            filtro_texto=filtro_texto,
            solo_rol=solo_rol,
            solo_activos=solo_activos,
            limit=limit
        )
    except Exception as e:
        log_error_bd("operarios", "obtener_operarios", e)
        return []


def obtener_operario(operario_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un operario específico por ID.

    Args:
        operario_id: ID del operario

    Returns:
        Diccionario con información del operario o None
    """
    try:
        return operarios_repo.get_by_id(operario_id)
    except Exception as e:
        log_error_bd("operarios", "obtener_operario", e)
        return None


def obtener_oficiales_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de oficiales activos (para asignar furgonetas).

    Returns:
        Lista de oficiales activos
    """
    try:
        return operarios_repo.get_oficiales_activos()
    except Exception as e:
        log_error_bd("operarios", "obtener_oficiales_activos", e)
        return []


def obtener_ayudantes_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de ayudantes activos.

    Returns:
        Lista de ayudantes activos
    """
    try:
        return operarios_repo.get_ayudantes_activos()
    except Exception as e:
        log_error_bd("operarios", "obtener_ayudantes_activos", e)
        return []


def obtener_operarios_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de todos los operarios activos.

    Returns:
        Lista de operarios activos
    """
    try:
        return operarios_repo.get_operarios_activos()
    except Exception as e:
        log_error_bd("operarios", "obtener_operarios_activos", e)
        return []


def obtener_movimientos_operario(
    operario_id: int,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene los movimientos de un operario en un rango de fechas.

    Args:
        operario_id: ID del operario
        fecha_desde: Fecha inicio (formato YYYY-MM-DD)
        fecha_hasta: Fecha fin (formato YYYY-MM-DD)

    Returns:
        Lista de movimientos del operario
    """
    try:
        return operarios_repo.get_movimientos_operario(
            operario_id=operario_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
    except Exception as e:
        log_error_bd("operarios", "obtener_movimientos_operario", e)
        return []


def obtener_estadisticas_operario(operario_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas de un operario.

    Args:
        operario_id: ID del operario

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return operarios_repo.get_estadisticas_operario(operario_id)
    except Exception as e:
        log_error_bd("operarios", "obtener_estadisticas_operario", e)
        return None


def obtener_estadisticas_generales() -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas generales de operarios.

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return operarios_repo.get_estadisticas_operarios()
    except Exception as e:
        log_error_bd("operarios", "obtener_estadisticas_generales", e)
        return None


def obtener_operarios_con_movimientos() -> List[Dict[str, Any]]:
    """
    Obtiene operarios que tienen movimientos registrados.

    Returns:
        Lista de operarios con cantidad de movimientos
    """
    try:
        return operarios_repo.get_operarios_con_movimientos()
    except Exception as e:
        log_error_bd("operarios", "obtener_operarios_con_movimientos", e)
        return []


def obtener_operarios_sin_movimientos() -> List[Dict[str, Any]]:
    """
    Obtiene operarios que no tienen movimientos registrados.

    Returns:
        Lista de operarios sin movimientos
    """
    try:
        return operarios_repo.get_operarios_sin_movimientos()
    except Exception as e:
        log_error_bd("operarios", "obtener_operarios_sin_movimientos", e)
        return []
