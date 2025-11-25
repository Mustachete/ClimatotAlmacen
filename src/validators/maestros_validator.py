# -*- coding: utf-8 -*-
"""
Validador para tablas maestras (proveedores, operarios, familias, etc.)
"""

from typing import Optional
from .base_validator import BaseValidator
from src.core.exceptions import ValidationError


class MaestrosValidator(BaseValidator):
    """
    Validador para entidades maestras del sistema.
    """

    ROLES_OPERARIO_VALIDOS = ['oficial', 'ayudante', 'especialista']
    ROLES_USUARIO_VALIDOS = ['admin', 'almacen', 'consulta']

    @classmethod
    def validate_proveedor(
        cls,
        nombre: str,
        telefono: Optional[str] = None,
        email: Optional[str] = None
    ) -> None:
        """
        Valida los datos de un proveedor.

        Args:
            nombre: Nombre del proveedor
            telefono: Teléfono (opcional)
            email: Email (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=2, max_len=255)

        if telefono and telefono.strip():
            cls.validate_string_length(telefono, "Teléfono", max_len=50)

        if email and email.strip():
            cls.validate_email(email)

    @classmethod
    def validate_operario(
        cls,
        nombre: str,
        rol_operario: str = 'ayudante'
    ) -> None:
        """
        Valida los datos de un operario.

        Args:
            nombre: Nombre del operario
            rol_operario: Rol del operario

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=2, max_len=255)

        cls.validate_required(rol_operario, "Rol")
        cls.validate_choice(rol_operario, "Rol", cls.ROLES_OPERARIO_VALIDOS)

    @classmethod
    def validate_familia(cls, nombre: str) -> None:
        """
        Valida los datos de una familia de artículos.

        Args:
            nombre: Nombre de la familia

        Raises:
            ValidationError: Si el nombre no es válido
        """
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=2, max_len=255)

    @classmethod
    def validate_ubicacion(cls, nombre: str) -> None:
        """
        Valida los datos de una ubicación.

        Args:
            nombre: Nombre de la ubicación

        Raises:
            ValidationError: Si el nombre no es válido
        """
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=1, max_len=255)

    @classmethod
    def validate_almacen(
        cls,
        nombre: str,
        tipo: str = 'almacen'
    ) -> None:
        """
        Valida los datos de un almacén.

        Args:
            nombre: Nombre del almacén
            tipo: Tipo de almacén ('almacen' o 'furgoneta')

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_required(nombre, "Nombre")
        cls.validate_string_length(nombre, "Nombre", min_len=2, max_len=255)

        cls.validate_required(tipo, "Tipo")
        cls.validate_choice(tipo, "Tipo", ['almacen', 'furgoneta'])

    @classmethod
    def validate_usuario(
        cls,
        usuario: str,
        password: str,
        rol: str = 'almacen'
    ) -> None:
        """
        Valida los datos de un usuario.

        Args:
            usuario: Nombre de usuario
            password: Contraseña
            rol: Rol del usuario

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_required(usuario, "Usuario")
        cls.validate_string_length(usuario, "Usuario", min_len=3, max_len=100)

        cls.validate_required(password, "Contraseña")
        cls.validate_string_length(password, "Contraseña", min_len=4)

        cls.validate_required(rol, "Rol")
        cls.validate_choice(rol, "Rol", cls.ROLES_USUARIO_VALIDOS)

    @classmethod
    def validate_email(cls, email: str) -> None:
        """
        Valida un email con un patrón básico.

        Args:
            email: Email a validar

        Raises:
            ValidationError: Si el email no es válido
        """
        import re

        if not email or not email.strip():
            return  # Email es opcional en muchos casos

        # Patrón básico de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email.strip()):
            raise ValidationError("Email", "formato de email inválido")

    @classmethod
    def validate_furgoneta(
        cls,
        matricula: str,
        nombre: Optional[str] = None
    ) -> None:
        """
        Valida los datos de una furgoneta.

        Args:
            matricula: Matrícula de la furgoneta
            nombre: Nombre descriptivo (opcional)

        Raises:
            ValidationError: Si algún dato no es válido
        """
        cls.validate_required(matricula, "Matrícula")
        cls.validate_string_length(matricula, "Matrícula", min_len=4, max_len=20)

        if nombre and nombre.strip():
            cls.validate_string_length(nombre, "Nombre", max_len=255)
