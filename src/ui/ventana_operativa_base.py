"""
ventana_operativa_base.py - Clase base abstracta para todas las ventanas operativas

Esta clase encapsula toda la lógica común de las ventanas de operaciones con artículos:
- Estructura visual: título + descripción + formulario cabecera + selector artículos + tabla temporal + totales
- Funcionalidad de artículos temporales: agregar, quitar, modificar
- Validaciones comunes
- Gestión de guardado con transacciones

Las clases hijas solo necesitan:
1. Definir el formulario de cabecera específico
2. Implementar la lógica de guardado
3. Configurar validaciones específicas
4. Personalizar el selector de artículos si es necesario

Ejemplo de uso:
    class VentanaRecepcion(VentanaOperativaBase):
        def __init__(self, parent=None):
            super().__init__(
                titulo="📦 Recepción de Albaranes",
                descripcion="Registra la entrada de material desde proveedores",
                parent=parent
            )

        def crear_formulario_cabecera(self, layout):
            # Formulario específico de recepción
            form = QFormLayout()
            self.txt_num_albaran = QLineEdit()
            self.cmb_proveedor = QComboBox()
            form.addRow("Nº Albarán:", self.txt_num_albaran)
            form.addRow("Proveedor:", self.cmb_proveedor)
            layout.addLayout(form)

        def validar_antes_guardar(self):
            if not self.txt_num_albaran.text():
                return False, "El número de albarán es obligatorio"
            return True, ""

        def ejecutar_guardado(self):
            # Lógica específica de guardado
            return movimientos_service.registrar_recepcion(...)

Reducción esperada: ~150-200 líneas por ventana operativa
"""

from abc import ABC, abstractmethod
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QGroupBox, QHeaderView,
    QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_base import TituloVentana, DescripcionVentana
from src.ui.widgets_personalizados import SpinBoxClimatot, crear_boton_quitar_centrado
from src.dialogs.buscador_articulos import BuscadorArticulos
from src.core.session_manager import session_manager


class VentanaOperativaBase(QWidget, ABC):
    """
    Clase base abstracta para todas las ventanas de operaciones con artículos.

    Proporciona:
    - Estructura visual estándar (título, formulario, selector de artículos, tabla temporal)
    - Gestión de artículos temporales (agregar, quitar, modificar)
    - Validaciones comunes
    - Resumen y totales
    - Botones de guardado y cancelación

    Métodos abstractos que DEBEN implementar las clases hijas:
    - crear_formulario_cabecera(layout): Define el formulario específico de la operación
    - validar_antes_guardar(): Valida los datos antes de guardar
    - ejecutar_guardado(): Ejecuta la lógica de guardado específica
    - configurar_columnas_articulos(): Define las columnas de la tabla de artículos

    Métodos opcionales que PUEDEN sobrescribir las clases hijas:
    - configurar_dimensiones(): Personaliza tamaño de ventana
    - on_articulo_agregado(articulo): Callback cuando se agrega un artículo
    - calcular_resumen(): Personaliza el cálculo del resumen
    - permitir_cantidad_negativa(): Si permite cantidades negativas (default: False)
    """

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        mostrar_fecha: bool = True,
        parent=None
    ):
        """
        Inicializa la ventana operativa.

        Args:
            titulo (str): Título de la ventana (ej: "📦 Recepción de Albaranes")
            descripcion (str): Descripción/subtítulo
            mostrar_fecha (bool): Si debe mostrar el campo fecha (default: True)
            parent: Widget padre
        """
        super().__init__(parent)

        self.titulo_texto = titulo
        self.descripcion_texto = descripcion
        self.mostrar_fecha = mostrar_fecha

        # Lista temporal de artículos
        self.articulos_temp = []
        self.articulo_actual = None

        # Configurar ventana
        self.setWindowTitle(titulo)
        self.setStyleSheet(ESTILO_VENTANA)

        # Dimensiones (pueden sobrescribirse en hijas)
        self.configurar_dimensiones()

        # Crear interfaz
        self._crear_interfaz()

    def configurar_dimensiones(self):
        """
        Configura las dimensiones de la ventana.
        Las clases hijas pueden sobrescribir este método para personalizar.
        """
        self.setMinimumSize(900, 600)
        self.resize(1000, 750)

    def _crear_interfaz(self):
        """Crea toda la estructura de la interfaz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Título y descripción
        titulo = TituloVentana(self.titulo_texto)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        descripcion = DescripcionVentana(self.descripcion_texto)
        descripcion.setAlignment(Qt.AlignCenter)
        layout.addWidget(descripcion)

        # Grupo: Datos de cabecera (fecha + campos específicos)
        grupo_cabecera = QGroupBox("📋 Datos de la Operación")
        cabecera_layout = QVBoxLayout()

        # Fecha (si se requiere)
        if self.mostrar_fecha:
            fecha_layout = QHBoxLayout()
            lbl_fecha = QLabel("📅 Fecha:")
            self.date_fecha = QDateEdit()
            self.date_fecha.setCalendarPopup(True)
            self.date_fecha.setDate(QDate.currentDate())
            self.date_fecha.setDisplayFormat("dd/MM/yyyy")
            self.date_fecha.setMaximumDate(QDate.currentDate())

            fecha_layout.addWidget(lbl_fecha)
            fecha_layout.addWidget(self.date_fecha)
            fecha_layout.addStretch()

            cabecera_layout.addLayout(fecha_layout)

        # Formulario específico de la operación (implementado por hijas)
        self.crear_formulario_cabecera(cabecera_layout)

        grupo_cabecera.setLayout(cabecera_layout)
        layout.addWidget(grupo_cabecera)

        # Grupo: Artículos
        grupo_articulos = QGroupBox("📦 Artículos")
        articulos_layout = QVBoxLayout()

        # Selector de artículos
        self._crear_selector_articulos(articulos_layout)

        # Tabla de artículos temporales
        self._crear_tabla_articulos(articulos_layout)

        # Resumen
        self.lbl_resumen = QLabel("📊 Total: 0 artículos")
        self.lbl_resumen.setStyleSheet(
            "background-color: #f0f9ff; border: 2px solid #1e3a8a; "
            "border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; "
            "color: #1e40af; margin-top: 5px;"
        )
        self.lbl_resumen.setAlignment(Qt.AlignCenter)
        articulos_layout.addWidget(self.lbl_resumen)

        grupo_articulos.setLayout(articulos_layout)
        layout.addWidget(grupo_articulos)

        # Botones finales
        self._crear_botones_finales(layout)

    def _crear_selector_articulos(self, layout):
        """Crea el selector de artículos con buscador y controles"""
        h_selector = QHBoxLayout()

        lbl_art = QLabel("Artículo:")

        self.buscador = BuscadorArticulos(
            self,
            mostrar_boton_lupa=True,
            placeholder="Buscar por EAN, referencia o nombre..."
        )
        self.buscador.articuloSeleccionado.connect(self.on_articulo_seleccionado)

        lbl_cant = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(-999999 if self.permitir_cantidad_negativa() else 0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(150)

        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.clicked.connect(self.agregar_articulo)
        self.btn_agregar.setEnabled(False)

        h_selector.addWidget(lbl_art)
        h_selector.addWidget(self.buscador, 3)
        h_selector.addWidget(lbl_cant)
        h_selector.addWidget(self.spin_cantidad, 1)
        h_selector.addStretch()
        h_selector.addWidget(self.btn_agregar)

        layout.addLayout(h_selector)

    def _crear_tabla_articulos(self, layout):
        """Crea la tabla de artículos temporales"""
        self.tabla_articulos = QTableWidget()
        self.configurar_columnas_articulos()
        self.tabla_articulos.setMaximumHeight(300)

        layout.addWidget(self.tabla_articulos)

    def _crear_botones_finales(self, layout):
        """Crea los botones de guardar y cancelar"""
        botones_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("💾 Guardar Operación")
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_guardar.setMinimumHeight(45)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.btn_guardar.setFont(font)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.limpiar_y_cerrar)
        btn_cancelar.setMinimumHeight(45)

        botones_layout.addStretch()
        botones_layout.addWidget(btn_cancelar)
        botones_layout.addWidget(self.btn_guardar)

        layout.addLayout(botones_layout)

    @abstractmethod
    def crear_formulario_cabecera(self, layout):
        """
        Crea el formulario de cabecera específico de la operación.
        DEBE ser implementado por las clases hijas.

        Args:
            layout: Layout donde agregar los controles del formulario

        Ejemplo:
            form = QFormLayout()
            self.txt_num_albaran = QLineEdit()
            self.cmb_proveedor = QComboBox()
            form.addRow("Nº Albarán:", self.txt_num_albaran)
            form.addRow("Proveedor:", self.cmb_proveedor)
            layout.addLayout(form)
        """
        pass

    @abstractmethod
    def configurar_columnas_articulos(self):
        """
        Configura las columnas de la tabla de artículos temporales.
        DEBE ser implementado por las clases hijas.

        Ejemplo:
            self.tabla_articulos.setColumnCount(5)
            self.tabla_articulos.setHorizontalHeaderLabels([
                "ID", "Artículo", "Cantidad", "Coste Unit.", "Acciones"
            ])
            self.tabla_articulos.setColumnHidden(0, True)
        """
        pass

    @abstractmethod
    def validar_antes_guardar(self):
        """
        Valida los datos antes de guardar.
        DEBE ser implementado por las clases hijas.

        Returns:
            tuple: (exito: bool, mensaje_error: str)

        Ejemplo:
            if not self.txt_num_albaran.text():
                return False, "El número de albarán es obligatorio"
            if not self.articulos_temp:
                return False, "Debe agregar al menos un artículo"
            return True, ""
        """
        pass

    @abstractmethod
    def ejecutar_guardado(self):
        """
        Ejecuta la lógica de guardado específica de la operación.
        DEBE ser implementado por las clases hijas.

        Returns:
            tuple: (exito: bool, mensaje: str)

        Ejemplo:
            return movimientos_service.registrar_recepcion(
                num_albaran=self.txt_num_albaran.text(),
                fecha=self.date_fecha.date().toString("yyyy-MM-dd"),
                proveedor_id=self.cmb_proveedor.currentData(),
                articulos=self.articulos_temp,
                usuario=session_manager.get_usuario_actual()
            )
        """
        pass

    def permitir_cantidad_negativa(self):
        """
        Indica si se permiten cantidades negativas.
        Las clases hijas pueden sobrescribir para permitirlas.

        Returns:
            bool: True si se permiten cantidades negativas
        """
        return False

    def on_articulo_seleccionado(self, articulo):
        """
        Callback cuando se selecciona un artículo en el buscador.

        Args:
            articulo (dict): Datos del artículo seleccionado
        """
        self.articulo_actual = articulo
        self.btn_agregar.setEnabled(True)
        self.spin_cantidad.setFocus()
        self.spin_cantidad.selectAll()

    def agregar_articulo(self):
        """Agrega el artículo actual a la lista temporal"""
        if not self.articulo_actual:
            QMessageBox.warning(self, "⚠️ Aviso", "Seleccione un artículo primero")
            return

        cantidad = self.spin_cantidad.value()
        if cantidad == 0:
            QMessageBox.warning(self, "⚠️ Aviso", "La cantidad debe ser mayor a 0")
            return

        # Verificar si el artículo ya está en la lista
        for item in self.articulos_temp:
            if item['articulo_id'] == self.articulo_actual['id']:
                # Sumar cantidad
                item['cantidad'] += cantidad
                self.actualizar_tabla_articulos()
                self.limpiar_selector()
                return

        # Agregar nuevo artículo
        articulo_temp = {
            'articulo_id': self.articulo_actual['id'],
            'nombre': self.articulo_actual['nombre'],
            'cantidad': cantidad,
            'u_medida': self.articulo_actual.get('u_medida', 'unidad'),
            'ref_proveedor': self.articulo_actual.get('ref_proveedor', ''),
            'ean': self.articulo_actual.get('ean', '')
        }

        self.articulos_temp.append(articulo_temp)
        self.on_articulo_agregado(articulo_temp)
        self.actualizar_tabla_articulos()
        self.limpiar_selector()

    def on_articulo_agregado(self, articulo):
        """
        Callback cuando se agrega un artículo.
        Las clases hijas pueden sobrescribir para lógica adicional.

        Args:
            articulo (dict): Artículo agregado
        """
        pass

    def quitar_articulo(self, index):
        """
        Quita un artículo de la lista temporal.

        Args:
            index (int): Índice del artículo a quitar
        """
        if 0 <= index < len(self.articulos_temp):
            nombre = self.articulos_temp[index]['nombre']
            respuesta = QMessageBox.question(
                self,
                "⚠️ Confirmar",
                f"¿Quitar '{nombre}' de la lista?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                del self.articulos_temp[index]
                self.actualizar_tabla_articulos()

    def actualizar_tabla_articulos(self):
        """Actualiza la tabla de artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))

        for i, art in enumerate(self.articulos_temp):
            # Las clases hijas deben implementar cómo llenar cada fila
            self.llenar_fila_articulo(i, art)

            # Botón quitar (siempre en la última columna)
            btn_quitar = crear_boton_quitar_centrado(lambda idx=i: self.quitar_articulo(idx))
            ultima_columna = self.tabla_articulos.columnCount() - 1
            self.tabla_articulos.setCellWidget(i, ultima_columna, btn_quitar)

        self.actualizar_resumen()

    def llenar_fila_articulo(self, fila, articulo):
        """
        Llena una fila de la tabla con los datos del artículo.
        Las clases hijas PUEDEN sobrescribir para personalizar.

        Args:
            fila (int): Número de fila
            articulo (dict): Datos del artículo
        """
        # Implementación por defecto básica
        self.tabla_articulos.setItem(fila, 0, QTableWidgetItem(str(articulo['articulo_id'])))
        self.tabla_articulos.setItem(fila, 1, QTableWidgetItem(articulo['nombre']))
        self.tabla_articulos.setItem(fila, 2, QTableWidgetItem(f"{articulo['cantidad']:.2f}"))

    def actualizar_resumen(self):
        """Actualiza el label de resumen"""
        resumen = self.calcular_resumen()
        self.lbl_resumen.setText(resumen)

    def calcular_resumen(self):
        """
        Calcula el resumen a mostrar.
        Las clases hijas pueden sobrescribir para personalizar.

        Returns:
            str: Texto del resumen
        """
        total_articulos = len(self.articulos_temp)
        total_cantidad = sum(art['cantidad'] for art in self.articulos_temp)

        return f"📊 Total: {total_articulos} artículos | Cantidad total: {total_cantidad:.2f}"

    def limpiar_selector(self):
        """Limpia el selector de artículos"""
        self.buscador.limpiar()
        self.articulo_actual = None
        self.spin_cantidad.setValue(1)
        self.btn_agregar.setEnabled(False)
        self.buscador.setFocus()

    def guardar(self):
        """Guarda la operación"""
        # Validar
        exito, mensaje = self.validar_antes_guardar()
        if not exito:
            QMessageBox.warning(self, "⚠️ Validación", mensaje)
            return

        # Validación común de artículos
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Validación", "Debe agregar al menos un artículo")
            return

        # Confirmar
        respuesta = QMessageBox.question(
            self,
            "💾 Confirmar",
            "¿Guardar esta operación?\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Ejecutar guardado
        try:
            exito, mensaje = self.ejecutar_guardado()

            if exito:
                QMessageBox.information(self, "✅ Éxito", mensaje)
                self.limpiar_todo()
                self.close()
            else:
                QMessageBox.warning(self, "⚠️ Error", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

    def limpiar_todo(self):
        """Limpia todos los campos y la lista temporal"""
        self.articulos_temp.clear()
        self.actualizar_tabla_articulos()
        self.limpiar_selector()

        # Resetear fecha si existe
        if hasattr(self, 'date_fecha'):
            self.date_fecha.setDate(QDate.currentDate())

    def limpiar_y_cerrar(self):
        """Limpia y cierra la ventana"""
        if self.articulos_temp:
            respuesta = QMessageBox.question(
                self,
                "⚠️ Confirmar",
                "Hay artículos sin guardar. ¿Desea salir sin guardar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if respuesta != QMessageBox.Yes:
                return

        self.close()
