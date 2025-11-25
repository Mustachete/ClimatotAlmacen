"""
Repositorio de Familias - Consultas SQL para gestión de familias de artículos
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


def get_todos(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Obtiene lista de familias con filtro opcional.

    Args:
        filtro_texto: Búsqueda por nombre
        limit: Límite de resultados

    Returns:
        Lista de familias
    """
    if filtro_texto:
        sql = """
            SELECT id, nombre
            FROM familias
            WHERE nombre ILIKE %s
            ORDER BY nombre
            LIMIT %s
        """
        return fetch_all(sql, (f"%{filtro_texto}%", limit))
    else:
        sql = """
            SELECT id, nombre
            FROM familias
            ORDER BY nombre
            LIMIT %s
        """
        return fetch_all(sql, (limit,))


def get_by_id(familia_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una familia por su ID."""
    sql = "SELECT id, nombre FROM familias WHERE id = %s"
    return fetch_one(sql, (familia_id,))


def get_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """Obtiene una familia por su nombre (verificar duplicados)."""
    sql = "SELECT id, nombre FROM familias WHERE nombre = %s"
    return fetch_one(sql, (nombre,))


def crear_familia(nombre: str) -> int:
    """Crea una nueva familia."""
    sql = "INSERT INTO familias(nombre) VALUES(%s)"
    return execute_query(sql, (nombre,))


def actualizar_familia(familia_id: int, nombre: str) -> bool:
    """Actualiza una familia existente."""
    sql = "UPDATE familias SET nombre=%s WHERE id=%s"
    execute_query(sql, (nombre, familia_id))
    return True


def eliminar_familia(familia_id: int) -> bool:
    """Elimina una familia (fallará si tiene artículos asociados)."""
    sql = "DELETE FROM familias WHERE id=%s"
    execute_query(sql, (familia_id,))
    return True


def verificar_articulos(familia_id: int) -> bool:
    """Verifica si una familia tiene artículos asociados."""
    sql = "SELECT COUNT(*) as count FROM articulos WHERE familia_id = %s"
    result = fetch_one(sql, (familia_id,))
    return result['count'] > 0 if result else False


def get_articulos_familia(familia_id: int) -> List[Dict[str, Any]]:
    """Obtiene artículos asociados a una familia."""
    sql = """
        SELECT id, nombre, ref_proveedor, activo
        FROM articulos
        WHERE familia_id = %s
        ORDER BY nombre
    """
    return fetch_all(sql, (familia_id,))


def get_estadisticas_familia(familia_id: int) -> Dict[str, Any]:
    """Obtiene estadísticas de una familia."""
    sql = """
        SELECT
            COUNT(*) as total_articulos,
            SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as articulos_activos
        FROM articulos
        WHERE familia_id = %s
    """
    result = fetch_one(sql, (familia_id,))
    return result if result else {}
