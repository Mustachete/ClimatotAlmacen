"""
Servicio de Proveedores - Lógica de negocio para gestión de proveedores
"""
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
import re
from src.repos import proveedores_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


# ========================================
# VALIDACIONES
# ========================================

def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """
    Valida que el nombre del proveedor sea válido.

    Args:
        nombre: Nombre del proveedor

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not nombre or not nombre.strip():
        log_validacion("proveedores", "nombre", "Nombre vacío")
        return False, "El nombre del proveedor es obligatorio"

    if len(nombre.strip()) < 2:
        log_validacion("proveedores", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 2 caracteres"

    if len(nombre.strip()) > 200:
        log_validacion("proveedores", "nombre", f"Nombre muy largo: {len(nombre)} caracteres")
        return False, "El nombre no puede exceder 200 caracteres"

    return True, ""


def validar_nombre_unico(nombre: str, proveedor_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Valida que el nombre del proveedor sea único.

    Args:
        nombre: Nombre del proveedor
        proveedor_id: ID del proveedor (para edición, permite el mismo nombre)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    existente = proveedores_repo.get_by_nombre(nombre)
    if existente:
        # Si estamos editando y es el mismo proveedor, está bien
        if proveedor_id and existente['id'] == proveedor_id:
            return True, ""
        log_validacion("proveedores", "nombre", f"Nombre duplicado: {nombre}")
        return False, f"Ya existe un proveedor con el nombre '{nombre}'"

    return True, ""


def validar_telefono(telefono: Optional[str]) -> Tuple[bool, str]:
    """
    Valida que el teléfono sea válido (formato básico).

    Args:
        telefono: Teléfono (puede ser None)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not telefono or not telefono.strip():
        return True, ""  # Teléfono es opcional

    telefono = telefono.strip()

    # Verificar longitud razonable
    if len(telefono) < 9:
        log_validacion("proveedores", "telefono", f"Teléfono muy corto: {telefono}")
        return False, "El teléfono debe tener al menos 9 caracteres"

    if len(telefono) > 20:
        log_validacion("proveedores", "telefono", f"Teléfono muy largo: {telefono}")
        return False, "El teléfono no puede exceder 20 caracteres"

    # Verificar que contenga principalmente números (permite +, espacios, guiones, paréntesis)
    patron_telefono = re.compile(r'^[\d\s\+\-\(\)]+$')
    if not patron_telefono.match(telefono):
        log_validacion("proveedores", "telefono", f"Formato inválido: {telefono}")
        return False, "El teléfono contiene caracteres no válidos"

    return True, ""


def validar_email(email: Optional[str]) -> Tuple[bool, str]:
    """
    Valida que el email sea válido (formato básico).

    Args:
        email: Email (puede ser None)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not email or not email.strip():
        return True, ""  # Email es opcional

    email = email.strip()

    # Verificar longitud razonable
    if len(email) > 100:
        log_validacion("proveedores", "email", f"Email muy largo: {len(email)} caracteres")
        return False, "El email no puede exceder 100 caracteres"

    # Patrón básico de email
    patron_email = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not patron_email.match(email):
        log_validacion("proveedores", "email", f"Formato inválido: {email}")
        return False, "El formato del email no es válido"

    return True, ""


def validar_contacto(contacto: Optional[str]) -> Tuple[bool, str]:
    """
    Valida que el contacto sea válido.

    Args:
        contacto: Nombre del contacto (puede ser None)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not contacto or not contacto.strip():
        return True, ""  # Contacto es opcional

    if len(contacto.strip()) > 200:
        log_validacion("proveedores", "contacto", f"Contacto muy largo: {len(contacto)} caracteres")
        return False, "El contacto no puede exceder 200 caracteres"

    return True, ""


# ========================================
# OPERACIONES DE PROVEEDORES
# ========================================

def crear_proveedor(
    nombre: str,
    telefono: Optional[str] = None,
    contacto: Optional[str] = None,
    email: Optional[str] = None,
    notas: Optional[str] = None,
    usuario: str = "admin"
) -> Tuple[bool, str, Optional[int]]:
    """
    Crea un nuevo proveedor con validaciones.

    Args:
        nombre: Nombre del proveedor (obligatorio)
        telefono: Teléfono de contacto
        contacto: Persona de contacto
        email: Email de contacto
        notas: Notas adicionales
        usuario: Usuario que crea el proveedor

    Returns:
        Tupla (exito, mensaje, proveedor_id)
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

        # Validar teléfono
        valido, error = validar_telefono(telefono)
        if not valido:
            return False, error, None

        # Validar email
        valido, error = validar_email(email)
        if not valido:
            return False, error, None

        # Validar contacto
        valido, error = validar_contacto(contacto)
        if not valido:
            return False, error, None

        # Normalizar campos opcionales
        nombre = nombre.strip()
        telefono = telefono.strip() if telefono else None
        contacto = contacto.strip() if contacto else None
        email = email.strip().lower() if email else None  # Email en minúsculas
        notas = notas.strip() if notas else None

        # Crear proveedor
        proveedor_id = proveedores_repo.crear_proveedor(
            nombre=nombre,
            telefono=telefono,
            contacto=contacto,
            email=email,
            notas=notas
        )

        # Logging
        detalles = f"Proveedor ID: {proveedor_id}, Nombre: {nombre}"
        log_operacion("proveedores", "crear", usuario, detalles)
        logger.info(f"Proveedor creado | ID: {proveedor_id} | {nombre}")

        return True, f"Proveedor '{nombre}' creado correctamente", proveedor_id

    except psycopg2.IntegrityError as e:
        mensaje = f"Ya existe un proveedor con el nombre '{nombre}'"
        log_error_bd("proveedores", "crear_proveedor", e)
        return False, mensaje, None

    except Exception as e:
        log_error_bd("proveedores", "crear_proveedor", e)
        return False, f"Error al crear proveedor: {str(e)}", None


def actualizar_proveedor(
    proveedor_id: int,
    nombre: str,
    telefono: Optional[str] = None,
    contacto: Optional[str] = None,
    email: Optional[str] = None,
    notas: Optional[str] = None,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Actualiza un proveedor existente con validaciones.

    Args:
        proveedor_id: ID del proveedor a actualizar
        (resto de parámetros igual que crear_proveedor)

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que el proveedor existe
        proveedor = proveedores_repo.get_by_id(proveedor_id)
        if not proveedor:
            return False, f"No se encontró el proveedor con ID {proveedor_id}"

        # Validar nombre
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        # Validar unicidad del nombre (pasando el ID para permitir el mismo nombre)
        valido, error = validar_nombre_unico(nombre, proveedor_id)
        if not valido:
            return False, error

        # Validar teléfono
        valido, error = validar_telefono(telefono)
        if not valido:
            return False, error

        # Validar email
        valido, error = validar_email(email)
        if not valido:
            return False, error

        # Validar contacto
        valido, error = validar_contacto(contacto)
        if not valido:
            return False, error

        # Normalizar campos
        nombre = nombre.strip()
        telefono = telefono.strip() if telefono else None
        contacto = contacto.strip() if contacto else None
        email = email.strip().lower() if email else None
        notas = notas.strip() if notas else None

        # Actualizar proveedor
        proveedores_repo.actualizar_proveedor(
            proveedor_id=proveedor_id,
            nombre=nombre,
            telefono=telefono,
            contacto=contacto,
            email=email,
            notas=notas
        )

        # Logging
        detalles = f"Proveedor ID: {proveedor_id}, Nombre: {nombre}"
        log_operacion("proveedores", "actualizar", usuario, detalles)
        logger.info(f"Proveedor actualizado | ID: {proveedor_id} | {nombre}")

        return True, f"Proveedor '{nombre}' actualizado correctamente"

    except psycopg2.IntegrityError as e:
        mensaje = f"Ya existe otro proveedor con el nombre '{nombre}'"
        log_error_bd("proveedores", "actualizar_proveedor", e)
        return False, mensaje

    except Exception as e:
        log_error_bd("proveedores", "actualizar_proveedor", e)
        return False, f"Error al actualizar proveedor: {str(e)}"


def eliminar_proveedor(
    proveedor_id: int,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Elimina un proveedor.

    Args:
        proveedor_id: ID del proveedor
        usuario: Usuario que elimina

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que existe
        proveedor = proveedores_repo.get_by_id(proveedor_id)
        if not proveedor:
            return False, f"No se encontró el proveedor con ID {proveedor_id}"

        nombre = proveedor['nombre']

        # Verificar si tiene artículos
        tiene_articulos = proveedores_repo.verificar_articulos(proveedor_id)
        if tiene_articulos:
            return False, (
                f"El proveedor '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar un proveedor que está siendo usado."
            )

        # Eliminar
        proveedores_repo.eliminar_proveedor(proveedor_id)

        # Logging
        detalles = f"Proveedor ID: {proveedor_id}, Nombre: {nombre}"
        log_operacion("proveedores", "eliminar", usuario, detalles)
        logger.info(f"Proveedor eliminado | ID: {proveedor_id} | {nombre}")

        return True, f"Proveedor '{nombre}' eliminado correctamente"

    except psycopg2.IntegrityError:
        # Por si acaso la verificación previa no funcionó
        return False, (
            f"El proveedor tiene artículos asociados.\n\n"
            "No se puede eliminar un proveedor que está siendo usado."
        )

    except Exception as e:
        log_error_bd("proveedores", "eliminar_proveedor", e)
        return False, f"Error al eliminar proveedor: {str(e)}"


# ========================================
# CONSULTAS Y REPORTES
# ========================================

def obtener_proveedores(
    filtro_texto: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de proveedores con filtros.

    Args:
        filtro_texto: Búsqueda por nombre, teléfono, contacto o email
        limit: Límite de resultados

    Returns:
        Lista de proveedores
    """
    try:
        return proveedores_repo.get_todos(
            filtro_texto=filtro_texto,
            limit=limit
        )
    except Exception as e:
        log_error_bd("proveedores", "obtener_proveedores", e)
        return []


def obtener_proveedor(proveedor_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un proveedor específico por ID.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Diccionario con información del proveedor o None
    """
    try:
        return proveedores_repo.get_by_id(proveedor_id)
    except Exception as e:
        log_error_bd("proveedores", "obtener_proveedor", e)
        return None


def obtener_articulos_proveedor(proveedor_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos asociados a un proveedor.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Lista de artículos del proveedor
    """
    try:
        return proveedores_repo.get_articulos_proveedor(proveedor_id)
    except Exception as e:
        log_error_bd("proveedores", "obtener_articulos_proveedor", e)
        return []


def obtener_estadisticas_proveedor(proveedor_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas de un proveedor.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return proveedores_repo.get_estadisticas_proveedor(proveedor_id)
    except Exception as e:
        log_error_bd("proveedores", "obtener_estadisticas_proveedor", e)
        return None


def obtener_estadisticas_generales() -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas generales de proveedores.

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return proveedores_repo.get_estadisticas_proveedores()
    except Exception as e:
        log_error_bd("proveedores", "obtener_estadisticas_generales", e)
        return None


def obtener_proveedores_con_articulos() -> List[Dict[str, Any]]:
    """
    Obtiene proveedores que tienen artículos asociados.

    Returns:
        Lista de proveedores con cantidad de artículos
    """
    try:
        return proveedores_repo.get_proveedores_con_articulos()
    except Exception as e:
        log_error_bd("proveedores", "obtener_proveedores_con_articulos", e)
        return []


def obtener_proveedores_sin_articulos() -> List[Dict[str, Any]]:
    """
    Obtiene proveedores que no tienen artículos asociados.

    Returns:
        Lista de proveedores sin artículos
    """
    try:
        return proveedores_repo.get_proveedores_sin_articulos()
    except Exception as e:
        log_error_bd("proveedores", "obtener_proveedores_sin_articulos", e)
        return []
