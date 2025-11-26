# -*- coding: utf-8 -*-
"""
Sistema de excepciones personalizadas para ClimatotAlmacen.
Permite un manejo más específico de errores y mejor debugging.
"""


# ========================================
# EXCEPCIONES BASE
# ========================================

class ClimatotAlmacenError(Exception):
    """Excepción base para todas las excepciones del sistema"""
    def __init__(self, mensaje: str, detalles: str = None):
        self.mensaje = mensaje
        self.detalles = detalles
        super().__init__(self.mensaje)

    def __str__(self):
        if self.detalles:
            return f"{self.mensaje}\nDetalles: {self.detalles}"
        return self.mensaje


# ========================================
# EXCEPCIONES DE BASE DE DATOS
# ========================================

class DatabaseError(ClimatotAlmacenError):
    """Error relacionado con operaciones de base de datos"""
    pass


class ConnectionError(DatabaseError):
    """Error al conectar con la base de datos"""
    pass


class IntegrityError(DatabaseError):
    """Error de integridad referencial (FK violations, unique constraints)"""
    pass


class TransactionError(DatabaseError):
    """Error durante una transacción"""
    pass


# ========================================
# EXCEPCIONES DE VALIDACIÓN
# ========================================

class ValidationError(ClimatotAlmacenError):
    """Error de validación de datos"""
    def __init__(self, campo: str, mensaje: str):
        self.campo = campo
        super().__init__(f"Validación falló en '{campo}': {mensaje}")


class RequiredFieldError(ValidationError):
    """Campo requerido faltante"""
    def __init__(self, campo: str):
        super().__init__(campo, "Este campo es obligatorio")


class InvalidValueError(ValidationError):
    """Valor inválido para un campo"""
    def __init__(self, campo: str, valor, razon: str = None):
        mensaje = f"Valor inválido: {valor}"
        if razon:
            mensaje += f" ({razon})"
        super().__init__(campo, mensaje)


class RangeError(ValidationError):
    """Valor fuera del rango permitido"""
    def __init__(self, campo: str, valor, minimo=None, maximo=None):
        if minimo is not None and maximo is not None:
            mensaje = f"El valor {valor} debe estar entre {minimo} y {maximo}"
        elif minimo is not None:
            mensaje = f"El valor {valor} debe ser mayor o igual a {minimo}"
        elif maximo is not None:
            mensaje = f"El valor {valor} debe ser menor o igual a {maximo}"
        else:
            mensaje = f"Valor {valor} fuera de rango"
        super().__init__(campo, mensaje)


# ========================================
# EXCEPCIONES DE NEGOCIO
# ========================================

class BusinessRuleError(ClimatotAlmacenError):
    """Error al violar una regla de negocio"""
    pass


class InsufficientStockError(BusinessRuleError):
    """Stock insuficiente para realizar operación"""
    def __init__(self, articulo: str, solicitado: float, disponible: float):
        mensaje = (
            f"Stock insuficiente de '{articulo}'. "
            f"Solicitado: {solicitado}, Disponible: {disponible}"
        )
        super().__init__(mensaje)


class DuplicateEntryError(BusinessRuleError):
    """Intento de crear un registro duplicado"""
    def __init__(self, entidad: str, campo: str, valor):
        mensaje = f"Ya existe un/a {entidad} con {campo} = '{valor}'"
        super().__init__(mensaje)


class NotFoundError(BusinessRuleError):
    """Registro no encontrado"""
    def __init__(self, entidad: str, identificador):
        mensaje = f"No se encontró {entidad} con identificador: {identificador}"
        super().__init__(mensaje)


class InactiveEntityError(BusinessRuleError):
    """Intento de operar con una entidad inactiva"""
    def __init__(self, entidad: str, identificador):
        mensaje = f"{entidad} {identificador} está inactivo y no puede ser utilizado"
        super().__init__(mensaje)


# ========================================
# EXCEPCIONES DE AUTENTICACIÓN
# ========================================

class AuthenticationError(ClimatotAlmacenError):
    """Error de autenticación"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Credenciales inválidas"""
    def __init__(self):
        super().__init__("Usuario o contraseña incorrectos")


class UnauthorizedError(AuthenticationError):
    """Usuario no autorizado para realizar la acción"""
    def __init__(self, accion: str):
        super().__init__(f"No tienes permisos para: {accion}")


class SessionExpiredError(AuthenticationError):
    """Sesión expirada"""
    def __init__(self):
        super().__init__("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")


# ========================================
# EXCEPCIONES DE CONFIGURACIÓN
# ========================================

class ConfigurationError(ClimatotAlmacenError):
    """Error de configuración del sistema"""
    pass


class MissingConfigError(ConfigurationError):
    """Configuración requerida faltante"""
    def __init__(self, parametro: str):
        super().__init__(f"Falta parámetro de configuración requerido: {parametro}")


# ========================================
# EXCEPCIONES DE IMPORTACIÓN/EXPORTACIÓN
# ========================================

class ImportExportError(ClimatotAlmacenError):
    """Error durante importación o exportación de datos"""
    pass


class FileFormatError(ImportExportError):
    """Formato de archivo inválido"""
    def __init__(self, archivo: str, formato_esperado: str):
        super().__init__(
            f"El archivo '{archivo}' no tiene el formato esperado: {formato_esperado}"
        )


class DataIntegrityError(ImportExportError):
    """Datos importados no cumplen con integridad"""
    def __init__(self, linea: int, error: str):
        super().__init__(f"Error en línea {linea}: {error}")
