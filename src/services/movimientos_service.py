"""
Servicio de Movimientos - Lógica de negocio para operaciones de movimientos de almacén
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from src.repos import movimientos_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


# ========================================
# VALIDACIONES
# ========================================

def validar_cantidad(cantidad: float) -> Tuple[bool, str]:
    """
    Valida que la cantidad sea válida.

    Args:
        cantidad: Cantidad a validar

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if cantidad <= 0:
        log_validacion("movimientos", "cantidad", f"Cantidad inválida: {cantidad}")
        return False, "La cantidad debe ser mayor que 0"

    if cantidad > 999999:
        log_validacion("movimientos", "cantidad", f"Cantidad excesiva: {cantidad}")
        return False, "La cantidad es demasiado grande"

    return True, ""


def validar_fecha(fecha: str) -> Tuple[bool, str]:
    """
    Valida que la fecha sea válida y no sea futura.

    Args:
        fecha: Fecha en formato YYYY-MM-DD

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()

        if fecha_obj > date.today():
            log_validacion("movimientos", "fecha", f"Fecha futura: {fecha}")
            return False, "La fecha no puede ser futura"

        # Opcional: limitar a 1 año atrás
        fecha_minima = date.today().replace(year=date.today().year - 1)
        if fecha_obj < fecha_minima:
            log_validacion("movimientos", "fecha", f"Fecha muy antigua: {fecha}")
            return False, "La fecha no puede ser de hace más de 1 año"

        return True, ""

    except ValueError:
        log_validacion("movimientos", "fecha", f"Formato de fecha inválido: {fecha}")
        return False, "Formato de fecha inválido (use YYYY-MM-DD)"


def validar_stock_disponible(articulo_id: int, almacen_id: int, cantidad_requerida: float) -> Tuple[bool, str, float]:
    """
    Valida que haya stock suficiente en un almacén para una operación.

    Args:
        articulo_id: ID del artículo
        almacen_id: ID del almacén
        cantidad_requerida: Cantidad que se necesita

    Returns:
        Tupla (hay_stock, mensaje, stock_actual)
    """
    try:
        stock_por_almacen = movimientos_repo.get_stock_por_almacen(articulo_id)

        stock_actual = 0
        for s in stock_por_almacen:
            if s['almacen_id'] == almacen_id:
                stock_actual = s['stock']
                break

        if stock_actual < cantidad_requerida:
            mensaje = f"Stock insuficiente. Disponible: {stock_actual:.2f}, Requerido: {cantidad_requerida:.2f}"
            log_validacion("movimientos", "stock", mensaje)
            return False, mensaje, stock_actual

        return True, "", stock_actual

    except Exception as e:
        log_error_bd("movimientos", "validar_stock", e)
        return False, f"Error al verificar stock: {str(e)}", 0


# ========================================
# OPERACIONES DE TRASPASO
# ========================================

def crear_traspaso_almacen_furgoneta(
    fecha: str,
    operario_id: int,
    articulos: List[Dict[str, Any]],
    usuario: str,
    modo: str = "ENTREGAR"
) -> Tuple[bool, str, Optional[List[int]]]:
    """
    Crea traspasos entre almacén y furgoneta para un operario.

    Args:
        fecha: Fecha del movimiento (YYYY-MM-DD)
        operario_id: ID del operario
        articulos: Lista de dicts con 'id' y 'cantidad'
        usuario: Usuario que realiza la operación
        modo: "ENTREGAR" (Almacén→Furgoneta) o "RECIBIR" (Furgoneta→Almacén)

    Returns:
        Tupla (exito, mensaje, lista_ids_movimientos)
    """
    try:
        # Validar fecha
        valido, error = validar_fecha(fecha)
        if not valido:
            return False, error, None

        # Validar artículos
        if not articulos or len(articulos) == 0:
            return False, "No hay artículos para procesar", None

        # Obtener almacén principal
        almacen = movimientos_repo.get_almacen_by_nombre("Almacén")
        if not almacen:
            return False, "No se encontró el almacén principal", None

        almacen_id = almacen['id']

        # Obtener furgoneta asignada al operario
        furgoneta = movimientos_repo.get_furgoneta_asignada(operario_id, fecha)
        if not furgoneta:
            return False, "El operario no tiene furgoneta asignada para esta fecha", None

        furgoneta_id = furgoneta['furgoneta_id']

        # Determinar origen y destino según el modo
        if modo == "ENTREGAR":
            origen_id = almacen_id
            destino_id = furgoneta_id
        else:  # RECIBIR
            origen_id = furgoneta_id
            destino_id = almacen_id

        # Validar stock disponible en origen (solo para salidas)
        for art in articulos:
            valido, mensaje = validar_cantidad(art['cantidad'])
            if not valido:
                return False, f"Artículo ID {art['id']}: {mensaje}", None

            # Validar stock en origen
            hay_stock, mensaje_stock, stock_actual = validar_stock_disponible(
                art['id'], origen_id, art['cantidad']
            )

            if not hay_stock:
                return False, f"Artículo ID {art['id']}: {mensaje_stock}", None

        # Crear movimientos
        movimientos = []
        for art in articulos:
            movimientos.append({
                'tipo': 'TRASPASO',
                'fecha': fecha,
                'articulo_id': art['id'],
                'origen_id': origen_id,
                'destino_id': destino_id,
                'cantidad': art['cantidad'],
                'operario_id': operario_id,
                'responsable': usuario,
                'motivo': f"{modo.capitalize()} material"
            })

        ids_creados = movimientos_repo.crear_movimientos_batch(movimientos)

        # Logging
        detalles = f"Modo: {modo}, Operario ID: {operario_id}, Artículos: {len(articulos)}"
        log_operacion("movimientos", "crear_traspaso_lote", usuario, detalles)
        logger.info(f"Traspaso creado | {modo} | Operario: {operario_id} | Items: {len(articulos)}")

        return True, f"{len(articulos)} artículo(s) procesado(s) correctamente", ids_creados

    except Exception as e:
        log_error_bd("movimientos", "crear_traspaso_almacen_furgoneta", e)
        return False, f"Error al crear traspasos: {str(e)}", None


# ========================================
# OPERACIONES DE ENTRADA
# ========================================

def crear_recepcion_material(
    fecha: str,
    articulos: List[Dict[str, Any]],
    almacen_nombre: str,
    albaran: Optional[str],
    usuario: str,
    proveedor_id: Optional[int] = None
) -> Tuple[bool, str, Optional[List[int]]]:
    """
    Crea entradas de material (recepciones).

    Args:
        fecha: Fecha de recepción
        articulos: Lista con 'articulo_id', 'cantidad', 'coste_unit'
        almacen_nombre: Nombre del almacén destino
        albaran: Número de albarán
        usuario: Usuario que realiza la recepción
        proveedor_id: ID del proveedor (opcional)

    Returns:
        Tupla (exito, mensaje, lista_ids)
    """
    try:
        # Validar fecha
        valido, error = validar_fecha(fecha)
        if not valido:
            return False, error, None

        # Validar artículos
        if not articulos:
            return False, "No hay artículos para recepcionar", None

        # Obtener almacén
        almacen = movimientos_repo.get_almacen_by_nombre(almacen_nombre)
        if not almacen:
            return False, f"No se encontró el almacén '{almacen_nombre}'", None

        almacen_id = almacen['id']

        # Validar cantidades
        for art in articulos:
            valido, mensaje = validar_cantidad(art['cantidad'])
            if not valido:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje}", None

        # Crear movimientos
        movimientos = []
        for art in articulos:
            movimientos.append({
                'tipo': 'ENTRADA',
                'fecha': fecha,
                'articulo_id': art['articulo_id'],
                'origen_id': proveedor_id,  # ID del proveedor
                'destino_id': almacen_id,
                'cantidad': art['cantidad'],
                'coste_unit': art.get('coste_unit'),
                'albaran': albaran,
                'responsable': usuario
            })

        ids_creados = movimientos_repo.crear_movimientos_batch(movimientos)

        # Logging
        detalles = f"Albarán: {albaran}, Almacén: {almacen_nombre}, Artículos: {len(articulos)}"
        log_operacion("movimientos", "crear_recepcion", usuario, detalles)
        logger.info(f"Recepción creada | Albarán: {albaran} | Items: {len(articulos)}")

        return True, f"{len(articulos)} artículo(s) recepcionado(s)", ids_creados

    except Exception as e:
        log_error_bd("movimientos", "crear_recepcion_material", e)
        return False, f"Error al crear recepción: {str(e)}", None


# ========================================
# OPERACIONES DE IMPUTACIÓN
# ========================================

def crear_imputacion_obra(
    fecha: str,
    operario_id: int,
    articulos: List[Dict[str, Any]],
    ot: str,
    motivo: Optional[str],
    usuario: str
) -> Tuple[bool, str, Optional[List[int]]]:
    """
    Crea imputaciones de material a obra.

    Args:
        fecha: Fecha de la imputación
        operario_id: ID del operario
        articulos: Lista con 'articulo_id' y 'cantidad'
        ot: Orden de trabajo
        motivo: Descripción/motivo
        usuario: Usuario que registra

    Returns:
        Tupla (exito, mensaje, lista_ids)
    """
    try:
        # Validar fecha
        valido, error = validar_fecha(fecha)
        if not valido:
            return False, error, None

        # Validar OT
        if not ot or ot.strip() == "":
            return False, "El número de OT es obligatorio", None

        # Validar artículos
        if not articulos:
            return False, "No hay artículos para imputar", None

        # Obtener furgoneta del operario
        furgoneta = movimientos_repo.get_furgoneta_asignada(operario_id, fecha)
        if not furgoneta:
            return False, "El operario no tiene furgoneta asignada", None

        furgoneta_id = furgoneta['furgoneta_id']

        # Validar stock y cantidades
        for art in articulos:
            valido, mensaje = validar_cantidad(art['cantidad'])
            if not valido:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje}", None

            hay_stock, mensaje_stock, _ = validar_stock_disponible(
                art['articulo_id'], furgoneta_id, art['cantidad']
            )

            if not hay_stock:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje_stock}", None

        # Crear movimientos
        movimientos = []
        for art in articulos:
            movimientos.append({
                'tipo': 'IMPUTACION',
                'fecha': fecha,
                'articulo_id': art['articulo_id'],
                'origen_id': furgoneta_id,
                'cantidad': art['cantidad'],
                'operario_id': operario_id,
                'ot': ot,
                'motivo': motivo
            })

        ids_creados = movimientos_repo.crear_movimientos_batch(movimientos)

        # Logging
        detalles = f"OT: {ot}, Operario ID: {operario_id}, Artículos: {len(articulos)}"
        log_operacion("movimientos", "crear_imputacion", usuario, detalles)
        logger.info(f"Imputación creada | OT: {ot} | Items: {len(articulos)}")

        return True, f"{len(articulos)} artículo(s) imputado(s) a OT {ot}", ids_creados

    except Exception as e:
        log_error_bd("movimientos", "crear_imputacion_obra", e)
        return False, f"Error al crear imputación: {str(e)}", None


# ========================================
# OPERACIONES DE PÉRDIDA/DEVOLUCIÓN
# ========================================

def crear_material_perdido(
    fecha: str,
    almacen_id: int,
    articulos: List[Dict[str, Any]],
    motivo: str,
    usuario: str
) -> Tuple[bool, str, Optional[List[int]]]:
    """
    Registra material perdido o dañado.

    Args:
        fecha: Fecha de la pérdida
        almacen_id: ID del almacén origen
        articulos: Lista con 'articulo_id' y 'cantidad'
        motivo: Motivo de la pérdida (obligatorio)
        usuario: Usuario que registra

    Returns:
        Tupla (exito, mensaje, lista_ids)
    """
    try:
        # Validar fecha
        valido, error = validar_fecha(fecha)
        if not valido:
            return False, error, None

        # Validar motivo
        if not motivo or motivo.strip() == "":
            return False, "El motivo es obligatorio para registrar pérdidas", None

        # Validar artículos
        if not articulos:
            return False, "No hay artículos para registrar", None

        # Validar stock y cantidades
        for art in articulos:
            valido, mensaje = validar_cantidad(art['cantidad'])
            if not valido:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje}", None

            hay_stock, mensaje_stock, _ = validar_stock_disponible(
                art['articulo_id'], almacen_id, art['cantidad']
            )

            if not hay_stock:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje_stock}", None

        # Crear movimientos
        movimientos = []
        for art in articulos:
            movimientos.append({
                'tipo': 'PERDIDA',
                'fecha': fecha,
                'articulo_id': art['articulo_id'],
                'origen_id': almacen_id,
                'cantidad': art['cantidad'],
                'motivo': motivo,
                'responsable': usuario
            })

        ids_creados = movimientos_repo.crear_movimientos_batch(movimientos)

        # Logging
        detalles = f"Almacén ID: {almacen_id}, Motivo: {motivo}, Artículos: {len(articulos)}"
        log_operacion("movimientos", "crear_perdida", usuario, detalles)
        logger.info(f"Pérdida registrada | Almacén: {almacen_id} | Items: {len(articulos)}")

        return True, f"{len(articulos)} artículo(s) registrado(s) como perdido(s)", ids_creados

    except Exception as e:
        log_error_bd("movimientos", "crear_material_perdido", e)
        return False, f"Error al registrar pérdida: {str(e)}", None


def crear_devolucion_proveedor(
    fecha: str,
    almacen_id: int,
    articulos: List[Dict[str, Any]],
    motivo: Optional[str],
    usuario: str
) -> Tuple[bool, str, Optional[List[int]]]:
    """
    Registra devolución de material a proveedor.

    Args:
        fecha: Fecha de la devolución
        almacen_id: ID del almacén origen
        articulos: Lista con 'articulo_id' y 'cantidad'
        motivo: Motivo de la devolución
        usuario: Usuario que registra

    Returns:
        Tupla (exito, mensaje, lista_ids)
    """
    try:
        # Validar fecha
        valido, error = validar_fecha(fecha)
        if not valido:
            return False, error, None

        # Validar artículos
        if not articulos:
            return False, "No hay artículos para devolver", None

        # Validar stock y cantidades
        for art in articulos:
            valido, mensaje = validar_cantidad(art['cantidad'])
            if not valido:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje}", None

            hay_stock, mensaje_stock, _ = validar_stock_disponible(
                art['articulo_id'], almacen_id, art['cantidad']
            )

            if not hay_stock:
                return False, f"Artículo ID {art['articulo_id']}: {mensaje_stock}", None

        # Crear movimientos
        movimientos = []
        for art in articulos:
            movimientos.append({
                'tipo': 'DEVOLUCION',
                'fecha': fecha,
                'articulo_id': art['articulo_id'],
                'origen_id': almacen_id,
                'cantidad': art['cantidad'],
                'motivo': motivo,
                'responsable': usuario
            })

        ids_creados = movimientos_repo.crear_movimientos_batch(movimientos)

        # Logging
        detalles = f"Almacén ID: {almacen_id}, Motivo: {motivo or 'N/A'}, Artículos: {len(articulos)}"
        log_operacion("movimientos", "crear_devolucion", usuario, detalles)
        logger.info(f"Devolución registrada | Almacén: {almacen_id} | Items: {len(articulos)}")

        return True, f"{len(articulos)} artículo(s) devuelto(s)", ids_creados

    except Exception as e:
        log_error_bd("movimientos", "crear_devolucion_proveedor", e)
        return False, f"Error al registrar devolución: {str(e)}", None


# ========================================
# CONSULTAS
# ========================================

def obtener_movimientos_filtrados(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    articulo_id: Optional[int] = None,
    almacen_id: Optional[int] = None,
    operario_id: Optional[int] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene movimientos aplicando filtros.

    Args:
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin
        tipo: Tipo de movimiento
        articulo_id: ID del artículo
        almacen_id: ID del almacén
        operario_id: ID del operario
        limit: Límite de resultados

    Returns:
        Lista de movimientos
    """
    try:
        return movimientos_repo.get_todos(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo=tipo,
            articulo_id=articulo_id,
            almacen_id=almacen_id,
            operario_id=operario_id,
            limit=limit
        )
    except Exception as e:
        log_error_bd("movimientos", "obtener_filtrados", e)
        return []


def obtener_historial_articulo(articulo_id: int, dias: int = 90) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de movimientos de un artículo.

    Args:
        articulo_id: ID del artículo
        dias: Días hacia atrás

    Returns:
        Lista de movimientos
    """
    try:
        from datetime import timedelta
        fecha_desde = (date.today() - timedelta(days=dias)).isoformat()
        return movimientos_repo.get_movimientos_articulo(articulo_id, fecha_desde)
    except Exception as e:
        log_error_bd("movimientos", "obtener_historial", e)
        return []
