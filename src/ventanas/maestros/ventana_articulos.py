# ventana_articulos.py - Gestión de Artículos
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QCheckBox, QTextEdit,
    QDoubleSpinBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.services import articulos_service
from src.core.session_manager import session_manager
from src.repos import articulos_repo

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR ARTÍCULO
# ========================================
class DialogoArticulo(QDialog):
    def __init__(self, parent=None, articulo_id=None, referencia_inicial=""):
        super().__init__(parent)
        self.articulo_id = articulo_id
        self.referencia_inicial = referencia_inicial
        self.setWindowTitle("✏️ Editar Artículo" if articulo_id else "➕ Nuevo Artículo")
        self.setMinimumSize(600, 600)
        self.resize(700, 700)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        # Scroll area para todo el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # ========== GRUPO 1: IDENTIFICACIÓN ==========
        grupo_id = QGroupBox("📋 Identificación del Artículo")
        form_id = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre descriptivo del artículo")
        
        self.txt_ean = QLineEdit()
        self.txt_ean.setPlaceholderText("Código de barras EAN (opcional)")
        
        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText("Referencia del fabricante/proveedor")
        
        self.txt_palabras = QTextEdit()
        self.txt_palabras.setPlaceholderText("Palabras clave para búsquedas (ej: montante, barra omega, pladur)")
        self.txt_palabras.setMaximumHeight(60)
        
        form_id.addRow("📦 Nombre *:", self.txt_nombre)
        form_id.addRow("🔢 EAN:", self.txt_ean)
        form_id.addRow("🏷️ Referencia:", self.txt_ref)
        form_id.addRow("🔍 Palabras clave:", self.txt_palabras)
        
        grupo_id.setLayout(form_id)
        layout.addWidget(grupo_id)
        
        # ========== GRUPO 2: CLASIFICACIÓN ==========
        grupo_clasif = QGroupBox("📂 Clasificación y Ubicación")
        form_clasif = QFormLayout()
        
        self.cmb_familia = QComboBox()
        self.cargar_familias()
        
        self.cmb_ubicacion = QComboBox()
        self.cargar_ubicaciones()
        
        self.cmb_proveedor = QComboBox()
        self.cargar_proveedores()
        
        self.txt_marca = QLineEdit()
        self.txt_marca.setPlaceholderText("Marca del producto")
        
        form_clasif.addRow("📂 Familia:", self.cmb_familia)
        form_clasif.addRow("📍 Ubicación:", self.cmb_ubicacion)
        form_clasif.addRow("🏭 Proveedor principal:", self.cmb_proveedor)
        form_clasif.addRow("🏢 Marca:", self.txt_marca)
        
        grupo_clasif.setLayout(form_clasif)
        layout.addWidget(grupo_clasif)
        
        # ========== GRUPO 3: UNIDADES Y STOCK ==========
        grupo_stock = QGroupBox("📊 Unidades y Stock")
        form_stock = QFormLayout()
        
        self.cmb_unidad = QComboBox()
        self.cmb_unidad.addItems(["unidad", "metro", "kilogramo", "litro", "metro cuadrado", "caja", "pack"])
        self.cmb_unidad.setEditable(True)
        
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 999999)
        self.spin_min.setDecimals(2)
        self.spin_min.setSuffix(" unidades")
        
        form_stock.addRow("📏 Unidad de medida:", self.cmb_unidad)
        form_stock.addRow("⚠️ Stock mínimo (alerta):", self.spin_min)
        
        grupo_stock.setLayout(form_stock)
        layout.addWidget(grupo_stock)
        
        # ========== GRUPO 4: PRECIOS ==========
        grupo_precios = QGroupBox("💰 Precios")
        form_precios = QFormLayout()
        
        self.spin_coste = QDoubleSpinBox()
        self.spin_coste.setRange(0, 999999)
        self.spin_coste.setDecimals(2)
        self.spin_coste.setPrefix("€ ")
        
        self.spin_pvp = QDoubleSpinBox()
        self.spin_pvp.setRange(0, 999999)
        self.spin_pvp.setDecimals(2)
        self.spin_pvp.setPrefix("€ ")
        
        self.spin_iva = QDoubleSpinBox()
        self.spin_iva.setRange(0, 100)
        self.spin_iva.setDecimals(0)
        self.spin_iva.setValue(21)
        self.spin_iva.setSuffix(" %")
        
        form_precios.addRow("💵 Coste (compra):", self.spin_coste)
        form_precios.addRow("💶 PVP sin IVA:", self.spin_pvp)
        form_precios.addRow("📈 IVA:", self.spin_iva)
        
        grupo_precios.setLayout(form_precios)
        layout.addWidget(grupo_precios)
        
        # ========== ESTADO ==========
        self.chk_activo = QCheckBox("✅ Artículo activo (visible en el sistema)")
        self.chk_activo.setChecked(True)
        self.chk_activo.setStyleSheet("font-weight: bold; margin: 10px;")
        layout.addWidget(self.chk_activo)
        
        # Nota
        nota = QLabel("* El nombre es obligatorio. Los demás campos son opcionales.")
        nota.setStyleSheet("color: gray; font-size: 11px; margin: 5px;")
        layout.addWidget(nota)
        
        scroll.setWidget(content_widget)
        
        # Layout principal del diálogo
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Artículo")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        main_layout.addLayout(btn_layout)
        
        # Si estamos editando, cargar datos
        if self.articulo_id:
            self.cargar_datos()
        elif self.referencia_inicial:
            # Si es un artículo nuevo con referencia inicial, pre-llenar el campo
            self.txt_ref.setText(self.referencia_inicial)
            self.txt_nombre.setFocus()
        else:
            # Focus en el campo de nombre
            self.txt_nombre.setFocus()
    
    def cargar_familias(self):
        """Carga las familias en el combo"""
        try:
            familias = articulos_repo.get_familias()

            self.cmb_familia.addItem("(Sin familia)", None)
            for fam in familias:
                self.cmb_familia.addItem(fam['nombre'], fam['id'])
        except Exception:
            pass
    
    def cargar_ubicaciones(self):
        """Carga las ubicaciones en el combo"""
        try:
            ubicaciones = articulos_repo.get_ubicaciones()

            self.cmb_ubicacion.addItem("(Sin ubicación)", None)
            for ubi in ubicaciones:
                self.cmb_ubicacion.addItem(ubi['nombre'], ubi['id'])
        except Exception:
            pass
    
    def cargar_proveedores(self):
        """Carga los proveedores en el combo"""
        try:
            proveedores = articulos_repo.get_proveedores()

            self.cmb_proveedor.addItem("(Sin proveedor)", None)
            for prov in proveedores:
                self.cmb_proveedor.addItem(prov['nombre'], prov['id'])
        except Exception:
            pass
    
    def cargar_datos(self):
        """Carga los datos del artículo a editar"""
        try:
            articulo = articulos_service.obtener_articulo(self.articulo_id)

            if articulo:
                self.txt_ean.setText(articulo['ean'] or "")
                self.txt_ref.setText(articulo['ref_proveedor'] or "")
                self.txt_nombre.setText(articulo['nombre'] or "")
                self.txt_palabras.setPlainText(articulo['palabras_clave'] or "")

                # Unidad de medida
                idx = self.cmb_unidad.findText(articulo['u_medida'] or "unidad")
                if idx >= 0:
                    self.cmb_unidad.setCurrentIndex(idx)

                self.spin_min.setValue(articulo['min_alerta'] or 0)

                # Ubicación
                if articulo['ubicacion_id']:
                    idx = self.cmb_ubicacion.findData(articulo['ubicacion_id'])
                    if idx >= 0:
                        self.cmb_ubicacion.setCurrentIndex(idx)

                # Proveedor
                if articulo['proveedor_id']:
                    idx = self.cmb_proveedor.findData(articulo['proveedor_id'])
                    if idx >= 0:
                        self.cmb_proveedor.setCurrentIndex(idx)

                # Familia
                if articulo['familia_id']:
                    idx = self.cmb_familia.findData(articulo['familia_id'])
                    if idx >= 0:
                        self.cmb_familia.setCurrentIndex(idx)

                self.txt_marca.setText(articulo['marca'] or "")
                self.spin_coste.setValue(articulo['coste'] or 0)
                self.spin_pvp.setValue(articulo['pvp_sin'] or 0)
                self.spin_iva.setValue(articulo['iva'] or 21)
                self.chk_activo.setChecked(articulo['activo'] == 1)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el artículo (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()

        # Recoger todos los datos
        ean = self.txt_ean.text().strip() or None
        ref = self.txt_ref.text().strip() or None
        palabras = self.txt_palabras.toPlainText().strip() or None
        u_medida = self.cmb_unidad.currentText()
        min_alerta = self.spin_min.value()
        ubicacion_id = self.cmb_ubicacion.currentData()
        proveedor_id = self.cmb_proveedor.currentData()
        familia_id = self.cmb_familia.currentData()
        marca = self.txt_marca.text().strip() or None
        coste = self.spin_coste.value()
        pvp = self.spin_pvp.value()
        iva = self.spin_iva.value()
        activo = self.chk_activo.isChecked()

        # Llamar al service
        if self.articulo_id:
            # Editar existente
            exito, mensaje = articulos_service.actualizar_articulo(
                articulo_id=self.articulo_id,
                nombre=nombre,
                ean=ean,
                ref_proveedor=ref,
                palabras_clave=palabras,
                u_medida=u_medida,
                min_alerta=min_alerta,
                ubicacion_id=ubicacion_id,
                proveedor_id=proveedor_id,
                familia_id=familia_id,
                marca=marca,
                coste=coste,
                pvp_sin=pvp,
                iva=iva,
                activo=activo,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            # Crear nuevo
            exito, mensaje, articulo_id = articulos_service.crear_articulo(
                nombre=nombre,
                ean=ean,
                ref_proveedor=ref,
                palabras_clave=palabras,
                u_medida=u_medida,
                min_alerta=min_alerta,
                ubicacion_id=ubicacion_id,
                proveedor_id=proveedor_id,
                familia_id=familia_id,
                marca=marca,
                coste=coste,
                pvp_sin=pvp,
                iva=iva,
                activo=activo,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

# ========================================
# VENTANA PRINCIPAL DE ARTÍCULOS
# ========================================
class VentanaArticulos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Gestión de Artículos")
        self.resize(1100, 650)
        self.setMinimumSize(900, 500)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📦 Gestión de Artículos del Almacén")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Barra de búsqueda y filtros
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, EAN, referencia o palabras clave...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        lbl_familia = QLabel("Familia:")
        self.cmb_familia_filtro = QComboBox()
        self.cmb_familia_filtro.addItem("Todas", None)
        self.cargar_familias_filtro()
        self.cmb_familia_filtro.currentTextChanged.connect(self.buscar)
        
        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Todos", "Solo Activos", "Solo Inactivos"])
        self.cmb_estado.currentTextChanged.connect(self.buscar)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar, 3)
        top_layout.addWidget(lbl_familia)
        top_layout.addWidget(self.cmb_familia_filtro, 1)
        top_layout.addWidget(lbl_estado)
        top_layout.addWidget(self.cmb_estado, 1)
        
        layout.addLayout(top_layout)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("➕ Nuevo Artículo")
        self.btn_nuevo.clicked.connect(self.nuevo_articulo)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_articulo)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_articulo)
        self.btn_eliminar.setEnabled(False)
        
        btn_layout.addWidget(self.btn_nuevo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Tabla de artículos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "EAN", "Ref", "Nombre", "Familia", "U.Medida", "Stock Mín", "Coste", "Estado"
        ])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_articulo)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Nombre
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_articulos()
    
    def cargar_familias_filtro(self):
        """Carga las familias en el combo de filtro"""
        try:
            familias = articulos_repo.get_familias()

            for fam in familias:
                self.cmb_familia_filtro.addItem(fam['nombre'], fam['id'])
        except Exception:
            pass
    
    def cargar_articulos(self):
        """Carga los artículos en la tabla"""
        filtro_texto = self.txt_buscar.text().strip() or None
        familia_id = self.cmb_familia_filtro.currentData()
        estado = self.cmb_estado.currentText()

        # Convertir estado a booleano o None
        solo_activos = None
        if estado == "Solo Activos":
            solo_activos = True
        elif estado == "Solo Inactivos":
            solo_activos = False

        try:
            articulos = articulos_service.obtener_articulos(
                filtro_texto=filtro_texto,
                familia_id=familia_id,
                solo_activos=solo_activos,
                limit=1000
            )

            self.tabla.setRowCount(len(articulos))

            for i, art in enumerate(articulos):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(art['id'])))
                # EAN
                self.tabla.setItem(i, 1, QTableWidgetItem(art['ean'] or ""))
                # Ref
                self.tabla.setItem(i, 2, QTableWidgetItem(art['ref_proveedor'] or ""))
                # Nombre
                self.tabla.setItem(i, 3, QTableWidgetItem(art['nombre']))
                # Familia
                self.tabla.setItem(i, 4, QTableWidgetItem(art['familia_nombre'] or "-"))
                # U.Medida
                self.tabla.setItem(i, 5, QTableWidgetItem(art['u_medida'] or "unidad"))
                # Stock Mín
                self.tabla.setItem(i, 6, QTableWidgetItem(str(art['min_alerta'] or 0)))
                # Coste
                coste_txt = f"€ {art['coste']:.2f}" if art['coste'] else "€ 0.00"
                self.tabla.setItem(i, 7, QTableWidgetItem(coste_txt))
                # Estado
                estado_txt = "✅ Activo" if art['activo'] == 1 else "❌ Inactivo"
                item_estado = QTableWidgetItem(estado_txt)
                if art['activo'] == 0:
                    item_estado.setForeground(Qt.gray)
                self.tabla.setItem(i, 8, item_estado)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def buscar(self):
        """Filtra la tabla"""
        self.cargar_articulos()
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nuevo_articulo(self):
        """Abre el diálogo para crear un nuevo artículo"""
        dialogo = DialogoArticulo(self)
        if dialogo.exec():
            self.cargar_articulos()
    
    def editar_articulo(self):
        """Abre el diálogo para editar el artículo seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        articulo_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoArticulo(self, articulo_id)
        if dialogo.exec():
            self.cargar_articulos()
    
    def eliminar_articulo(self):
        """Elimina el artículo seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return

        articulo_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 3).text()

        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar el artículo '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.\n"
            "Si el artículo tiene movimientos, no podrá eliminarse.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Llamar al service
        exito, mensaje = articulos_service.eliminar_articulo(
            articulo_id=articulo_id,
            usuario=session_manager.get_usuario_actual() or "admin"
        )

        if not exito:
            QMessageBox.warning(self, "⚠️ No se puede eliminar", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.cargar_articulos()