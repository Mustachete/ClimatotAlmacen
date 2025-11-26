# informes_furgonetas_service.py - Servicio para generar informes semanales de furgonetas
"""
Servicio para calcular y generar informes semanales de consumo por furgoneta.
Calcula stock inicial, movimientos diarios (E/D/G) y stock final.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.db_utils import fetch_all, fetch_one
from src.core.logger import logger


def calcular_lunes_de_semana(fecha: str) -> str:
    """
    Dado cualquier fecha, retorna el lunes de esa semana en formato YYYY-MM-DD.

    Args:
        fecha: Fecha en formato YYYY-MM-DD

    Returns:
        Fecha del lunes de esa semana
    """
    dt = datetime.strptime(fecha, "%Y-%m-%d")
    # weekday(): 0=Lunes, 6=Domingo
    dias_desde_lunes = dt.weekday()
    lunes = dt - timedelta(days=dias_desde_lunes)
    return lunes.strftime("%Y-%m-%d")


def calcular_stock_inicial_furgoneta(furgoneta_id: int, fecha_inicio_semana: str) -> Dict[int, float]:
    """
    Calcula el stock inicial de una furgoneta al inicio de la semana (domingo anterior).

    Lógica: Suma todos los movimientos HASTA el domingo anterior (inclusive):
    - ENTRADAS a la furgoneta: suman
    - SALIDAS de la furgoneta: restan

    Args:
        furgoneta_id: ID de la furgoneta
        fecha_inicio_semana: Lunes de la semana (YYYY-MM-DD)

    Returns:
        Dict {articulo_id: cantidad_stock}
    """
    try:
        # Calcular domingo anterior al lunes
        lunes = datetime.strptime(fecha_inicio_semana, "%Y-%m-%d")
        domingo_anterior = lunes - timedelta(days=1)
        fecha_limite = domingo_anterior.strftime("%Y-%m-%d")

        stock = defaultdict(float)

        # ENTRADAS: destino_id = furgoneta (suma al stock)
        query_entradas = """
            SELECT articulo_id, SUM(cantidad) as total
            FROM movimientos
            WHERE destino_id = %s AND fecha <= %s
            GROUP BY articulo_id
        """
        entradas = fetch_all(query_entradas, (furgoneta_id, fecha_limite))
        for row in entradas:
            stock[row['articulo_id']] += float(row['total'])  # Convertir Decimal a float

        # SALIDAS: origen_id = furgoneta (resta al stock)
        query_salidas = """
            SELECT articulo_id, SUM(cantidad) as total
            FROM movimientos
            WHERE origen_id = %s AND fecha <= %s
            GROUP BY articulo_id
        """
        salidas = fetch_all(query_salidas, (furgoneta_id, fecha_limite))
        for row in salidas:
            stock[row['articulo_id']] -= float(row['total'])  # Convertir Decimal a float

        return dict(stock)

    except Exception as e:
        logger.exception(f"Error al calcular stock inicial: {e}")
        return {}


def obtener_movimientos_semana(
    furgoneta_id: int,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict[str, Any]]:
    """
    Obtiene todos los movimientos de una furgoneta durante una semana.

    Args:
        furgoneta_id: ID de la furgoneta
        fecha_inicio: Lunes (YYYY-MM-DD)
        fecha_fin: Viernes o Sábado (YYYY-MM-DD)

    Returns:
        Lista de movimientos con estructura:
        {
            'fecha': str,
            'articulo_id': int,
            'articulo_nombre': str,
            'cantidad': float,
            'tipo_movimiento': str,  # 'E', 'D', 'G'
            'operario': str (opcional)
        }
    """
    try:
        query = """
            SELECT
                m.fecha,
                m.articulo_id,
                a.nombre as articulo_nombre,
                a.familia_id,
                f.nombre as familia_nombre,
                m.cantidad,
                m.tipo,
                m.origen_id,
                m.destino_id,
                m.ot,
                m.motivo,
                m.operario_id,
                o.nombre as operario_nombre
            FROM movimientos m
            JOIN articulos a ON m.articulo_id = a.id
            LEFT JOIN familias f ON a.familia_id = f.id
            LEFT JOIN operarios o ON m.operario_id = o.id
            WHERE m.fecha BETWEEN %s AND %s
              AND (m.origen_id = %s OR m.destino_id = %s)
            ORDER BY m.fecha, a.nombre
        """

        rows = fetch_all(query, (fecha_inicio, fecha_fin, furgoneta_id, furgoneta_id))
        logger.info(f"Filas obtenidas de BD: {len(rows)}")

        movimientos = []
        for row in rows:
            fecha = row['fecha']
            art_id = row['articulo_id']
            art_nombre = row['articulo_nombre']
            fam_id = row['familia_id']
            fam_nombre = row['familia_nombre']
            cantidad = row['cantidad']
            tipo = row['tipo']
            origen = row['origen_id']
            destino = row['destino_id']
            ot = row['ot']
            motivo = row['motivo']
            op_id = row['operario_id']
            op_nombre = row['operario_nombre']

            # Determinar tipo de movimiento (E/D/G)
            tipo_mov = None

            if destino == furgoneta_id:
                # Material que ENTRA a la furgoneta (TRASPASO almacen->furgoneta, ENTRADA directa)
                tipo_mov = 'E'
            elif origen == furgoneta_id:
                # Material que SALE de la furgoneta
                if tipo == 'DEVOLUCION':
                    # Devolución: furgoneta devuelve al almacén
                    tipo_mov = 'D'
                elif tipo == 'IMPUTACION' or tipo == 'PERDIDA':
                    # Imputaciones y pérdidas son gastos
                    tipo_mov = 'G'
                elif tipo == 'TRASPASO':
                    # TRASPASO desde furgoneta: verificar destino
                    if destino == 1:  # Devuelve al almacén principal
                        tipo_mov = 'D'
                    else:
                        tipo_mov = 'G'  # Traspaso a otra ubicación = gasto

            if tipo_mov:
                movimientos.append({
                    'fecha': fecha,
                    'articulo_id': art_id,
                    'articulo_nombre': art_nombre,
                    'familia_id': fam_id,
                    'familia_nombre': fam_nombre or 'SIN GRUPO',
                    'cantidad': cantidad,
                    'tipo_movimiento': tipo_mov,
                    'operario_id': op_id,
                    'operario_nombre': op_nombre
                })
            else:
                logger.warning(f"Movimiento sin clasificar: tipo={tipo}, origen={origen}, destino={destino}, furgoneta={furgoneta_id}")

        logger.info(f"Movimientos clasificados: {len(movimientos)} de {len(rows)} filas")
        return movimientos

    except Exception as e:
        logger.exception(f"Error al obtener movimientos: {e}")
        return []


def generar_datos_informe(
    furgoneta_id: int,
    fecha_lunes: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Genera todos los datos necesarios para el informe semanal de una furgoneta.

    Args:
        furgoneta_id: ID de la furgoneta
        fecha_lunes: Lunes de la semana a informar (YYYY-MM-DD)

    Returns:
        Tuple (exito, mensaje, datos)
        datos = {
            'furgoneta_id': int,
            'furgoneta_nombre': str,
            'fecha_inicio': str,
            'fecha_fin': str,
            'dias_semana': [{'fecha': str, 'dia_nombre': str}, ...],
            'operarios': [str],  # Lista de operarios únicos
            'articulos': [
                {
                    'familia': str,
                    'articulo_id': int,
                    'articulo_nombre': str,
                    'stock_inicial': float,
                    'movimientos_diarios': {
                        'YYYY-MM-DD': {'E': float, 'D': float, 'G': float}
                    },
                    'total_e': float,
                    'total_d': float,
                    'total_g': float,
                    'stock_final': float
                }
            ]
        }
    """
    try:
        # 1. Validar lunes
        lunes = calcular_lunes_de_semana(fecha_lunes)
        logger.info(f"Generando informe para furgoneta_id={furgoneta_id}, semana={lunes}")

        # 2. Obtener datos de la furgoneta
        furgoneta_query = "SELECT id, nombre FROM almacenes WHERE id = %s AND tipo = 'furgoneta'"
        furgoneta = fetch_one(furgoneta_query, (furgoneta_id,))

        if not furgoneta:
            logger.warning(f"Furgoneta con id={furgoneta_id} no encontrada o no es de tipo 'furgoneta'")
            return False, "Furgoneta no encontrada o no es válida", None

        furgoneta_nombre = furgoneta['nombre']
        logger.info(f"Furgoneta encontrada: {furgoneta_nombre} (ID: {furgoneta_id})")

        # 3. Determinar rango de fechas (L-V o L-S si hay movimientos el sábado)
        viernes = datetime.strptime(lunes, "%Y-%m-%d") + timedelta(days=4)
        sabado = viernes + timedelta(days=1)

        # Verificar si hay movimientos el sábado
        movs_sabado = fetch_one(
            "SELECT COUNT(*) as count FROM movimientos WHERE fecha = %s AND (origen_id = %s OR destino_id = %s)",
            (sabado.strftime("%Y-%m-%d"), furgoneta_id, furgoneta_id)
        )

        incluir_sabado = movs_sabado and movs_sabado['count'] > 0
        fecha_fin = sabado.strftime("%Y-%m-%d") if incluir_sabado else viernes.strftime("%Y-%m-%d")
        logger.info(f"Rango de fechas: {lunes} a {fecha_fin} (incluye sábado: {incluir_sabado})")

        # 4. Generar lista de días
        dias_semana = []
        fecha_actual = datetime.strptime(lunes, "%Y-%m-%d")
        num_dias = 6 if incluir_sabado else 5
        dias_nombres = ['L', 'M', 'X', 'J', 'V', 'S']

        for i in range(num_dias):
            dias_semana.append({
                'fecha': fecha_actual.strftime("%Y-%m-%d"),
                'dia_nombre': dias_nombres[i],
                'dia_completo': fecha_actual.strftime("%d/%m")
            })
            fecha_actual += timedelta(days=1)

        # 5. Calcular stock inicial (domingo anterior)
        stock_inicial_dict = calcular_stock_inicial_furgoneta(furgoneta_id, lunes)
        logger.info(f"Stock inicial calculado: {len(stock_inicial_dict)} artículos")

        # 6. Obtener movimientos de la semana
        movimientos = obtener_movimientos_semana(furgoneta_id, lunes, fecha_fin)
        logger.info(f"Movimientos obtenidos: {len(movimientos)} registros")

        # 7. Organizar datos por artículo
        articulos_dict = defaultdict(lambda: {
            'familia': '',
            'articulo_nombre': '',
            'stock_inicial': 0.0,
            'movimientos_diarios': defaultdict(lambda: {'E': 0.0, 'D': 0.0, 'G': 0.0}),
            'total_e': 0.0,
            'total_d': 0.0,
            'total_g': 0.0
        })

        operarios_set = set()

        for mov in movimientos:
            art_id = mov['articulo_id']
            fecha = mov['fecha']
            tipo = mov['tipo_movimiento']
            cantidad = float(mov['cantidad'])  # Convertir Decimal a float

            articulos_dict[art_id]['familia'] = mov['familia_nombre']
            articulos_dict[art_id]['articulo_nombre'] = mov['articulo_nombre']
            articulos_dict[art_id]['movimientos_diarios'][fecha][tipo] += cantidad

            if tipo == 'E':
                articulos_dict[art_id]['total_e'] += cantidad
            elif tipo == 'D':
                articulos_dict[art_id]['total_d'] += cantidad
            elif tipo == 'G':
                articulos_dict[art_id]['total_g'] += cantidad

            if mov['operario_nombre']:
                operarios_set.add(mov['operario_nombre'])

        # Añadir stock inicial a cada artículo
        for art_id in articulos_dict:
            articulos_dict[art_id]['stock_inicial'] = stock_inicial_dict.get(art_id, 0.0)

        # También incluir artículos con stock inicial pero sin movimientos
        for art_id, stock in stock_inicial_dict.items():
            if art_id not in articulos_dict and stock != 0:
                # Obtener nombre del artículo
                art_info = fetch_one(
                    "SELECT a.nombre as articulo_nombre, f.nombre as familia_nombre FROM articulos a LEFT JOIN familias f ON a.familia_id = f.id WHERE a.id = %s",
                    (art_id,)
                )
                if art_info:
                    articulos_dict[art_id]['articulo_nombre'] = art_info['articulo_nombre']
                    articulos_dict[art_id]['familia'] = art_info['familia_nombre'] or 'SIN GRUPO'
                    articulos_dict[art_id]['stock_inicial'] = stock

        # 8. Calcular stock final y convertir a lista
        articulos_lista = []
        for art_id, datos in articulos_dict.items():
            stock_final = (
                datos['stock_inicial'] +
                datos['total_e'] -
                datos['total_d'] -
                datos['total_g']
            )

            articulos_lista.append({
                'articulo_id': art_id,
                'familia': datos['familia'],
                'articulo_nombre': datos['articulo_nombre'],
                'stock_inicial': datos['stock_inicial'],
                'movimientos_diarios': dict(datos['movimientos_diarios']),
                'total_e': datos['total_e'],
                'total_d': datos['total_d'],
                'total_g': datos['total_g'],
                'stock_final': stock_final
            })

        # Ordenar por familia y luego por nombre de artículo
        articulos_lista.sort(key=lambda x: (x['familia'], x['articulo_nombre']))

        logger.info(f"Artículos procesados: {len(articulos_lista)}")
        logger.info(f"Operarios únicos: {len(operarios_set)}")

        # 9. Construir resultado
        resultado = {
            'furgoneta_id': furgoneta_id,
            'furgoneta_nombre': furgoneta_nombre,
            'fecha_inicio': lunes,
            'fecha_fin': fecha_fin,
            'dias_semana': dias_semana,
            'operarios': sorted(list(operarios_set)),
            'articulos': articulos_lista
        }

        return True, "Datos generados correctamente", resultado

    except Exception as e:
        logger.exception(f"Error al generar datos de informe: {e}")
        return False, f"Error: {str(e)}", None
