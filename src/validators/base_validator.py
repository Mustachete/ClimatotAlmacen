# -*- coding: utf-8 -*-
"""
Validador base con métodos comunes reutilizables.
"""

from typing import Any, Optional
from src.core.exceptions import (
    ValidationError,
    RequiredFieldError,
    InvalidValueError,
    RangeError
)


class BaseValidator:
    """
    Clase base para validadores.
    Proporciona métodos comunes de validación.
    """

    @staticmethod
    def validate_required(valor: Any, campo: str) -> None:
        """
        Valida que un campo requerido no esté vacío.

        Args:
            valor: Valor a validar
            campo: Nombre del campo

        Raises:
            RequiredFieldError: Si el campo está vacío
        """
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise RequiredFieldError(campo)

    @staticmethod
    def validate_positive(valor: float, campo: str) -> None:
        """
        Valida que un valor numérico sea positivo.

        Args:
            valor: Valor a validar
            campo: Nombre del campo

        Raises:
            InvalidValueError: Si el valor no es positivo
        """
        if valor is None:
            raise RequiredFieldError(campo)

        try:
            valor_float = float(valor)
            if valor_float <= 0:
                raise InvalidValueError(
                    campo,
                    valor,
                    "debe ser un número positivo mayor a cero"
                )
        except (ValueError, TypeError):
            raise InvalidValueError(campo, valor, "debe ser un número válido")

    @staticmethod
    def validate_non_negative(valor: float, campo: str) -> None:
        """
        Valida que un valor numérico sea mayor o igual a cero.

        Args:
            valor: Valor a validar
            campo: Nombre del campo

        Raises:
            InvalidValueError: Si el valor es negativo
        """
        if valor is None:
            raise RequiredFieldError(campo)

        try:
            valor_float = float(valor)
            if valor_float < 0:
                raise InvalidValueError(
                    campo,
                    valor,
                    "no puede ser negativo"
                )
        except (ValueError, TypeError):
            raise InvalidValueError(campo, valor, "debe ser un número válido")

    @staticmethod
    def validate_range(valor: float, campo: str, minimo: float = None, maximo: float = None) -> None:
        """
        Valida que un valor esté dentro de un rango.

        Args:
            valor: Valor a validar
            campo: Nombre del campo
            minimo: Valor mínimo permitido (opcional)
            maximo: Valor máximo permitido (opcional)

        Raises:
            RangeError: Si el valor está fuera de rango
        """
        if valor is None:
            raise RequiredFieldError(campo)

        try:
            valor_float = float(valor)
            if minimo is not None and valor_float < minimo:
                raise RangeError(campo, valor, minimo=minimo)
            if maximo is not None and valor_float > maximo:
                raise RangeError(campo, valor, maximo=maximo)
        except (ValueError, TypeError):
            raise InvalidValueError(campo, valor, "debe ser un número válido")

    @staticmethod
    def validate_string_length(valor: str, campo: str, min_len: int = None, max_len: int = None) -> None:
        """
        Valida la longitud de un string.

        Args:
            valor: String a validar
            campo: Nombre del campo
            min_len: Longitud mínima (opcional)
            max_len: Longitud máxima (opcional)

        Raises:
            ValidationError: Si la longitud no es válida
        """
        if valor is None:
            raise RequiredFieldError(campo)

        if not isinstance(valor, str):
            raise InvalidValueError(campo, valor, "debe ser texto")

        longitud = len(valor.strip())

        if min_len is not None and longitud < min_len:
            raise ValidationError(
                campo,
                f"debe tener al menos {min_len} caracteres (actual: {longitud})"
            )

        if max_len is not None and longitud > max_len:
            raise ValidationError(
                campo,
                f"no puede exceder {max_len} caracteres (actual: {longitud})"
            )

    @staticmethod
    def validate_id(valor: Any, campo: str) -> None:
        """
        Valida que un ID sea un entero positivo.

        Args:
            valor: ID a validar
            campo: Nombre del campo

        Raises:
            InvalidValueError: Si el ID no es válido
        """
        if valor is None:
            raise RequiredFieldError(campo)

        try:
            id_int = int(valor)
            if id_int <= 0:
                raise InvalidValueError(campo, valor, "debe ser un número positivo")
        except (ValueError, TypeError):
            raise InvalidValueError(campo, valor, "debe ser un ID válido")

    @staticmethod
    def validate_choice(valor: Any, campo: str, opciones: list) -> None:
        """
        Valida que un valor esté dentro de una lista de opciones permitidas.

        Args:
            valor: Valor a validar
            campo: Nombre del campo
            opciones: Lista de valores permitidos

        Raises:
            InvalidValueError: Si el valor no está en las opciones
        """
        if valor is None:
            raise RequiredFieldError(campo)

        if valor not in opciones:
            opciones_str = ", ".join([str(o) for o in opciones])
            raise InvalidValueError(
                campo,
                valor,
                f"debe ser uno de: {opciones_str}"
            )
