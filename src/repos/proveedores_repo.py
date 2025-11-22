"""
Repositorio de Proveedores - Consultas SQL para gestión de proveedores
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


# ========================================
# CONSULTAS DE PROVEEDORES
# ========================================

def get_todos(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Obtiene lista de proveedores con filtro opcional.

    Args:
        filtro_texto: Búsqueda por nombre, teléfono, contacto o email
        limit: Límite de resultados

    Returns:
        Lista de proveedores
    """
    if filtro_texto:
        sql = """
            SELECT id, nombre, telefono, contacto, email, notas
            FROM proveedores
            WHERE nombre LIKE %s
               OR telefono LIKE %s
               OR contacto LIKE %s
               OR email LIKE %s
            ORDER BY nombre
            LIMIT %s
        """
        patron = f"%{filtro_texto}%"
        return fetch_all(sql, (patron, patron, patron, patron, limit))
    else:
        sql = """
            SELECT id, nombre, telefono, contacto, email, notas
            FROM proveedores
            ORDER BY nombre
            LIMIT %s
        """
        return fetch_all(sql, (limit,))


def get_by_id(proveedor_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un proveedor específico por su ID.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Diccionario con información del proveedor o None
    """
    sql = """
        SELECT id, nombre, telefono, contacto, email, notas
        FROM proveedores
        WHERE id = %s
    """
    return fetch_one(sql, (proveedor_id,))


def get_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un proveedor por su nombre (para verificar duplicados).

    Args:
        nombre: Nombre del proveedor

    Returns:
        Diccionario con información del proveedor o None
    """
    sql = """
        SELECT id, nombre, telefono, contacto, email
        FROM proveedores
        WHERE nombre = %s
    """
    return fetch_one(sql, (nombre,))


def crear_proveedor(
    nombre: str,
    telefono: Optional[str] = None,
    contacto: Optional[str] = None,
    email: Optional[str] = None,
    notas: Optional[str] = None
) -> int:
    """
    Crea un nuevo proveedor.

    Args:
        nombre: Nombre del proveedor (obligatorio, debe ser único)
        telefono: Teléfono de contacto
        contacto: Persona de contacto
        email: Email de contacto
        notas: Notas adicionales

    Returns:
        ID del proveedor creado
    """
    sql = """
        INSERT INTO proveedores(nombre, telefono, contacto, email, notas)
        VALUES(%s, %s, %s, %s, %s)
    """
    return execute_query(sql, (nombre, telefono, contacto, email, notas))


def actualizar_proveedor(
    proveedor_id: int,
    nombre: str,
    telefono: Optional[str] = None,
    contacto: Optional[str] = None,
    email: Optional[str] = None,
    notas: Optional[str] = None
) -> bool:
    """
    Actualiza un proveedor existente.

    Args:
        proveedor_id: ID del proveedor a actualizar
        nombre: Nombre del proveedor
        telefono: Teléfono de contacto
        contacto: Persona de contacto
        email: Email de contacto
        notas: Notas adicionales

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE proveedores
        SET nombre=%s, telefono=%s, contacto=%s, email=%s, notas=%s
        WHERE id=%s
    """
    execute_query(sql, (nombre, telefono, contacto, email, notas, proveedor_id))
    return True


def eliminar_proveedor(proveedor_id: int) -> bool:
    """
    Elimina un proveedor.

    IMPORTANTE: Fallará si el proveedor tiene artículos asociados (constraint FK).

    Args:
        proveedor_id: ID del proveedor

    Returns:
        True si se eliminó correctamente

    Raises:
        IntegrityError: Si el proveedor tiene artículos asociados
    """
    sql = "DELETE FROM proveedores WHERE id=%s"
    execute_query(sql, (proveedor_id,))
    return True


# ========================================
# CONSULTAS AUXILIARES
# ========================================

def verificar_articulos(proveedor_id: int) -> bool:
    """
    Verifica si un proveedor tiene artículos asociados.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        True si tiene artículos, False si no tiene
    """
    sql = "SELECT COUNT(*) as count FROM articulos WHERE proveedor_id = %s"
    result = fetch_one(sql, (proveedor_id,))
    return result['count'] > 0 if result else False


def get_articulos_proveedor(proveedor_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos asociados a un proveedor.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Lista de artículos del proveedor
    """
    sql = """
        SELECT id, nombre, ref_proveedor, coste, activo
        FROM articulos
        WHERE proveedor_id = %s
        ORDER BY nombre
    """
    return fetch_all(sql, (proveedor_id,))


def get_estadisticas_proveedor(proveedor_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un proveedor.

    Args:
        proveedor_id: ID del proveedor

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(*) as total_articulos,
            SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as articulos_activos,
            AVG(coste) as coste_promedio
        FROM articulos
        WHERE proveedor_id = %s
    """
    result = fetch_one(sql, (proveedor_id,))
    return result if result else {}


def get_estadisticas_proveedores() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de proveedores.

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(DISTINCT p.id) as total_proveedores,
            COUNT(a.id) as total_articulos,
            AVG(a.coste) as coste_promedio_articulos
        FROM proveedores p
        LEFT JOIN articulos a ON p.id = a.proveedor_id
    """
    result = fetch_one(sql)
    return result if result else {}


def get_proveedores_con_articulos() -> List[Dict[str, Any]]:
    """
    Obtiene proveedores que tienen artículos asociados.

    Returns:
        Lista de proveedores con cantidad de artículos
    """
    sql = """
        SELECT
            p.id,
            p.nombre,
            COUNT(a.id) as total_articulos,
            SUM(CASE WHEN a.activo = 1 THEN 1 ELSE 0 END) as articulos_activos
        FROM proveedores p
        INNER JOIN articulos a ON p.id = a.proveedor_id
        GROUP BY p.id, p.nombre
        ORDER BY total_articulos DESC
    """
    return fetch_all(sql)


def get_proveedores_sin_articulos() -> List[Dict[str, Any]]:
    """
    Obtiene proveedores que no tienen artículos asociados.

    Returns:
        Lista de proveedores sin artículos
    """
    sql = """
        SELECT p.id, p.nombre, p.telefono, p.contacto, p.email
        FROM proveedores p
        LEFT JOIN articulos a ON p.id = a.proveedor_id
        WHERE a.id IS NULL
        ORDER BY p.nombre
    """
    return fetch_all(sql)
