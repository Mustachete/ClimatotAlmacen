"""
Servicio de Artículos - Lógica de negocio para gestión de artículos del almacén
"""
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from src.repos import articulos_repo
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


# ========================================
# VALIDACIONES
# ========================================

def validar_nombre(nombre: str) -> Tuple[bool, str]:
    """
    Valida que el nombre del artículo sea válido.

    Args:
        nombre: Nombre del artículo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not nombre or not nombre.strip():
        log_validacion("articulos", "nombre", "Nombre vacío")
        return False, "El nombre del artículo es obligatorio"

    if len(nombre.strip()) < 3:
        log_validacion("articulos", "nombre", f"Nombre muy corto: {nombre}")
        return False, "El nombre debe tener al menos 3 caracteres"

    if len(nombre.strip()) > 200:
        log_validacion("articulos", "nombre", f"Nombre muy largo: {len(nombre)} caracteres")
        return False, "El nombre no puede exceder 200 caracteres"

    return True, ""


def validar_ean(ean: Optional[str], articulo_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Valida que el código EAN sea válido y único.

    Args:
        ean: Código EAN (puede ser None)
        articulo_id: ID del artículo (para edición, permite el mismo EAN)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not ean or not ean.strip():
        return True, ""  # EAN es opcional

    ean = ean.strip()

    # Verificar longitud (EAN-8, EAN-13 son los más comunes)
    if len(ean) not in [8, 13]:
        log_validacion("articulos", "ean", f"Longitud inválida: {len(ean)}")
        return False, "El código EAN debe tener 8 o 13 dígitos"

    # Verificar que sea numérico
    if not ean.isdigit():
        log_validacion("articulos", "ean", f"Contiene caracteres no numéricos: {ean}")
        return False, "El código EAN solo puede contener números"

    # Verificar unicidad
    existente = articulos_repo.get_by_ean(ean)
    if existente:
        # Si estamos editando y es el mismo artículo, está bien
        if articulo_id and existente['id'] == articulo_id:
            return True, ""
        log_validacion("articulos", "ean", f"EAN duplicado: {ean}")
        return False, f"Ya existe un artículo con el EAN '{ean}': {existente['nombre']}"

    return True, ""


def validar_referencia(ref: Optional[str], articulo_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Valida que la referencia del proveedor sea única.

    Args:
        ref: Referencia del proveedor (puede ser None)
        articulo_id: ID del artículo (para edición)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not ref or not ref.strip():
        return True, ""  # Referencia es opcional

    ref = ref.strip()

    # Verificar longitud razonable
    if len(ref) > 100:
        log_validacion("articulos", "referencia", f"Referencia muy larga: {len(ref)}")
        return False, "La referencia no puede exceder 100 caracteres"

    # Verificar unicidad
    existente = articulos_repo.get_by_referencia(ref)
    if existente:
        # Si estamos editando y es el mismo artículo, está bien
        if articulo_id and existente['id'] == articulo_id:
            return True, ""
        log_validacion("articulos", "referencia", f"Referencia duplicada: {ref}")
        return False, f"Ya existe un artículo con la referencia '{ref}': {existente['nombre']}"

    return True, ""


def validar_precios(coste: float, pvp: float) -> Tuple[bool, str]:
    """
    Valida que los precios sean válidos.

    Args:
        coste: Coste de compra
        pvp: PVP sin IVA

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if coste < 0:
        log_validacion("articulos", "coste", f"Coste negativo: {coste}")
        return False, "El coste no puede ser negativo"

    if pvp < 0:
        log_validacion("articulos", "pvp", f"PVP negativo: {pvp}")
        return False, "El PVP no puede ser negativo"

    if coste > 0 and pvp > 0 and pvp < coste:
        # Advertencia, pero no error bloqueante
        logger.warning(f"Artículo con PVP ({pvp}) menor que coste ({coste})")

    return True, ""


def validar_stock_minimo(min_alerta: float) -> Tuple[bool, str]:
    """
    Valida que el stock mínimo sea válido.

    Args:
        min_alerta: Stock mínimo para alerta

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if min_alerta < 0:
        log_validacion("articulos", "min_alerta", f"Stock mínimo negativo: {min_alerta}")
        return False, "El stock mínimo no puede ser negativo"

    if min_alerta > 999999:
        log_validacion("articulos", "min_alerta", f"Stock mínimo excesivo: {min_alerta}")
        return False, "El stock mínimo es demasiado grande"

    return True, ""


# ========================================
# OPERACIONES DE ARTÍCULOS
# ========================================

def crear_articulo(
    nombre: str,
    ean: Optional[str] = None,
    ref_proveedor: Optional[str] = None,
    palabras_clave: Optional[str] = None,
    u_medida: str = "unidad",
    min_alerta: float = 0,
    ubicacion_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    familia_id: Optional[int] = None,
    marca: Optional[str] = None,
    coste: float = 0,
    pvp_sin: float = 0,
    iva: float = 21,
    activo: bool = True,
    usuario: str = "admin"
) -> Tuple[bool, str, Optional[int]]:
    """
    Crea un nuevo artículo con validaciones.

    Args:
        nombre: Nombre del artículo (obligatorio)
        ean: Código EAN (opcional, debe ser único)
        ref_proveedor: Referencia del proveedor (opcional, debe ser única)
        palabras_clave: Palabras clave para búsqueda
        u_medida: Unidad de medida
        min_alerta: Stock mínimo para alertas
        ubicacion_id: ID de la ubicación
        proveedor_id: ID del proveedor principal
        familia_id: ID de la familia
        marca: Marca del producto
        coste: Coste de compra
        pvp_sin: PVP sin IVA
        iva: Porcentaje de IVA
        activo: Si está activo
        usuario: Usuario que crea el artículo

    Returns:
        Tupla (exito, mensaje, articulo_id)
    """
    try:
        # Validar nombre
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error, None

        # Validar EAN
        valido, error = validar_ean(ean)
        if not valido:
            return False, error, None

        # Validar referencia
        valido, error = validar_referencia(ref_proveedor)
        if not valido:
            return False, error, None

        # Validar precios
        valido, error = validar_precios(coste, pvp_sin)
        if not valido:
            return False, error, None

        # Validar stock mínimo
        valido, error = validar_stock_minimo(min_alerta)
        if not valido:
            return False, error, None

        # Normalizar campos opcionales
        nombre = nombre.strip()
        ean = ean.strip() if ean else None
        ref_proveedor = ref_proveedor.strip() if ref_proveedor else None
        palabras_clave = palabras_clave.strip() if palabras_clave else None
        marca = marca.strip() if marca else None

        # Crear artículo
        articulo_id = articulos_repo.crear_articulo(
            nombre=nombre,
            ean=ean,
            ref_proveedor=ref_proveedor,
            palabras_clave=palabras_clave,
            u_medida=u_medida,
            min_alerta=min_alerta,
            ubicacion_id=ubicacion_id,
            proveedor_id=proveedor_id,
            familia_id=familia_id,
            marca=marca,
            coste=coste,
            pvp_sin=pvp_sin,
            iva=iva,
            activo=activo
        )

        # Logging
        detalles = (
            f"Artículo ID: {articulo_id}, Nombre: {nombre}, "
            f"EAN: {ean or 'N/A'}, Ref: {ref_proveedor or 'N/A'}"
        )
        log_operacion("articulos", "crear", usuario, detalles)
        logger.info(f"Artículo creado | ID: {articulo_id} | {nombre}")

        return True, f"Artículo '{nombre}' creado correctamente", articulo_id

    except psycopg2.IntegrityError as e:
        error_msg = str(e).lower()
        if "ean" in error_msg:
            mensaje = f"Ya existe un artículo con el EAN '{ean}'"
        elif "ref_proveedor" in error_msg:
            mensaje = f"Ya existe un artículo con la referencia '{ref_proveedor}'"
        else:
            mensaje = "Ya existe un artículo con esos datos únicos"

        log_error_bd("articulos", "crear_articulo", e)
        return False, mensaje, None

    except Exception as e:
        log_error_bd("articulos", "crear_articulo", e)
        return False, f"Error al crear artículo: {str(e)}", None


def actualizar_articulo(
    articulo_id: int,
    nombre: str,
    ean: Optional[str] = None,
    ref_proveedor: Optional[str] = None,
    palabras_clave: Optional[str] = None,
    u_medida: str = "unidad",
    min_alerta: float = 0,
    ubicacion_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    familia_id: Optional[int] = None,
    marca: Optional[str] = None,
    coste: float = 0,
    pvp_sin: float = 0,
    iva: float = 21,
    activo: bool = True,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Actualiza un artículo existente con validaciones.

    Args:
        articulo_id: ID del artículo a actualizar
        (resto de parámetros igual que crear_articulo)

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que el artículo existe
        articulo = articulos_repo.get_by_id(articulo_id)
        if not articulo:
            return False, f"No se encontró el artículo con ID {articulo_id}"

        # Validar nombre
        valido, error = validar_nombre(nombre)
        if not valido:
            return False, error

        # Validar EAN (pasando el ID para permitir el mismo EAN)
        valido, error = validar_ean(ean, articulo_id)
        if not valido:
            return False, error

        # Validar referencia
        valido, error = validar_referencia(ref_proveedor, articulo_id)
        if not valido:
            return False, error

        # Validar precios
        valido, error = validar_precios(coste, pvp_sin)
        if not valido:
            return False, error

        # Validar stock mínimo
        valido, error = validar_stock_minimo(min_alerta)
        if not valido:
            return False, error

        # Normalizar campos
        nombre = nombre.strip()
        ean = ean.strip() if ean else None
        ref_proveedor = ref_proveedor.strip() if ref_proveedor else None
        palabras_clave = palabras_clave.strip() if palabras_clave else None
        marca = marca.strip() if marca else None

        # Actualizar artículo
        articulos_repo.actualizar_articulo(
            articulo_id=articulo_id,
            nombre=nombre,
            ean=ean,
            ref_proveedor=ref_proveedor,
            palabras_clave=palabras_clave,
            u_medida=u_medida,
            min_alerta=min_alerta,
            ubicacion_id=ubicacion_id,
            proveedor_id=proveedor_id,
            familia_id=familia_id,
            marca=marca,
            coste=coste,
            pvp_sin=pvp_sin,
            iva=iva,
            activo=activo
        )

        # Logging
        detalles = f"Artículo ID: {articulo_id}, Nombre: {nombre}"
        log_operacion("articulos", "actualizar", usuario, detalles)
        logger.info(f"Artículo actualizado | ID: {articulo_id} | {nombre}")

        return True, f"Artículo '{nombre}' actualizado correctamente"

    except psycopg2.IntegrityError as e:
        error_msg = str(e).lower()
        if "ean" in error_msg:
            mensaje = f"Ya existe otro artículo con el EAN '{ean}'"
        elif "ref_proveedor" in error_msg:
            mensaje = f"Ya existe otro artículo con la referencia '{ref_proveedor}'"
        else:
            mensaje = "Ya existe otro artículo con esos datos únicos"

        log_error_bd("articulos", "actualizar_articulo", e)
        return False, mensaje

    except Exception as e:
        log_error_bd("articulos", "actualizar_articulo", e)
        return False, f"Error al actualizar artículo: {str(e)}"


def eliminar_articulo(
    articulo_id: int,
    usuario: str = "admin"
) -> Tuple[bool, str]:
    """
    Elimina un artículo.

    Args:
        articulo_id: ID del artículo
        usuario: Usuario que elimina

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        # Verificar que existe
        articulo = articulos_repo.get_by_id(articulo_id)
        if not articulo:
            return False, f"No se encontró el artículo con ID {articulo_id}"

        nombre = articulo['nombre']

        # Verificar si tiene movimientos
        tiene_movimientos = articulos_repo.verificar_movimientos(articulo_id)
        if tiene_movimientos:
            return False, (
                f"El artículo '{nombre}' tiene movimientos asociados.\n\n"
                "No se puede eliminar. En su lugar, puede marcarlo como 'Inactivo'."
            )

        # Eliminar
        articulos_repo.eliminar_articulo(articulo_id)

        # Logging
        detalles = f"Artículo ID: {articulo_id}, Nombre: {nombre}"
        log_operacion("articulos", "eliminar", usuario, detalles)
        logger.info(f"Artículo eliminado | ID: {articulo_id} | {nombre}")

        return True, f"Artículo '{nombre}' eliminado correctamente"

    except psycopg2.IntegrityError:
        # Por si acaso la verificación previa no funcionó
        return False, (
            f"El artículo tiene movimientos asociados.\n\n"
            "No se puede eliminar. Márquelo como 'Inactivo' en su lugar."
        )

    except Exception as e:
        log_error_bd("articulos", "eliminar_articulo", e)
        return False, f"Error al eliminar artículo: {str(e)}"


def activar_articulo(articulo_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """
    Activa un artículo.

    Args:
        articulo_id: ID del artículo
        usuario: Usuario que activa

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        articulo = articulos_repo.get_by_id(articulo_id)
        if not articulo:
            return False, f"No se encontró el artículo con ID {articulo_id}"

        articulos_repo.activar_desactivar_articulo(articulo_id, True)

        detalles = f"Artículo ID: {articulo_id}, Nombre: {articulo['nombre']}"
        log_operacion("articulos", "activar", usuario, detalles)

        return True, f"Artículo '{articulo['nombre']}' activado"

    except Exception as e:
        log_error_bd("articulos", "activar_articulo", e)
        return False, f"Error al activar artículo: {str(e)}"


def desactivar_articulo(articulo_id: int, usuario: str = "admin") -> Tuple[bool, str]:
    """
    Desactiva un artículo.

    Args:
        articulo_id: ID del artículo
        usuario: Usuario que desactiva

    Returns:
        Tupla (exito, mensaje)
    """
    try:
        articulo = articulos_repo.get_by_id(articulo_id)
        if not articulo:
            return False, f"No se encontró el artículo con ID {articulo_id}"

        articulos_repo.activar_desactivar_articulo(articulo_id, False)

        detalles = f"Artículo ID: {articulo_id}, Nombre: {articulo['nombre']}"
        log_operacion("articulos", "desactivar", usuario, detalles)

        return True, f"Artículo '{articulo['nombre']}' desactivado"

    except Exception as e:
        log_error_bd("articulos", "desactivar_articulo", e)
        return False, f"Error al desactivar artículo: {str(e)}"


# ========================================
# CONSULTAS Y REPORTES
# ========================================

def obtener_articulos(
    filtro_texto: Optional[str] = None,
    familia_id: Optional[int] = None,
    solo_activos: Optional[bool] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de artículos con filtros.

    Args:
        filtro_texto: Búsqueda por nombre, EAN, referencia o palabras clave
        familia_id: Filtrar por familia
        solo_activos: Si True solo activos, si False solo inactivos, si None todos
        limit: Límite de resultados

    Returns:
        Lista de artículos
    """
    try:
        return articulos_repo.get_todos(
            filtro_texto=filtro_texto,
            familia_id=familia_id,
            solo_activos=solo_activos,
            limit=limit
        )
    except Exception as e:
        log_error_bd("articulos", "obtener_articulos", e)
        return []


def obtener_articulo(articulo_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un artículo específico por ID.

    Args:
        articulo_id: ID del artículo

    Returns:
        Diccionario con información del artículo o None
    """
    try:
        return articulos_repo.get_by_id(articulo_id)
    except Exception as e:
        log_error_bd("articulos", "obtener_articulo", e)
        return None


def obtener_articulos_bajo_minimo() -> List[Dict[str, Any]]:
    """
    Obtiene artículos con stock por debajo del mínimo configurado.

    Returns:
        Lista de artículos con stock bajo
    """
    try:
        return articulos_repo.get_articulos_bajo_minimo()
    except Exception as e:
        log_error_bd("articulos", "obtener_articulos_bajo_minimo", e)
        return []


def obtener_estadisticas() -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas generales de artículos.

    Returns:
        Diccionario con estadísticas o None
    """
    try:
        return articulos_repo.get_estadisticas_articulos()
    except Exception as e:
        log_error_bd("articulos", "obtener_estadisticas", e)
        return None
