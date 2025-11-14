"""
Repositorio de Inventarios - Consultas SQL para gestión de inventarios físicos
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query, get_con


# ========================================
# CONSULTAS DE INVENTARIOS (CABECERA)
# ========================================

def get_todos(
    estado: Optional[str] = None,
    almacen_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de inventarios con filtros opcionales.

    Args:
        estado: Filtrar por estado (EN_PROCESO, FINALIZADO)
        almacen_id: Filtrar por almacén
        limit: Límite de resultados

    Returns:
        Lista de inventarios con información completa
    """
    condiciones = []
    params = []

    if estado:
        condiciones.append("i.estado = ?")
        params.append(estado)

    if almacen_id:
        condiciones.append("i.almacen_id = ?")
        params.append(almacen_id)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"

    sql = f"""
        SELECT
            i.id,
            i.fecha,
            i.responsable,
            i.almacen_id,
            i.observaciones,
            i.estado,
            i.fecha_cierre,
            a.nombre AS almacen_nombre,
            COUNT(DISTINCT id.id) AS total_articulos,
            SUM(CASE WHEN id.stock_contado > 0 THEN 1 ELSE 0 END) AS articulos_contados,
            SUM(CASE WHEN id.diferencia != 0 THEN 1 ELSE 0 END) AS articulos_con_diferencia
        FROM inventarios i
        JOIN almacenes a ON i.almacen_id = a.id
        LEFT JOIN inventario_detalle id ON i.id = id.inventario_id
        WHERE {where_clause}
        GROUP BY i.id, i.fecha, i.responsable, i.almacen_id, i.observaciones, i.estado, i.fecha_cierre, a.nombre
        ORDER BY i.fecha DESC, i.id DESC
        LIMIT ?
    """
    params.append(limit)

    return fetch_all(sql, params)


def get_by_id(inventario_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un inventario específico por su ID.

    Args:
        inventario_id: ID del inventario

    Returns:
        Diccionario con información del inventario o None
    """
    sql = """
        SELECT
            i.id,
            i.fecha,
            i.responsable,
            i.almacen_id,
            i.observaciones,
            i.estado,
            i.fecha_cierre,
            a.nombre AS almacen_nombre
        FROM inventarios i
        JOIN almacenes a ON i.almacen_id = a.id
        WHERE i.id = ?
    """
    return fetch_one(sql, (inventario_id,))


def get_inventario_abierto_usuario(usuario: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el inventario abierto de un usuario específico.

    Args:
        usuario: Nombre del usuario/responsable

    Returns:
        Inventario EN_PROCESO del usuario o None
    """
    sql = """
        SELECT
            i.id,
            i.fecha,
            i.responsable,
            i.almacen_id,
            i.observaciones,
            i.estado,
            a.nombre AS almacen_nombre
        FROM inventarios i
        JOIN almacenes a ON i.almacen_id = a.id
        WHERE i.responsable = ? AND i.estado = 'EN_PROCESO'
        ORDER BY i.fecha DESC
        LIMIT 1
    """
    return fetch_one(sql, (usuario,))


def crear_inventario(
    fecha: str,
    responsable: str,
    almacen_id: int,
    observaciones: Optional[str] = None
) -> int:
    """
    Crea la cabecera de un nuevo inventario.

    Args:
        fecha: Fecha del inventario (YYYY-MM-DD)
        responsable: Nombre del responsable
        almacen_id: ID del almacén
        observaciones: Observaciones opcionales

    Returns:
        ID del inventario creado
    """
    sql = """
        INSERT INTO inventarios(fecha, responsable, almacen_id, observaciones, estado)
        VALUES(?, ?, ?, ?, 'EN_PROCESO')
    """
    return execute_query(sql, (fecha, responsable, almacen_id, observaciones))


def finalizar_inventario(inventario_id: int, fecha_cierre: str) -> bool:
    """
    Marca un inventario como finalizado.

    Args:
        inventario_id: ID del inventario
        fecha_cierre: Fecha de cierre (YYYY-MM-DD HH:MM:SS)

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE inventarios
        SET estado = 'FINALIZADO', fecha_cierre = ?
        WHERE id = ?
    """
    execute_query(sql, (fecha_cierre, inventario_id))
    return True


# ========================================
# CONSULTAS DE DETALLE DE INVENTARIO
# ========================================

def get_detalle(inventario_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle completo de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Lista de líneas del inventario con información de artículos
    """
    sql = """
        SELECT
            id.id,
            id.inventario_id,
            id.articulo_id,
            id.stock_teorico,
            id.stock_contado,
            id.diferencia,
            a.nombre AS articulo_nombre,
            a.u_medida AS articulo_u_medida,
            a.ean AS articulo_ean,
            a.ref_proveedor AS articulo_ref
        FROM inventario_detalle id
        JOIN articulos a ON id.articulo_id = a.id
        WHERE id.inventario_id = ?
        ORDER BY a.nombre
    """
    return fetch_all(sql, (inventario_id,))


def get_linea_detalle(detalle_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene una línea específica del detalle.

    Args:
        detalle_id: ID de la línea de detalle

    Returns:
        Diccionario con la línea o None
    """
    sql = """
        SELECT
            id.id,
            id.inventario_id,
            id.articulo_id,
            id.stock_teorico,
            id.stock_contado,
            id.diferencia,
            a.nombre AS articulo_nombre,
            a.u_medida AS articulo_u_medida
        FROM inventario_detalle id
        JOIN articulos a ON id.articulo_id = a.id
        WHERE id.id = ?
    """
    return fetch_one(sql, (detalle_id,))


def crear_lineas_detalle(
    inventario_id: int,
    almacen_id: int,
    solo_con_stock: bool = False
) -> int:
    """
    Crea las líneas de detalle de un inventario basándose en los artículos.

    Args:
        inventario_id: ID del inventario
        almacen_id: ID del almacén
        solo_con_stock: Si True, solo incluye artículos con stock > 0

    Returns:
        Cantidad de líneas creadas
    """
    con = get_con()
    cur = con.cursor()

    try:
        # Obtener artículos a inventariar
        if solo_con_stock:
            query = """
                SELECT DISTINCT a.id, COALESCE(SUM(v.delta), 0) as stock
                FROM articulos a
                LEFT JOIN vw_stock v ON a.id = v.articulo_id AND v.almacen_id = ?
                WHERE a.activo = 1
                GROUP BY a.id
                HAVING stock > 0
                ORDER BY a.nombre
            """
            cur.execute(query, (almacen_id,))
        else:
            query = """
                SELECT a.id, COALESCE(SUM(v.delta), 0) as stock
                FROM articulos a
                LEFT JOIN vw_stock v ON a.id = v.articulo_id AND v.almacen_id = ?
                WHERE a.activo = 1
                GROUP BY a.id
                ORDER BY a.nombre
            """
            cur.execute(query, (almacen_id,))

        articulos = cur.fetchall()

        # Crear líneas de detalle
        for art in articulos:
            articulo_id = art[0]
            stock_teorico = art[1]

            cur.execute("""
                INSERT INTO inventario_detalle(inventario_id, articulo_id, stock_teorico, stock_contado, diferencia)
                VALUES(?, ?, ?, 0, ?)
            """, (inventario_id, articulo_id, stock_teorico, -stock_teorico))

        con.commit()
        count = len(articulos)
        return count

    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()


def actualizar_conteo(detalle_id: int, stock_contado: float) -> bool:
    """
    Actualiza el conteo físico de una línea de inventario.

    Args:
        detalle_id: ID de la línea de detalle
        stock_contado: Cantidad contada físicamente

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE inventario_detalle
        SET stock_contado = ?,
            diferencia = ? - stock_teorico
        WHERE id = ?
    """
    execute_query(sql, (stock_contado, stock_contado, detalle_id))
    return True


def get_diferencias(inventario_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene solo las líneas con diferencias de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Lista de líneas con diferencia != 0
    """
    sql = """
        SELECT
            id.id,
            id.inventario_id,
            id.articulo_id,
            id.stock_teorico,
            id.stock_contado,
            id.diferencia,
            a.nombre AS articulo_nombre,
            a.u_medida AS articulo_u_medida
        FROM inventario_detalle id
        JOIN articulos a ON id.articulo_id = a.id
        WHERE id.inventario_id = ? AND id.diferencia != 0
        ORDER BY ABS(id.diferencia) DESC
    """
    return fetch_all(sql, (inventario_id,))


def get_estadisticas_inventario(inventario_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas resumidas de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(*) as total_lineas,
            SUM(CASE WHEN stock_contado > 0 THEN 1 ELSE 0 END) as lineas_contadas,
            SUM(CASE WHEN diferencia != 0 THEN 1 ELSE 0 END) as lineas_con_diferencia,
            SUM(CASE WHEN diferencia > 0 THEN 1 ELSE 0 END) as sobrantes,
            SUM(CASE WHEN diferencia < 0 THEN 1 ELSE 0 END) as faltantes,
            SUM(CASE WHEN diferencia > 0 THEN diferencia ELSE 0 END) as total_sobrante,
            SUM(CASE WHEN diferencia < 0 THEN ABS(diferencia) ELSE 0 END) as total_faltante
        FROM inventario_detalle
        WHERE inventario_id = ?
    """
    result = fetch_one(sql, (inventario_id,))
    return result if result else {}


# ========================================
# OPERACIONES AUXILIARES
# ========================================

def get_almacenes() -> List[Dict[str, Any]]:
    """
    Obtiene lista de almacenes disponibles.

    Returns:
        Lista de almacenes
    """
    sql = """
        SELECT id, nombre, tipo
        FROM almacenes
        ORDER BY nombre
    """
    return fetch_all(sql)


def get_articulos_sin_inventario_reciente(dias: int = 90) -> List[Dict[str, Any]]:
    """
    Obtiene artículos que no han sido inventariados recientemente.

    Args:
        dias: Número de días hacia atrás

    Returns:
        Lista de artículos sin inventario reciente
    """
    sql = """
        SELECT
            a.id,
            a.nombre,
            a.u_medida,
            MAX(i.fecha) as ultimo_inventario,
            julianday('now') - julianday(MAX(i.fecha)) as dias_desde_ultimo
        FROM articulos a
        LEFT JOIN inventario_detalle id ON a.id = id.articulo_id
        LEFT JOIN inventarios i ON id.inventario_id = i.id AND i.estado = 'FINALIZADO'
        WHERE a.activo = 1
        GROUP BY a.id, a.nombre, a.u_medida
        HAVING ultimo_inventario IS NULL OR dias_desde_ultimo > ?
        ORDER BY dias_desde_ultimo DESC NULLS FIRST
    """
    return fetch_all(sql, (dias,))
