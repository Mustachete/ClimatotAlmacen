"""
Módulo de Validaciones Centralizadas
Funciones reutilizables para validar datos en toda la aplicación.
"""
from typing import Tuple
from datetime import date, datetime
import re


# ========================================
# VALIDACIONES DE CAMPOS DE TEXTO
# ========================================

def validar_campo_obligatorio(valor: str, nombre_campo: str = "campo") -> Tuple[bool, str]:
    """
    Valida que un campo de texto no esté vacío.

    Args:
        valor: Valor a validar
        nombre_campo: Nombre descriptivo del campo para el mensaje de error

    Returns:
        Tupla (es_valido, mensaje_error)

    Ejemplos:
        >>> validar_campo_obligatorio("", "nombre")
        (False, "El nombre es obligatorio")
        >>> validar_campo_obligatorio("Juan", "nombre")
        (True, "")
    """
    if not valor or not valor.strip():
        return False, f"El {nombre_campo} es obligatorio"
    return True, ""


def validar_longitud_minima(valor: str, minimo: int, nombre_campo: str = "campo") -> Tuple[bool, str]:
    """
    Valida que un campo tenga una longitud mínima.

    Args:
        valor: Valor a validar
        minimo: Longitud mínima requerida
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if len(valor.strip()) < minimo:
        return False, f"El {nombre_campo} debe tener al menos {minimo} caracteres"
    return True, ""


def validar_longitud_maxima(valor: str, maximo: int, nombre_campo: str = "campo") -> Tuple[bool, str]:
    """
    Valida que un campo no exceda una longitud máxima.

    Args:
        valor: Valor a validar
        maximo: Longitud máxima permitida
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if len(valor.strip()) > maximo:
        return False, f"El {nombre_campo} no puede exceder {maximo} caracteres"
    return True, ""


# ========================================
# VALIDACIONES NUMÉRICAS
# ========================================

def validar_numero_positivo(valor: str, nombre_campo: str = "valor") -> Tuple[bool, str]:
    """
    Valida que un valor sea un número positivo.

    Args:
        valor: Valor a validar (puede ser string)
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        numero = float(valor)
        if numero <= 0:
            return False, f"El {nombre_campo} debe ser mayor que 0"
        return True, ""
    except (ValueError, TypeError):
        return False, f"El {nombre_campo} debe ser un número válido"


def validar_cantidad(cantidad: float, minimo: float = 0, maximo: float = 999999) -> Tuple[bool, str]:
    """
    Valida que una cantidad esté dentro de rangos válidos.

    Args:
        cantidad: Cantidad a validar
        minimo: Valor mínimo permitido (exclusivo)
        maximo: Valor máximo permitido (inclusivo)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if cantidad <= minimo:
        return False, f"La cantidad debe ser mayor que {minimo}"

    if cantidad > maximo:
        return False, f"La cantidad no puede exceder {maximo}"

    return True, ""


def validar_rango_numerico(valor: float, minimo: float, maximo: float, nombre_campo: str = "valor") -> Tuple[bool, str]:
    """
    Valida que un número esté dentro de un rango específico.

    Args:
        valor: Valor numérico a validar
        minimo: Valor mínimo permitido (inclusivo)
        maximo: Valor máximo permitido (inclusivo)
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if valor < minimo or valor > maximo:
        return False, f"El {nombre_campo} debe estar entre {minimo} y {maximo}"
    return True, ""


def validar_entero_positivo(valor: str, nombre_campo: str = "valor") -> Tuple[bool, str]:
    """
    Valida que un valor sea un entero positivo.

    Args:
        valor: Valor a validar
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        numero = int(valor)
        if numero <= 0:
            return False, f"El {nombre_campo} debe ser un entero positivo"
        return True, ""
    except (ValueError, TypeError):
        return False, f"El {nombre_campo} debe ser un número entero válido"


# ========================================
# VALIDACIONES DE FECHA
# ========================================

def validar_fecha_formato(fecha: str, formato: str = "%Y-%m-%d") -> Tuple[bool, str]:
    """
    Valida que una fecha tenga el formato correcto.

    Args:
        fecha: Fecha en string
        formato: Formato esperado (por defecto: YYYY-MM-DD)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        datetime.strptime(fecha, formato)
        return True, ""
    except ValueError:
        return False, f"Formato de fecha inválido (use {formato})"


def validar_fecha_no_futura(fecha: str, formato: str = "%Y-%m-%d") -> Tuple[bool, str]:
    """
    Valida que una fecha no sea futura.

    Args:
        fecha: Fecha en string
        formato: Formato de la fecha

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        fecha_obj = datetime.strptime(fecha, formato).date()
        if fecha_obj > date.today():
            return False, "La fecha no puede ser futura"
        return True, ""
    except ValueError:
        return False, f"Formato de fecha inválido (use {formato})"


def validar_fecha_rango(fecha: str, fecha_minima: str = None, fecha_maxima: str = None, formato: str = "%Y-%m-%d") -> Tuple[bool, str]:
    """
    Valida que una fecha esté dentro de un rango.

    Args:
        fecha: Fecha a validar
        fecha_minima: Fecha mínima permitida (opcional)
        fecha_maxima: Fecha máxima permitida (opcional)
        formato: Formato de las fechas

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    try:
        fecha_obj = datetime.strptime(fecha, formato).date()

        if fecha_minima:
            fecha_min_obj = datetime.strptime(fecha_minima, formato).date()
            if fecha_obj < fecha_min_obj:
                return False, f"La fecha no puede ser anterior a {fecha_minima}"

        if fecha_maxima:
            fecha_max_obj = datetime.strptime(fecha_maxima, formato).date()
            if fecha_obj > fecha_max_obj:
                return False, f"La fecha no puede ser posterior a {fecha_maxima}"

        return True, ""
    except ValueError:
        return False, f"Formato de fecha inválido (use {formato})"


# ========================================
# VALIDACIONES DE EMAIL Y CONTACTO
# ========================================

def validar_email(email: str, obligatorio: bool = False) -> Tuple[bool, str]:
    """
    Valida el formato de un email.

    Args:
        email: Email a validar
        obligatorio: Si es True, el email no puede estar vacío

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not email or not email.strip():
        if obligatorio:
            return False, "El email es obligatorio"
        return True, ""  # Email opcional y vacío es válido

    # Patrón regex para validar email
    patron = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not re.match(patron, email.strip()):
        return False, "El formato del email no es válido"

    return True, ""


def validar_telefono(telefono: str, obligatorio: bool = False) -> Tuple[bool, str]:
    """
    Valida el formato de un teléfono (admite varios formatos comunes).

    Args:
        telefono: Teléfono a validar
        obligatorio: Si es True, el teléfono no puede estar vacío

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not telefono or not telefono.strip():
        if obligatorio:
            return False, "El teléfono es obligatorio"
        return True, ""

    # Eliminar espacios, guiones y paréntesis
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)

    # Validar que solo contenga dígitos y opcionalmente un + al inicio
    if not re.match(r'^\+?\d{9,15}$', telefono_limpio):
        return False, "El formato del teléfono no es válido"

    return True, ""


# ========================================
# VALIDACIONES DE CÓDIGOS
# ========================================

def validar_codigo_unico(codigo: str, verificar_existencia_func, nombre_campo: str = "código") -> Tuple[bool, str]:
    """
    Valida que un código sea único (no exista en la base de datos).

    Args:
        codigo: Código a validar
        verificar_existencia_func: Función que retorna True si el código existe
        nombre_campo: Nombre descriptivo del campo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if verificar_existencia_func(codigo):
        return False, f"El {nombre_campo} '{codigo}' ya existe"
    return True, ""


def validar_ean(ean: str, obligatorio: bool = False) -> Tuple[bool, str]:
    """
    Valida el formato de un código EAN (8 o 13 dígitos).

    Args:
        ean: Código EAN a validar
        obligatorio: Si es True, el EAN no puede estar vacío

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not ean or not ean.strip():
        if obligatorio:
            return False, "El código EAN es obligatorio"
        return True, ""

    ean_limpio = ean.strip()

    # Validar que solo contenga dígitos y sea de 8 o 13 caracteres
    if not re.match(r'^\d{8}$|^\d{13}$', ean_limpio):
        return False, "El código EAN debe tener 8 o 13 dígitos"

    return True, ""


# ========================================
# VALIDACIONES COMBINADAS
# ========================================

def validar_campos_requeridos(datos: dict, campos_requeridos: list) -> Tuple[bool, str]:
    """
    Valida que múltiples campos requeridos no estén vacíos.

    Args:
        datos: Diccionario con los datos a validar
        campos_requeridos: Lista de nombres de campos que son obligatorios

    Returns:
        Tupla (es_valido, mensaje_error)

    Ejemplo:
        >>> datos = {'nombre': 'Juan', 'email': '', 'telefono': '123'}
        >>> validar_campos_requeridos(datos, ['nombre', 'email'])
        (False, "El campo 'email' es obligatorio")
    """
    for campo in campos_requeridos:
        valor = datos.get(campo, "")
        if isinstance(valor, str):
            if not valor or not valor.strip():
                return False, f"El campo '{campo}' es obligatorio"
        elif valor is None:
            return False, f"El campo '{campo}' es obligatorio"

    return True, ""


# ========================================
# VALIDACIONES ESPECÍFICAS DEL DOMINIO
# ========================================

def validar_password_seguro(password: str, minimo_caracteres: int = 6) -> Tuple[bool, str]:
    """
    Valida que una contraseña sea segura.

    Args:
        password: Contraseña a validar
        minimo_caracteres: Número mínimo de caracteres

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not password or len(password) < minimo_caracteres:
        return False, f"La contraseña debe tener al menos {minimo_caracteres} caracteres"

    # Opcional: validar complejidad (mayúsculas, números, símbolos)
    # if not re.search(r'[A-Z]', password):
    #     return False, "La contraseña debe contener al menos una mayúscula"
    # if not re.search(r'[0-9]', password):
    #     return False, "La contraseña debe contener al menos un número"

    return True, ""


def validar_nombre_usuario(username: str) -> Tuple[bool, str]:
    """
    Valida el formato de un nombre de usuario.

    Args:
        username: Nombre de usuario a validar

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not username or len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"

    if len(username) > 30:
        return False, "El nombre de usuario no puede exceder 30 caracteres"

    # Solo letras, números y guión bajo
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números y guión bajo"

    return True, ""


# ========================================
# UTILIDADES
# ========================================

def combinar_validaciones(*resultados_validacion) -> Tuple[bool, str]:
    """
    Combina múltiples resultados de validación.
    Retorna el primer error encontrado, o True si todas son válidas.

    Args:
        *resultados_validacion: Tuplas (es_valido, mensaje) de diferentes validaciones

    Returns:
        Tupla (es_valido, mensaje_error)

    Ejemplo:
        >>> r1 = validar_campo_obligatorio("", "nombre")
        >>> r2 = validar_email("test@test.com")
        >>> combinar_validaciones(r1, r2)
        (False, "El nombre es obligatorio")
    """
    for es_valido, mensaje in resultados_validacion:
        if not es_valido:
            return False, mensaje
    return True, ""
