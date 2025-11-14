"""
widgets_base.py - Widgets reutilizables con estilos predefinidos

Este módulo contiene widgets base que encapsulan estilos y comportamientos comunes,
evitando duplicación de código y asegurando consistencia visual en toda la aplicación.

Widgets disponibles:
- TituloVentana: Título grande azul para encabezados de ventanas
- DescripcionVentana: Subtítulo gris itálico para descripciones
- TablaEstandar: Tabla con estilos y configuración predefinida
- PanelFiltros: GroupBox estilizado para paneles de filtros
- Alerta: Labels de alerta con diferentes tipos (info/warning/error/success)
- BotonPrimario: Botón azul principal
- BotonSecundario: Botón gris secundario

Uso:
    from src.ui.widgets_base import TituloVentana, TablaEstandar

    titulo = TituloVentana("Mi Ventana")
    tabla = TablaEstandar()
"""

from PySide6.QtWidgets import (
    QLabel, QTableWidget, QGroupBox, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt

from src.ui.estilos import (
    ESTILO_TITULO_VENTANA,
    ESTILO_DESCRIPCION,
    ESTILO_TABLA_DATOS,
    ESTILO_PANEL_FILTROS,
    ESTILO_ALERTA_INFO,
    ESTILO_ALERTA_WARNING,
    ESTILO_ALERTA_ERROR,
    ESTILO_ALERTA_SUCCESS,
    COLOR_AZUL_PRINCIPAL,
    COLOR_BLANCO,
    COLOR_GRIS_BORDE,
    COLOR_TEXTO_GRIS
)


class TituloVentana(QLabel):
    """
    Título principal de ventana - Grande, azul, negrita.

    Uso:
        titulo = TituloVentana("📊 Mi Ventana")
        titulo.setAlignment(Qt.AlignCenter)  # Opcional
    """

    def __init__(self, texto: str = "", parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(ESTILO_TITULO_VENTANA)


class DescripcionVentana(QLabel):
    """
    Descripción/subtítulo de ventana - Gris, itálico, pequeño.

    Uso:
        descripcion = DescripcionVentana("Esta ventana muestra información importante")
    """

    def __init__(self, texto: str = "", parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(ESTILO_DESCRIPCION)


class TablaEstandar(QTableWidget):
    """
    Tabla con estilos predefinidos y configuración estándar.

    Características:
    - Estilos visuales consistentes
    - Selección por filas
    - Modo selección simple
    - Filas alternadas
    - Scrollbars personalizados

    Uso:
        tabla = TablaEstandar()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["Col1", "Col2", "Col3", "Col4", "Col5"])

    Parámetros:
        filas (int): Número inicial de filas (default: 0)
        columnas (int): Número de columnas (default: 0)
        parent: Widget padre
    """

    def __init__(self, filas: int = 0, columnas: int = 0, parent=None):
        super().__init__(filas, columnas, parent)

        # Aplicar estilos
        self.setStyleSheet(ESTILO_TABLA_DATOS)

        # Configuración estándar
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)  # Se puede habilitar después si se necesita

        # Configurar header horizontal para que sea responsive
        if columnas > 0:
            header = self.horizontalHeader()
            # La primera columna se estira, las demás se ajustan al contenido
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for i in range(1, columnas):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)


class PanelFiltros(QGroupBox):
    """
    Panel de filtros estilizado - GroupBox con fondo azul pastel.

    Uso:
        panel = PanelFiltros("Filtros de Búsqueda")
        layout = QVBoxLayout()
        # ... agregar widgets al layout ...
        panel.setLayout(layout)
    """

    def __init__(self, titulo: str = "Filtros", parent=None):
        super().__init__(titulo, parent)
        self.setStyleSheet(ESTILO_PANEL_FILTROS)


class Alerta(QLabel):
    """
    Label de alerta con diferentes tipos visuales.

    Tipos disponibles:
    - 'info': Azul - Para información general
    - 'warning': Amarillo/naranja - Para advertencias
    - 'error': Rojo - Para errores
    - 'success': Verde - Para confirmaciones exitosas

    Uso:
        alerta_info = Alerta("Este es un mensaje informativo", tipo='info')
        alerta_error = Alerta("Ha ocurrido un error", tipo='error')
        alerta_success = Alerta("Operación completada con éxito", tipo='success')

    Parámetros:
        texto (str): Mensaje a mostrar
        tipo (str): Tipo de alerta ('info', 'warning', 'error', 'success')
        parent: Widget padre
    """

    def __init__(self, texto: str = "", tipo: str = 'info', parent=None):
        super().__init__(texto, parent)
        self.tipo = tipo
        self._aplicar_estilo()

    def _aplicar_estilo(self):
        """Aplica el estilo según el tipo de alerta"""
        estilos = {
            'info': ESTILO_ALERTA_INFO,
            'warning': ESTILO_ALERTA_WARNING,
            'error': ESTILO_ALERTA_ERROR,
            'success': ESTILO_ALERTA_SUCCESS
        }

        estilo = estilos.get(self.tipo, ESTILO_ALERTA_INFO)
        self.setStyleSheet(estilo)

    def cambiar_tipo(self, nuevo_tipo: str):
        """
        Cambia el tipo de alerta dinámicamente.

        Args:
            nuevo_tipo (str): Nuevo tipo ('info', 'warning', 'error', 'success')
        """
        if nuevo_tipo in ['info', 'warning', 'error', 'success']:
            self.tipo = nuevo_tipo
            self._aplicar_estilo()


class BotonPrimario(QPushButton):
    """
    Botón primario - Azul, para acciones principales.

    Características:
    - Color azul principal
    - Texto en blanco al hover
    - Tamaño mínimo definido

    Uso:
        btn_guardar = BotonPrimario("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar)
    """

    def __init__(self, texto: str = "", parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px;
                background-color: {COLOR_AZUL_PRINCIPAL};
                border: 2px solid {COLOR_AZUL_PRINCIPAL};
                border-radius: 6px;
                color: {COLOR_BLANCO};
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: #1e40af;
                border-color: #1e40af;
            }}
            QPushButton:pressed {{
                background-color: #1e293b;
            }}
            QPushButton:disabled {{
                background-color: {COLOR_GRIS_BORDE};
                border-color: {COLOR_GRIS_BORDE};
                color: {COLOR_TEXTO_GRIS};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)


class BotonSecundario(QPushButton):
    """
    Botón secundario - Blanco con borde azul, para acciones secundarias.

    Características:
    - Fondo blanco
    - Borde azul
    - Se vuelve azul al hover

    Uso:
        btn_cancelar = BotonSecundario("❌ Cancelar")
        btn_cancelar.clicked.connect(self.close)
    """

    def __init__(self, texto: str = "", parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px;
                background-color: {COLOR_BLANCO};
                border: 2px solid {COLOR_AZUL_PRINCIPAL};
                border-radius: 6px;
                color: {COLOR_AZUL_PRINCIPAL};
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_AZUL_PRINCIPAL};
                color: {COLOR_BLANCO};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
            QPushButton:disabled {{
                background-color: {COLOR_GRIS_BORDE};
                border-color: {COLOR_GRIS_BORDE};
                color: {COLOR_TEXTO_GRIS};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)


# ========================================
# FUNCIONES HELPER PARA CREAR WIDGETS
# ========================================

def crear_titulo(texto: str, centrado: bool = False) -> TituloVentana:
    """
    Helper para crear un título de ventana.

    Args:
        texto (str): Texto del título
        centrado (bool): Si debe estar centrado (default: False)

    Returns:
        TituloVentana configurado

    Uso:
        titulo = crear_titulo("📊 Mi Ventana", centrado=True)
    """
    titulo = TituloVentana(texto)
    if centrado:
        titulo.setAlignment(Qt.AlignCenter)
    return titulo


def crear_descripcion(texto: str, centrado: bool = False) -> DescripcionVentana:
    """
    Helper para crear una descripción de ventana.

    Args:
        texto (str): Texto de la descripción
        centrado (bool): Si debe estar centrado (default: False)

    Returns:
        DescripcionVentana configurado
    """
    desc = DescripcionVentana(texto)
    if centrado:
        desc.setAlignment(Qt.AlignCenter)
    return desc


def crear_tabla(columnas: list, stretch_column: int = 0) -> TablaEstandar:
    """
    Helper para crear una tabla con columnas predefinidas.

    Args:
        columnas (list): Lista de nombres de columnas
        stretch_column (int): Índice de la columna que se estira (default: 0)

    Returns:
        TablaEstandar configurada

    Uso:
        tabla = crear_tabla(["ID", "Nombre", "Cantidad", "Precio"])
    """
    tabla = TablaEstandar(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)

    # Ocultar primera columna si es ID
    if columnas[0].upper() == "ID":
        tabla.setColumnHidden(0, True)

    # Configurar columna que se estira
    header = tabla.horizontalHeader()
    for i in range(len(columnas)):
        if i == stretch_column:
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

    return tabla
