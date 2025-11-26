# -*- coding: utf-8 -*-
"""
Utilidades centralizadas para formateo y configuración de tablas QTableWidget.

Este módulo proporciona funciones estándar para colorizar celdas, ajustar columnas
y aplicar estilos de forma consistente en toda la aplicación.

Uso:
    from src.ui.table_formatter import TableFormatter, EstadoColor

    # Configurar columnas
    TableFormatter.configurar_columnas_auto(
        tabla,
        ['ID', 'Artículo', 'Stock', 'Estado'],
        columnas_stretch=[1],  # Artículo se estira
        ocultar_primera=True
    )

    # Colorizar una celda
    item = QTableWidgetItem("✅ OK")
    TableFormatter.aplicar_color_estado(item, EstadoColor.OK)
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from enum import Enum
from typing import List, Tuple, Optional


class EstadoColor(Enum):
    """Colores estándar para estados en la aplicación"""
    OK = ("#d1fae5", "#065f46")           # Verde claro / Verde oscuro
    BAJO = ("#fee2e2", "#991b1b")         # Rojo claro / Rojo oscuro
    VACIO = ("#fecaca", "#991b1b")        # Rojo más claro / Rojo oscuro
    PENDIENTE = ("#fef3c7", "#92400e")    # Amarillo / Marrón
    SOBRA = ("#dbeafe", "#1e3a8a")        # Azul claro / Azul oscuro
    FALTA = ("#fee2e2", "#991b1b")        # Rojo claro / Rojo oscuro
    GRIS = ("#f1f5f9", "#475569")         # Gris claro / Gris oscuro
    ALERTA = ("#fecaca", "#991b1b")       # Rojo / Rojo oscuro

    # Colores para tipos de movimiento
    ENTRADA = ("#d1fae5", "#065f46")      # Verde
    TRASPASO = ("#dbeafe", "#1e3a8a")     # Azul
    IMPUTACION = ("#fef3c7", "#92400e")   # Amarillo
    PERDIDA = ("#fee2e2", "#991b1b")      # Rojo
    DEVOLUCION = ("#fce7f3", "#831843")   # Rosa


class TableFormatter:
    """Formateador de tablas estándar para la aplicación"""

    @staticmethod
    def configurar_columnas(
        tabla: QTableWidget,
        config: List[Tuple[int, str]],
        ocultar_primera: bool = True
    ) -> None:
        """
        Configura las columnas de una tabla según una configuración específica.

        Args:
            tabla: QTableWidget a configurar
            config: Lista de tuplas (numero_columna, modo)
                   Modos: 'stretch', 'content', 'fixed', 'interactive'
            ocultar_primera: Si True, oculta la columna 0 (usualmente ID)

        Ejemplo:
            config = [
                (1, 'stretch'),    # Columna 1 se estira
                (2, 'content'),    # Columna 2 ajusta a contenido
                (3, 'content'),
            ]
            TableFormatter.configurar_columnas(tabla, config)
        """
        if ocultar_primera:
            tabla.setColumnHidden(0, True)

        header = tabla.horizontalHeader()
        for col_num, modo in config:
            if modo == 'stretch':
                header.setSectionResizeMode(col_num, QHeaderView.Stretch)
            elif modo == 'content':
                header.setSectionResizeMode(col_num, QHeaderView.ResizeToContents)
            elif modo == 'fixed':
                header.setSectionResizeMode(col_num, QHeaderView.Fixed)
            elif modo == 'interactive':
                header.setSectionResizeMode(col_num, QHeaderView.Interactive)

    @staticmethod
    def configurar_columnas_auto(
        tabla: QTableWidget,
        headers: List[str],
        columnas_stretch: Optional[List[int]] = None,
        columnas_fixed: Optional[List[int]] = None,
        ocultar_primera: bool = True
    ) -> None:
        """
        Configura columnas automáticamente: las especificadas se estiran/fijan,
        el resto ajusta a contenido.

        Args:
            tabla: QTableWidget a configurar
            headers: Lista de nombres de columnas
            columnas_stretch: Índices de columnas que se estiran (ej: [1, 5])
            columnas_fixed: Índices de columnas con tamaño fijo
            ocultar_primera: Si True, oculta la columna 0 (usualmente ID)

        Ejemplo:
            TableFormatter.configurar_columnas_auto(
                tabla,
                ['ID', 'Artículo', 'Stock', 'Estado'],
                columnas_stretch=[1],  # Artículo se estira
                ocultar_primera=True
            )
        """
        columnas_stretch = columnas_stretch or []
        columnas_fixed = columnas_fixed or []

        if ocultar_primera:
            tabla.setColumnHidden(0, True)

        header = tabla.horizontalHeader()
        for i in range(len(headers)):
            if i in columnas_stretch:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif i in columnas_fixed:
                header.setSectionResizeMode(i, QHeaderView.Fixed)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

    @staticmethod
    def aplicar_color_estado(
        item: QTableWidgetItem,
        estado: EstadoColor,
        alineacion: Optional[Qt.AlignmentFlag] = Qt.AlignCenter
    ) -> None:
        """
        Aplica colores de estado a un item de tabla.

        Args:
            item: QTableWidgetItem a colorizar
            estado: EstadoColor con colores predefinidos
            alineacion: Alineación del texto (por defecto: centro)

        Ejemplo:
            item = QTableWidgetItem("✅ OK")
            TableFormatter.aplicar_color_estado(item, EstadoColor.OK)
            tabla.setItem(fila, columna, item)
        """
        bg_color, fg_color = estado.value
        item.setBackground(QColor(bg_color))
        item.setForeground(QColor(fg_color))
        if alineacion:
            item.setTextAlignment(alineacion | Qt.AlignVCenter)

    @staticmethod
    def crear_item_con_color(
        texto: str,
        estado: EstadoColor,
        alineacion: Optional[Qt.AlignmentFlag] = Qt.AlignCenter
    ) -> QTableWidgetItem:
        """
        Crea un QTableWidgetItem con color de estado aplicado.

        Args:
            texto: Texto del item
            estado: EstadoColor a aplicar
            alineacion: Alineación del texto

        Returns:
            QTableWidgetItem con color aplicado

        Ejemplo:
            item = TableFormatter.crear_item_con_color("✅ OK", EstadoColor.OK)
            tabla.setItem(fila, columna, item)
        """
        item = QTableWidgetItem(texto)
        TableFormatter.aplicar_color_estado(item, estado, alineacion)
        return item

    @staticmethod
    def colorizar_stock(
        item: QTableWidgetItem,
        stock: float,
        minimo: float = 0,
        alineacion: Optional[Qt.AlignmentFlag] = Qt.AlignRight
    ) -> None:
        """
        Coloriza un item de stock según su nivel.

        Args:
            item: QTableWidgetItem con valor de stock
            stock: Valor de stock
            minimo: Valor mínimo para considerar "bajo"
            alineacion: Alineación del texto (por defecto: derecha)

        Ejemplo:
            item = QTableWidgetItem(f"{stock:.2f}")
            TableFormatter.colorizar_stock(item, stock, minimo=10)
            tabla.setItem(fila, col, item)
        """
        if stock == 0:
            estado = EstadoColor.VACIO
        elif stock < minimo:
            estado = EstadoColor.BAJO
        else:
            estado = EstadoColor.OK

        TableFormatter.aplicar_color_estado(item, estado, alineacion)

    @staticmethod
    def colorizar_diferencia(
        item: QTableWidgetItem,
        diferencia: float,
        alineacion: Optional[Qt.AlignmentFlag] = Qt.AlignRight
    ) -> None:
        """
        Coloriza un item basado en una diferencia (positivo/negativo).
        Útil para inventarios.

        Args:
            item: QTableWidgetItem
            diferencia: Valor de diferencia (positivo/negativo)
            alineacion: Alineación del texto

        Ejemplo:
            dif = stock_contado - stock_teorico
            item = QTableWidgetItem(f"{dif:+.2f}")
            TableFormatter.colorizar_diferencia(item, dif)
            tabla.setItem(fila, col, item)
        """
        if diferencia > 0:
            estado = EstadoColor.SOBRA
        elif diferencia < 0:
            estado = EstadoColor.FALTA
        else:
            estado = EstadoColor.OK

        TableFormatter.aplicar_color_estado(item, estado, alineacion)

    @staticmethod
    def colorizar_tipo_movimiento(
        item: QTableWidgetItem,
        tipo: str
    ) -> None:
        """
        Coloriza un item según el tipo de movimiento.

        Args:
            item: QTableWidgetItem con tipo de movimiento
            tipo: Tipo de movimiento (ENTRADA, TRASPASO, IMPUTACION, etc.)

        Ejemplo:
            item = QTableWidgetItem(tipo)
            TableFormatter.colorizar_tipo_movimiento(item, tipo)
            tabla.setItem(fila, col, item)
        """
        mapeo_estados = {
            'ENTRADA': EstadoColor.ENTRADA,
            'TRASPASO': EstadoColor.TRASPASO,
            'IMPUTACION': EstadoColor.IMPUTACION,
            'PERDIDA': EstadoColor.PERDIDA,
            'DEVOLUCION': EstadoColor.DEVOLUCION,
        }

        estado = mapeo_estados.get(tipo.upper(), EstadoColor.GRIS)
        TableFormatter.aplicar_color_estado(item, estado)

    @staticmethod
    def crear_item_numerico(
        valor: float,
        decimales: int = 2,
        alineacion: Optional[Qt.AlignmentFlag] = Qt.AlignRight,
        con_color: bool = False,
        minimo: Optional[float] = None
    ) -> QTableWidgetItem:
        """
        Crea un item con valor numérico formateado.

        Args:
            valor: Valor numérico
            decimales: Número de decimales a mostrar
            alineacion: Alineación del texto
            con_color: Si True, coloriza según el valor
            minimo: Si se especifica y con_color=True, coloriza según si está bajo mínimo

        Returns:
            QTableWidgetItem con valor formateado

        Ejemplo:
            item = TableFormatter.crear_item_numerico(
                stock, decimales=2, con_color=True, minimo=10
            )
            tabla.setItem(fila, col, item)
        """
        texto = f"{valor:.{decimales}f}"
        item = QTableWidgetItem(texto)

        if alineacion:
            item.setTextAlignment(alineacion | Qt.AlignVCenter)

        if con_color and minimo is not None:
            TableFormatter.colorizar_stock(item, valor, minimo, alineacion)

        return item

    @staticmethod
    def aplicar_estilo_fila(
        tabla: QTableWidget,
        fila: int,
        estado: EstadoColor,
        excepto_columnas: Optional[List[int]] = None
    ) -> None:
        """
        Aplica un color de estado a toda una fila (excepto algunas columnas).

        Args:
            tabla: QTableWidget
            fila: Número de fila
            estado: EstadoColor a aplicar
            excepto_columnas: Columnas a no colorizar (ej: [0] para excepto ID)

        Ejemplo:
            # Colorizar toda la fila como pendiente, excepto la columna ID
            TableFormatter.aplicar_estilo_fila(
                tabla, fila, EstadoColor.PENDIENTE, excepto_columnas=[0]
            )
        """
        excepto = excepto_columnas or []

        for col in range(tabla.columnCount()):
            if col not in excepto:
                item = tabla.item(fila, col)
                if item:
                    TableFormatter.aplicar_color_estado(item, estado)

    @staticmethod
    def colorizar_estado_inventario(
        item: QTableWidgetItem,
        stock_contado: float,
        diferencia: float
    ) -> None:
        """
        Coloriza un item de estado de inventario.

        Args:
            item: QTableWidgetItem con texto de estado
            stock_contado: Stock contado
            diferencia: Diferencia (contado - teórico)

        Ejemplo:
            if stock_contado == 0:
                estado = "⏳ Pendiente"
            elif diferencia == 0:
                estado = "✅ OK"
            elif diferencia > 0:
                estado = "📈 Sobra"
            else:
                estado = "📉 Falta"

            item = QTableWidgetItem(estado)
            TableFormatter.colorizar_estado_inventario(item, stock_contado, diferencia)
        """
        if stock_contado == 0:
            estado = EstadoColor.PENDIENTE
        elif diferencia == 0:
            estado = EstadoColor.OK
        elif diferencia > 0:
            estado = EstadoColor.SOBRA
        else:
            estado = EstadoColor.FALTA

        TableFormatter.aplicar_color_estado(item, estado)

    @staticmethod
    def habilitar_ordenamiento(tabla: QTableWidget, habilitado: bool = True) -> None:
        """
        Habilita/deshabilita el ordenamiento por columnas en una tabla.

        Args:
            tabla: QTableWidget
            habilitado: True para habilitar, False para deshabilitar

        Ejemplo:
            # Deshabilitar mientras se carga
            TableFormatter.habilitar_ordenamiento(tabla, False)
            # ... cargar datos ...
            TableFormatter.habilitar_ordenamiento(tabla, True)
        """
        tabla.setSortingEnabled(habilitado)

    @staticmethod
    def configurar_tabla_estandar(
        tabla: QTableWidget,
        headers: List[str],
        columnas_stretch: Optional[List[int]] = None,
        ocultar_primera: bool = True,
        alternar_colores: bool = True,
        seleccion_fila: bool = True
    ) -> None:
        """
        Configura una tabla con ajustes estándar de la aplicación.

        Args:
            tabla: QTableWidget a configurar
            headers: Lista de nombres de columnas
            columnas_stretch: Índices de columnas que se estiran
            ocultar_primera: Si True, oculta la columna 0
            alternar_colores: Si True, alterna colores de filas
            seleccion_fila: Si True, selección por fila completa

        Ejemplo:
            TableFormatter.configurar_tabla_estandar(
                self.tabla,
                ['ID', 'Artículo', 'Stock', 'Estado'],
                columnas_stretch=[1]
            )
        """
        # Configurar columnas
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        TableFormatter.configurar_columnas_auto(
            tabla, headers, columnas_stretch, ocultar_primera=ocultar_primera
        )

        # Configuración de comportamiento
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setAlternatingRowColors(alternar_colores)

        if seleccion_fila:
            tabla.setSelectionBehavior(QTableWidget.SelectRows)
            tabla.setSelectionMode(QTableWidget.SingleSelection)
