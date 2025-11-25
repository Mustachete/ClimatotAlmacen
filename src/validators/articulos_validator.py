# -*- coding: utf-8 -*-
"""
Validador para artículos.
"""

from typing import Optional
from .base_validator import BaseValidator
from src.core.exceptions import ValidationError


class ArticulosValidator(BaseValidator):
    """
    Validador para operaciones con artículos.
    """

    UNIDADES_MEDIDA_VALIDAS = ['unidad', 'metro', 'kilogramo', 'litro', 'caja', 'paquete']

    @classmethod
    def validate_articulo(
        cls,
        nombre: str,
        ean: Optional[str] = None,
        ref_proveedor: Optional[str] = None,
        u_medida: str = 'unidad',
        coste: Optional[float] = None,
        pvp_sin: Optional[float] = None,
        iva: Optional[float] = None,
        min_alerta: Optional[float] = None
    ) -> None:
        """
        Valida los datos de un artículo.

        Args:
            nombre: Nombre del artículo
            ean: Código EAN/código de barras (opcional)
            ref_proveedor: Referencia del proveedor (opcional)
            u_medida: Unidad de medida
            coste: Coste unitario (opcional)
            pvp_sin: Precio de venta sin IVA (opcional)
            iva: Porcentaje de IVA (opcional)
            min_alerta: Stock mínimo de alerta (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        # Nombre es obligatorio
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=2, max_len=500)

        # EAN: si está presente, validar longitud
        if ean and ean.strip():
            cls.validate_string_length(ean, "EAN", max_len=50)
            # Validar que solo contenga dígitos
            if not ean.strip().isdigit():
                raise ValidationError("EAN", "debe contener solo dígitos")

        # Referencia proveedor
        if ref_proveedor and ref_proveedor.strip():
            cls.validate_string_length(ref_proveedor, "Referencia proveedor", max_len=100)

        # Unidad de medida
        cls.validate_required(u_medida, "Unidad de medida")
        # Nota: No validamos contra lista fija, permitimos cualquier valor

        # Coste
        if coste is not None:
            cls.validate_non_negative(coste, "Coste")

        # PVP
        if pvp_sin is not None:
            cls.validate_non_negative(pvp_sin, "PVP sin IVA")

        # IVA
        if iva is not None:
            cls.validate_range(iva, "IVA", minimo=0, maximo=100)

        # Stock mínimo de alerta
        if min_alerta is not None:
            cls.validate_non_negative(min_alerta, "Stock mínimo de alerta")

    @classmethod
    def validate_stock_update(cls, stock_actual: float, cantidad: float) -> None:
        """
        Valida que una actualización de stock sea posible.

        Args:
            stock_actual: Stock actual en el sistema
            cantidad: Cantidad a descontar (puede ser negativa)

        Raises:
            ValidationError: Si el stock resultante sería negativo
        """
        stock_resultante = stock_actual + cantidad

        if stock_resultante < 0:
            raise ValidationError(
                "Stock",
                f"Stock insuficiente. Actual: {stock_actual}, Solicita: {abs(cantidad)}, "
                f"Faltante: {abs(stock_resultante)}"
            )

    @classmethod
    def validate_precio_coherente(cls, coste: float, pvp: float) -> None:
        """
        Valida que el PVP sea coherente con el coste.

        Args:
            coste: Coste del artículo
            pvp: Precio de venta

        Raises:
            ValidationError: Si el PVP es menor que el coste (warning)
        """
        if coste > 0 and pvp > 0 and pvp < coste:
            raise ValidationError(
                "Precio",
                f"El PVP ({pvp}€) es menor que el coste ({coste}€). "
                "Esto generará pérdidas."
            )
