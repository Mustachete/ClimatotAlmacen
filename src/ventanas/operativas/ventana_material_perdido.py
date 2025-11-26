# ventana_material_perdido.py - Registro de Material Perdido
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QGroupBox, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QShortcut, QKeySequence
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_personalizados import SpinBoxClimatot
from src.core.logger import logger
from src.services import movimientos_service, historial_service, almacenes_service
from src.core.session_manager import session_manager
from src.repos import movimientos_repo

# ========================================
# VENTANA DE MATERIAL PERDIDO
# ========================================
class VentanaMaterialPerdido(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Registro de Material Perdido")
        self.setMinimumSize(750, 550)
        self.resize(900, 700)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("⚠️ Registro de Material Perdido")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #dc2626;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("⚠️ SOLO ADMINISTRADOR - Registra material perdido, roto o sin justificación")
        desc.setStyleSheet("color: #dc2626; font-size: 13px; margin-bottom: 10px; font-weight: bold;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DEL INCIDENTE ==========
        grupo_datos = QGroupBox("📋 Datos del Incidente")
        datos_layout = QVBoxLayout()
        
        # Fila 1: Fecha y Operario
        fila1 = QHBoxLayout()
        
        lbl_fecha = QLabel("📅 Fecha del incidente:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        lbl_operario = QLabel("👷 Operario responsable *:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(250)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)
        
        fila1.addWidget(lbl_fecha)
        fila1.addWidget(self.date_fecha)
        fila1.addSpacing(20)
        fila1.addWidget(lbl_operario)
        fila1.addWidget(self.cmb_operario)
        fila1.addStretch()
        
        # Fila 2: Furgoneta
        fila2 = QHBoxLayout()
        
        lbl_furgoneta = QLabel("🚚 Furgoneta asignada:")
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
        
        fila2.addWidget(lbl_furgoneta)
        fila2.addWidget(self.lbl_furgoneta_asignada)
        fila2.addStretch()
        
        datos_layout.addLayout(fila1)
        datos_layout.addLayout(fila2)
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: ARTÍCULO PERDIDO ==========
        grupo_articulo = QGroupBox("📦 Artículo Perdido")
        articulo_layout = QVBoxLayout()
        
        # Selector de artículo
        select_layout = QHBoxLayout()
        
        lbl_art = QLabel("Artículo *:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(350)
        self.cargar_articulos()
        
        lbl_cant = QLabel("Cantidad *:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(120)
        
        select_layout.addWidget(lbl_art)
        select_layout.addWidget(self.cmb_articulo, 2)
        select_layout.addWidget(lbl_cant)
        select_layout.addWidget(self.spin_cantidad)
        select_layout.addStretch()
        
        articulo_layout.addLayout(select_layout)
        
        grupo_articulo.setLayout(articulo_layout)
        layout.addWidget(grupo_articulo)
        
        # ========== GRUPO: MOTIVO ==========
        grupo_motivo = QGroupBox("📝 Motivo / Justificación")
        motivo_layout = QVBoxLayout()
        
        lbl_motivo = QLabel("Describe qué ocurrió *:")
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText(
            "Ejemplos:\n"
            "- Material roto durante la instalación\n"
            "- Material perdido en el transporte\n"
            "- Error en el conteo\n"
            "- Artículo defectuoso\n"
            "- Sin justificación clara"
        )
        self.txt_motivo.setMaximumHeight(120)
        
        motivo_layout.addWidget(lbl_motivo)
        motivo_layout.addWidget(self.txt_motivo)
        
        grupo_motivo.setLayout(motivo_layout)
        layout.addWidget(grupo_motivo)
        
        # Nota
        nota = QLabel(
            "* Campos obligatorios\n\n"
            "⚠️ Esta acción quedará registrada en el historial del operario.\n"
            "El material se descontará de la furgoneta del operario."
        )
        nota.setStyleSheet("color: #dc2626; font-size: 12px; margin: 10px; padding: 10px; "
                          "background-color: #fee2e2; border-radius: 5px;")
        layout.addWidget(nota)
        
        # ========== BOTONES ==========
        layout.addStretch()
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("⚠️ REGISTRAR PÉRDIDA")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                background-color: white;
                border: 2px solid #dc2626;
                color: #dc2626;
            }
            QPushButton:hover {
                background-color: #dc2626;
                color: white;
            }
        """)
        self.btn_guardar.clicked.connect(self.guardar_perdida)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 2)
        botones_layout.addWidget(self.btn_cancelar, 1)
        botones_layout.addWidget(self.btn_volver, 1)

        layout.addLayout(botones_layout)

        # ========== ATAJOS DE TECLADO ==========
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
        layout.addWidget(ayuda_atajos)

        # Focus inicial
        self.cmb_articulo.setFocus()

    def configurar_atajos_teclado(self):
        """Configura los atajos de teclado para la ventana"""
        # F2: Focus en búsqueda de artículo
        shortcut_buscar = QShortcut(QKeySequence("F2"), self)
        shortcut_buscar.activated.connect(lambda: self.cmb_articulo.setFocus())

        # F4: Focus en motivo
        shortcut_motivo = QShortcut(QKeySequence("F4"), self)
        shortcut_motivo.activated.connect(lambda: self.txt_motivo.setFocus())

        # F5: Limpiar formulario
        shortcut_limpiar = QShortcut(QKeySequence("F5"), self)
        shortcut_limpiar.activated.connect(self.limpiar)

        # Ctrl+Return: Guardar registro
        shortcut_guardar = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_guardar.activated.connect(self.guardar_perdida)

        # Esc: Cancelar/limpiar
        shortcut_cancelar = QShortcut(QKeySequence("Esc"), self)
        shortcut_cancelar.activated.connect(self.limpiar)

        # Actualizar tooltips
        self.btn_guardar.setToolTip("Guardar registro (Ctrl+Enter)")
        self.btn_cancelar.setToolTip("Cancelar y limpiar (Esc)")
        self.cmb_articulo.setToolTip("Buscar artículo (F2)")
        self.txt_motivo.setToolTip("Motivo de pérdida (F4)")

    def cargar_operarios(self):
        """Carga los operarios activos"""
        try:
            operarios = movimientos_repo.get_operarios_activos()

            self.cmb_operario.addItem("(Seleccione operario)", None)
            for op in operarios:
                emoji = "👷" if op['rol_operario'] == "oficial" else "🔨"
                texto = f"{emoji} {op['nombre']} ({op['rol_operario']})"
                self.cmb_operario.addItem(texto, op['id'])
        except Exception as e:
            logger.error(f"Error al cargar operarios: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")
    
    def cambio_operario(self):
        """Al cambiar de operario, busca su furgoneta y carga artículos de la furgoneta"""
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            self.furgoneta_id = None
            self.cmb_articulo.clear()
            self.cmb_articulo.addItem("(Seleccione operario primero)", None)
            return

        try:
            from src.services.furgonetas_service import obtener_furgoneta_operario
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            furgoneta = obtener_furgoneta_operario(operario_id, fecha_hoy)

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
                self.cmb_articulo.addItem("(Sin furgoneta asignada)", None)
        except Exception as e:
            logger.warning(f"Error al obtener furgoneta para material perdido: {e}")
    
    def cargar_articulos(self):
        """Carga artículos - se llama al inicio pero está vacío hasta seleccionar operario"""
        self.cmb_articulo.clear()
        self.cmb_articulo.addItem("(Seleccione operario primero)", None)

    def cargar_articulos_furgoneta(self):
        """Carga los artículos disponibles en la furgoneta del operario"""
        if not self.furgoneta_id:
            self.cmb_articulo.clear()
            self.cmb_articulo.addItem("(Sin furgoneta asignada)", None)
            return

        try:
            # Usar almacenes_service en lugar de SQL directo
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
            logger.exception(f"Error al cargar artículos de la furgoneta: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def guardar_perdida(self):
        """Guarda el registro de material perdido usando el service"""
        # Validaciones básicas
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un operario responsable.")
            return

        if not self.furgoneta_id:
            QMessageBox.warning(self, "⚠️ Aviso", "El operario no tiene furgoneta asignada.")
            return

        articulo_data = self.cmb_articulo.currentData()
        if not articulo_data or not isinstance(articulo_data, dict):
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un artículo.")
            return

        cantidad = self.spin_cantidad.value()
        motivo = self.txt_motivo.toPlainText().strip()

        if not motivo:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe especificar el motivo de la pérdida.")
            self.txt_motivo.setFocus()
            return

        fecha = self.date_fecha.date().toString("yyyy-MM-dd")

        # Confirmación
        operario_nombre = self.cmb_operario.currentText()
        articulo_nombre = articulo_data['nombre']

        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar registro de pérdida",
            f"¿Confirma el registro de esta pérdida?\n\n"
            f"Operario: {operario_nombre}\n"
            f"Artículo: {articulo_nombre}\n"
            f"Cantidad: {cantidad:.2f} {articulo_data['u_medida']}\n"
            f"Motivo: {motivo[:50]}...\n\n"
            f"Esta acción NO se puede deshacer y quedará en el historial.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Preparar datos para el service
        articulos = [{'articulo_id': articulo_data['id'], 'cantidad': cantidad}]

        # Llamar al service
        exito, mensaje, ids_creados = movimientos_service.crear_material_perdido(
            fecha=fecha,
            almacen_id=self.furgoneta_id,
            articulos=articulos,
            motivo=motivo,
            usuario=session_manager.get_usuario_actual() or "admin"
        )

        if not exito:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{mensaje}")
            return

        # Guardar en historial
        usuario = session_manager.get_usuario_actual()
        if usuario:
            historial_service.guardar_en_historial(
                usuario=usuario,
                tipo_operacion='material_perdido',
                articulo_id=articulo_data['id'],
                articulo_nombre=articulo_data['nombre'],
                cantidad=cantidad,
                u_medida=articulo_data['u_medida'],
                datos_adicionales={'motivo': motivo[:100]}
            )

        QMessageBox.information(
            self,
            "✅ Registrado",
            f"Pérdida registrada correctamente.\n\n"
            f"Operario: {operario_nombre}\n"
            f"Artículo: {articulo_nombre}\n"
            f"Cantidad: {cantidad:.2f}"
        )

        self.limpiar()
    
    def limpiar(self):
        """Limpia todos los campos"""
        self.cmb_operario.setCurrentIndex(0)
        self.cmb_articulo.setCurrentIndex(0)
        self.spin_cantidad.setValue(1)
        self.txt_motivo.clear()
        self.date_fecha.setDate(QDate.currentDate())