"""
Repositorio de Pedido Ideal - Consultas SQL para cálculo de pedidos
"""
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from src.core.db_utils import fetch_all, fetch_one


# ========================================
# CONSULTAS PARA ANÁLISIS DE CONSUMO
# ========================================

def get_articulos_para_analizar(incluir_sin_alerta: bool = False) -> List[Dict[str, Any]]:
    """
    Obtiene artículos candidatos para análisis de pedido.
    
    Args:
        incluir_sin_alerta: Si True, incluye todos los artículos activos
        
    Returns:
        Lista de artículos con su info básica
    """
    condiciones = ["a.activo = 1"]
    
    if not incluir_sin_alerta:
        condiciones.append("a.min_alerta > 0")
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            a.id,
            a.nombre,
            a.ean,
            a.ref_proveedor,
            COALESCE(v.stock, 0) AS stock,
            a.min_alerta AS nivel_alerta,
            a.u_medida,
            a.coste,
            a.proveedor_id,
            COALESCE(a.unidad_compra, 1) AS unidad_compra,
            COALESCE(a.dias_seguridad, 5) AS dias_seguridad,
            COALESCE(a.critico, 0) AS critico,
            p.nombre AS proveedor_nombre,
            p.email AS proveedor_email,
            p.telefono AS proveedor_telefono
        FROM articulos a
        LEFT JOIN (
            SELECT 
                articulo_id,
                SUM(delta) AS stock
            FROM vw_stock
            GROUP BY articulo_id
        ) v ON a.id = v.articulo_id
        LEFT JOIN proveedores p ON a.proveedor_id = p.id
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN COALESCE(v.stock, 0) < a.min_alerta THEN 0
                WHEN COALESCE(v.stock, 0) < (a.min_alerta * 1.5) THEN 1
                ELSE 2
            END,
            COALESCE(a.critico, 0) DESC,
            a.nombre
    """
    return fetch_all(sql)


def get_consumo_articulo_periodo(articulo_id: int, dias: int) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle de consumos de un artículo en los últimos X días.
    
    Args:
        articulo_id: ID del artículo
        dias: Número de días hacia atrás
        
    Returns:
        Lista con fecha y cantidad consumida cada día
    """
    fecha_inicio = (date.today() - timedelta(days=dias)).isoformat()
    
    sql = """
        SELECT 
            DATE(m.fecha) AS fecha,
            SUM(m.cantidad) AS cantidad_dia
        FROM movimientos m
        WHERE m.articulo_id = ?
          AND m.tipo = 'IMPUTACION'
          AND m.fecha >= ?
        GROUP BY DATE(m.fecha)
        ORDER BY m.fecha
    """
    return fetch_all(sql, (articulo_id, fecha_inicio))


def get_estadisticas_consumo(articulo_id: int, dias: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas agregadas de consumo de un artículo.
    
    Returns:
        Dict con: total_consumido, dias_con_movimiento, consumo_diario_medio, consumo_maximo
    """
    fecha_inicio = (date.today() - timedelta(days=dias)).isoformat()
    
    sql = """
        SELECT 
            SUM(m.cantidad) AS total_consumido,
            COUNT(DISTINCT DATE(m.fecha)) AS dias_con_movimiento,
            AVG(daily.cantidad_dia) AS consumo_diario_medio,
            MAX(daily.cantidad_dia) AS consumo_maximo
        FROM movimientos m
        LEFT JOIN (
            SELECT 
                articulo_id,
                DATE(fecha) AS fecha_dia,
                SUM(cantidad) AS cantidad_dia
            FROM movimientos
            WHERE tipo = 'IMPUTACION'
              AND fecha >= ?
              AND articulo_id = ?
            GROUP BY articulo_id, DATE(fecha)
        ) daily ON m.articulo_id = daily.articulo_id
        WHERE m.tipo = 'IMPUTACION'
          AND m.fecha >= ?
          AND m.articulo_id = ?
    """
    return fetch_one(sql, (fecha_inicio, articulo_id, fecha_inicio, articulo_id))


# ========================================
# CONSULTAS PARA PROVEEDORES
# ========================================

def get_lista_proveedores_activos() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de proveedores activos con artículos.
    
    Returns:
        Lista con: id, nombre, email, telefono, total_articulos
    """
    sql = """
        SELECT 
            p.id,
            p.nombre,
            p.email,
            p.telefono,
            p.direccion,
            COUNT(a.id) AS total_articulos
        FROM proveedores p
        LEFT JOIN articulos a ON p.id = a.proveedor_id AND a.activo = 1
        WHERE p.activo = 1
        GROUP BY p.id, p.nombre, p.email, p.telefono, p.direccion
        HAVING total_articulos > 0
        ORDER BY p.nombre
    """
    return fetch_all(sql)


def get_articulos_sin_proveedor() -> List[Dict[str, Any]]:
    """
    Obtiene artículos activos sin proveedor asignado.
    
    Returns:
        Lista con artículos que necesitan proveedor
    """
    sql = """
        SELECT 
            a.id,
            a.nombre,
            a.stock,
            a.nivel_alerta
        FROM articulos a
        WHERE a.activo = 1
          AND (a.proveedor_id IS NULL OR a.proveedor_id = 0)
          AND a.nivel_alerta > 0
        ORDER BY 
            CASE WHEN a.stock < a.nivel_alerta THEN 0 ELSE 1 END,
            a.nombre
    """
    return fetch_all(sql)


# ========================================
# CONSULTAS PARA ÚLTIMAS COMPRAS
# ========================================

def get_ultima_compra_articulo(articulo_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene información de la última compra de un artículo.
    
    Returns:
        Dict con: fecha, cantidad, coste_unit, proveedor (si disponible)
    """
    sql = """
        SELECT 
            m.fecha,
            m.cantidad,
            m.coste_unit,
            p.nombre AS proveedor
        FROM movimientos m
        LEFT JOIN proveedores p ON m.proveedor_id = p.id
        WHERE m.articulo_id = ?
          AND m.tipo = 'ENTRADA'
        ORDER BY m.fecha DESC
        LIMIT 1
    """
    return fetch_one(sql, (articulo_id,))


def get_historial_compras_articulo(articulo_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene el histórico de las últimas compras de un artículo.
    
    Returns:
        Lista con las últimas compras
    """
    sql = """
        SELECT 
            m.fecha,
            m.cantidad,
            m.coste_unit,
            (m.cantidad * m.coste_unit) AS coste_total,
            p.nombre AS proveedor
        FROM movimientos m
        LEFT JOIN proveedores p ON m.proveedor_id = p.id
        WHERE m.articulo_id = ?
          AND m.tipo = 'ENTRADA'
        ORDER BY m.fecha DESC
        LIMIT ?
    """
    return fetch_all(sql, (articulo_id, limit))


# ========================================
# FUNCIONES AUXILIARES
# ========================================

def existe_columna_en_articulos(nombre_columna: str) -> bool:
    """
    Verifica si una columna existe en la tabla articulos.
    Útil para compatibilidad con BDs que no han ejecutado el script de actualización.
    
    Args:
        nombre_columna: Nombre de la columna a verificar
        
    Returns:
        True si existe, False si no
    """
    sql = "PRAGMA table_info(articulos)"
    columnas = fetch_all(sql)
    return any(col['name'] == nombre_columna for col in columnas)


def get_resumen_pedido_ideal(filtros: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Obtiene un resumen general para el pedido ideal.
    
    Returns:
        Dict con: total_articulos, articulos_criticos, total_estimado
    """
    # Esta función se implementará en el servicio combinando múltiples consultas
    pass
