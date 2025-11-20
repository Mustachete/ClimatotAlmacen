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
            "(a.nombre LIKE %s OR a.ean LIKE %s OR a.ref_proveedor LIKE %s OR a.palabras_clave LIKE %s)"
        )
        params.extend([f"%{filtro_texto}%"] * 4)

    if familia_id:
        condiciones.append("a.familia_id = %s")
        params.append(familia_id)

    if solo_activos is not None:
        condiciones.append("a.activo = %s")
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
        LIMIT %s
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
        WHERE a.id = %s
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
        WHERE ean = %s
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
        WHERE ref_proveedor = %s
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
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        SET ean=%s, ref_proveedor=%s, nombre=%s, palabras_clave=%s, u_medida=%s,
            min_alerta=%s, ubicacion_id=%s, proveedor_id=%s, familia_id=%s,
            marca=%s, coste=%s, pvp_sin=%s, iva=%s, activo=%s
        WHERE id=%s
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
    sql = "DELETE FROM articulos WHERE id=%s"
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
    sql = "UPDATE articulos SET activo=%s WHERE id=%s"
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
    sql = "SELECT COUNT(*) as count FROM movimientos WHERE articulo_id = %s"
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
            ean LIKE %s OR
            ref_proveedor LIKE %s OR
            nombre LIKE %s OR
            palabras_clave LIKE %s
        )
        ORDER BY
            CASE
                WHEN ean = %s THEN 1
                WHEN ref_proveedor = %s THEN 2
                WHEN nombre LIKE %s THEN 3
                ELSE 4
            END
        LIMIT %s
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


def buscar_articulos_completo(
    texto: str,
    filtro_proveedor_id: Optional[int] = None,
    filtro_almacen_id: Optional[int] = None,
    filtro_familia_id: Optional[int] = None,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """
    Busca artículos con todos los campos y soporta filtros múltiples.
    Usada por el buscador avanzado de artículos.

    Args:
        texto: Texto de búsqueda (EAN, ref, nombre, palabras clave)
        filtro_proveedor_id: Filtrar por proveedor (opcional)
        filtro_almacen_id: Filtrar solo artículos con stock en ese almacén (opcional)
        filtro_familia_id: Filtrar por familia (opcional)
        limit: Número máximo de resultados

    Returns:
        Lista de artículos con todos los campos
    """
    query = """
        SELECT a.id, a.nombre, a.u_medida, a.ean, a.ref_proveedor, a.coste, a.pvp_sin,
               a.proveedor_id, a.familia_id, a.ubicacion_id, a.marca
        FROM articulos a
        WHERE a.activo=1
    """
    params = []

    if texto:
        query += """ AND (
            a.ean LIKE %s OR
            a.ref_proveedor LIKE %s OR
            a.nombre LIKE %s OR
            a.palabras_clave LIKE %s
        )"""
        params.extend([f"%{texto}%"] * 4)

    if filtro_proveedor_id:
        query += " AND a.proveedor_id=%s"
        params.append(filtro_proveedor_id)

    if filtro_almacen_id:
        query += """ AND EXISTS (
            SELECT 1 FROM vw_stock v
            WHERE v.articulo_id=a.id AND v.almacen_id=%s AND v.delta > 0
        )"""
        params.append(filtro_almacen_id)

    if filtro_familia_id:
        query += " AND a.familia_id=%s"
        params.append(filtro_familia_id)

    if texto:
        # Ordenar por relevancia si hay texto de búsqueda
        query += """
            ORDER BY
                CASE
                    WHEN a.ean = %s THEN 1
                    WHEN a.ref_proveedor = %s THEN 2
                    WHEN a.nombre LIKE %s THEN 3
                    ELSE 4
                END
        """
        params.extend([texto, texto, f"{texto}%"])
    else:
        query += " ORDER BY a.nombre"

    query += " LIMIT %s"
    params.append(limit)

    return fetch_all(query, tuple(params))


def buscar_articulo_exacto(
    texto: str,
    filtro_proveedor_id: Optional[int] = None,
    filtro_almacen_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Busca un artículo por coincidencia EXACTA de EAN o referencia.
    Usada para búsqueda rápida por código de barras.

    Args:
        texto: EAN o referencia a buscar (exacta)
        filtro_proveedor_id: Filtrar por proveedor (opcional)
        filtro_almacen_id: Filtrar solo si tiene stock en ese almacén (opcional)

    Returns:
        Artículo encontrado o None
    """
    query = """
        SELECT a.id, a.nombre, a.u_medida, a.ean, a.ref_proveedor, a.coste, a.pvp_sin,
               a.proveedor_id, a.familia_id, a.ubicacion_id, a.marca
        FROM articulos a
        WHERE a.activo=1 AND (a.ean=%s OR a.ref_proveedor=%s)
    """
    params = [texto, texto]

    if filtro_proveedor_id:
        query += " AND a.proveedor_id=%s"
        params.append(filtro_proveedor_id)

    if filtro_almacen_id:
        query += """ AND EXISTS (
            SELECT 1 FROM vw_stock v
            WHERE v.articulo_id=a.id AND v.almacen_id=%s AND v.delta > 0
        )"""
        params.append(filtro_almacen_id)

    query += " LIMIT 1"

    return fetch_one(query, tuple(params))


def get_ultimas_entradas(articulo_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtiene las últimas entradas (recepciones) de un artículo desde proveedores.

    Args:
        articulo_id: ID del artículo
        limit: Número máximo de entradas a devolver (por defecto 50)

    Returns:
        Lista de entradas con fecha, cantidad y proveedor
    """
    sql = """
        SELECT
            m.fecha,
            m.cantidad,
            p.nombre AS proveedor,
            m.albaran,
            m.coste_unit
        FROM movimientos m
        LEFT JOIN proveedores p ON m.origen_id = p.id
        WHERE m.articulo_id = %s
          AND m.tipo = 'ENTRADA'
        ORDER BY m.fecha DESC, m.id DESC
        LIMIT %s
    """

    return fetch_all(sql, (articulo_id, limit))
