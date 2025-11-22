"""
Servicio de Notificaciones - Gestión de notificaciones del sistema PostgreSQL
"""
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from src.core.db_utils import fetch_all, fetch_one, execute_query
from src.core.logger import logger


# ========================================
# TIPOS DE NOTIFICACIONES
# ========================================
TIPOS_NOTIFICACIONES = {
    'stock_critico': {
        'nombre': '🔴 Stock Crítico',
        'descripcion': 'Artículos con stock agotado (≤ 0)',
        'destino': 'maestros_articulos'
    },
    'stock_bajo': {
        'nombre': '🟡 Stock Bajo',
        'descripcion': 'Artículos por debajo del nivel de alerta',
        'destino': 'maestros_articulos'
    },
    'inventario_pendiente': {
        'nombre': '📦 Inventario Pendiente',
        'descripcion': 'Inventarios sin finalizar hace más de 7 días',
        'destino': 'inventarios'
    }
}


# ========================================
# GENERACIÓN DE NOTIFICACIONES
# ========================================

def generar_notificaciones_usuario(usuario: str) -> int:
    """
    Genera todas las notificaciones pendientes para un usuario según su configuración.

    Args:
        usuario: Nombre del usuario

    Returns:
        Número de notificaciones nuevas generadas
    """
    try:
        # Obtener configuración del usuario
        config = obtener_configuracion_usuario(usuario)

        # Limpiar notificaciones antiguas (más de 30 días)
        _limpiar_notificaciones_antiguas(usuario)

        total_nuevas = 0

        # Generar cada tipo de notificación si está activa
        if config.get('stock_critico', True):
            total_nuevas += _generar_notificaciones_stock_critico(usuario)

        if config.get('stock_bajo', True):
            total_nuevas += _generar_notificaciones_stock_bajo(usuario)

        if config.get('inventario_pendiente', True):
            total_nuevas += _generar_notificaciones_inventario_pendiente(usuario)

        logger.info(f"Generadas {total_nuevas} notificaciones para {usuario}")
        return total_nuevas

    except Exception as e:
        logger.exception(f"Error al generar notificaciones para {usuario}: {e}")
        return 0


def _generar_notificaciones_stock_critico(usuario: str) -> int:
    """Genera notificaciones de stock crítico (stock <= 0)"""
    try:
        # Obtener artículos con stock crítico
        articulos = fetch_all("""
            SELECT a.id, a.nombre, a.u_medida, COALESCE(s.stock_total, 0) as stock
            FROM articulos a
            LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
            WHERE a.activo = 1
            AND COALESCE(s.stock_total, 0) <= 0
        """)

        contador = 0
        for art in articulos:
            # Verificar si ya existe una notificación reciente (últimas 24 horas)
            existe = fetch_one("""
                SELECT id FROM notificaciones
                WHERE usuario = %s
                AND tipo = 'stock_critico'
                AND datos_adicionales::jsonb @> %s::jsonb
                AND fecha_creacion > NOW() - INTERVAL '24 hours'
            """, (usuario, json.dumps({'articulo_id': art["id"]})))

            if not existe:
                mensaje = f"❌ {art['nombre']} - Stock agotado: {art['stock']:.2f} {art['u_medida']}"
                datos = json.dumps({'articulo_id': art['id'], 'articulo_nombre': art['nombre']})

                execute_query("""
                    INSERT INTO notificaciones (usuario, tipo, mensaje, datos_adicionales)
                    VALUES (%s, 'stock_critico', %s, %s)
                """, (usuario, mensaje, datos))
                contador += 1

        return contador

    except Exception as e:
        logger.exception(f"Error en notificaciones stock crítico: {e}")
        return 0


def _generar_notificaciones_stock_bajo(usuario: str) -> int:
    """Genera notificaciones de stock bajo (stock <= min_alerta)"""
    try:
        # Obtener artículos con stock bajo
        articulos = fetch_all("""
            SELECT a.id, a.nombre, a.u_medida,
                   COALESCE(s.stock_total, 0) as stock,
                   a.min_alerta
            FROM articulos a
            LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
            WHERE a.activo = 1
            AND a.min_alerta > 0
            AND COALESCE(s.stock_total, 0) > 0
            AND COALESCE(s.stock_total, 0) <= a.min_alerta
        """)

        contador = 0
        for art in articulos:
            # Verificar si ya existe una notificación reciente (últimas 24 horas)
            existe = fetch_one("""
                SELECT id FROM notificaciones
                WHERE usuario = %s
                AND tipo = 'stock_bajo'
                AND datos_adicionales::jsonb @> %s::jsonb
                AND fecha_creacion > NOW() - INTERVAL '24 hours'
            """, (usuario, json.dumps({'articulo_id': art["id"]})))

            if not existe:
                mensaje = f"⚠️ {art['nombre']} - Stock bajo: {art['stock']:.2f}/{art['min_alerta']:.2f} {art['u_medida']}"
                datos = json.dumps({'articulo_id': art['id'], 'articulo_nombre': art['nombre']})

                execute_query("""
                    INSERT INTO notificaciones (usuario, tipo, mensaje, datos_adicionales)
                    VALUES (%s, 'stock_bajo', %s, %s)
                """, (usuario, mensaje, datos))
                contador += 1

        return contador

    except Exception as e:
        logger.exception(f"Error en notificaciones stock bajo: {e}")
        return 0


def _generar_notificaciones_inventario_pendiente(usuario: str) -> int:
    """Genera notificaciones de inventarios sin finalizar hace más de 7 días"""
    try:
        inventarios = fetch_all("""
            SELECT id, fecha, responsable,
                   (CURRENT_DATE - fecha::timestamp::date) as dias_pendiente
            FROM inventarios
            WHERE estado = 'EN_PROCESO'
            AND fecha::timestamp <= CURRENT_TIMESTAMP - INTERVAL '7 days'
        """)

        contador = 0
        for inv in inventarios:
            # Verificar si ya existe una notificación reciente (últimas 24 horas)
            existe = fetch_one("""
                SELECT id FROM notificaciones
                WHERE usuario = %s
                AND tipo = 'inventario_pendiente'
                AND datos_adicionales::jsonb @> %s::jsonb
                AND fecha_creacion > NOW() - INTERVAL '24 hours'
            """, (usuario, json.dumps({'inventario_id': inv['id']})))

            if not existe:
                dias = int(inv['dias_pendiente'])
                mensaje = f"📦 Inventario pendiente desde hace {dias} días - Responsable: {inv['responsable']}"
                datos = json.dumps({'inventario_id': inv['id'], 'fecha': str(inv['fecha'])})

                execute_query("""
                    INSERT INTO notificaciones (usuario, tipo, mensaje, datos_adicionales)
                    VALUES (%s, 'inventario_pendiente', %s, %s)
                """, (usuario, mensaje, datos))
                contador += 1

        return contador

    except Exception as e:
        logger.exception(f"Error en notificaciones inventario pendiente: {e}")
        return 0


def _limpiar_notificaciones_antiguas(usuario: str):
    """Elimina notificaciones de más de 30 días"""
    try:
        execute_query("""
            DELETE FROM notificaciones
            WHERE usuario = %s
            AND fecha_creacion < NOW() - INTERVAL '30 days'
        """, (usuario,))
    except Exception as e:
        logger.exception(f"Error al limpiar notificaciones antiguas: {e}")


# ========================================
# CONSULTAS DE NOTIFICACIONES
# ========================================

def obtener_notificaciones(usuario: str) -> List[Dict[str, Any]]:
    """
    Obtiene todas las notificaciones de un usuario ordenadas por fecha.

    Args:
        usuario: Nombre del usuario

    Returns:
        Lista de notificaciones
    """
    try:
        return fetch_all("""
            SELECT id, tipo, mensaje, fecha_creacion, datos_adicionales
            FROM notificaciones
            WHERE usuario = %s
            ORDER BY fecha_creacion DESC
        """, (usuario,))
    except Exception as e:
        logger.exception(f"Error al obtener notificaciones: {e}")
        return []


def contar_notificaciones(usuario: str) -> int:
    """
    Cuenta las notificaciones pendientes de un usuario.

    Args:
        usuario: Nombre del usuario

    Returns:
        Número de notificaciones
    """
    try:
        resultado = fetch_one("""
            SELECT COUNT(*) as total
            FROM notificaciones
            WHERE usuario = %s
        """, (usuario,))
        return resultado['total'] if resultado else 0
    except Exception as e:
        logger.exception(f"Error al contar notificaciones: {e}")
        return 0


def eliminar_notificacion(notificacion_id: int) -> Tuple[bool, str]:
    """
    Elimina una notificación.

    Args:
        notificacion_id: ID de la notificación

    Returns:
        Tupla (éxito, mensaje)
    """
    try:
        execute_query("DELETE FROM notificaciones WHERE id = %s", (notificacion_id,))
        return True, "Notificación eliminada"
    except Exception as e:
        logger.exception(f"Error al eliminar notificación: {e}")
        return False, f"Error: {e}"


def eliminar_notificaciones_multiples(ids: List[int]) -> Tuple[bool, str]:
    """
    Elimina múltiples notificaciones.

    Args:
        ids: Lista de IDs de notificaciones

    Returns:
        Tupla (éxito, mensaje)
    """
    try:
        if not ids:
            return False, "No hay notificaciones seleccionadas"

        placeholders = ','.join(['%s'] * len(ids))
        query = f"DELETE FROM notificaciones WHERE id IN ({placeholders})"
        execute_query(query, ids)
        return True, f"{len(ids)} notificaciones eliminadas"
    except Exception as e:
        logger.exception(f"Error al eliminar notificaciones: {e}")
        return False, f"Error: {e}"


# ========================================
# CONFIGURACIÓN DE NOTIFICACIONES
# ========================================

def obtener_configuracion_usuario(usuario: str) -> Dict[str, bool]:
    """
    Obtiene la configuración de notificaciones de un usuario.

    Args:
        usuario: Nombre del usuario

    Returns:
        Dict con tipo_notificacion: activa (bool)
    """
    try:
        configs = fetch_all("""
            SELECT tipo_notificacion, activa
            FROM config_notificaciones
            WHERE usuario = %s
        """, (usuario,))

        # Si no tiene configuración, crear por defecto
        if not configs:
            _crear_configuracion_defecto(usuario)
            return {tipo: True for tipo in TIPOS_NOTIFICACIONES.keys()}

        return {c['tipo_notificacion']: bool(c['activa']) for c in configs}

    except Exception as e:
        logger.exception(f"Error al obtener configuración: {e}")
        return {tipo: True for tipo in TIPOS_NOTIFICACIONES.keys()}


def _crear_configuracion_defecto(usuario: str):
    """Crea configuración por defecto para un usuario"""
    try:
        for tipo in TIPOS_NOTIFICACIONES.keys():
            execute_query("""
                INSERT INTO config_notificaciones (usuario, tipo_notificacion, activa)
                VALUES (%s, %s, %s)
                ON CONFLICT (usuario, tipo_notificacion) DO NOTHING
            """, (usuario, tipo, 1))
    except Exception as e:
        logger.exception(f"Error al crear configuración por defecto: {e}")


def actualizar_configuracion(usuario: str, tipo_notificacion: str, activa: bool) -> Tuple[bool, str]:
    """
    Actualiza la configuración de un tipo de notificación para un usuario.

    Args:
        usuario: Nombre del usuario
        tipo_notificacion: Tipo de notificación
        activa: True para activar, False para desactivar

    Returns:
        Tupla (éxito, mensaje)
    """
    try:
        execute_query("""
            INSERT INTO config_notificaciones (usuario, tipo_notificacion, activa)
            VALUES (%s, %s, %s)
            ON CONFLICT (usuario, tipo_notificacion)
            DO UPDATE SET activa = EXCLUDED.activa
        """, (usuario, tipo_notificacion, 1 if activa else 0))

        return True, "Configuración actualizada"
    except Exception as e:
        logger.exception(f"Error al actualizar configuración: {e}")
        return False, f"Error: {e}"


def obtener_todos_tipos() -> Dict[str, Dict[str, str]]:
    """Retorna todos los tipos de notificaciones disponibles"""
    return TIPOS_NOTIFICACIONES
