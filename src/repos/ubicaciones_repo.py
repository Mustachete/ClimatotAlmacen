"""
Repositorio de Ubicaciones - Consultas SQL para gestión de ubicaciones del almacén
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


def get_todos(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Obtiene lista de ubicaciones con filtro opcional.

    Args:
        filtro_texto: Búsqueda por nombre
        limit: Límite de resultados

    Returns:
        Lista de ubicaciones
    """
    if filtro_texto:
        sql = """
            SELECT id, nombre
            FROM ubicaciones
            WHERE nombre LIKE %s
            ORDER BY nombre
            LIMIT %s
        """
        return fetch_all(sql, (f"%{filtro_texto}%", limit))
    else:
        sql = """
            SELECT id, nombre
            FROM ubicaciones
            ORDER BY nombre
            LIMIT %s
        """
        return fetch_all(sql, (limit,))


def get_by_id(ubicacion_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una ubicación por su ID."""
    sql = "SELECT id, nombre FROM ubicaciones WHERE id = %s"
    return fetch_one(sql, (ubicacion_id,))


def get_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """Obtiene una ubicación por su nombre (verificar duplicados)."""
    sql = "SELECT id, nombre FROM ubicaciones WHERE nombre = %s"
    return fetch_one(sql, (nombre,))


def crear_ubicacion(nombre: str) -> int:
    """Crea una nueva ubicación."""
    sql = "INSERT INTO ubicaciones(nombre) VALUES(%s)"
    return execute_query(sql, (nombre,))


def actualizar_ubicacion(ubicacion_id: int, nombre: str) -> bool:
    """Actualiza una ubicación existente."""
    sql = "UPDATE ubicaciones SET nombre=%s WHERE id=%s"
    execute_query(sql, (nombre, ubicacion_id))
    return True


def eliminar_ubicacion(ubicacion_id: int) -> bool:
    """Elimina una ubicación (fallará si tiene artículos asociados)."""
    sql = "DELETE FROM ubicaciones WHERE id=%s"
    execute_query(sql, (ubicacion_id,))
    return True


def verificar_articulos(ubicacion_id: int) -> bool:
    """Verifica si una ubicación tiene artículos asociados."""
    sql = "SELECT COUNT(*) as count FROM articulos WHERE ubicacion_id = %s"
    result = fetch_one(sql, (ubicacion_id,))
    return result['count'] > 0 if result else False


def get_articulos_ubicacion(ubicacion_id: int) -> List[Dict[str, Any]]:
    """Obtiene artículos asociados a una ubicación."""
    sql = """
        SELECT id, nombre, ref_proveedor, activo
        FROM articulos
        WHERE ubicacion_id = %s
        ORDER BY nombre
    """
    return fetch_all(sql, (ubicacion_id,))


def get_estadisticas_ubicacion(ubicacion_id: int) -> Dict[str, Any]:
    """Obtiene estadísticas de una ubicación."""
    sql = """
        SELECT
            COUNT(*) as total_articulos,
            SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as articulos_activos
        FROM articulos
        WHERE ubicacion_id = %s
    """
    result = fetch_one(sql, (ubicacion_id,))
    return result if result else {}
