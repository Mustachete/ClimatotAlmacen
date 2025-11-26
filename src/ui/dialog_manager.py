# -*- coding: utf-8 -*-
"""
Gestor centralizado de diálogos y mensajes de usuario.

Este módulo proporciona métodos estándar para mostrar errores, advertencias,
información y confirmaciones de forma consistente en toda la aplicación.

Uso:
    from src.ui.dialog_manager import DialogManager

    # Mostrar error
    DialogManager.mostrar_error(self, "Error al cargar datos")

    # Confirmar acción
    if DialogManager.confirmar(self, "¿Está seguro de eliminar?"):
        # proceder con eliminación
"""

from PySide6.QtWidgets import QMessageBox, QWidget
from src.core.logger import logger
from typing import Callable, Optional, TypeVar, Any

T = TypeVar('T')


class DialogManager:
    """Gestor centralizado de diálogos de usuario"""

    # Textos estándar
    TITULO_ERROR = "❌ Error"
    TITULO_ADVERTENCIA = "⚠️ Advertencia"
    TITULO_INFO = "ℹ️ Información"
    TITULO_EXITO = "✅ Éxito"
    TITULO_CONFIRMACION = "⚠️ Confirmación"

    # Mensajes estándar para operaciones comunes
    MENSAJES = {
        'cargar_datos': 'Error al cargar datos:\n{detalle}',
        'cargar_familias': 'No se pudieron cargar las familias:\n{detalle}',
        'cargar_proveedores': 'No se pudieron cargar los proveedores:\n{detalle}',
        'cargar_almacenes': 'No se pudieron cargar los almacenes:\n{detalle}',
        'cargar_operarios': 'No se pudieron cargar los operarios:\n{detalle}',
        'cargar_ubicaciones': 'No se pudieron cargar las ubicaciones:\n{detalle}',
        'guardar_datos': 'Error al guardar:\n{detalle}',
        'eliminar_datos': 'Error al eliminar:\n{detalle}',
        'validacion': 'Error de validación:\n{detalle}',
        'bd': 'Error de base de datos:\n{detalle}',
    }

    @staticmethod
    def mostrar_error(
        parent: QWidget,
        mensaje: str,
        titulo: str = TITULO_ERROR,
        log: bool = True
    ) -> None:
        """
        Muestra un diálogo de error al usuario.

        Args:
            parent: Widget padre
            mensaje: Mensaje de error
            titulo: Título del diálogo (por defecto: "❌ Error")
            log: Si True, registra el error en el logger

        Ejemplo:
            DialogManager.mostrar_error(self, "No se pudo cargar el archivo")
        """
        if log:
            logger.error(mensaje)

        QMessageBox.critical(parent, titulo, mensaje)

    @staticmethod
    def mostrar_advertencia(
        parent: QWidget,
        mensaje: str,
        titulo: str = TITULO_ADVERTENCIA,
        log: bool = True
    ) -> None:
        """
        Muestra un diálogo de advertencia al usuario.

        Args:
            parent: Widget padre
            mensaje: Mensaje de advertencia
            titulo: Título del diálogo (por defecto: "⚠️ Advertencia")
            log: Si True, registra la advertencia en el logger

        Ejemplo:
            DialogManager.mostrar_advertencia(
                self,
                "El stock está por debajo del mínimo"
            )
        """
        if log:
            logger.warning(mensaje)

        QMessageBox.warning(parent, titulo, mensaje)

    @staticmethod
    def mostrar_info(
        parent: QWidget,
        mensaje: str,
        titulo: str = TITULO_INFO
    ) -> None:
        """
        Muestra un diálogo informativo al usuario.

        Args:
            parent: Widget padre
            mensaje: Mensaje informativo
            titulo: Título del diálogo (por defecto: "ℹ️ Información")

        Ejemplo:
            DialogManager.mostrar_info(
                self,
                "Esta operación puede tardar unos segundos"
            )
        """
        QMessageBox.information(parent, titulo, mensaje)

    @staticmethod
    def mostrar_exito(
        parent: QWidget,
        mensaje: str,
        titulo: str = TITULO_EXITO
    ) -> None:
        """
        Muestra un diálogo de éxito al usuario.

        Args:
            parent: Widget padre
            mensaje: Mensaje de éxito
            titulo: Título del diálogo (por defecto: "✅ Éxito")

        Ejemplo:
            DialogManager.mostrar_exito(self, "Datos guardados correctamente")
        """
        logger.info(f"Operación exitosa: {mensaje}")
        QMessageBox.information(parent, titulo, mensaje)

    @staticmethod
    def confirmar(
        parent: QWidget,
        mensaje: str,
        titulo: str = TITULO_CONFIRMACION
    ) -> bool:
        """
        Muestra un diálogo de confirmación.

        Args:
            parent: Widget padre
            mensaje: Mensaje a confirmar
            titulo: Título del diálogo

        Returns:
            True si el usuario hace clic en "Sí", False si en "No"

        Ejemplo:
            if DialogManager.confirmar(self, "¿Está seguro de eliminar este registro?"):
                # proceder con eliminación
        """
        respuesta = QMessageBox.question(
            parent,
            titulo,
            mensaje,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return respuesta == QMessageBox.Yes

    @staticmethod
    def confirmar_eliminar(
        parent: QWidget,
        nombre_item: str,
        tipo_item: str = "registro"
    ) -> bool:
        """
        Muestra un diálogo estándar de confirmación de eliminación.

        Args:
            parent: Widget padre
            nombre_item: Nombre del item a eliminar
            tipo_item: Tipo de item (ej: "artículo", "proveedor")

        Returns:
            True si el usuario confirma, False en caso contrario

        Ejemplo:
            if DialogManager.confirmar_eliminar(self, "Familia A", "familia"):
                # eliminar familia
        """
        mensaje = (
            f"¿Está seguro de eliminar {tipo_item} '{nombre_item}'?\n\n"
            "Esta acción no se puede deshacer."
        )
        return DialogManager.confirmar(parent, mensaje)

    @staticmethod
    def manejar_error_carga(
        parent: QWidget,
        tipo_dato: str,
        excepcion: Exception,
        continuar_permitido: bool = False
    ) -> bool:
        """
        Maneja errores estándar de carga de datos.

        Args:
            parent: Widget padre
            tipo_dato: Tipo de dato que no se pudo cargar (ej: "familias")
            excepcion: Excepción capturada
            continuar_permitido: Si True, solo muestra advertencia; si False, error crítico

        Returns:
            True si se puede continuar, False si se debe cancelar

        Ejemplo:
            try:
                familias = familias_service.obtener_familias()
            except Exception as e:
                puede_continuar = DialogManager.manejar_error_carga(
                    self, "familias", e, continuar_permitido=True
                )
                if not puede_continuar:
                    return
        """
        mensaje = f"No se pudieron cargar {tipo_dato}:\n{str(excepcion)}"

        if continuar_permitido:
            DialogManager.mostrar_advertencia(
                parent,
                f"{mensaje}\n\nPuede continuar sin estos datos.",
                log=True
            )
            return True
        else:
            DialogManager.mostrar_error(parent, mensaje, log=True)
            return False

    @staticmethod
    def con_manejo_error(
        parent: QWidget,
        operacion: Callable[..., T],
        tipo_dato: str = "datos",
        continuar_permitido: bool = False,
        *args,
        **kwargs
    ) -> Optional[T]:
        """
        Ejecuta una operación con manejo automático de errores.

        Args:
            parent: Widget padre
            operacion: Función a ejecutar
            tipo_dato: Descripción del tipo de dato (para mensajes)
            continuar_permitido: Si se puede continuar tras error
            *args, **kwargs: Argumentos para la operación

        Returns:
            Resultado de la operación o None si hay error

        Ejemplo:
            familias = DialogManager.con_manejo_error(
                self,
                familias_service.obtener_familias,
                "familias",
                continuar_permitido=True
            )
            if familias is None:
                return  # Error manejado
        """
        try:
            return operacion(*args, **kwargs)
        except Exception as e:
            DialogManager.manejar_error_carga(
                parent, tipo_dato, e, continuar_permitido
            )
            return None

    @staticmethod
    def mostrar_error_estandar(
        parent: QWidget,
        tipo_operacion: str,
        excepcion: Exception,
        log: bool = True
    ) -> None:
        """
        Muestra un error usando plantillas estándar.

        Args:
            parent: Widget padre
            tipo_operacion: Tipo de operación (clave en MENSAJES)
            excepcion: Excepción capturada
            log: Si True, loguea el error

        Ejemplo:
            try:
                guardar_datos()
            except Exception as e:
                DialogManager.mostrar_error_estandar(
                    self, 'guardar_datos', e
                )
        """
        plantilla = DialogManager.MENSAJES.get(
            tipo_operacion,
            'Error en {detalle}'
        )
        mensaje = plantilla.format(detalle=str(excepcion))
        DialogManager.mostrar_error(parent, mensaje, log=log)

    @staticmethod
    def notificar_guardado_exitoso(
        parent: QWidget,
        tipo_dato: str = "datos",
        nombre: Optional[str] = None
    ) -> None:
        """
        Muestra notificación estándar de guardado exitoso.

        Args:
            parent: Widget padre
            tipo_dato: Tipo de dato guardado
            nombre: Nombre específico del item (opcional)

        Ejemplo:
            DialogManager.notificar_guardado_exitoso(
                self, "artículo", "Tornillo M6"
            )
        """
        if nombre:
            mensaje = f"{tipo_dato.capitalize()} '{nombre}' guardado correctamente"
        else:
            mensaje = f"{tipo_dato.capitalize()} guardado correctamente"

        DialogManager.mostrar_exito(parent, mensaje)

    @staticmethod
    def notificar_eliminacion_exitosa(
        parent: QWidget,
        tipo_dato: str = "registro",
        nombre: Optional[str] = None
    ) -> None:
        """
        Muestra notificación estándar de eliminación exitosa.

        Args:
            parent: Widget padre
            tipo_dato: Tipo de dato eliminado
            nombre: Nombre específico del item (opcional)

        Ejemplo:
            DialogManager.notificar_eliminacion_exitosa(
                self, "proveedor", "Proveedor ABC"
            )
        """
        if nombre:
            mensaje = f"{tipo_dato.capitalize()} '{nombre}' eliminado correctamente"
        else:
            mensaje = f"{tipo_dato.capitalize()} eliminado correctamente"

        DialogManager.mostrar_exito(parent, mensaje)
