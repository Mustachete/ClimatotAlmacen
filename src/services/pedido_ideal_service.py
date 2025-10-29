"""
Servicio de Pedido Ideal - Lógica de negocio para cálculo de pedidos óptimos
"""
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import math
from src.repos import pedido_ideal_repo


# ========================================
# CONFIGURACIÓN POR DEFECTO
# ========================================

CONFIG_DEFAULT = {
    'dias_cobertura': 20,      # Días que queremos cubrir (1 mes laboral)
    'dias_seguridad': 5,       # Días de stock de seguridad por defecto
    'periodo_analisis': 90,    # Días hacia atrás para analizar consumo
    'min_dias_datos': 7,       # Mínimo de días con datos para calcular
}


# ========================================
# CÁLCULO DEL PEDIDO IDEAL
# ========================================

def calcular_pedido_articulo(
    articulo: Dict[str, Any],
    dias_cobertura: int = 20,
    dias_seguridad: int = None,
    periodo_analisis: int = 90
) -> Dict[str, Any]:
    """
    Calcula el pedido ideal para un artículo específico.
    
    Args:
        articulo: Diccionario con datos del artículo
        dias_cobertura: Días de stock que queremos tener
        dias_seguridad: Días de stock de seguridad (None = usar el del artículo)
        periodo_analisis: Días hacia atrás para analizar consumo
        
    Returns:
        Dict con pedido_sugerido, consumo_diario, prioridad, etc.
    """
    articulo_id = articulo['id']
    stock_actual = articulo.get('stock', 0)
    nivel_alerta = articulo.get('nivel_alerta', 0)
    unidad_compra = articulo.get('unidad_compra', 1) or 1
    
    # Usar días de seguridad del artículo si no se especifica
    if dias_seguridad is None:
        dias_seguridad = articulo.get('dias_seguridad', 5)
    
    # Obtener estadísticas de consumo
    stats = pedido_ideal_repo.get_estadisticas_consumo(articulo_id, periodo_analisis)
    
    # Si no hay datos de consumo
    if not stats or stats.get('dias_con_movimiento', 0) < CONFIG_DEFAULT['min_dias_datos']:
        return {
            'articulo_id': articulo_id,
            'articulo_nombre': articulo['nombre'],
            'stock_actual': stock_actual,
            'nivel_alerta': nivel_alerta,
            'pedido_sugerido': 0,
            'consumo_diario': 0,
            'dias_restantes': 999,
            'prioridad': 'SIN DATOS',
            'emoji': '⚪',
            'orden_prioridad': 999,  # ← AGREGADO
            'razon': 'Sin consumo reciente',
            'coste_estimado': 0,
            'unidad_compra': unidad_compra,
            'requiere_pedido': False
        }
    
    # Calcular consumo diario medio
    dias_con_movimiento = stats['dias_con_movimiento']
    total_consumido = stats['total_consumido'] or 0
    consumo_diario = total_consumido / dias_con_movimiento if dias_con_movimiento > 0 else 0
    
    # Si el consumo es muy bajo, no sugerir pedido
    if consumo_diario < 0.1:  # Menos de 0.1 unidades por día
        return {
            'articulo_id': articulo_id,
            'articulo_nombre': articulo['nombre'],
            'stock_actual': stock_actual,
            'nivel_alerta': nivel_alerta,
            'pedido_sugerido': 0,
            'consumo_diario': consumo_diario,
            'dias_restantes': stock_actual / consumo_diario if consumo_diario > 0 else 999,
            'prioridad': 'BAJO CONSUMO',
            'emoji': '⚪',
            'orden_prioridad': 998,  # ← AGREGADO
            'razon': 'Consumo muy bajo',
            'coste_estimado': 0,
            'unidad_compra': unidad_compra,
            'requiere_pedido': False
        }
    
    # Calcular necesidades
    consumo_proyectado = consumo_diario * dias_cobertura
    stock_seguridad = consumo_diario * dias_seguridad
    necesidad_total = consumo_proyectado + stock_seguridad
    
    # Calcular pedido bruto
    pedido_bruto = necesidad_total - stock_actual
    
    # Si ya tenemos suficiente stock, no pedir
    if pedido_bruto <= 0:
        dias_restantes = stock_actual / consumo_diario if consumo_diario > 0 else 999
        return {
            'articulo_id': articulo_id,
            'articulo_nombre': articulo['nombre'],
            'stock_actual': stock_actual,
            'nivel_alerta': nivel_alerta,
            'pedido_sugerido': 0,
            'consumo_diario': consumo_diario,
            'dias_restantes': dias_restantes,
            'prioridad': 'STOCK SUFICIENTE',
            'emoji': '✅',
            'orden_prioridad': 997,  # ← AGREGADO
            'razon': f'Stock actual cubre {dias_restantes:.1f} días',
            'coste_estimado': 0,
            'unidad_compra': unidad_compra,
            'requiere_pedido': False
        }
    
    # Redondear a unidad de compra
    if unidad_compra > 1:
        pedido_final = math.ceil(pedido_bruto / unidad_compra) * unidad_compra
    else:
        pedido_final = math.ceil(pedido_bruto)
    
    # Determinar prioridad
    es_critico = articulo.get('critico', 0) == 1
    
    if stock_actual < nivel_alerta:
        if es_critico:
            prioridad = "🚨 CRÍTICO URGENTE"
            emoji = "🔴"
            orden = 0
        else:
            prioridad = "CRÍTICO"
            emoji = "🔴"
            orden = 1
    elif stock_actual < (nivel_alerta * 1.5):
        prioridad = "PREVENTIVO"
        emoji = "🟡"
        orden = 2
    else:
        prioridad = "NORMAL"
        emoji = "🟢"
        orden = 3
    
    # Calcular días restantes
    dias_restantes = stock_actual / consumo_diario if consumo_diario > 0 else 999
    
    # Coste estimado
    coste_unit = articulo.get('coste', 0) or 0
    coste_estimado = pedido_final * coste_unit
    
    return {
        'articulo_id': articulo_id,
        'articulo_nombre': articulo['nombre'],
        'ean': articulo.get('ean', ''),
        'ref_proveedor': articulo.get('ref_proveedor', ''),
        'stock_actual': stock_actual,
        'nivel_alerta': nivel_alerta,
        'pedido_sugerido': pedido_final,
        'consumo_diario': consumo_diario,
        'dias_restantes': dias_restantes,
        'prioridad': prioridad,
        'emoji': emoji,
        'orden_prioridad': orden,
        'razon': f'Cobertura {dias_cobertura} días + seguridad {dias_seguridad} días',
        'coste_unitario': coste_unit,
        'coste_estimado': coste_estimado,
        'unidad_compra': unidad_compra,
        'u_medida': articulo.get('u_medida', ''),
        'proveedor_id': articulo.get('proveedor_id'),
        'proveedor_nombre': articulo.get('proveedor_nombre', 'SIN PROVEEDOR'),
        'requiere_pedido': True,
        'es_critico': es_critico
    }


def calcular_pedidos_multiples(
    articulos: List[Dict[str, Any]],
    dias_cobertura: int = 20,
    dias_seguridad: int = None,
    periodo_analisis: int = 90,
    filtros: Dict[str, bool] = None
) -> List[Dict[str, Any]]:
    """
    Calcula pedidos ideales para múltiples artículos.
    
    Args:
        articulos: Lista de diccionarios con datos de artículos
        dias_cobertura: Días de cobertura deseados
        dias_seguridad: Días de seguridad (None = usar el de cada artículo)
        periodo_analisis: Días hacia atrás para analizar
        filtros: Diccionario con filtros a aplicar
        
    Returns:
        Lista de pedidos calculados
    """
    filtros = filtros or {}
    resultados = []
    
    for articulo in articulos:
        pedido = calcular_pedido_articulo(
            articulo,
            dias_cobertura,
            dias_seguridad,
            periodo_analisis
        )
        
        # Aplicar filtros
        if filtros.get('solo_criticos') and pedido['prioridad'] not in ['CRÍTICO', '🚨 CRÍTICO URGENTE']:
            continue
        
        if filtros.get('solo_bajo_alerta') and pedido['stock_actual'] >= pedido['nivel_alerta']:
            continue
        
        if filtros.get('excluir_sin_consumo') and not pedido['requiere_pedido']:
            continue
        
        if filtros.get('solo_con_proveedor') and not pedido.get('proveedor_id'):
            continue
        
        resultados.append(pedido)
    
    # Ordenar por prioridad y luego por nombre
    resultados.sort(key=lambda x: (x['orden_prioridad'], x['articulo_nombre']))
    
    return resultados


# ========================================
# AGRUPACIÓN POR PROVEEDORES
# ========================================

def agrupar_por_proveedor(pedidos: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Agrupa los pedidos calculados por proveedor.
    
    Args:
        pedidos: Lista de pedidos calculados
        
    Returns:
        Dict donde la clave es proveedor_id y el valor es un dict con:
        - proveedor_nombre
        - proveedor_email
        - proveedor_telefono
        - articulos: lista de pedidos
        - total_articulos: cantidad de artículos
        - coste_total: suma de costes estimados
    """
    grupos = {}
    sin_proveedor = {
        'proveedor_id': None,
        'proveedor_nombre': '⚠️ SIN PROVEEDOR ASIGNADO',
        'proveedor_email': None,
        'proveedor_telefono': None,
        'articulos': [],
        'total_articulos': 0,
        'coste_total': 0
    }
    
    for pedido in pedidos:
        # Solo incluir pedidos que requieran reposición
        if not pedido.get('requiere_pedido') or pedido['pedido_sugerido'] <= 0:
            continue
        
        proveedor_id = pedido.get('proveedor_id')
        
        if not proveedor_id:
            sin_proveedor['articulos'].append(pedido)
            sin_proveedor['coste_total'] += pedido['coste_estimado']
            continue
        
        if proveedor_id not in grupos:
            grupos[proveedor_id] = {
                'proveedor_id': proveedor_id,
                'proveedor_nombre': pedido.get('proveedor_nombre', f'Proveedor {proveedor_id}'),
                'proveedor_email': None,  # Se llenará desde la BD si es necesario
                'proveedor_telefono': None,
                'articulos': [],
                'total_articulos': 0,
                'coste_total': 0
            }
        
        grupos[proveedor_id]['articulos'].append(pedido)
        grupos[proveedor_id]['coste_total'] += pedido['coste_estimado']
    
    # Actualizar conteos
    for grupo in grupos.values():
        grupo['total_articulos'] = len(grupo['articulos'])
    
    sin_proveedor['total_articulos'] = len(sin_proveedor['articulos'])
    
    # Agregar grupo sin proveedor si tiene artículos
    if sin_proveedor['total_articulos'] > 0:
        grupos['sin_proveedor'] = sin_proveedor
    
    return grupos


# ========================================
# RESÚMENES Y ESTADÍSTICAS
# ========================================

def calcular_resumen(pedidos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula un resumen de los pedidos.
    
    Returns:
        Dict con estadísticas generales
    """
    total_articulos = len(pedidos)
    articulos_criticos = sum(1 for p in pedidos if 'CRÍTICO' in p['prioridad'])
    articulos_preventivos = sum(1 for p in pedidos if p['prioridad'] == 'PREVENTIVO')
    articulos_con_pedido = sum(1 for p in pedidos if p['pedido_sugerido'] > 0)
    articulos_sin_proveedor = sum(1 for p in pedidos if not p.get('proveedor_id'))
    
    coste_total = sum(p['coste_estimado'] for p in pedidos if p['requiere_pedido'])
    coste_criticos = sum(
        p['coste_estimado'] for p in pedidos 
        if p['requiere_pedido'] and 'CRÍTICO' in p['prioridad']
    )
    
    return {
        'total_articulos': total_articulos,
        'articulos_criticos': articulos_criticos,
        'articulos_preventivos': articulos_preventivos,
        'articulos_normales': total_articulos - articulos_criticos - articulos_preventivos,
        'articulos_con_pedido': articulos_con_pedido,
        'articulos_sin_proveedor': articulos_sin_proveedor,
        'coste_total': coste_total,
        'coste_criticos': coste_criticos,
        'coste_preventivos': coste_total - coste_criticos
    }


# ========================================
# GENERACIÓN DE LISTAS DE PEDIDO
# ========================================

def generar_lista_pedido_proveedor(
    proveedor_info: Dict[str, Any],
    incluir_detalles: bool = True
) -> Dict[str, Any]:
    """
    Genera una lista de pedido formateada para un proveedor.
    
    Args:
        proveedor_info: Dict con info del proveedor y sus artículos
        incluir_detalles: Si incluir consumo diario, días restantes, etc.
        
    Returns:
        Dict con la lista de pedido formateada
    """
    articulos_formateados = []
    
    for articulo in proveedor_info['articulos']:
        item = {
            'nombre': articulo['articulo_nombre'],
            'cantidad': articulo['pedido_sugerido'],
            'unidad': articulo['u_medida'],
            'coste_unitario': articulo['coste_unitario'],
            'coste_total': articulo['coste_estimado'],
            'stock_actual': articulo['stock_actual'],
            'nivel_alerta': articulo['nivel_alerta'],
            'prioridad': articulo['prioridad']
        }
        
        if incluir_detalles:
            item['ref_proveedor'] = articulo.get('ref_proveedor', '')
            item['ean'] = articulo.get('ean', '')
            item['consumo_diario'] = articulo['consumo_diario']
            item['dias_restantes'] = articulo['dias_restantes']
        
        articulos_formateados.append(item)
    
    return {
        'proveedor': proveedor_info['proveedor_nombre'],
        'email': proveedor_info.get('proveedor_email'),
        'telefono': proveedor_info.get('proveedor_telefono'),
        'fecha': date.today().isoformat(),
        'total_articulos': proveedor_info['total_articulos'],
        'coste_total': proveedor_info['coste_total'],
        'articulos': articulos_formateados
    }


# ========================================
# UTILIDADES
# ========================================

def formatear_coste(valor: float) -> str:
    """Formatea un valor monetario al estilo español"""
    if valor is None:
        return "0,00 €"
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def formatear_cantidad(valor: float, unidad: str = "") -> str:
    """Formatea una cantidad con su unidad"""
    if valor is None:
        return "0"
    
    # Si es unidad, sin decimales
    if unidad.lower() in ['unidad', 'uds', 'ud', 'u']:
        return f"{int(valor)} uds"
    
    # Para otras unidades
    if valor == int(valor):
        return f"{int(valor)} {unidad}".strip()
    else:
        return f"{valor:.2f} {unidad}".strip()
