# ventana_devolucion.py - Devolución a Proveedor
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QComboBox,
    QHeaderView, QTextEdit, QTableWidgetItem, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from src.ui.ventana_operativa_base import VentanaOperativaBase
from src.services import movimientos_service, historial_service
from src.core.session_manager import session_manager
from src.repos import movimientos_repo, articulos_repo


# ========================================
# VENTANA DE DEVOLUCIÓN A PROVEEDOR
# ========================================
class VentanaDevolucion(VentanaOperativaBase):
    """
    Ventana para registrar devoluciones de material a proveedores.
    Hereda de VentanaOperativaBase para aprovechar toda la estructura común.
    """

    def __init__(self, parent=None):
        self.proveedor_id = None
        super().__init__(
            titulo="↩️ Devolución a Proveedor",
            descripcion="Registra material que se devuelve al proveedor (defectuoso, equivocado, sobrante...)",
            mostrar_fecha=True,
            parent=parent
        )

        # Configurar atajos de teclado
        self.configurar_atajos_teclado()

        # Mostrar ayuda de atajos
        ayuda_atajos = QLabel(
            "⌨️ Atajos: F2=Buscar artículo | F4=Motivo | F5=Limpiar | "
            "Ctrl+Enter=Guardar | Esc=Cancelar"
        )
        ayuda_atajos.setStyleSheet(
            "background-color: #f1f5f9; padding: 8px; border-radius: 4px; "
            "color: #475569; font-size: 11px; margin-top: 5px;"
        )
        ayuda_atajos.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(ayuda_atajos)

        # Variable para almacenar artículo seleccionado
        self.articulo_actual = None

    def configurar_dimensiones(self):
        """Personaliza las dimensiones para la ventana de devolución"""
        self.setMinimumSize(850, 600)
        self.resize(1000, 750)

    def crear_formulario_cabecera(self, layout):
        """Crea el formulario de cabecera con proveedor, albarán y motivo"""
        form = QFormLayout()

        # Proveedor
        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setMinimumWidth(250)
        self.cargar_proveedores()
        form.addRow("🏭 Proveedor *:", self.cmb_proveedor)

        # Albarán original (opcional)
        from PySide6.QtWidgets import QLineEdit
        self.txt_albaran = QLineEdit()
        self.txt_albaran.setPlaceholderText("(Opcional) Si la devolución es de un albarán específico")
        self.txt_albaran.setMinimumWidth(300)
        form.addRow("📄 Nº Albarán original:", self.txt_albaran)

        layout.addLayout(form)

        # Motivo de devolución (en área de texto)
        lbl_motivo = QLabel("📝 Motivo de la Devolución *:")
        lbl_motivo.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_motivo)

        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText(
            "Ejemplos:\n"
            "- Material defectuoso\n"
            "- Artículo incorrecto (pedimos X y trajeron Y)\n"
            "- Cantidad incorrecta (pedimos 5 y trajeron 10)\n"
            "- Material sobrante de obra\n"
            "- No cumple especificaciones"
        )
        self.txt_motivo.setMaximumHeight(100)
        layout.addWidget(self.txt_motivo)

        # Nota informativa
        nota = QLabel(
            "💡 Los artículos se descontarán del Almacén principal.\n"
            "Asegúrate de que el material esté físicamente en el almacén antes de registrar la devolución."
        )
        nota.setStyleSheet("color: #64748b; font-size: 11px; margin: 5px; padding: 8px; "
                          "background-color: #dbeafe; border-radius: 5px;")
        layout.addWidget(nota)

    def configurar_columnas_articulos(self):
        """Configura las columnas de la tabla de artículos"""
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels([
            "ID", "Artículo", "U.Medida", "Cantidad", "Acciones"
        ])
        self.tabla_articulos.setColumnHidden(0, True)

        header = self.tabla_articulos.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def _crear_selector_articulos(self, layout):
        """Sobrescribe el selector para usar BuscadorArticulos"""
        select_layout = QHBoxLayout()

        lbl_art = QLabel("Artículo:")

        # Usar BuscadorArticulos en lugar de QComboBox
        from src.dialogs.buscador_articulos import BuscadorArticulos
        self.buscador = BuscadorArticulos(
            self,
            mostrar_boton_lupa=True,
            placeholder="Buscar por EAN, referencia o nombre..."
        )
        self.buscador.articuloSeleccionado.connect(self.on_articulo_seleccionado)

        lbl_cant = QLabel("Cantidad:")

        from src.ui.widgets_personalizados import SpinBoxClimatot
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(120)

        from PySide6.QtWidgets import QPushButton
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.setMinimumHeight(40)
        self.btn_agregar.setEnabled(False)  # Deshabilitado hasta seleccionar artículo
        self.btn_agregar.clicked.connect(self.agregar_articulo)

        select_layout.addWidget(lbl_art)
        select_layout.addWidget(self.buscador, 2)
        select_layout.addWidget(lbl_cant)
        select_layout.addWidget(self.spin_cantidad)
        select_layout.addWidget(self.btn_agregar)

        layout.addLayout(select_layout)

    def cargar_proveedores(self):
        """Carga los proveedores"""
        try:
            proveedores = articulos_repo.get_proveedores()

            self.cmb_proveedor.addItem("(Seleccione proveedor)", None)
            for prov in proveedores:
                self.cmb_proveedor.addItem(prov['nombre'], prov['id'])
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar proveedores:\n{e}")

    def on_articulo_seleccionado(self, articulo):
        """Cuando se selecciona un artículo en el buscador"""
        self.articulo_actual = articulo
        self.btn_agregar.setEnabled(True)
        self.spin_cantidad.setFocus()
        self.spin_cantidad.line_edit.selectAll()

    def agregar_articulo(self):
        """Agrega un artículo a la lista temporal"""
        # Si hay texto en el buscador pero no hay artículo seleccionado, forzar búsqueda
        if not self.articulo_actual and self.buscador.txt_buscar.text().strip():
            self.buscador.buscar_exacto()
            if not self.articulo_actual:
                return  # La búsqueda ya habrá mostrado el diálogo de crear

        if not self.articulo_actual:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe buscar y seleccionar un artículo primero.")
            self.buscador.txt_buscar.setFocus()
            return

        cantidad = self.spin_cantidad.value()

        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['articulo_id'] == self.articulo_actual['id']:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.")
                return

        # Agregar
        self.articulos_temp.append({
            'articulo_id': self.articulo_actual['id'],
            'nombre': self.articulo_actual['nombre'],
            'u_medida': self.articulo_actual['u_medida'],
            'cantidad': cantidad
        })

        self.actualizar_tabla_articulos()

        # Limpiar selección
        self.articulo_actual = None
        self.btn_agregar.setEnabled(False)
        self.buscador.limpiar()
        self.spin_cantidad.setValue(1)
        self.buscador.txt_buscar.setFocus()

    def llenar_fila_articulo(self, fila, articulo):
        """Llena una fila de la tabla con los datos del artículo"""
        # ID (oculto)
        self.tabla_articulos.setItem(fila, 0, QTableWidgetItem(str(articulo['articulo_id'])))
        # Nombre
        self.tabla_articulos.setItem(fila, 1, QTableWidgetItem(articulo['nombre']))
        # U.Medida
        self.tabla_articulos.setItem(fila, 2, QTableWidgetItem(articulo['u_medida']))
        # Cantidad
        self.tabla_articulos.setItem(fila, 3, QTableWidgetItem(f"{articulo['cantidad']:.2f}"))
        # Botón quitar se añade en actualizar_tabla_articulos de la base

    def validar_antes_guardar(self):
        """Valida los datos antes de guardar"""
        self.proveedor_id = self.cmb_proveedor.currentData()
        if not self.proveedor_id:
            return False, "Debe seleccionar un proveedor."

        motivo = self.txt_motivo.toPlainText().strip()
        if not motivo:
            self.txt_motivo.setFocus()
            return False, "Debe especificar el motivo de la devolución."

        if not self.articulos_temp:
            return False, "Debe agregar al menos un artículo."

        return True, ""

    def ejecutar_guardado(self):
        """Ejecuta el guardado de la devolución"""
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        motivo = self.txt_motivo.toPlainText().strip()
        proveedor_nombre = self.cmb_proveedor.currentText()

        # Obtener ID del almacén principal
        almacen = movimientos_repo.get_almacen_by_nombre("Almacén")
        if not almacen:
            return False, "No se encontró el almacén principal."

        almacen_id = almacen['id']

        # Preparar datos para el service
        articulos = [
            {'articulo_id': art['articulo_id'], 'cantidad': art['cantidad']}
            for art in self.articulos_temp
        ]

        # Llamar al service
        exito, mensaje, ids_creados = movimientos_service.crear_devolucion_proveedor(
            fecha=fecha,
            almacen_id=almacen_id,
            articulos=articulos,
            motivo=motivo,
            usuario=session_manager.get_usuario_actual() or "admin"
        )

        if not exito:
            return False, f"Error al guardar:\n{mensaje}"

        # Guardar en historial
        usuario = session_manager.get_usuario_actual()
        if usuario:
            for art in self.articulos_temp:
                historial_service.guardar_en_historial(
                    usuario=usuario,
                    tipo_operacion='devolucion',
                    articulo_id=art['articulo_id'],
                    articulo_nombre=art['nombre'],
                    cantidad=art['cantidad'],
                    u_medida=art['u_medida'],
                    datos_adicionales={'proveedor': proveedor_nombre, 'motivo': motivo[:100]}
                )

        return True, (f"Devolución registrada correctamente.\n\n"
                     f"{len(self.articulos_temp)} artículo(s) devueltos a {proveedor_nombre}.")

    def configurar_atajos_teclado(self):
        """Configura los atajos de teclado para la ventana"""
        # F2: Focus en búsqueda de artículo
        shortcut_buscar = QShortcut(QKeySequence("F2"), self)
        shortcut_buscar.activated.connect(lambda: self.buscador.txt_buscar.setFocus())

        # F4: Focus en motivo
        shortcut_motivo = QShortcut(QKeySequence("F4"), self)
        shortcut_motivo.activated.connect(lambda: self.txt_motivo.setFocus())

        # F5: Limpiar formulario
        shortcut_limpiar = QShortcut(QKeySequence("F5"), self)
        shortcut_limpiar.activated.connect(self.limpiar_todo)

        # Ctrl+Return: Guardar devolución
        shortcut_guardar = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_guardar.activated.connect(self.guardar)

        # Esc: Cancelar/limpiar
        shortcut_cancelar = QShortcut(QKeySequence("Esc"), self)
        shortcut_cancelar.activated.connect(self.limpiar_y_cerrar)

        # Actualizar tooltips
        self.btn_guardar.setToolTip("Guardar devolución (Ctrl+Enter)")
        self.buscador.txt_buscar.setToolTip("Buscar artículo (F2)")
        self.txt_motivo.setToolTip("Motivo de devolución (F4)")

    def limpiar_todo(self):
        """Sobrescribe para limpiar también los campos específicos de devolución"""
        super().limpiar_todo()
        self.cmb_proveedor.setCurrentIndex(0)
        self.txt_albaran.clear()
        self.txt_motivo.clear()
        self.spin_cantidad.setValue(1)
