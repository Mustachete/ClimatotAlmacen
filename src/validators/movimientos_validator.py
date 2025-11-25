# -*- coding: utf-8 -*-
"""
Validador para operaciones de movimientos de almacén.
"""

from typing import Optional
from .base_validator import BaseValidator
from src.core.exceptions import ValidationError, InvalidValueError


class MovimientosValidator(BaseValidator):
    """
    Validador para movimientos de almacén (entradas, traspasos, imputaciones, etc.)
    """

    TIPOS_VALIDOS = ['ENTRADA', 'TRASPASO', 'IMPUTACION', 'PERDIDA', 'DEVOLUCION']

    @classmethod
    def validate_entrada(
        cls,
        articulo_id: int,
        cantidad: float,
        almacen_destino_id: int,
        proveedor_id: Optional[int] = None,
        coste_unit: Optional[float] = None
    ) -> None:
        """
        Valida los datos de una entrada de material.

        Args:
            articulo_id: ID del artículo
            cantidad: Cantidad a recibir
            almacen_destino_id: ID del almacén destino
            proveedor_id: ID del proveedor (opcional)
            coste_unit: Coste unitario (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        # Validaciones básicas
        cls.validate_id(articulo_id, "Artículo")
        cls.validate_positive(cantidad, "Cantidad")
        cls.validate_id(almacen_destino_id, "Almacén destino")

        # Validaciones opcionales
        if proveedor_id is not None:
            cls.validate_id(proveedor_id, "Proveedor")

        if coste_unit is not None:
            cls.validate_non_negative(coste_unit, "Coste unitario")

    @classmethod
    def validate_traspaso(
        cls,
        articulo_id: int,
        cantidad: float,
        almacen_origen_id: int,
        almacen_destino_id: int
    ) -> None:
        """
        Valida los datos de un traspaso entre almacenes.

        Args:
            articulo_id: ID del artículo
            cantidad: Cantidad a traspasar
            almacen_origen_id: ID del almacén origen
            almacen_destino_id: ID del almacén destino

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_id(articulo_id, "Artículo")
        cls.validate_positive(cantidad, "Cantidad")
        cls.validate_id(almacen_origen_id, "Almacén origen")
        cls.validate_id(almacen_destino_id, "Almacén destino")

        # No se puede traspasar al mismo almacén
        if almacen_origen_id == almacen_destino_id:
            raise ValidationError(
                "Almacenes",
                "El almacén origen y destino no pueden ser el mismo"
            )

    @classmethod
    def validate_imputacion(
        cls,
        articulo_id: int,
        cantidad: float,
        almacen_origen_id: int,
        ot: Optional[str] = None,
        operario_id: Optional[int] = None
    ) -> None:
        """
        Valida los datos de una imputación de material a OT.

        Args:
            articulo_id: ID del artículo
            cantidad: Cantidad a imputar
            almacen_origen_id: ID del almacén origen
            ot: Número de orden de trabajo (opcional)
            operario_id: ID del operario (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_id(articulo_id, "Artículo")
        cls.validate_positive(cantidad, "Cantidad")
        cls.validate_id(almacen_origen_id, "Almacén origen")

        if ot is not None and ot.strip():
            cls.validate_string_length(ot, "OT", max_len=100)

        if operario_id is not None:
            cls.validate_id(operario_id, "Operario")

    @classmethod
    def validate_devolucion(
        cls,
        articulo_id: int,
        cantidad: float,
        almacen_origen_id: int,
        proveedor_id: Optional[int] = None,
        motivo: Optional[str] = None
    ) -> None:
        """
        Valida los datos de una devolución a proveedor.

        Args:
            articulo_id: ID del artículo
            cantidad: Cantidad a devolver
            almacen_origen_id: ID del almacén origen
            proveedor_id: ID del proveedor (opcional)
            motivo: Motivo de la devolución (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_id(articulo_id, "Artículo")
        cls.validate_positive(cantidad, "Cantidad")
        cls.validate_id(almacen_origen_id, "Almacén origen")

        if proveedor_id is not None:
            cls.validate_id(proveedor_id, "Proveedor")

        if motivo is not None and motivo.strip():
            cls.validate_string_length(motivo, "Motivo", max_len=500)

    @classmethod
    def validate_perdida(
        cls,
        articulo_id: int,
        cantidad: float,
        almacen_origen_id: int,
        motivo: Optional[str] = None
    ) -> None:
        """
        Valida los datos de un registro de material perdido.

        Args:
            articulo_id: ID del artículo
            cantidad: Cantidad perdida
            almacen_origen_id: ID del almacén origen
            motivo: Motivo de la pérdida (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_id(articulo_id, "Artículo")
        cls.validate_positive(cantidad, "Cantidad")
        cls.validate_id(almacen_origen_id, "Almacén origen")

        if motivo is not None and motivo.strip():
            cls.validate_string_length(motivo, "Motivo", max_len=500)

    @classmethod
    def validate_tipo_movimiento(cls, tipo: str) -> None:
        """
        Valida que el tipo de movimiento sea válido.

        Args:
            tipo: Tipo de movimiento

        Raises:
            ValidationError: Si el tipo no es válido
        """
        cls.validate_required(tipo, "Tipo de movimiento")
        cls.validate_choice(tipo, "Tipo de movimiento", cls.TIPOS_VALIDOS)

    @classmethod
    def validate_fecha(cls, fecha: str) -> None:
        """
        Valida el formato de una fecha (YYYY-MM-DD).

        Args:
            fecha: Fecha en formato ISO

        Raises:
            ValidationError: Si la fecha no es válida
        """
        from datetime import datetime

        cls.validate_required(fecha, "Fecha")

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise InvalidValueError(
                "Fecha",
                fecha,
                "debe tener formato YYYY-MM-DD"
            )
