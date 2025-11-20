# historial_service.py - Servicio para gestionar historial de operaciones
"""
Servicio para guardar y recuperar el historial de operaciones de usuarios.
Permite repetir operaciones frecuentes con un solo click.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.repos import historial_repo
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
    fecha_hora = datetime.now().isoformat()
    datos_json = json.dumps(datos_adicionales) if datos_adicionales else None

    return historial_repo.insertar_historial(
        usuario_id=usuario,
        tipo_operacion=tipo_operacion,
        articulo_id=articulo_id,
        articulo_nombre=articulo_nombre,
        cantidad=cantidad,
        u_medida=u_medida,
        fecha_hora=fecha_hora,
        datos_adicionales=datos_json
    )


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
    registros = historial_repo.get_historial_reciente(
        usuario_id=usuario,
        tipo_operacion=tipo_operacion,
        limite=limite
    )

    # Parsear JSON de datos_adicionales
    for registro in registros:
        datos_json = registro.get('datos_adicionales')
        registro['datos_adicionales'] = json.loads(datos_json) if datos_json else {}

    return registros


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
    return historial_repo.get_articulos_frecuentes(
        usuario_id=usuario,
        tipo_operacion=tipo_operacion,
        limite=limite,
        dias=dias
    )


def limpiar_historial_antiguo(dias: int = 90) -> int:
    """
    Elimina registros del historial más antiguos que X días.

    Args:
        dias: Eliminar registros más antiguos que este número de días

    Returns:
        Número de registros eliminados
    """
    eliminados = historial_repo.eliminar_historial_antiguo(dias)
    logger.info(f"Limpieza de historial: {eliminados} registros eliminados (>{dias} días)")
    return eliminados
