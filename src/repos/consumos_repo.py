"""
Repositorio de Consumos - Consultas SQL para análisis de consumos
"""
from typing import List, Dict, Any, Optional
from datetime import date
from src.core.db_utils import fetch_all, fetch_one


# ========================================
# CONSUMOS POR OT
# ========================================

def get_consumos_por_ot(ot: str) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle de material consumido en una OT específica.
    
    Args:
        ot: Número de orden de trabajo
        
    Returns:
        Lista de diccionarios con: articulo, cantidad, coste_unit, coste_total
    """
    sql = """
        SELECT 
            a.nombre AS articulo,
            a.u_medida AS unidad,
            m.cantidad,
            m.coste_unit,
            (m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total,
            m.fecha,
            o.nombre AS operario
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN operarios o ON m.operario_id = o.id
        WHERE m.tipo = 'IMPUTACION'
          AND m.ot = %s
        ORDER BY m.fecha DESC, a.nombre
    """
    return fetch_all(sql, (ot,))


def get_resumen_ot(ot: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el resumen total de una OT.

    Returns:
        Dict con: total_articulos, total_imputaciones, coste_total, fecha_primera, fecha_ultima
    """
    sql = """
        SELECT
            COUNT(DISTINCT m.articulo_id) AS total_articulos,
            COUNT(*) AS total_imputaciones,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total,
            MIN(m.fecha) AS fecha_primera,
            MAX(m.fecha) AS fecha_ultima
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE m.tipo = 'IMPUTACION'
          AND m.ot = %s
    """
    return fetch_one(sql, (ot,))


def get_ots_recientes(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtiene las OTs más recientes con consumos.
    
    Returns:
        Lista de diccionarios con: ot, fecha_ultima, total_imputaciones, coste_total
    """
    sql = """
        SELECT 
            m.ot,
            MAX(m.fecha) AS fecha_ultima,
            COUNT(*) AS total_imputaciones,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE m.tipo = 'IMPUTACION'
          AND m.ot IS NOT NULL
          AND m.ot != ''
        GROUP BY m.ot
        ORDER BY MAX(m.fecha) DESC
        LIMIT %s
    """
    return fetch_all(sql, (limit,))


# ========================================
# CONSUMOS POR OPERARIO
# ========================================

def get_consumos_por_operario(operario_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle de consumos de un operario en un período.

    Args:
        operario_id: ID del operario
        fecha_desde: Fecha inicio (formato ISO: yyyy-mm-dd)
        fecha_hasta: Fecha fin (formato ISO: yyyy-mm-dd)

    Returns:
        Lista con detalle de imputaciones
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.operario_id = %s"]
    params = [operario_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            m.fecha,
            m.ot,
            a.nombre AS articulo,
            m.cantidad,
            a.u_medida AS unidad,
            m.coste_unit,
            (m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC
    """
    return fetch_all(sql, tuple(params))


def get_resumen_operario(operario_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene el resumen de actividad de un operario.

    Returns:
        Dict con: total_imputaciones, total_ots, coste_total, operario_nombre
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.operario_id = %s"]
    params = [operario_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            o.nombre AS operario_nombre,
            COUNT(*) AS total_imputaciones,
            COUNT(DISTINCT m.ot) AS total_ots,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        INNER JOIN operarios o ON m.operario_id = o.id
        WHERE {where_clause}
        GROUP BY o.nombre
    """
    return fetch_one(sql, tuple(params))


def get_top_articulos_operario(operario_id: int, fecha_desde: str = None, fecha_hasta: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos más usados por un operario.

    Returns:
        Lista con: articulo, cantidad_total, veces_usado, coste_total
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.operario_id = %s"]
    params = [operario_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)

    where_clause = " AND ".join(condiciones)
    params.append(limit)

    sql = f"""
        SELECT
            a.nombre AS articulo,
            a.u_medida AS unidad,
            SUM(m.cantidad) AS cantidad_total,
            COUNT(*) AS veces_usado,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE {where_clause}
        GROUP BY a.id, a.nombre, a.u_medida
        ORDER BY cantidad_total DESC
        LIMIT %s
    """
    return fetch_all(sql, tuple(params))


# ========================================
# CONSUMOS POR FURGONETA
# ========================================

def get_consumos_por_furgoneta(furgoneta_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene consumos realizados desde una furgoneta específica.

    Args:
        furgoneta_id: ID de la furgoneta (almacén tipo furgoneta)
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin

    Returns:
        Lista con detalle de imputaciones desde esa furgoneta
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.origen_id = %s"]
    params = [furgoneta_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            m.fecha,
            m.ot,
            a.nombre AS articulo,
            m.cantidad,
            a.u_medida AS unidad,
            o.nombre AS operario,
            (m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN operarios o ON m.operario_id = o.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC
    """
    return fetch_all(sql, tuple(params))


def get_resumen_furgoneta(furgoneta_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene resumen de consumos de una furgoneta.

    Returns:
        Dict con: furgoneta_nombre, total_imputaciones, coste_total
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.origen_id = %s"]
    params = [furgoneta_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            al.nombre AS furgoneta_nombre,
            COUNT(*) AS total_imputaciones,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        INNER JOIN almacenes al ON m.origen_id = al.id
        WHERE {where_clause}
        GROUP BY al.nombre
    """
    return fetch_one(sql, tuple(params))


# ========================================
# CONSUMOS POR PERÍODO
# ========================================

def get_resumen_periodo(fecha_desde: str, fecha_hasta: str) -> Dict[str, Any]:
    """
    Obtiene un resumen completo de movimientos en un período.
    
    Returns:
        Dict con totales de entradas, salidas, pérdidas, devoluciones
    """
    sql = """
        SELECT 
            SUM(CASE WHEN tipo = 'ENTRADA' THEN cantidad * COALESCE(coste_unit, 0) ELSE 0 END) AS total_entradas,
            SUM(CASE WHEN tipo = 'IMPUTACION' THEN cantidad * COALESCE(coste_unit, 0) ELSE 0 END) AS total_imputaciones,
            SUM(CASE WHEN tipo = 'PERDIDA' THEN cantidad * COALESCE(coste_unit, 0) ELSE 0 END) AS total_perdidas,
            SUM(CASE WHEN tipo = 'DEVOLUCION' THEN cantidad * COALESCE(coste_unit, 0) ELSE 0 END) AS total_devoluciones,
            COUNT(DISTINCT CASE WHEN tipo = 'IMPUTACION' THEN ot END) AS total_ots,
            COUNT(*) AS total_movimientos
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE m.fecha BETWEEN %s AND %s
    """
    result = fetch_one(sql, (fecha_desde, fecha_hasta))
    return result if result else {}


def get_articulos_mas_consumidos_periodo(fecha_desde: str, fecha_hasta: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos más consumidos en un período.
    
    Returns:
        Lista con: articulo, cantidad_total, coste_total, veces_usado
    """
    sql = """
        SELECT 
            a.nombre AS articulo,
            a.u_medida AS unidad,
            SUM(m.cantidad) AS cantidad_total,
            COUNT(*) AS veces_usado,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE m.tipo = 'IMPUTACION'
          AND m.fecha BETWEEN %s AND %s
        GROUP BY a.id, a.nombre, a.u_medida
        ORDER BY cantidad_total DESC
        LIMIT %s
    """
    return fetch_all(sql, (fecha_desde, fecha_hasta, limit))


def get_operarios_mas_activos_periodo(fecha_desde: str, fecha_hasta: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los operarios más activos en un período.
    
    Returns:
        Lista con: operario, total_imputaciones, coste_total
    """
    sql = """
        SELECT 
            o.nombre AS operario,
            COUNT(*) AS total_imputaciones,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN operarios o ON m.operario_id = o.id
        WHERE m.tipo = 'IMPUTACION'
          AND m.fecha BETWEEN %s AND %s
          AND o.nombre IS NOT NULL
        GROUP BY o.id, o.nombre
        ORDER BY total_imputaciones DESC
        LIMIT %s
    """
    return fetch_all(sql, (fecha_desde, fecha_hasta, limit))


# ========================================
# CONSUMOS POR ARTÍCULO
# ========================================

def get_consumos_por_articulo(articulo_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> List[Dict[str, Any]]:
    """
    Obtiene el histórico de consumos de un artículo específico.

    Returns:
        Lista con: fecha, ot, operario, cantidad, coste_total
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.articulo_id = %s"]
    params = [articulo_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            m.fecha,
            m.ot,
            o.nombre AS operario,
            m.cantidad,
            a.u_medida AS unidad,
            (m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN operarios o ON m.operario_id = o.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC
    """
    return fetch_all(sql, tuple(params))


def get_resumen_articulo(articulo_id: int, fecha_desde: str = None, fecha_hasta: str = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene el resumen de consumos de un artículo.

    Returns:
        Dict con: articulo_nombre, cantidad_total, veces_usado, coste_total
    """
    condiciones = ["m.tipo = 'IMPUTACION'", "m.articulo_id = %s"]
    params = [articulo_id]

    if fecha_desde:
        condiciones.append("m.fecha >= %s")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= %s")
        params.append(fecha_hasta)
    
    where_clause = " AND ".join(condiciones)
    
    sql = f"""
        SELECT 
            a.nombre AS articulo_nombre,
            a.u_medida AS unidad,
            SUM(m.cantidad) AS cantidad_total,
            COUNT(*) AS veces_usado,
            SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS coste_total
        FROM movimientos m
        INNER JOIN articulos a ON m.articulo_id = a.id
        WHERE {where_clause}
        GROUP BY a.nombre, a.u_medida
    """
    return fetch_one(sql, tuple(params))


# ========================================
# FUNCIONES AUXILIARES
# ========================================

def get_lista_operarios_con_consumos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de operarios que han realizado imputaciones.
    
    Returns:
        Lista con: id, nombre
    """
    sql = """
        SELECT DISTINCT o.id, o.nombre
        FROM operarios o
        INNER JOIN movimientos m ON o.id = m.operario_id
        WHERE m.tipo = 'IMPUTACION'
        ORDER BY o.nombre
    """
    return fetch_all(sql)


def get_lista_furgonetas() -> List[Dict[str, Any]]:
    """
    Obtiene lista de furgonetas (almacenes de tipo furgoneta).
    
    Returns:
        Lista con: id, nombre, tipo
    """
    # Primero intentamos con la tabla furgonetas si existe
    sql_furgonetas = """
        SELECT id, matricula as nombre, 'furgoneta' as tipo
        FROM furgonetas
        WHERE activa = 1
        ORDER BY matricula
    """
    
    # Si no existe, usamos almacenes
    sql_almacenes = """
        SELECT id, nombre, tipo
        FROM almacenes
        WHERE tipo = 'furgoneta' OR tipo LIKE '%furgon%'
        ORDER BY nombre
    """
    
    try:
        return fetch_all(sql_furgonetas)
    except Exception as e:
        # Si falla la query de furgonetas, intentar con todos los almacenes
        logger.warning(f"Error al obtener furgonetas, usando todos los almacenes: {e}")
        return fetch_all(sql_almacenes)


def buscar_articulo_por_nombre(nombre: str) -> List[Dict[str, Any]]:
    """
    Busca artículos por nombre o palabras clave.
    
    Returns:
        Lista con: id, nombre, ean, ref_proveedor
    """
    sql = """
        SELECT id, nombre, ean, ref_proveedor, u_medida
        FROM articulos
        WHERE activo = 1
          AND (nombre ILIKE %s OR palabras_clave ILIKE %s OR ean ILIKE %s OR ref_proveedor ILIKE %s)
        ORDER BY nombre
        LIMIT 50
    """
    patron = f"%{nombre}%"
    return fetch_all(sql, (patron, patron, patron, patron))
