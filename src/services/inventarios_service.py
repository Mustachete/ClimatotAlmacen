"""
Servicio de Inventarios - Lógica de negocio para gestión de inventarios físicos
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from src.repos import inventarios_repo, movimientos_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


# ========================================
# VALIDACIONES
# ========================================

def validar_responsable(responsable: str) -> Tuple[bool, str]:
    """
    Valida que el responsable sea válido.

    Args:
        responsable: Nombre del responsable

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not responsable or not responsable.strip():
        log_validacion("inventarios", "responsable", "Responsable vacío")
        return False, "El responsable es obligatorio"

    if len(responsable.strip()) < 3:
        log_validacion("inventarios", "responsable", f"Responsable muy corto: {responsable}")
        return False, "El nombre del responsable debe tener al menos 3 caracteres"

    return True, ""


def validar_stock_contado(stock_contado: float) -> Tuple[bool, str]:
    """
    Valida que el stock contado sea válido.

    Args:
        stock_contado: Cantidad contada

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if stock_contado < 0:
        log_validacion("inventarios", "stock_contado", f"Stock negativo: {stock_contado}")
        return False, "El stock contado no puede ser negativo"

    if stock_contado > 999999:
        log_validacion("inventarios", "stock_contado", f"Stock excesivo: {stock_contado}")
        return False, "El stock contado es demasiado grande"

    return True, ""


# ========================================
# OPERACIONES DE INVENTARIO
# ========================================

def crear_inventario(
    fecha: str,
    responsable: str,
    almacen_id: int,
    observaciones: Optional[str],
    solo_con_stock: bool,
    usuario: str
) -> Tuple[bool, str, Optional[int]]:
    """
    Crea un nuevo inventario con sus líneas de detalle.

    Args:
        fecha: Fecha del inventario (YYYY-MM-DD)
        responsable: Nombre del responsable
        almacen_id: ID del almacén
        observaciones: Observaciones opcionales
        solo_con_stock: Si True, solo incluye artículos con stock
        usuario: Usuario que crea el inventario

    Returns:
        Tupla (exito, mensaje, inventario_id)
    """
    try:
        # Validar responsable
        valido, error = validar_responsable(responsable)
        if not valido:
            return False, error, None

        # Verificar si el responsable ya tiene un inventario abierto
        inventario_abierto = inventarios_repo.get_inventario_abierto_usuario(responsable)
        if inventario_abierto:
            mensaje = (
                f"El usuario '{responsable}' ya tiene un inventario abierto "
                f"(ID: {inventario_abierto['id']}, Fecha: {inventario_abierto['fecha']})"
            )
            log_validacion("inventarios", "inventario_duplicado", mensaje)
            return False, mensaje, None

        # Crear cabecera del inventario
        inventario_id = inventarios_repo.crear_inventario(
            fecha=fecha,
            responsable=responsable,
            almacen_id=almacen_id,
            observaciones=observaciones
        )

        # Crear líneas de detalle
        count = inventarios_repo.crear_lineas_detalle(
            inventario_id=inventario_id,
            almacen_id=almacen_id,
            solo_con_stock=solo_con_stock
        )

        if count == 0:
            return False, "No hay artículos para inventariar en este almacén", None

        # Logging
        detalles = f"Inventario ID: {inventario_id}, Responsable: {responsable}, Artículos: {count}"
        log_operacion("inventarios", "crear", usuario, detalles)
        logger.info(f"Inventario creado | ID: {inventario_id} | Líneas: {count}")

        mensaje = f"Inventario creado correctamente con {count} artículo(s) a contar"
        return True, mensaje, inventario_id

    except Exception as e:
        log_error_bd("inventarios", "crear_inventario", e)
        return False, f"Error al crear inventario: {str(e)}", None


def actualizar_conteo(
    detalle_id: int,
    stock_contado: float,
    usuario: str
) -> Tuple[bool, str]:
    """
    Actualiza el conteo físico de un artículo en el inventario.

    Args:
        detalle_id: ID de la línea de detalle
        stock_contado: Cantidad contada físicamente
        usuario: Usuario que realiza el conteo

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Validar stock contado
        valido, error = validar_stock_contado(stock_contado)
        if not valido:
            return False, error

        # Obtener línea actual
        linea = inventarios_repo.get_linea_detalle(detalle_id)
        if not linea:
            return False, f"No se encontró la línea de detalle {detalle_id}"

        # Actualizar conteo
        inventarios_repo.actualizar_conteo(detalle_id, stock_contado)

        # Calcular diferencia
        diferencia = stock_contado - linea['stock_teorico']

        # Logging
        detalles = (
            f"Línea ID: {detalle_id}, Artículo: {linea['articulo_nombre']}, "
            f"Teórico: {linea['stock_teorico']}, Contado: {stock_contado}, Diferencia: {diferencia}"
        )
        log_operacion("inventarios", "actualizar_conteo", usuario, detalles)

        return True, "Conteo actualizado correctamente"

    except Exception as e:
        log_error_bd("inventarios", "actualizar_conteo", e)
        return False, f"Error al actualizar conteo: {str(e)}"


def finalizar_inventario(
    inventario_id: int,
    aplicar_ajustes: bool,
    usuario: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Finaliza un inventario y opcionalmente aplica los ajustes al stock.

    Args:
        inventario_id: ID del inventario
        aplicar_ajustes: Si True, crea movimientos para ajustar el stock
        usuario: Usuario que finaliza

    Returns:
        Tupla (exito, mensaje, estadisticas)
    """
    try:
        # Obtener inventario
        inventario = inventarios_repo.get_by_id(inventario_id)
        if not inventario:
            return False, f"No se encontró el inventario {inventario_id}", None

        if inventario['estado'] == 'FINALIZADO':
            return False, "Este inventario ya está finalizado", None

        # Obtener estadísticas
        stats = inventarios_repo.get_estadisticas_inventario(inventario_id)

        if stats['lineas_contadas'] == 0:
            return False, "No se ha contado ningún artículo. No se puede finalizar", None

        # Si se deben aplicar ajustes
        if aplicar_ajustes:
            diferencias = inventarios_repo.get_diferencias(inventario_id)

            if diferencias:
                # Crear movimientos de ajuste por inventario
                from src.repos.movimientos_repo import crear_movimientos_batch

                movimientos = []
                fecha_hoy = date.today().isoformat()

                for diff in diferencias:
                    if diff['diferencia'] > 0:
                        # Sobrante: crear ENTRADA
                        movimientos.append({
                            'tipo': 'ENTRADA',
                            'fecha': fecha_hoy,
                            'articulo_id': diff['articulo_id'],
                            'destino_id': inventario['almacen_id'],
                            'cantidad': abs(diff['diferencia']),
                            'coste_unit': None,
                            'albaran': f"INV-{inventario_id}",
                            'responsable': f"Ajuste Inventario {inventario_id}"
                        })
                    elif diff['diferencia'] < 0:
                        # Faltante: crear PERDIDA
                        movimientos.append({
                            'tipo': 'PERDIDA',
                            'fecha': fecha_hoy,
                            'articulo_id': diff['articulo_id'],
                            'origen_id': inventario['almacen_id'],
                            'cantidad': abs(diff['diferencia']),
                            'motivo': f"Ajuste por inventario {inventario_id}",
                            'responsable': usuario
                        })

                # Crear movimientos en batch
                crear_movimientos_batch(movimientos)

                logger.info(
                    f"Inventario {inventario_id} | Ajustes aplicados | "
                    f"Movimientos creados: {len(movimientos)}"
                )

        # Marcar como finalizado
        fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        inventarios_repo.finalizar_inventario(inventario_id, fecha_cierre)

        # Logging
        detalles = (
            f"Inventario ID: {inventario_id}, "
            f"Total líneas: {stats['total_lineas']}, "
            f"Contadas: {stats['lineas_contadas']}, "
            f"Con diferencia: {stats['lineas_con_diferencia']}, "
            f"Ajustes aplicados: {'Sí' if aplicar_ajustes else 'No'}"
        )
        log_operacion("inventarios", "finalizar", usuario, detalles)
        logger.info(f"Inventario finalizado | ID: {inventario_id}")

        mensaje = (
            f"Inventario finalizado correctamente.\n"
            f"Líneas contadas: {stats['lineas_contadas']}/{stats['total_lineas']}\n"
            f"Diferencias encontradas: {stats['lineas_con_diferencia']}"
        )

        if aplicar_ajustes and stats['lineas_con_diferencia'] > 0:
            mensaje += f"\n\nSe han aplicado {stats['lineas_con_diferencia']} ajuste(s) al stock"

        return True, mensaje, stats

    except Exception as e:
        log_error_bd("inventarios", "finalizar_inventario", e)
        return False, f"Error al finalizar inventario: {str(e)}", None


def cancelar_inventario(
    inventario_id: int,
    motivo: str,
    usuario: str
) -> Tuple[bool, str]:
    """
    Cancela un inventario en proceso (NO IMPLEMENTADO - futuro).

    Args:
        inventario_id: ID del inventario
        motivo: Motivo de la cancelación
        usuario: Usuario que cancela

    Returns:
        Tupla (exito, mensaje)
    """
    # TODO: Implementar cancelación de inventarios
    return False, "Funcionalidad no implementada aún"


# ========================================
# CONSULTAS Y REPORTES
# ========================================

def obtener_inventarios(
    estado: Optional[str] = None,
    almacen_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de inventarios con filtros.

    Args:
        estado: Filtrar por estado
        almacen_id: Filtrar por almacén
        limit: Límite de resultados

    Returns:
        Lista de inventarios
    """
    try:
        return inventarios_repo.get_todos(
            estado=estado,
            almacen_id=almacen_id,
            limit=limit
        )
    except Exception as e:
        log_error_bd("inventarios", "obtener_inventarios", e)
        return []


def obtener_detalle_inventario(inventario_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle completo de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Lista de líneas del inventario
    """
    try:
        return inventarios_repo.get_detalle(inventario_id)
    except Exception as e:
        log_error_bd("inventarios", "obtener_detalle", e)
        return []


def obtener_estadisticas(inventario_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return inventarios_repo.get_estadisticas_inventario(inventario_id)
    except Exception as e:
        log_error_bd("inventarios", "obtener_estadisticas", e)
        return None


def obtener_diferencias(inventario_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene solo las líneas con diferencias de un inventario.

    Args:
        inventario_id: ID del inventario

    Returns:
        Lista de líneas con diferencia != 0
    """
    try:
        return inventarios_repo.get_diferencias(inventario_id)
    except Exception as e:
        log_error_bd("inventarios", "obtener_diferencias", e)
        return []


def obtener_articulos_sin_inventario(dias: int = 90) -> List[Dict[str, Any]]:
    """
    Obtiene artículos que no han sido inventariados recientemente.

    Args:
        dias: Días de antigüedad

    Returns:
        Lista de artículos sin inventario reciente
    """
    try:
        return inventarios_repo.get_articulos_sin_inventario_reciente(dias)
    except Exception as e:
        log_error_bd("inventarios", "obtener_articulos_sin_inventario", e)
        return []


def verificar_inventario_abierto(responsable: str) -> Optional[Dict[str, Any]]:
    """
    Verifica si un usuario tiene un inventario abierto.

    Args:
        responsable: Nombre del responsable

    Returns:
        Inventario abierto o None
    """
    try:
        return inventarios_repo.get_inventario_abierto_usuario(responsable)
    except Exception as e:
        log_error_bd("inventarios", "verificar_inventario_abierto", e)
        return None
