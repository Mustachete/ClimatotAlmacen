"""
Repositorio de Movimientos - Consultas SQL para operaciones de movimientos de almacén
"""
from typing import List, Dict, Any, Optional
from datetime import date
from src.core.db_utils import fetch_all, fetch_one, execute_query, get_con


# ========================================
# CONSULTAS DE LECTURA
# ========================================

def get_todos(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    articulo_id: Optional[int] = None,
    almacen_id: Optional[int] = None,
    operario_id: Optional[int] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene movimientos con filtros opcionales.

    Args:
        fecha_desde: Fecha inicio (formato YYYY-MM-DD)
        fecha_hasta: Fecha fin (formato YYYY-MM-DD)
        tipo: Tipo de movimiento (ENTRADA, TRASPASO, IMPUTACION, PERDIDA, DEVOLUCION)
        articulo_id: ID del artículo
        almacen_id: ID del almacén (origen o destino)
        operario_id: ID del operario
        limit: Límite de resultados

    Returns:
        Lista de movimientos con información completa
    """
    condiciones = []
    params = []

    if fecha_desde:
        condiciones.append("m.fecha >= ?")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("m.fecha <= ?")
        params.append(fecha_hasta)

    if tipo:
        condiciones.append("m.tipo = ?")
        params.append(tipo)

    if articulo_id:
        condiciones.append("m.articulo_id = ?")
        params.append(articulo_id)

    if almacen_id:
        condiciones.append("(m.origen_id = ? OR m.destino_id = ?)")
        params.extend([almacen_id, almacen_id])

    if operario_id:
        condiciones.append("m.operario_id = ?")
        params.append(operario_id)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"

    sql = f"""
        SELECT
            m.id,
            m.fecha,
            m.tipo,
            m.cantidad,
            m.coste_unit,
            m.motivo,
            m.ot,
            m.albaran,
            m.responsable,
            a.id AS articulo_id,
            a.nombre AS articulo_nombre,
            a.u_medida AS articulo_u_medida,
            origen.id AS origen_id,
            origen.nombre AS origen_nombre,
            destino.id AS destino_id,
            destino.nombre AS destino_nombre,
            op.id AS operario_id,
            op.nombre AS operario_nombre
        FROM movimientos m
        JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN almacenes origen ON m.origen_id = origen.id
        LEFT JOIN almacenes destino ON m.destino_id = destino.id
        LEFT JOIN operarios op ON m.operario_id = op.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC, m.id DESC
        LIMIT ?
    """
    params.append(limit)

    return fetch_all(sql, params)


def get_by_id(movimiento_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un movimiento por su ID.

    Args:
        movimiento_id: ID del movimiento

    Returns:
        Diccionario con la información del movimiento o None si no existe
    """
    sql = """
        SELECT
            m.id,
            m.fecha,
            m.tipo,
            m.cantidad,
            m.coste_unit,
            m.motivo,
            m.ot,
            m.albaran,
            m.responsable,
            a.id AS articulo_id,
            a.nombre AS articulo_nombre,
            origen.id AS origen_id,
            origen.nombre AS origen_nombre,
            destino.id AS destino_id,
            destino.nombre AS destino_nombre,
            op.id AS operario_id,
            op.nombre AS operario_nombre
        FROM movimientos m
        JOIN articulos a ON m.articulo_id = a.id
        LEFT JOIN almacenes origen ON m.origen_id = origen.id
        LEFT JOIN almacenes destino ON m.destino_id = destino.id
        LEFT JOIN operarios op ON m.operario_id = op.id
        WHERE m.id = ?
    """
    return fetch_one(sql, (movimiento_id,))


def get_movimientos_articulo(
    articulo_id: int,
    fecha_desde: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de movimientos de un artículo específico.

    Args:
        articulo_id: ID del artículo
        fecha_desde: Fecha inicio opcional
        limit: Límite de resultados

    Returns:
        Lista de movimientos del artículo
    """
    condiciones = ["m.articulo_id = ?"]
    params = [articulo_id]

    if fecha_desde:
        condiciones.append("m.fecha >= ?")
        params.append(fecha_desde)

    where_clause = " AND ".join(condiciones)

    sql = f"""
        SELECT
            m.id,
            m.fecha,
            m.tipo,
            m.cantidad,
            m.coste_unit,
            m.motivo,
            origen.nombre AS origen_nombre,
            destino.nombre AS destino_nombre,
            op.nombre AS operario_nombre
        FROM movimientos m
        LEFT JOIN almacenes origen ON m.origen_id = origen.id
        LEFT JOIN almacenes destino ON m.destino_id = destino.id
        LEFT JOIN operarios op ON m.operario_id = op.id
        WHERE {where_clause}
        ORDER BY m.fecha DESC, m.id DESC
        LIMIT ?
    """
    params.append(limit)

    return fetch_all(sql, params)


def get_stock_por_almacen(articulo_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock de un artículo desglosado por almacén.

    Args:
        articulo_id: ID del artículo

    Returns:
        Lista con almacen_id, almacen_nombre y stock
    """
    sql = """
        SELECT
            v.almacen_id,
            a.nombre AS almacen_nombre,
            COALESCE(SUM(v.delta), 0) AS stock
        FROM vw_stock v
        JOIN almacenes a ON v.almacen_id = a.id
        WHERE v.articulo_id = ?
        GROUP BY v.almacen_id, a.nombre
        HAVING stock > 0
        ORDER BY a.nombre
    """
    return fetch_all(sql, (articulo_id,))


# ========================================
# OPERACIONES DE ESCRITURA
# ========================================

def crear_entrada(
    fecha: str,
    articulo_id: int,
    destino_id: int,
    cantidad: float,
    coste_unit: Optional[float] = None,
    albaran: Optional[str] = None,
    responsable: Optional[str] = None
) -> int:
    """
    Crea un movimiento de ENTRADA (recepción de material).

    Args:
        fecha: Fecha del movimiento (YYYY-MM-DD)
        articulo_id: ID del artículo
        destino_id: ID del almacén destino
        cantidad: Cantidad (siempre positiva)
        coste_unit: Coste unitario opcional
        albaran: Número de albarán opcional
        responsable: Responsable del movimiento

    Returns:
        ID del movimiento creado
    """
    sql = """
        INSERT INTO movimientos(fecha, tipo, destino_id, articulo_id, cantidad, coste_unit, albaran, responsable)
        VALUES(?, 'ENTRADA', ?, ?, ?, ?, ?, ?)
    """
    return execute_query(sql, (fecha, destino_id, articulo_id, cantidad, coste_unit, albaran, responsable))


def crear_traspaso(
    fecha: str,
    articulo_id: int,
    origen_id: int,
    destino_id: int,
    cantidad: float,
    operario_id: Optional[int] = None,
    responsable: Optional[str] = None,
    motivo: Optional[str] = None
) -> int:
    """
    Crea un movimiento de TRASPASO entre almacenes.

    Args:
        fecha: Fecha del movimiento
        articulo_id: ID del artículo
        origen_id: ID del almacén origen
        destino_id: ID del almacén destino
        cantidad: Cantidad a traspasar
        operario_id: ID del operario que realiza el traspaso
        responsable: Nombre del responsable
        motivo: Motivo del traspaso

    Returns:
        ID del movimiento creado
    """
    sql = """
        INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, operario_id, responsable, motivo)
        VALUES(?, 'TRASPASO', ?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(sql, (fecha, origen_id, destino_id, articulo_id, cantidad, operario_id, responsable, motivo))


def crear_imputacion(
    fecha: str,
    articulo_id: int,
    origen_id: int,
    cantidad: float,
    operario_id: Optional[int] = None,
    ot: Optional[str] = None,
    motivo: Optional[str] = None
) -> int:
    """
    Crea un movimiento de IMPUTACION (consumo en obra).

    Args:
        fecha: Fecha del movimiento
        articulo_id: ID del artículo
        origen_id: ID del almacén origen (usualmente furgoneta)
        cantidad: Cantidad consumida
        operario_id: ID del operario
        ot: Número de orden de trabajo
        motivo: Motivo/descripción

    Returns:
        ID del movimiento creado
    """
    sql = """
        INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, operario_id, ot, motivo)
        VALUES(?, 'IMPUTACION', ?, ?, ?, ?, ?, ?)
    """
    return execute_query(sql, (fecha, origen_id, articulo_id, cantidad, operario_id, ot, motivo))


def crear_perdida(
    fecha: str,
    articulo_id: int,
    origen_id: int,
    cantidad: float,
    motivo: str,
    responsable: Optional[str] = None
) -> int:
    """
    Crea un movimiento de PERDIDA (material perdido/dañado).

    Args:
        fecha: Fecha del movimiento
        articulo_id: ID del artículo
        origen_id: ID del almacén origen
        cantidad: Cantidad perdida
        motivo: Motivo de la pérdida (obligatorio)
        responsable: Responsable

    Returns:
        ID del movimiento creado
    """
    sql = """
        INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, motivo, responsable)
        VALUES(?, 'PERDIDA', ?, ?, ?, ?, ?)
    """
    return execute_query(sql, (fecha, origen_id, articulo_id, cantidad, motivo, responsable))


def crear_devolucion(
    fecha: str,
    articulo_id: int,
    origen_id: int,
    cantidad: float,
    motivo: Optional[str] = None,
    responsable: Optional[str] = None
) -> int:
    """
    Crea un movimiento de DEVOLUCION (devolución a proveedor).

    Args:
        fecha: Fecha del movimiento
        articulo_id: ID del artículo
        origen_id: ID del almacén origen
        cantidad: Cantidad devuelta
        motivo: Motivo de la devolución
        responsable: Responsable

    Returns:
        ID del movimiento creado
    """
    sql = """
        INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, motivo, responsable)
        VALUES(?, 'DEVOLUCION', ?, ?, ?, ?, ?)
    """
    return execute_query(sql, (fecha, origen_id, articulo_id, cantidad, motivo, responsable))


def crear_movimientos_batch(movimientos: List[Dict[str, Any]]) -> List[int]:
    """
    Crea múltiples movimientos en una sola transacción.

    Args:
        movimientos: Lista de diccionarios con datos de movimientos
                    Cada uno debe tener: tipo, fecha, articulo_id, cantidad, y otros campos según tipo

    Returns:
        Lista de IDs de los movimientos creados
    """
    con = get_con()
    cur = con.cursor()
    ids_creados = []

    try:
        for mov in movimientos:
            tipo = mov['tipo']

            if tipo == 'ENTRADA':
                sql = """
                    INSERT INTO movimientos(fecha, tipo, destino_id, articulo_id, cantidad, coste_unit, albaran, responsable)
                    VALUES(?, 'ENTRADA', ?, ?, ?, ?, ?, ?)
                """
                cur.execute(sql, (
                    mov['fecha'],
                    mov['destino_id'],
                    mov['articulo_id'],
                    mov['cantidad'],
                    mov.get('coste_unit'),
                    mov.get('albaran'),
                    mov.get('responsable')
                ))

            elif tipo == 'TRASPASO':
                sql = """
                    INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, operario_id, responsable, motivo)
                    VALUES(?, 'TRASPASO', ?, ?, ?, ?, ?, ?, ?)
                """
                cur.execute(sql, (
                    mov['fecha'],
                    mov['origen_id'],
                    mov['destino_id'],
                    mov['articulo_id'],
                    mov['cantidad'],
                    mov.get('operario_id'),
                    mov.get('responsable'),
                    mov.get('motivo')
                ))

            elif tipo == 'IMPUTACION':
                sql = """
                    INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, operario_id, ot, motivo)
                    VALUES(?, 'IMPUTACION', ?, ?, ?, ?, ?, ?)
                """
                cur.execute(sql, (
                    mov['fecha'],
                    mov['origen_id'],
                    mov['articulo_id'],
                    mov['cantidad'],
                    mov.get('operario_id'),
                    mov.get('ot'),
                    mov.get('motivo')
                ))

            elif tipo == 'PERDIDA':
                sql = """
                    INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, motivo, responsable)
                    VALUES(?, 'PERDIDA', ?, ?, ?, ?, ?)
                """
                cur.execute(sql, (
                    mov['fecha'],
                    mov['origen_id'],
                    mov['articulo_id'],
                    mov['cantidad'],
                    mov['motivo'],
                    mov.get('responsable')
                ))

            elif tipo == 'DEVOLUCION':
                sql = """
                    INSERT INTO movimientos(fecha, tipo, origen_id, articulo_id, cantidad, motivo, responsable)
                    VALUES(?, 'DEVOLUCION', ?, ?, ?, ?, ?)
                """
                cur.execute(sql, (
                    mov['fecha'],
                    mov['origen_id'],
                    mov['articulo_id'],
                    mov['cantidad'],
                    mov.get('motivo'),
                    mov.get('responsable')
                ))

            ids_creados.append(cur.lastrowid)

        con.commit()
        return ids_creados

    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()


# ========================================
# OPERACIONES AUXILIARES
# ========================================

def get_almacen_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un almacén por su nombre.

    Args:
        nombre: Nombre del almacén

    Returns:
        Diccionario con id y nombre o None
    """
    sql = "SELECT id, nombre, tipo FROM almacenes WHERE nombre = ?"
    return fetch_one(sql, (nombre,))


def get_furgoneta_asignada(operario_id: int, fecha: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la furgoneta asignada a un operario en una fecha específica.
    NUEVO: Usa la tabla asignaciones_furgoneta con soporte de turnos.

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)

    Returns:
        Diccionario con furgoneta_id y nombre o None
    """
    # NUEVO: Buscar en la tabla asignaciones_furgoneta
    # Prioridad: turno completo > turno específico (mañana/tarde)
    sql = """
        SELECT af.furgoneta_id,
               a.nombre AS furgoneta_nombre,
               af.turno
        FROM asignaciones_furgoneta af
        JOIN almacenes a ON af.furgoneta_id = a.id
        WHERE af.operario_id = ?
          AND af.fecha = ?
        ORDER BY
            CASE af.turno
                WHEN 'completo' THEN 1
                WHEN 'manana' THEN 2
                WHEN 'tarde' THEN 3
            END
        LIMIT 1
    """
    return fetch_one(sql, (operario_id, fecha))


def get_operarios_activos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de operarios activos.

    Returns:
        Lista de operarios con id, nombre y rol
    """
    sql = """
        SELECT id, nombre, rol_operario
        FROM operarios
        WHERE activo = 1
        ORDER BY rol_operario DESC, nombre
    """
    return fetch_all(sql)
