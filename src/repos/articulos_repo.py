"""
Repositorio de Artículos - Consultas SQL para gestión de artículos del almacén
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query, get_con


# ========================================
# CONSULTAS DE ARTÍCULOS
# ========================================

def get_todos(
    filtro_texto: Optional[str] = None,
    familia_id: Optional[int] = None,
    solo_activos: Optional[bool] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de artículos con filtros opcionales.

    Args:
        filtro_texto: Búsqueda por nombre, EAN, referencia o palabras clave
        familia_id: Filtrar por familia
        solo_activos: Si True solo activos, si False solo inactivos, si None todos
        limit: Límite de resultados

    Returns:
        Lista de artículos con información completa
    """
    condiciones = []
    params = []

    if filtro_texto:
        condiciones.append(
            "(a.nombre LIKE ? OR a.ean LIKE ? OR a.ref_proveedor LIKE ? OR a.palabras_clave LIKE ?)"
        )
        params.extend([f"%{filtro_texto}%"] * 4)

    if familia_id:
        condiciones.append("a.familia_id = ?")
        params.append(familia_id)

    if solo_activos is not None:
        condiciones.append("a.activo = ?")
        params.append(1 if solo_activos else 0)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"

    sql = f"""
        SELECT
            a.id,
            a.ean,
            a.ref_proveedor,
            a.nombre,
            f.nombre AS familia_nombre,
            a.u_medida,
            a.min_alerta,
            a.coste,
            a.activo
        FROM articulos a
        LEFT JOIN familias f ON a.familia_id = f.id
        WHERE {where_clause}
        ORDER BY a.nombre
        LIMIT ?
    """
    params.append(limit)

    return fetch_all(sql, params)


def get_by_id(articulo_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un artículo específico por su ID con toda su información.

    Args:
        articulo_id: ID del artículo

    Returns:
        Diccionario con información del artículo o None
    """
    sql = """
        SELECT
            a.id,
            a.ean,
            a.ref_proveedor,
            a.nombre,
            a.palabras_clave,
            a.u_medida,
            a.min_alerta,
            a.ubicacion_id,
            a.proveedor_id,
            a.familia_id,
            a.marca,
            a.coste,
            a.pvp_sin,
            a.iva,
            a.activo,
            u.nombre AS ubicacion_nombre,
            p.nombre AS proveedor_nombre,
            f.nombre AS familia_nombre
        FROM articulos a
        LEFT JOIN ubicaciones u ON a.ubicacion_id = u.id
        LEFT JOIN proveedores p ON a.proveedor_id = p.id
        LEFT JOIN familias f ON a.familia_id = f.id
        WHERE a.id = ?
    """
    return fetch_one(sql, (articulo_id,))


def get_by_ean(ean: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un artículo por su código EAN.

    Args:
        ean: Código EAN del artículo

    Returns:
        Diccionario con información del artículo o None
    """
    sql = """
        SELECT id, nombre, ean, ref_proveedor, activo
        FROM articulos
        WHERE ean = ?
    """
    return fetch_one(sql, (ean,))


def get_by_referencia(ref_proveedor: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un artículo por su referencia de proveedor.

    Args:
        ref_proveedor: Referencia del proveedor

    Returns:
        Diccionario con información del artículo o None
    """
    sql = """
        SELECT id, nombre, ean, ref_proveedor, activo
        FROM articulos
        WHERE ref_proveedor = ?
    """
    return fetch_one(sql, (ref_proveedor,))


def crear_articulo(
    nombre: str,
    ean: Optional[str] = None,
    ref_proveedor: Optional[str] = None,
    palabras_clave: Optional[str] = None,
    u_medida: str = "unidad",
    min_alerta: float = 0,
    ubicacion_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    familia_id: Optional[int] = None,
    marca: Optional[str] = None,
    coste: float = 0,
    pvp_sin: float = 0,
    iva: float = 21,
    activo: bool = True
) -> int:
    """
    Crea un nuevo artículo.

    Args:
        nombre: Nombre del artículo (obligatorio)
        ean: Código EAN (opcional, debe ser único)
        ref_proveedor: Referencia del proveedor (opcional, debe ser única)
        palabras_clave: Palabras clave para búsqueda
        u_medida: Unidad de medida
        min_alerta: Stock mínimo para alertas
        ubicacion_id: ID de la ubicación
        proveedor_id: ID del proveedor principal
        familia_id: ID de la familia
        marca: Marca del producto
        coste: Coste de compra
        pvp_sin: PVP sin IVA
        iva: Porcentaje de IVA
        activo: Si está activo

    Returns:
        ID del artículo creado
    """
    sql = """
        INSERT INTO articulos(
            ean, ref_proveedor, nombre, palabras_clave, u_medida,
            min_alerta, ubicacion_id, proveedor_id, familia_id,
            marca, coste, pvp_sin, iva, activo
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(
        sql,
        (
            ean, ref_proveedor, nombre, palabras_clave, u_medida,
            min_alerta, ubicacion_id, proveedor_id, familia_id,
            marca, coste, pvp_sin, iva, 1 if activo else 0
        )
    )


def actualizar_articulo(
    articulo_id: int,
    nombre: str,
    ean: Optional[str] = None,
    ref_proveedor: Optional[str] = None,
    palabras_clave: Optional[str] = None,
    u_medida: str = "unidad",
    min_alerta: float = 0,
    ubicacion_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    familia_id: Optional[int] = None,
    marca: Optional[str] = None,
    coste: float = 0,
    pvp_sin: float = 0,
    iva: float = 21,
    activo: bool = True
) -> bool:
    """
    Actualiza un artículo existente.

    Args:
        articulo_id: ID del artículo a actualizar
        nombre: Nombre del artículo
        (resto de parámetros igual que crear_articulo)

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE articulos
        SET ean=?, ref_proveedor=?, nombre=?, palabras_clave=?, u_medida=?,
            min_alerta=?, ubicacion_id=?, proveedor_id=?, familia_id=?,
            marca=?, coste=?, pvp_sin=?, iva=?, activo=?
        WHERE id=?
    """
    execute_query(
        sql,
        (
            ean, ref_proveedor, nombre, palabras_clave, u_medida,
            min_alerta, ubicacion_id, proveedor_id, familia_id,
            marca, coste, pvp_sin, iva, 1 if activo else 0,
            articulo_id
        )
    )
    return True


def eliminar_articulo(articulo_id: int) -> bool:
    """
    Elimina un artículo.

    IMPORTANTE: Fallará si el artículo tiene movimientos asociados (constraint FK).

    Args:
        articulo_id: ID del artículo

    Returns:
        True si se eliminó correctamente

    Raises:
        IntegrityError: Si el artículo tiene movimientos asociados
    """
    sql = "DELETE FROM articulos WHERE id=?"
    execute_query(sql, (articulo_id,))
    return True


def activar_desactivar_articulo(articulo_id: int, activo: bool) -> bool:
    """
    Activa o desactiva un artículo.

    Args:
        articulo_id: ID del artículo
        activo: True para activar, False para desactivar

    Returns:
        True si se actualizó correctamente
    """
    sql = "UPDATE articulos SET activo=? WHERE id=?"
    execute_query(sql, (1 if activo else 0, articulo_id))
    return True


# ========================================
# CONSULTAS AUXILIARES
# ========================================

def get_familias() -> List[Dict[str, Any]]:
    """
    Obtiene lista de familias para combos.

    Returns:
        Lista de familias ordenadas por nombre
    """
    sql = "SELECT id, nombre FROM familias ORDER BY nombre"
    return fetch_all(sql)


def get_ubicaciones() -> List[Dict[str, Any]]:
    """
    Obtiene lista de ubicaciones para combos.

    Returns:
        Lista de ubicaciones ordenadas por nombre
    """
    sql = "SELECT id, nombre FROM ubicaciones ORDER BY nombre"
    return fetch_all(sql)


def get_proveedores() -> List[Dict[str, Any]]:
    """
    Obtiene lista de proveedores para combos.

    Returns:
        Lista de proveedores ordenados por nombre
    """
    sql = "SELECT id, nombre FROM proveedores ORDER BY nombre"
    return fetch_all(sql)


def verificar_movimientos(articulo_id: int) -> bool:
    """
    Verifica si un artículo tiene movimientos asociados.

    Args:
        articulo_id: ID del artículo

    Returns:
        True si tiene movimientos, False si no tiene
    """
    sql = "SELECT COUNT(*) as count FROM movimientos WHERE articulo_id = ?"
    result = fetch_one(sql, (articulo_id,))
    return result['count'] > 0 if result else False


def get_articulos_bajo_minimo() -> List[Dict[str, Any]]:
    """
    Obtiene artículos cuyo stock está por debajo del mínimo configurado.

    Returns:
        Lista de artículos con stock bajo
    """
    sql = """
        SELECT
            a.id,
            a.nombre,
            a.u_medida,
            a.min_alerta,
            COALESCE(SUM(v.delta), 0) AS stock_actual
        FROM articulos a
        LEFT JOIN vw_stock_total v ON a.id = v.articulo_id
        WHERE a.activo = 1 AND a.min_alerta > 0
        GROUP BY a.id, a.nombre, a.u_medida, a.min_alerta
        HAVING stock_actual < a.min_alerta
        ORDER BY a.nombre
    """
    return fetch_all(sql)


def buscar_articulos_por_texto(texto: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Busca artículos por EAN, referencia, nombre o palabras clave.
    Los resultados se ordenan por relevancia: coincidencias exactas primero.

    Args:
        texto: Texto de búsqueda (EAN, referencia, nombre, etc.)
        limit: Número máximo de resultados a devolver

    Returns:
        Lista de artículos ordenados por relevancia
    """
    sql = """
        SELECT id, nombre, u_medida, ean, ref_proveedor
        FROM articulos
        WHERE activo=1 AND (
            ean LIKE ? OR
            ref_proveedor LIKE ? OR
            nombre LIKE ? OR
            palabras_clave LIKE ?
        )
        ORDER BY
            CASE
                WHEN ean = ? THEN 1
                WHEN ref_proveedor = ? THEN 2
                WHEN nombre LIKE ? THEN 3
                ELSE 4
            END
        LIMIT ?
    """
    params = (
        f"%{texto}%", f"%{texto}%", f"%{texto}%", f"%{texto}%",
        texto, texto, f"{texto}%",
        limit
    )
    return fetch_all(sql, params)


def get_estadisticas_articulos() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de artículos.

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(*) as total_articulos,
            SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN activo = 0 THEN 1 ELSE 0 END) as inactivos,
            COUNT(DISTINCT familia_id) as total_familias
        FROM articulos
    """
    result = fetch_one(sql)
    return result if result else {}
