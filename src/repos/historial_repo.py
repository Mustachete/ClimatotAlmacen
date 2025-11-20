"""
Repositorio de historial de operaciones
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import execute_query, fetch_all, get_con
from src.core.logger import logger


def insertar_historial(
    usuario_id: str,
    tipo_operacion: str,
    articulo_id: int,
    articulo_nombre: str,
    cantidad: float,
    u_medida: str,
    fecha_hora: str,
    datos_adicionales: Optional[str] = None
) -> bool:
    """
    Inserta un registro en el historial de operaciones.

    Args:
        usuario_id: ID del usuario
        tipo_operacion: Tipo de operación
        articulo_id: ID del artículo
        articulo_nombre: Nombre del artículo
        cantidad: Cantidad
        u_medida: Unidad de medida
        fecha_hora: Fecha y hora en formato ISO
        datos_adicionales: JSON string con datos adicionales (opcional)

    Returns:
        True si se insertó correctamente
    """
    try:
        execute_query(
            """
            INSERT INTO historial_operaciones
            (usuario_id, tipo_operacion, articulo_id, articulo_nombre, cantidad, u_medida, fecha_hora, datos_adicionales)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (usuario_id, tipo_operacion, articulo_id, articulo_nombre, cantidad, u_medida, fecha_hora, datos_adicionales)
        )
        return True
    except Exception as e:
        logger.exception(f"Error al insertar en historial: {e}")
        return False


def get_historial_reciente(
    usuario_id: str,
    tipo_operacion: Optional[str] = None,
    limite: int = 20
) -> List[Dict[str, Any]]:
    """
    Obtiene el historial reciente de operaciones de un usuario.

    Args:
        usuario_id: ID del usuario
        tipo_operacion: Filtrar por tipo (opcional)
        limite: Número máximo de resultados

    Returns:
        Lista de diccionarios con los registros del historial
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
            WHERE usuario_id = %s
        """
        params = [usuario_id]

        if tipo_operacion:
            query += " AND tipo_operacion = %s"
            params.append(tipo_operacion)

        query += " ORDER BY fecha_hora DESC LIMIT %s"
        params.append(limite)

        rows = fetch_all(query, tuple(params))

        return [
            {
                'id': row[0],
                'tipo_operacion': row[1],
                'articulo_id': row[2],
                'articulo_nombre': row[3],
                'cantidad': row[4],
                'u_medida': row[5],
                'fecha_hora': row[6],
                'datos_adicionales': row[7]  # JSON string
            }
            for row in rows
        ]

    except Exception as e:
        logger.exception(f"Error al obtener historial: {e}")
        return []


def get_articulos_frecuentes(
    usuario_id: str,
    tipo_operacion: Optional[str] = None,
    limite: int = 10,
    dias: int = 30
) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos más frecuentemente usados por un usuario.

    Args:
        usuario_id: ID del usuario
        tipo_operacion: Filtrar por tipo (opcional)
        limite: Número máximo de resultados
        dias: Considerar últimos X días

    Returns:
        Lista de artículos ordenados por frecuencia
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
            WHERE usuario_id = %s
                AND fecha_hora >= NOW() - INTERVAL '%s days'
        """
        params = [usuario_id, dias]

        if tipo_operacion:
            query += " AND tipo_operacion = %s"
            params.append(tipo_operacion)

        query += """
            GROUP BY articulo_id, articulo_nombre, u_medida
            ORDER BY veces_usado DESC, ultima_vez DESC
            LIMIT %s
        """
        params.append(limite)

        rows = fetch_all(query, tuple(params))

        return [
            {
                'articulo_id': row[0],
                'articulo_nombre': row[1],
                'u_medida': row[2],
                'veces_usado': row[3],
                'cantidad_total': row[4],
                'ultima_vez': row[5]
            }
            for row in rows
        ]

    except Exception as e:
        logger.exception(f"Error al obtener artículos frecuentes: {e}")
        return []


def eliminar_historial_antiguo(dias: int = 90) -> int:
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
            WHERE fecha_hora < NOW() - INTERVAL '%s days'
        """, (dias,))

        eliminados = cur.rowcount
        con.commit()
        con.close()

        return eliminados

    except Exception as e:
        logger.exception(f"Error al eliminar historial antiguo: {e}")
        return 0
