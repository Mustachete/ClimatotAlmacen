"""
Servicio de Consumos - Lógica de negocio para análisis de consumos
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from src.repos import consumos_repo


# ========================================
# SERVICIOS POR OT
# ========================================

def obtener_consumos_ot(ot: str) -> Dict[str, Any]:
    """
    Obtiene el detalle completo de consumos de una OT.
    
    Returns:
        Dict con 'detalle' (lista) y 'resumen' (dict)
    """
    detalle = consumos_repo.get_consumos_por_ot(ot)
    resumen = consumos_repo.get_resumen_ot(ot)
    
    return {
        'detalle': detalle,
        'resumen': resumen if resumen else {
            'total_articulos': 0,
            'total_imputaciones': 0,
            'coste_total': 0.0
        }
    }


def obtener_ots_recientes(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtiene las OTs más recientes.
    """
    return consumos_repo.get_ots_recientes(limit)


# ========================================
# SERVICIOS POR OPERARIO
# ========================================

def obtener_consumos_operario(operario_id: int, fecha_desde: date = None, fecha_hasta: date = None) -> Dict[str, Any]:
    """
    Obtiene análisis completo de consumos de un operario.
    
    Returns:
        Dict con 'detalle', 'resumen', 'top_articulos'
    """
    # Convertir fechas a string ISO
    desde_str = fecha_desde.isoformat() if fecha_desde else None
    hasta_str = fecha_hasta.isoformat() if fecha_hasta else None
    
    detalle = consumos_repo.get_consumos_por_operario(operario_id, desde_str, hasta_str)
    resumen = consumos_repo.get_resumen_operario(operario_id, desde_str, hasta_str)
    top_articulos = consumos_repo.get_top_articulos_operario(operario_id, desde_str, hasta_str, 10)
    
    return {
        'detalle': detalle,
        'resumen': resumen if resumen else {
            'operario_nombre': 'Desconocido',
            'total_imputaciones': 0,
            'total_ots': 0,
            'coste_total': 0.0
        },
        'top_articulos': top_articulos
    }


def obtener_operarios_con_consumos() -> List[Dict[str, Any]]:
    """
    Obtiene lista de operarios que han hecho imputaciones.
    """
    return consumos_repo.get_lista_operarios_con_consumos()


# ========================================
# SERVICIOS POR FURGONETA
# ========================================

def obtener_consumos_furgoneta(furgoneta_id: int, fecha_desde: date = None, fecha_hasta: date = None) -> Dict[str, Any]:
    """
    Obtiene análisis de consumos de una furgoneta.
    
    Returns:
        Dict con 'detalle' y 'resumen'
    """
    desde_str = fecha_desde.isoformat() if fecha_desde else None
    hasta_str = fecha_hasta.isoformat() if fecha_hasta else None
    
    detalle = consumos_repo.get_consumos_por_furgoneta(furgoneta_id, desde_str, hasta_str)
    resumen = consumos_repo.get_resumen_furgoneta(furgoneta_id, desde_str, hasta_str)
    
    return {
        'detalle': detalle,
        'resumen': resumen if resumen else {
            'furgoneta_nombre': 'Desconocida',
            'total_imputaciones': 0,
            'coste_total': 0.0
        }
    }


def obtener_lista_furgonetas() -> List[Dict[str, Any]]:
    """
    Obtiene lista de furgonetas disponibles.
    """
    return consumos_repo.get_lista_furgonetas()


# ========================================
# SERVICIOS POR PERÍODO
# ========================================

def obtener_analisis_periodo(fecha_desde: date, fecha_hasta: date) -> Dict[str, Any]:
    """
    Obtiene análisis completo de un período.
    
    Returns:
        Dict con 'resumen', 'articulos_top', 'operarios_top'
    """
    desde_str = fecha_desde.isoformat()
    hasta_str = fecha_hasta.isoformat()
    
    resumen = consumos_repo.get_resumen_periodo(desde_str, hasta_str)
    articulos = consumos_repo.get_articulos_mas_consumidos_periodo(desde_str, hasta_str, 10)
    operarios = consumos_repo.get_operarios_mas_activos_periodo(desde_str, hasta_str, 10)
    
    return {
        'resumen': resumen if resumen else {},
        'articulos_top': articulos,
        'operarios_top': operarios
    }


def obtener_periodo_mes_actual() -> tuple[date, date]:
    """
    Retorna el rango de fechas del mes actual.
    
    Returns:
        (fecha_inicio, fecha_fin)
    """
    hoy = date.today()
    inicio = date(hoy.year, hoy.month, 1)
    
    # Último día del mes
    if hoy.month == 12:
        fin = date(hoy.year, 12, 31)
    else:
        fin = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
    
    return inicio, fin


def obtener_periodo_mes_anterior() -> tuple[date, date]:
    """
    Retorna el rango de fechas del mes anterior.
    """
    hoy = date.today()
    
    if hoy.month == 1:
        inicio = date(hoy.year - 1, 12, 1)
        fin = date(hoy.year - 1, 12, 31)
    else:
        inicio = date(hoy.year, hoy.month - 1, 1)
        fin = date(hoy.year, hoy.month, 1) - timedelta(days=1)
    
    return inicio, fin


# ========================================
# SERVICIOS POR ARTÍCULO
# ========================================

def obtener_consumos_articulo(articulo_id: int, fecha_desde: date = None, fecha_hasta: date = None) -> Dict[str, Any]:
    """
    Obtiene análisis de consumos de un artículo específico.
    
    Returns:
        Dict con 'detalle' y 'resumen'
    """
    desde_str = fecha_desde.isoformat() if fecha_desde else None
    hasta_str = fecha_hasta.isoformat() if fecha_hasta else None
    
    detalle = consumos_repo.get_consumos_por_articulo(articulo_id, desde_str, hasta_str)
    resumen = consumos_repo.get_resumen_articulo(articulo_id, desde_str, hasta_str)
    
    return {
        'detalle': detalle,
        'resumen': resumen if resumen else {
            'articulo_nombre': 'Desconocido',
            'cantidad_total': 0,
            'veces_usado': 0,
            'coste_total': 0.0
        }
    }


def buscar_articulos(texto: str) -> List[Dict[str, Any]]:
    """
    Busca artículos por texto.
    """
    if not texto or len(texto.strip()) < 2:
        return []
    
    return consumos_repo.buscar_articulo_por_nombre(texto.strip())


# ========================================
# UTILIDADES DE FORMATO
# ========================================

def formatear_coste(valor: float) -> str:
    """
    Formatea un valor monetario.
    
    Args:
        valor: Valor numérico
        
    Returns:
        String formateado como "1.234,56 €"
    """
    if valor is None:
        return "0,00 €"
    
    # Formatear con separadores de miles y 2 decimales
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def formatear_cantidad(valor: float, unidad: str = "unidad") -> str:
    """
    Formatea una cantidad con su unidad.
    
    Args:
        valor: Valor numérico
        unidad: Unidad de medida
        
    Returns:
        String formateado como "24 uds" o "15,5 m"
    """
    if valor is None:
        return "0"
    
    # Si es unidad, sin decimales
    if unidad.lower() in ['unidad', 'uds', 'ud', 'u']:
        return f"{int(valor)} uds"
    
    # Para otras unidades, con decimales si los tiene
    if valor == int(valor):
        return f"{int(valor)} {unidad}"
    else:
        return f"{valor:.2f} {unidad}"
