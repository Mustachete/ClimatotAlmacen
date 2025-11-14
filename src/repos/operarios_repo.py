"""
Repositorio de Operarios - Consultas SQL para gestión de operarios/técnicos
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


# ========================================
# CONSULTAS DE OPERARIOS
# ========================================

def get_todos(
    filtro_texto: Optional[str] = None,
    solo_rol: Optional[str] = None,
    solo_activos: Optional[bool] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de operarios con filtros opcionales.

    Args:
        filtro_texto: Búsqueda por nombre
        solo_rol: Filtrar por rol ('oficial' o 'ayudante')
        solo_activos: Si True solo activos, si False solo inactivos, si None todos
        limit: Límite de resultados

    Returns:
        Lista de operarios
    """
    condiciones = []
    params = []

    if filtro_texto:
        condiciones.append("nombre LIKE ?")
        params.append(f"%{filtro_texto}%")

    if solo_rol:
        condiciones.append("rol_operario = ?")
        params.append(solo_rol)

    if solo_activos is not None:
        condiciones.append("activo = ?")
        params.append(1 if solo_activos else 0)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"

    sql = f"""
        SELECT id, nombre, rol_operario, activo
        FROM operarios
        WHERE {where_clause}
        ORDER BY rol_operario DESC, nombre
        LIMIT ?
    """
    params.append(limit)

    return fetch_all(sql, params)


def get_by_id(operario_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un operario específico por su ID.

    Args:
        operario_id: ID del operario

    Returns:
        Diccionario con información del operario o None
    """
    sql = """
        SELECT id, nombre, rol_operario, activo
        FROM operarios
        WHERE id = ?
    """
    return fetch_one(sql, (operario_id,))


def get_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un operario por su nombre (para verificar duplicados).

    Args:
        nombre: Nombre del operario

    Returns:
        Diccionario con información del operario o None
    """
    sql = """
        SELECT id, nombre, rol_operario, activo
        FROM operarios
        WHERE nombre = ?
    """
    return fetch_one(sql, (nombre,))


def crear_operario(
    nombre: str,
    rol_operario: str = "ayudante",
    activo: bool = True
) -> int:
    """
    Crea un nuevo operario.

    Args:
        nombre: Nombre del operario (obligatorio, debe ser único)
        rol_operario: 'oficial' o 'ayudante'
        activo: Si está activo

    Returns:
        ID del operario creado
    """
    sql = """
        INSERT INTO operarios(nombre, rol_operario, activo)
        VALUES(?, ?, ?)
    """
    return execute_query(sql, (nombre, rol_operario, 1 if activo else 0))


def actualizar_operario(
    operario_id: int,
    nombre: str,
    rol_operario: str = "ayudante",
    activo: bool = True
) -> bool:
    """
    Actualiza un operario existente.

    Args:
        operario_id: ID del operario a actualizar
        nombre: Nombre del operario
        rol_operario: 'oficial' o 'ayudante'
        activo: Si está activo

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE operarios
        SET nombre=?, rol_operario=?, activo=?
        WHERE id=?
    """
    execute_query(sql, (nombre, rol_operario, 1 if activo else 0, operario_id))
    return True


def eliminar_operario(operario_id: int) -> bool:
    """
    Elimina un operario.

    IMPORTANTE: Fallará si el operario tiene movimientos o asignaciones (constraint FK).

    Args:
        operario_id: ID del operario

    Returns:
        True si se eliminó correctamente

    Raises:
        IntegrityError: Si el operario tiene movimientos/asignaciones
    """
    sql = "DELETE FROM operarios WHERE id=?"
    execute_query(sql, (operario_id,))
    return True


def activar_desactivar_operario(operario_id: int, activo: bool) -> bool:
    """
    Activa o desactiva un operario.

    Args:
        operario_id: ID del operario
        activo: True para activar, False para desactivar

    Returns:
        True si se actualizó correctamente
    """
    sql = "UPDATE operarios SET activo=? WHERE id=?"
    execute_query(sql, (1 if activo else 0, operario_id))
    return True


# ========================================
# CONSULTAS AUXILIARES
# ========================================

def verificar_movimientos(operario_id: int) -> bool:
    """
    Verifica si un operario tiene movimientos asociados.

    Args:
        operario_id: ID del operario

    Returns:
        True si tiene movimientos, False si no tiene
    """
    sql = "SELECT COUNT(*) as count FROM movimientos WHERE operario_id = ?"
    result = fetch_one(sql, (operario_id,))
    return result['count'] > 0 if result else False


def get_movimientos_operario(
    operario_id: int,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene los movimientos de un operario en un rango de fechas.

    Args:
        operario_id: ID del operario
        fecha_desde: Fecha inicio (formato YYYY-MM-DD)
        fecha_hasta: Fecha fin (formato YYYY-MM-DD)

    Returns:
        Lista de movimientos del operario
    """
    condiciones = ["operario_id = ?"]
    params = [operario_id]

    if fecha_desde:
        condiciones.append("fecha >= ?")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("fecha <= ?")
        params.append(fecha_hasta)

    where_clause = " AND ".join(condiciones)

    sql = f"""
        SELECT
            m.id,
            m.fecha,
            m.tipo,
            a.nombre as articulo_nombre,
            m.cantidad,
            o.nombre as almacen_origen,
            d.nombre as almacen_destino
        FROM movimientos m
        LEFT JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN almacenes o ON m.origen_id = o.id
        LEFT JOIN almacenes d ON m.destino_id = d.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC, m.id DESC
    """

    return fetch_all(sql, params)


def get_oficiales_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de oficiales activos (para asignar furgonetas).

    Returns:
        Lista de oficiales activos
    """
    sql = """
        SELECT id, nombre
        FROM operarios
        WHERE rol_operario = 'oficial' AND activo = 1
        ORDER BY nombre
    """
    return fetch_all(sql)


def get_ayudantes_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de ayudantes activos.

    Returns:
        Lista de ayudantes activos
    """
    sql = """
        SELECT id, nombre
        FROM operarios
        WHERE rol_operario = 'ayudante' AND activo = 1
        ORDER BY nombre
    """
    return fetch_all(sql)


def get_operarios_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de todos los operarios activos (oficiales y ayudantes).

    Returns:
        Lista de operarios activos
    """
    sql = """
        SELECT id, nombre, rol_operario
        FROM operarios
        WHERE activo = 1
        ORDER BY rol_operario DESC, nombre
    """
    return fetch_all(sql)


def get_estadisticas_operario(operario_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un operario.

    Args:
        operario_id: ID del operario

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(*) as total_movimientos,
            COUNT(DISTINCT fecha) as dias_trabajados,
            MIN(fecha) as primer_movimiento,
            MAX(fecha) as ultimo_movimiento
        FROM movimientos
        WHERE operario_id = ?
    """
    result = fetch_one(sql, (operario_id,))
    return result if result else {}


def get_estadisticas_operarios() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de operarios.

    Returns:
        Diccionario con estadísticas
    """
    sql = """
        SELECT
            COUNT(*) as total_operarios,
            SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN activo = 0 THEN 1 ELSE 0 END) as inactivos,
            SUM(CASE WHEN rol_operario = 'oficial' THEN 1 ELSE 0 END) as oficiales,
            SUM(CASE WHEN rol_operario = 'ayudante' THEN 1 ELSE 0 END) as ayudantes
        FROM operarios
    """
    result = fetch_one(sql)
    return result if result else {}


def get_operarios_con_movimientos() -> List[Dict[str, Any]]:
    """
    Obtiene operarios que tienen movimientos registrados.

    Returns:
        Lista de operarios con cantidad de movimientos
    """
    sql = """
        SELECT
            o.id,
            o.nombre,
            o.rol_operario,
            COUNT(m.id) as total_movimientos,
            MAX(m.fecha) as ultimo_movimiento
        FROM operarios o
        INNER JOIN movimientos m ON o.id = m.operario_id
        GROUP BY o.id, o.nombre, o.rol_operario
        ORDER BY total_movimientos DESC
    """
    return fetch_all(sql)


def get_operarios_sin_movimientos() -> List[Dict[str, Any]]:
    """
    Obtiene operarios que no tienen movimientos registrados.

    Returns:
        Lista de operarios sin movimientos
    """
    sql = """
        SELECT o.id, o.nombre, o.rol_operario, o.activo
        FROM operarios o
        LEFT JOIN movimientos m ON o.id = m.operario_id
        WHERE m.id IS NULL
        ORDER BY o.nombre
    """
    return fetch_all(sql)
