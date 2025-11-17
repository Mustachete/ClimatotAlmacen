"""
Servicio de Stock - Lógica de negocio para consultas de stock
"""
from typing import List, Dict, Any, Optional
from src.repos import stock_repo
from src.core.logger import logger, log_error_bd


def obtener_stock_completo(
    filtro_texto: Optional[str] = None,
    familia: Optional[str] = None,
    almacen: Optional[str] = None,
    solo_con_stock: bool = False,
    solo_alertas: bool = False
) -> List[Dict[str, Any]]:
    """
    Obtiene el stock completo de todos los artículos con filtros opcionales.

    Args:
        filtro_texto: Búsqueda por nombre, EAN o referencia
        familia: Filtro por nombre de familia
        almacen: Filtro por nombre de almacén
        solo_con_stock: Si True, solo artículos con stock > 0
        solo_alertas: Si True, solo artículos con stock < mínimo

    Returns:
        Lista de artículos con su stock por almacén
    """
    try:
        return stock_repo.get_stock_completo(
            filtro_texto=filtro_texto,
            familia=familia,
            almacen=almacen,
            solo_con_stock=solo_con_stock,
            solo_alertas=solo_alertas
        )
    except Exception as e:
        log_error_bd("stock", "obtener_stock_completo", e)
        logger.error(f"Error al obtener stock completo: {e}")
        return []


def obtener_stock_articulo_por_almacen(articulo_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock de un artículo específico en todos los almacenes.

    Args:
        articulo_id: ID del artículo

    Returns:
        Lista con el stock del artículo por almacén
    """
    try:
        return stock_repo.get_stock_articulo_por_almacen(articulo_id)
    except Exception as e:
        log_error_bd("stock", "obtener_stock_articulo_por_almacen", e)
        logger.error(f"Error al obtener stock del artículo {articulo_id}: {e}")
        return []


def obtener_stock_total_articulo(articulo_id: int) -> float:
    """
    Obtiene el stock total de un artículo (sumando todos los almacenes).

    Args:
        articulo_id: ID del artículo

    Returns:
        Stock total del artículo
    """
    try:
        return stock_repo.get_stock_total_articulo(articulo_id)
    except Exception as e:
        log_error_bd("stock", "obtener_stock_total_articulo", e)
        logger.error(f"Error al obtener stock total del artículo {articulo_id}: {e}")
        return 0.0


def obtener_articulos_con_stock_bajo() -> List[Dict[str, Any]]:
    """
    Obtiene artículos con stock por debajo del mínimo de alerta.

    Returns:
        Lista de artículos con stock bajo
    """
    try:
        return stock_repo.get_articulos_con_stock_bajo()
    except Exception as e:
        log_error_bd("stock", "obtener_articulos_con_stock_bajo", e)
        logger.error(f"Error al obtener artículos con stock bajo: {e}")
        return []


def obtener_articulos_sin_stock() -> List[Dict[str, Any]]:
    """
    Obtiene artículos activos sin stock en ningún almacén.

    Returns:
        Lista de artículos sin stock
    """
    try:
        return stock_repo.get_articulos_sin_stock()
    except Exception as e:
        log_error_bd("stock", "obtener_articulos_sin_stock", e)
        logger.error(f"Error al obtener artículos sin stock: {e}")
        return []


def obtener_estadisticas_stock() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de stock.

    Returns:
        Diccionario con estadísticas de stock
    """
    try:
        return stock_repo.get_estadisticas_stock()
    except Exception as e:
        log_error_bd("stock", "obtener_estadisticas_stock", e)
        logger.error(f"Error al obtener estadísticas de stock: {e}")
        return {
            'total_articulos': 0,
            'articulos_con_stock': 0,
            'articulos_bajo_minimo': 0,
            'articulos_sin_stock': 0
        }


def verificar_stock_disponible(articulo_id: int, almacen_id: int, cantidad_requerida: float) -> tuple[bool, str]:
    """
    Verifica si hay stock disponible de un artículo en un almacén.

    Args:
        articulo_id: ID del artículo
        almacen_id: ID del almacén
        cantidad_requerida: Cantidad que se necesita

    Returns:
        Tupla (hay_stock: bool, mensaje: str)
    """
    try:
        stock_por_almacen = stock_repo.get_stock_articulo_por_almacen(articulo_id)

        for almacen in stock_por_almacen:
            if almacen['almacen_id'] == almacen_id:
                stock_disponible = almacen['stock']
                if stock_disponible >= cantidad_requerida:
                    return True, f"Stock disponible: {stock_disponible:.2f}"
                else:
                    return False, f"Stock insuficiente. Disponible: {stock_disponible:.2f}, Requerido: {cantidad_requerida:.2f}"

        return False, "No hay stock en este almacén"

    except Exception as e:
        log_error_bd("stock", "verificar_stock_disponible", e)
        logger.error(f"Error al verificar stock disponible: {e}")
        return False, f"Error al verificar stock: {e}"
