# ventana_imputacion.py - Imputar Material a OT
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QComboBox,
    QHeaderView, QTableWidgetItem, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
import datetime

from src.ui.ventana_operativa_base import VentanaOperativaBase
from src.ui.widgets_personalizados import SpinBoxClimatot
from src.ui.combo_loaders import ComboLoader
from src.ui.dialog_manager import DialogManager
from src.core.logger import logger
from src.services import movimientos_service, historial_service, almacenes_service
from src.repos import movimientos_repo
from src.core.session_manager import session_manager


# ========================================
# VENTANA DE IMPUTACIÓN
# ========================================
class VentanaImputacion(VentanaOperativaBase):
    """
    Ventana para imputar material a órdenes de trabajo.
    Hereda de VentanaOperativaBase para aprovechar toda la estructura común.
    """

    def __init__(self, parent=None):
        self.operario_id = None
        self.furgoneta_id = None
        super().__init__(
            titulo="📝 Imputar Material a Orden de Trabajo",
            descripcion="Registra el material usado por los operarios en trabajos de instalación",
            mostrar_fecha=True,
            parent=parent
        )

        # Configurar atajos de teclado
        self.configurar_atajos_teclado()

        # Mostrar ayuda de atajos
        ayuda_atajos = QLabel(
            "⌨️ Atajos: F2=Buscar artículo | F3=Focus OT | F5=Limpiar | "
            "Ctrl+Enter=Guardar | Esc=Cancelar"
        )
        ayuda_atajos.setStyleSheet(
            "background-color: #f1f5f9; padding: 8px; border-radius: 4px; "
            "color: #475569; font-size: 11px; margin-top: 5px;"
        )
        ayuda_atajos.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(ayuda_atajos)

        # Focus inicial
        self.txt_ot.setFocus()

    def configurar_dimensiones(self):
        """Personaliza las dimensiones para la ventana de imputación"""
        self.setMinimumSize(900, 600)
        self.resize(1100, 750)

    def crear_formulario_cabecera(self, layout):
        """Crea el formulario de cabecera con operario, furgoneta y OT"""
        form = QFormLayout()

        # Operario
        h_operario = QHBoxLayout()
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(200)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)

        # Furgoneta (label informativo)
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")

        h_operario.addWidget(self.cmb_operario)
        h_operario.addSpacing(20)
        h_operario.addWidget(QLabel("🚚 Furgoneta:"))
        h_operario.addWidget(self.lbl_furgoneta_asignada)
        h_operario.addStretch()

        form.addRow("👷 Operario:", h_operario)

        # Orden de Trabajo
        self.txt_ot = QLineEdit()
        self.txt_ot.setPlaceholderText("Número de Orden de Trabajo (ej: OT-2025-001)")
        self.txt_ot.setMinimumWidth(300)
        form.addRow("📄 Nº OT *:", self.txt_ot)

        layout.addLayout(form)

        # Nota
        nota_ot = QLabel("💡 Si no hay OT específica, puedes dejarla en blanco")
        nota_ot.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic; margin: 5px;")
        layout.addWidget(nota_ot)

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
        """Sobrescribe el selector para usar ComboBox y mostrar stock"""
        select_layout = QHBoxLayout()

        lbl_art = QLabel("Artículo:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(400)
        self.cmb_articulo.currentIndexChanged.connect(self.articulo_seleccionado)

        lbl_cant = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(120)

        from PySide6.QtWidgets import QPushButton
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.setMinimumHeight(40)
        self.btn_agregar.clicked.connect(self.agregar_articulo)

        select_layout.addWidget(lbl_art)
        select_layout.addWidget(self.cmb_articulo, 2)
        select_layout.addWidget(lbl_cant)
        select_layout.addWidget(self.spin_cantidad)
        select_layout.addWidget(self.btn_agregar)

        layout.addLayout(select_layout)

    def cargar_operarios(self):
        """Carga los operarios activos usando ComboLoader"""
        exito = ComboLoader.cargar_operarios(
            self.cmb_operario,
            movimientos_repo.get_operarios_activos,
            opcion_vacia=True,
            texto_vacio="(Seleccione operario)",
            con_emoji=True
        )
        if not exito:
            DialogManager.mostrar_error(self, "Error al cargar operarios")

    def cambio_operario(self):
        """Al cambiar de operario, busca su furgoneta y carga artículos"""
        self.operario_id = self.cmb_operario.currentData()
        if not self.operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            self.cmb_articulo.clear()
            self.furgoneta_id = None
            return

        try:
            from src.services.furgonetas_service import obtener_furgoneta_operario
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            furgoneta = obtener_furgoneta_operario(self.operario_id, fecha_hoy)

            if furgoneta:
                self.lbl_furgoneta_asignada.setText(f"🚚 Furgoneta {furgoneta['furgoneta_nombre']}")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #1e3a8a; font-weight: bold;")
                self.furgoneta_id = furgoneta['furgoneta_id']
                self.cargar_articulos_furgoneta()
            else:
                self.lbl_furgoneta_asignada.setText("⚠️ Sin furgoneta asignada hoy")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #dc2626; font-weight: bold;")
                self.furgoneta_id = None
                self.cmb_articulo.clear()
        except Exception as e:
            logger.exception(f"Error al cambiar operario en imputación: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error:\n{e}")

    def cargar_articulos_furgoneta(self):
        """Carga los artículos disponibles en la furgoneta del operario"""
        if not self.furgoneta_id:
            return

        try:
            # Obtener stock actual en la furgoneta usando el service
            articulos = almacenes_service.obtener_stock_almacen(self.furgoneta_id)

            self.cmb_articulo.clear()
            self.cmb_articulo.addItem("(Seleccione artículo)", None)

            for art in articulos:
                texto = f"{art['nombre']} ({art['u_medida']}) - Stock: {art['stock']:.2f}"
                self.cmb_articulo.addItem(texto, {
                    'id': art['id'],
                    'nombre': art['nombre'],
                    'u_medida': art['u_medida'],
                    'stock': art['stock']
                })
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")

    def articulo_seleccionado(self):
        """Cuando se selecciona un artículo, ajustar cantidad máxima"""
        data = self.cmb_articulo.currentData()
        if data and isinstance(data, dict):
            # Ajustar rango según stock disponible
            self.spin_cantidad.setRange(0.01, data['stock'])
            self.spin_cantidad.setValue(min(1.0, data['stock']))

    def agregar_articulo(self):
        """Agrega un artículo a la lista temporal"""
        data = self.cmb_articulo.currentData()
        if not data or not isinstance(data, dict):
            QMessageBox.warning(self, "⚠️ Aviso", "Seleccione un artículo.")
            return

        cantidad = self.spin_cantidad.value()

        # Verificar que no exceda el stock
        if cantidad > data['stock']:
            QMessageBox.warning(self, "⚠️ Aviso", f"No hay suficiente stock.\nDisponible: {data['stock']:.2f}")
            return

        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['articulo_id'] == data['id']:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.")
                return

        # Agregar
        self.articulos_temp.append({
            'articulo_id': data['id'],
            'nombre': data['nombre'],
            'u_medida': data['u_medida'],
            'cantidad': cantidad,
            'stock': data['stock']
        })

        self.actualizar_tabla_articulos()
        self.spin_cantidad.setValue(1)

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
        if not self.operario_id:
            return False, "Debe seleccionar un operario."

        if not self.furgoneta_id:
            return False, "El operario no tiene furgoneta asignada."

        ot = self.txt_ot.text().strip()
        if not ot:
            self.txt_ot.setFocus()
            return False, "El número de OT es obligatorio."

        if not self.articulos_temp:
            return False, "Debe agregar al menos un artículo."

        return True, ""

    def ejecutar_guardado(self):
        """Ejecuta el guardado de la imputación"""
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        ot = self.txt_ot.text().strip()
        operario_nombre = self.cmb_operario.currentText()

        # Preparar datos para el service
        articulos = [
            {'articulo_id': art['articulo_id'], 'cantidad': art['cantidad']}
            for art in self.articulos_temp
        ]

        # Llamar al service
        exito, mensaje, ids_creados = movimientos_service.crear_imputacion_obra(
            fecha=fecha,
            operario_id=self.operario_id,
            articulos=articulos,
            ot=ot,
            motivo=None,
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
                    tipo_operacion='imputacion',
                    articulo_id=art['articulo_id'],
                    articulo_nombre=art['nombre'],
                    cantidad=art['cantidad'],
                    u_medida=art['u_medida'],
                    datos_adicionales={'ot': ot, 'operario': operario_nombre}
                )

        return True, f"Imputación registrada correctamente.\n\n{mensaje}"

    def configurar_atajos_teclado(self):
        """Configura los atajos de teclado para la ventana"""
        # F2: Focus en búsqueda de artículo
        shortcut_buscar = QShortcut(QKeySequence("F2"), self)
        shortcut_buscar.activated.connect(lambda: self.cmb_articulo.setFocus())

        # F3: Focus en campo OT
        shortcut_ot = QShortcut(QKeySequence("F3"), self)
        shortcut_ot.activated.connect(lambda: self.txt_ot.setFocus())

        # F5: Limpiar formulario
        shortcut_limpiar = QShortcut(QKeySequence("F5"), self)
        shortcut_limpiar.activated.connect(self.limpiar_todo)

        # Ctrl+Return: Guardar imputación
        shortcut_guardar = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_guardar.activated.connect(self.guardar)

        # Esc: Cancelar/limpiar
        shortcut_cancelar = QShortcut(QKeySequence("Esc"), self)
        shortcut_cancelar.activated.connect(self.limpiar_y_cerrar)

        # Actualizar tooltips
        self.btn_guardar.setToolTip("Guardar imputación (Ctrl+Enter)")
        self.cmb_articulo.setToolTip("Buscar artículo (F2)")
        self.txt_ot.setToolTip("Número de OT (F3)")

    def limpiar_todo(self):
        """Sobrescribe para limpiar también los campos específicos de imputación"""
        super().limpiar_todo()
        self.txt_ot.clear()
        self.spin_cantidad.setValue(1)
        self.cmb_operario.setCurrentIndex(0)
