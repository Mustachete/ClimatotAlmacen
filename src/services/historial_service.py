# historial_service.py - Servicio para gestionar historial de operaciones
"""
Servicio para guardar y recuperar el historial de operaciones de usuarios.
Permite repetir operaciones frecuentes con un solo click.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.core.db_utils import get_con, execute_query, fetch_all
from src.core.logger import logger


def guardar_en_historial(
    usuario: str,
    tipo_operacion: str,
    articulo_id: int,
    articulo_nombre: str,
    cantidad: float,
    u_medida: str = "unidad",
    datos_adicionales: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Guarda una operación en el historial.

    Args:
        usuario: Nombre de usuario
        tipo_operacion: Tipo de operación ('movimiento', 'imputacion', 'material_perdido', 'devolucion')
        articulo_id: ID del artículo
        articulo_nombre: Nombre del artículo
        cantidad: Cantidad usada
        u_medida: Unidad de medida
        datos_adicionales: Dict con info extra (ej: {'ot': '12345', 'modo': 'entregar'})

    Returns:
        True si se guardó correctamente, False en caso contrario
    """
    try:
        fecha_hora = datetime.now().isoformat()
        datos_json = json.dumps(datos_adicionales) if datos_adicionales else None

        execute_query(
            """
            INSERT INTO historial_operaciones
            (usuario_id, tipo_operacion, articulo_id, articulo_nombre, cantidad, u_medida, fecha_hora, datos_adicionales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (usuario, tipo_operacion, articulo_id, articulo_nombre, cantidad, u_medida, fecha_hora, datos_json)
        )

        return True

    except Exception as e:
        logger.exception(f"Error al guardar en historial: {e}")
        return False


def obtener_historial_reciente(
    usuario: str,
    tipo_operacion: Optional[str] = None,
    limite: int = 20
) -> List[Dict[str, Any]]:
    """
    Obtiene el historial reciente de operaciones de un usuario.

    Args:
        usuario: Nombre de usuario
        tipo_operacion: Filtrar por tipo (opcional)
        limite: Número máximo de resultados

    Returns:
        Lista de diccionarios con el historial
    """
    try:
        query = """
            SELECT
                id,
                tipo_operacion,
                articulo_id,
                articulo_nombre,
                cantidad,
                u_medida,
                fecha_hora,
                datos_adicionales
            FROM historial_operaciones
            WHERE usuario_id = ?
        """
        params = [usuario]

        if tipo_operacion:
            query += " AND tipo_operacion = ?"
            params.append(tipo_operacion)

        query += " ORDER BY fecha_hora DESC LIMIT ?"
        params.append(limite)

        rows = fetch_all(query, tuple(params))

        historial = []
        for row in rows:
            item = {
                'id': row[0],
                'tipo_operacion': row[1],
                'articulo_id': row[2],
                'articulo_nombre': row[3],
                'cantidad': row[4],
                'u_medida': row[5],
                'fecha_hora': row[6],
                'datos_adicionales': json.loads(row[7]) if row[7] else {}
            }
            historial.append(item)

        return historial

    except Exception as e:
        logger.exception(f"Error al obtener historial: {e}")
        return []


def obtener_articulos_frecuentes(
    usuario: str,
    tipo_operacion: Optional[str] = None,
    limite: int = 10,
    dias: int = 30
) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos más frecuentemente usados por un usuario.

    Args:
        usuario: Nombre de usuario
        tipo_operacion: Filtrar por tipo (opcional)
        limite: Número máximo de resultados
        dias: Considerar últimos X días

    Returns:
        Lista de artículos ordenados por frecuencia de uso
    """
    try:
        query = """
            SELECT
                articulo_id,
                articulo_nombre,
                u_medida,
                COUNT(*) as veces_usado,
                SUM(cantidad) as cantidad_total,
                MAX(fecha_hora) as ultima_vez
            FROM historial_operaciones
            WHERE usuario_id = ?
                AND fecha_hora >= datetime('now', '-' || ? || ' days')
        """
        params = [usuario, dias]

        if tipo_operacion:
            query += " AND tipo_operacion = ?"
            params.append(tipo_operacion)

        query += """
            GROUP BY articulo_id, articulo_nombre, u_medida
            ORDER BY veces_usado DESC, ultima_vez DESC
            LIMIT ?
        """
        params.append(limite)

        rows = fetch_all(query, tuple(params))

        frecuentes = []
        for row in rows:
            item = {
                'articulo_id': row[0],
                'articulo_nombre': row[1],
                'u_medida': row[2],
                'veces_usado': row[3],
                'cantidad_total': row[4],
                'ultima_vez': row[5]
            }
            frecuentes.append(item)

        return frecuentes

    except Exception as e:
        logger.exception(f"Error al obtener artículos frecuentes: {e}")
        return []


def limpiar_historial_antiguo(dias: int = 90) -> int:
    """
    Elimina registros del historial más antiguos que X días.

    Args:
        dias: Eliminar registros más antiguos que este número de días

    Returns:
        Número de registros eliminados
    """
    try:
        con = get_con()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM historial_operaciones
            WHERE fecha_hora < datetime('now', '-' || ? || ' days')
        """, (dias,))

        eliminados = cur.rowcount
        con.commit()
        con.close()

        logger.info(f"Limpieza de historial: {eliminados} registros eliminados (>{dias} días)")
        return eliminados

    except Exception as e:
        logger.exception(f"Error al limpiar historial: {e}")
        return 0
