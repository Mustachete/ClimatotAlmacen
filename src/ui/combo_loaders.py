# -*- coding: utf-8 -*-
"""
Funciones centralizadas para cargar datos en combos (QComboBox).

Este módulo proporciona una interfaz estándar para llenar combos con datos
de la base de datos, eliminando código duplicado en múltiples ventanas.

Uso:
    from src.ui.combo_loaders import ComboLoader
    from src.repos import articulos_repo

    # En tu ventana:
    ComboLoader.cargar_familias(
        self.cmb_familia,
        articulos_repo.get_familias,
        opcion_vacia=True
    )
"""

from PySide6.QtWidgets import QComboBox, QMessageBox
from src.core.logger import logger
from typing import Callable, List, Dict, Any, Optional


class ComboLoader:
    """Helper para cargar datos en combos de forma consistente"""

    @staticmethod
    def cargar_items(
        combo: QComboBox,
        items: List[Dict[str, Any]],
        text_key: str,
        data_key: str,
        opcion_vacia: Optional[tuple] = None,
        custom_formatter: Optional[Callable] = None
    ) -> None:
        """
        Carga items en un combo de forma estándar.

        Args:
            combo: QComboBox a cargar
            items: Lista de diccionarios con datos
            text_key: Clave del diccionario para el texto mostrado
            data_key: Clave del diccionario para el dato asociado
            opcion_vacia: Tupla (texto, valor) para opción vacía (ej: ("Todos", None))
            custom_formatter: Función opcional para personalizar el texto mostrado

        Ejemplo:
            items = [{'id': 1, 'nombre': 'Familia A'}, {'id': 2, 'nombre': 'Familia B'}]
            ComboLoader.cargar_items(
                combo=self.cmb_familia,
                items=items,
                text_key='nombre',
                data_key='id',
                opcion_vacia=("Todas", None)
            )
        """
        combo.clear()

        if opcion_vacia:
            combo.addItem(opcion_vacia[0], opcion_vacia[1])

        for item in items:
            if custom_formatter:
                text = custom_formatter(item)
            else:
                text = str(item.get(text_key, ""))

            data = item.get(data_key)
            combo.addItem(text, data)

    @staticmethod
    def cargar_familias(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "(Sin familia)"
    ) -> bool:
        """
        Carga familias de artículos en un combo.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de familias
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.repos import articulos_repo

            exito = ComboLoader.cargar_familias(
                self.cmb_familia,
                articulos_repo.get_familias
            )
        """
        try:
            familias = repo_func()
            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, familias, 'nombre', 'id', opcion)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar familias: {e}")
            # Dejar el combo vacío o solo con opción vacía
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False

    @staticmethod
    def cargar_proveedores(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "(Sin proveedor)"
    ) -> bool:
        """
        Carga proveedores en un combo.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de proveedores
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.repos import articulos_repo

            exito = ComboLoader.cargar_proveedores(
                self.cmb_proveedor,
                articulos_repo.get_proveedores
            )
        """
        try:
            proveedores = repo_func()
            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, proveedores, 'nombre', 'id', opcion)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar proveedores: {e}")
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False

    @staticmethod
    def cargar_almacenes(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "Todos"
    ) -> bool:
        """
        Carga almacenes/furgonetas en un combo.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de almacenes
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía (por defecto: "Todos")

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.services import almacenes_service

            exito = ComboLoader.cargar_almacenes(
                self.cmb_almacen,
                almacenes_service.obtener_almacenes
            )
        """
        try:
            almacenes = repo_func()
            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, almacenes, 'nombre', 'id', opcion)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar almacenes: {e}")
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False

    @staticmethod
    def cargar_operarios(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "(Seleccione operario)",
        con_emoji: bool = True
    ) -> bool:
        """
        Carga operarios en un combo con emoji según rol.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de operarios
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía
            con_emoji: Si True, añade emoji según rol del operario

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.repos import movimientos_repo

            exito = ComboLoader.cargar_operarios(
                self.cmb_operario,
                movimientos_repo.get_operarios_activos
            )
        """
        try:
            operarios = repo_func()

            def formatter(op):
                if con_emoji:
                    emoji = "👷" if op.get('rol_operario') == "oficial" else "🔨"
                    return f"{emoji} {op['nombre']} ({op.get('rol_operario', 'sin rol')})"
                else:
                    return f"{op['nombre']} ({op.get('rol_operario', 'sin rol')})"

            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, operarios, None, 'id', opcion, formatter)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar operarios: {e}")
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False

    @staticmethod
    def cargar_ubicaciones(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "(Sin ubicación)"
    ) -> bool:
        """
        Carga ubicaciones en un combo.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de ubicaciones
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.repos import articulos_repo

            exito = ComboLoader.cargar_ubicaciones(
                self.cmb_ubicacion,
                articulos_repo.get_ubicaciones
            )
        """
        try:
            ubicaciones = repo_func()
            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, ubicaciones, 'nombre', 'id', opcion)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar ubicaciones: {e}")
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False

    @staticmethod
    def cargar_articulos(
        combo: QComboBox,
        repo_func: Callable[[], List[Dict[str, Any]]],
        opcion_vacia: bool = True,
        texto_vacio: str = "(Seleccione un artículo)",
        incluir_ean_ref: bool = True
    ) -> bool:
        """
        Carga artículos en un combo.

        Args:
            combo: QComboBox destino
            repo_func: Función que retorna lista de artículos
            opcion_vacia: Si incluir opción vacía
            texto_vacio: Texto para la opción vacía
            incluir_ean_ref: Si True, muestra EAN y referencia en el texto

        Returns:
            True si se cargó exitosamente, False si hubo error

        Ejemplo:
            from src.repos import articulos_repo

            exito = ComboLoader.cargar_articulos(
                self.cmb_articulo,
                lambda: articulos_repo.get_todos(solo_activos=True)
            )
        """
        try:
            articulos = repo_func()

            def formatter(art):
                texto = art['nombre']
                if incluir_ean_ref:
                    if art.get('ean'):
                        texto += f" [EAN: {art['ean']}]"
                    if art.get('ref_proveedor'):
                        texto += f" [REF: {art['ref_proveedor']}]"
                return texto

            opcion = (texto_vacio, None) if opcion_vacia else None
            ComboLoader.cargar_items(combo, articulos, None, 'id', opcion, formatter)
            return True
        except Exception as e:
            logger.warning(f"No se pudieron cargar artículos: {e}")
            if opcion_vacia:
                combo.clear()
                combo.addItem(texto_vacio, None)
            return False
