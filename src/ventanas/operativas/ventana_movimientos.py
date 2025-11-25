# ventana_movimientos.py - Hacer Movimientos (Supermercado)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QRadioButton, QButtonGroup, QGroupBox, QHeaderView, QDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_personalizados import SpinBoxClimatot, crear_boton_quitar_centrado
from src.ui.combo_loaders import ComboLoader
from src.ui.dialog_manager import DialogManager
from src.core.logger import logger
from src.core.error_handler import handle_db_errors, validate_field, show_warning, show_info
from src.services import movimientos_service, historial_service
from src.repos import movimientos_repo, articulos_repo
from src.services.furgonetas_service import list_furgonetas
from src.core.session_manager import session_manager

# ========================================
# VENTANA DE HACER MOVIMIENTOS
# ========================================
class VentanaMovimientos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Hacer Movimientos - Supermercado")
        self.setMinimumSize(900, 600)
        self.resize(1100, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Lista temporal de artículos
        self.articulos_temp = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("🔄 Hacer Movimientos - Supermercado")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Registra entregas y devoluciones de material entre almacén y furgonetas")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DEL MOVIMIENTO ==========
        grupo_datos = QGroupBox("📋 Datos del Movimiento")
        datos_layout = QHBoxLayout()
        
        # Fecha
        lbl_fecha = QLabel("📅 Fecha:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        # Operario/Furgoneta
        lbl_operario = QLabel("👷 Operario:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(200)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)
        
        lbl_furgoneta = QLabel("🚚 Furgoneta:")
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")

        # Botón para asignar/cambiar furgoneta
        self.btn_asignar_furgoneta = QPushButton("Asignar Furgoneta")
        self.btn_asignar_furgoneta.setMaximumWidth(150)
        self.btn_asignar_furgoneta.clicked.connect(self.abrir_dialogo_asignar_furgoneta)
        self.btn_asignar_furgoneta.setEnabled(False)  # Habilitado solo cuando hay operario seleccionado

        datos_layout.addWidget(lbl_fecha)
        datos_layout.addWidget(self.date_fecha)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_operario)
        datos_layout.addWidget(self.cmb_operario)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_furgoneta)
        datos_layout.addWidget(self.lbl_furgoneta_asignada)
        datos_layout.addWidget(self.btn_asignar_furgoneta)
        datos_layout.addStretch()
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: MODO DE OPERACIÓN ==========
        grupo_modo = QGroupBox("🔀 Modo de Operación")
        modo_layout = QHBoxLayout()
        
        self.btn_group_modo = QButtonGroup()
        
        self.radio_entregar = QRadioButton("📤 ENTREGAR material (Almacén → Furgoneta)")
        self.radio_entregar.setChecked(True)
        self.radio_entregar.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.radio_recibir = QRadioButton("📥 RECIBIR material (Furgoneta → Almacén)")
        self.radio_recibir.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.btn_group_modo.addButton(self.radio_entregar, 1)
        self.btn_group_modo.addButton(self.radio_recibir, 2)
        
        modo_layout.addWidget(self.radio_entregar)
        modo_layout.addSpacing(30)
        modo_layout.addWidget(self.radio_recibir)
        modo_layout.addStretch()
        
        grupo_modo.setLayout(modo_layout)
        layout.addWidget(grupo_modo)
        
        # ========== GRUPO: BUSCAR Y AÑADIR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Buscar y Añadir Artículos")
        articulos_layout = QVBoxLayout()
        
        # Barra de búsqueda
        busqueda_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar artículo:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escanea código de barras o escribe nombre/referencia/palabras clave...")
        self.txt_buscar.returnPressed.connect(self.buscar_o_seleccionar)
        self.txt_buscar.textChanged.connect(self.busqueda_tiempo_real)
        # Instalar event filter para capturar flechas
        self.txt_buscar.installEventFilter(self)
        
        # Timer para búsqueda en tiempo real (espera 300ms después de escribir)
        self.timer_busqueda = QTimer()
        self.timer_busqueda.setSingleShot(True)
        self.timer_busqueda.timeout.connect(self.buscar_articulo)
        
        lbl_cantidad = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(100)
        
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.setMinimumHeight(40)
        self.btn_agregar.clicked.connect(self.agregar_desde_busqueda)

        self.btn_historial = QPushButton("📜 Historial")
        self.btn_historial.setMinimumHeight(40)
        self.btn_historial.setToolTip("Ver historial de operaciones recientes y artículos frecuentes")
        self.btn_historial.clicked.connect(self.abrir_historial)

        busqueda_layout.addWidget(lbl_buscar)
        busqueda_layout.addWidget(self.txt_buscar, 3)
        busqueda_layout.addWidget(lbl_cantidad)
        busqueda_layout.addWidget(self.spin_cantidad)
        busqueda_layout.addWidget(self.btn_agregar)
        busqueda_layout.addWidget(self.btn_historial)
        
        articulos_layout.addLayout(busqueda_layout)

        # Lista de sugerencias (dropdown interactivo)
        self.lista_sugerencias = QListWidget()
        self.lista_sugerencias.setMaximumHeight(120)
        self.lista_sugerencias.setVisible(False)
        self.lista_sugerencias.itemClicked.connect(self.seleccionar_sugerencia)
        self.lista_sugerencias.setStyleSheet("""
            QListWidget {
                border: 2px solid #1e3a8a;
                border-radius: 5px;
                background-color: white;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            QListWidget::item:hover {
                background-color: #dbeafe;
            }
            QListWidget::item:selected {
                background-color: #1e3a8a;
                color: white;
            }
        """)
        articulos_layout.addWidget(self.lista_sugerencias)

        # Sugerencias de búsqueda (label de estado)
        self.lbl_sugerencia = QLabel("")
        self.lbl_sugerencia.setStyleSheet("color: #1e3a8a; font-size: 12px; margin: 5px; font-style: italic;")
        articulos_layout.addWidget(self.lbl_sugerencia)
        
        grupo_articulos.setLayout(articulos_layout)
        layout.addWidget(grupo_articulos)
        
        # ========== TABLA DE ARTÍCULOS SELECCIONADOS ==========
        lbl_tabla = QLabel("📋 Artículos seleccionados:")
        lbl_tabla.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_tabla)
        
        self.tabla_articulos = QTableWidget()
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels(["ID", "Artículo", "U.Medida", "Cantidad", "Acciones"])
        self.tabla_articulos.setColumnHidden(0, True)
        
        header = self.tabla_articulos.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.tabla_articulos.setMinimumHeight(200)
        layout.addWidget(self.tabla_articulos)
        
        # ========== BOTONES FINALES ==========
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 CONFIRMAR Y GUARDAR")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_movimiento)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar_todo)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 3)
        botones_layout.addWidget(self.btn_cancelar, 1)
        botones_layout.addWidget(self.btn_volver, 1)

        layout.addLayout(botones_layout)

        # ========== ATAJOS DE TECLADO ==========
        self.configurar_atajos_teclado()

        # Mostrar ayuda de atajos en barra de estado simulada
        ayuda_atajos = QLabel(
            "⌨️ Atajos: F2=Buscar | F5=Limpiar | Ctrl+Enter=Guardar | "
            "Esc=Cancelar | Ctrl+1=Entregar | Ctrl+2=Recibir"
        )
        ayuda_atajos.setStyleSheet(
            "background-color: #f1f5f9; padding: 8px; border-radius: 4px; "
            "color: #475569; font-size: 11px; margin-top: 5px;"
        )
        ayuda_atajos.setAlignment(Qt.AlignCenter)
        layout.addWidget(ayuda_atajos)
        
        # Focus inicial en búsqueda
        self.txt_buscar.setFocus()

    def configurar_atajos_teclado(self):
        """Configura los atajos de teclado para la ventana"""
        # F2: Focus en búsqueda para añadir rápido
        shortcut_buscar = QShortcut(QKeySequence("F2"), self)
        shortcut_buscar.activated.connect(lambda: self.txt_buscar.setFocus())

        # F5: Limpiar formulario
        shortcut_limpiar = QShortcut(QKeySequence("F5"), self)
        shortcut_limpiar.activated.connect(self.limpiar_todo)

        # Ctrl+Return: Guardar movimiento
        shortcut_guardar = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_guardar.activated.connect(self.guardar_movimiento)

        # Esc: Cancelar/limpiar
        shortcut_cancelar = QShortcut(QKeySequence("Esc"), self)
        shortcut_cancelar.activated.connect(self.limpiar_todo)

        # Ctrl+1: Modo entregar
        shortcut_entregar = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_entregar.activated.connect(lambda: self.radio_entregar.setChecked(True))

        # Ctrl+2: Modo recibir
        shortcut_recibir = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_recibir.activated.connect(lambda: self.radio_recibir.setChecked(True))

        # Actualizar tooltips de botones con atajos
        self.btn_guardar.setToolTip("Guardar movimiento (Ctrl+Enter)")
        self.btn_cancelar.setToolTip("Cancelar y limpiar (Esc)")
        self.txt_buscar.setToolTip("Buscar artículo (F2 para focus rápido)")

    @handle_db_errors("cargar_operarios")
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
            # Manejo de error silencioso - ya está logueado en ComboLoader
            pass
            
    def cambio_operario(self):
        """Al cambiar de operario, busca su furgoneta asignada"""
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            self.btn_asignar_furgoneta.setEnabled(False)
            return

        # Habilitar botón de asignar furgoneta
        self.btn_asignar_furgoneta.setEnabled(True)

        try:
            from src.services.furgonetas_service import obtener_furgoneta_operario
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            furgoneta = obtener_furgoneta_operario(operario_id, fecha_hoy)

            if furgoneta:
                self.lbl_furgoneta_asignada.setText(f"🚚 Furgoneta {furgoneta['furgoneta_nombre']}")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #1e3a8a; font-weight: bold;")
            else:
                self.lbl_furgoneta_asignada.setText("⚠️ Sin furgoneta asignada hoy")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #dc2626; font-weight: bold;")
        except Exception as e:
            logger.warning(f"Error al obtener furgoneta asignada: {e}")

    def abrir_dialogo_asignar_furgoneta(self):
        """Abre el diálogo para asignar una furgoneta al operario seleccionado"""
        operario_id = self.cmb_operario.currentData()
        operario_nombre = self.cmb_operario.currentText()

        if not operario_id:
            QMessageBox.warning(self, "⚠️ Validación", "Debes seleccionar un operario primero.")
            return

        try:
            # Obtener lista de furgonetas para mostrar opciones
            furgonetas = list_furgonetas(include_inactive=False)

            if not furgonetas:
                QMessageBox.warning(
                    self,
                    "⚠️ Sin furgonetas",
                    "No hay furgonetas registradas en el sistema.\n\nPor favor, registra furgonetas en Maestros → Almacén/Furgonetas."
                )
                return

            # Crear un diálogo simplificado para seleccionar furgoneta
            from PySide6.QtWidgets import QVBoxLayout, QFormLayout, QComboBox, QButtonGroup, QRadioButton
            from src.ui.estilos import ESTILO_DIALOGO

            dialogo = QDialog(self)
            dialogo.setWindowTitle(f"🚚 Asignar Furgoneta a: {operario_nombre}")
            dialogo.setMinimumSize(500, 300)
            dialogo.resize(550, 350)
            dialogo.setStyleSheet(ESTILO_DIALOGO)

            layout = QVBoxLayout(dialogo)

            # Información
            info = QLabel(f"📋 Asignar furgoneta a '{operario_nombre}'")
            info.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
            layout.addWidget(info)

            # Formulario
            form = QFormLayout()

            cmb_furgoneta = QComboBox()
            cmb_furgoneta.addItem("(Selecciona una furgoneta)", None)

            for f in furgonetas:
                numero = f.get('numero')
                matricula = f.get('matricula', '')
                if numero:
                    texto = f"🚚 Furgoneta {numero} - {matricula}"
                else:
                    texto = f"🚚 {matricula}"
                cmb_furgoneta.addItem(texto, f['id'])

            date_desde = QDateEdit()
            date_desde.setCalendarPopup(True)
            date_desde.setDate(QDate.currentDate())
            date_desde.setDisplayFormat("dd/MM/yyyy")

            # Selector de turno
            turno_group = QButtonGroup(dialogo)
            radio_completo = QRadioButton("🕐 Día completo")
            radio_manana = QRadioButton("🌅 Mañana")
            radio_tarde = QRadioButton("🌆 Tarde")
            radio_completo.setChecked(True)

            turno_group.addButton(radio_completo, 0)
            turno_group.addButton(radio_manana, 1)
            turno_group.addButton(radio_tarde, 2)

            turno_layout = QHBoxLayout()
            turno_layout.addWidget(radio_completo)
            turno_layout.addWidget(radio_manana)
            turno_layout.addWidget(radio_tarde)

            form.addRow("🚚 Furgoneta *:", cmb_furgoneta)
            form.addRow("📅 Fecha desde:", date_desde)
            form.addRow("⏰ Turno:", turno_layout)

            layout.addLayout(form)

            # Nota
            nota = QLabel("* Campos obligatorios")
            nota.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
            layout.addWidget(nota)

            # Botones
            layout.addStretch()
            btn_layout = QHBoxLayout()

            btn_asignar = QPushButton("✅ Asignar")
            btn_asignar.setMinimumHeight(40)
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setMinimumHeight(40)

            btn_layout.addWidget(btn_asignar)
            btn_layout.addWidget(btn_cancelar)
            layout.addLayout(btn_layout)

            # Conectar botones
            btn_cancelar.clicked.connect(dialogo.reject)

            def asignar(forzar_asignacion=False):
                furgoneta_id = cmb_furgoneta.currentData()
                if not furgoneta_id:
                    QMessageBox.warning(dialogo, "⚠️ Validación", "Debes seleccionar una furgoneta.")
                    return

                fecha = date_desde.date().toPython().strftime("%Y-%m-%d")

                # Determinar turno
                if radio_completo.isChecked():
                    turno = 'completo'
                elif radio_manana.isChecked():
                    turno = 'manana'
                else:
                    turno = 'tarde'

                try:
                    from src.services.furgonetas_service import asignar_furgoneta_a_operario
                    asignar_furgoneta_a_operario(operario_id, furgoneta_id, fecha, turno, forzar=forzar_asignacion)

                    turno_texto = {'completo': 'día completo', 'manana': 'turno mañana', 'tarde': 'turno tarde'}[turno]
                    QMessageBox.information(
                        dialogo,
                        "✅ Éxito",
                        f"Furgoneta asignada a {operario_nombre} correctamente.\n\n"
                        f"Fecha: {fecha}\n"
                        f"Turno: {turno_texto}"
                    )
                    dialogo.accept()
                    # Actualizar la etiqueta de furgoneta
                    self.cambio_operario()
                except ValueError as e:
                    error_msg = str(e)
                    # Detectar conflicto de día completo
                    if error_msg.startswith("CONFLICTO_DIA_COMPLETO"):
                        partes = error_msg.split("|")
                        if len(partes) == 3:
                            furgoneta_actual = partes[1]
                            furgoneta_nueva_id = partes[2]

                            # Obtener nombre de la furgoneta nueva
                            furgoneta_nueva = next((f for f in furgonetas if f['id'] == int(furgoneta_nueva_id)), None)
                            if furgoneta_nueva:
                                numero = furgoneta_nueva.get('numero')
                                matricula = furgoneta_nueva.get('matricula', '')
                                if numero:
                                    furgoneta_nueva_nombre = f"Furgoneta {numero} - {matricula}"
                                else:
                                    furgoneta_nueva_nombre = matricula
                            else:
                                furgoneta_nueva_nombre = 'Desconocida'

                            respuesta = QMessageBox.question(
                                dialogo,
                                "⚠️ Confirmar Cambio de Furgoneta",
                                f"El operario {operario_nombre} ya tiene asignada la furgoneta:\n\n"
                                f"  🚚 {furgoneta_actual} (Día completo)\n\n"
                                f"¿Deseas cambiarla por la furgoneta seleccionada?\n\n"
                                f"  🚚 {furgoneta_nueva_nombre} (Día completo)\n\n"
                                f"Esto eliminará la asignación anterior.",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )

                            if respuesta == QMessageBox.Yes:
                                # Reintentar con forzar=True
                                asignar(forzar_asignacion=True)
                        else:
                            QMessageBox.critical(dialogo, "❌ Error", f"Error de formato en conflicto:\n{e}")
                    else:
                        QMessageBox.critical(dialogo, "❌ Error", f"Error de validación:\n{e}")
                except Exception as e:
                    logger.exception(f"Error al asignar furgoneta: {e}")
                    QMessageBox.critical(dialogo, "❌ Error", f"Error al asignar:\n{e}")

            btn_asignar.clicked.connect(asignar)

            dialogo.exec()

        except Exception as e:
            logger.exception(f"Error al abrir diálogo de asignación: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir diálogo:\n{e}")

    def eventFilter(self, obj, event):
        """Captura eventos de teclado para navegación de sugerencias"""
        if obj == self.txt_buscar and event.type() == event.Type.KeyPress:
            if self.lista_sugerencias.isVisible():
                if event.key() == Qt.Key_Down:
                    # Flecha abajo: pasar al siguiente elemento
                    current_row = self.lista_sugerencias.currentRow()
                    if current_row < self.lista_sugerencias.count() - 1:
                        self.lista_sugerencias.setCurrentRow(current_row + 1)
                    else:
                        self.lista_sugerencias.setCurrentRow(0)
                    return True
                elif event.key() == Qt.Key_Up:
                    # Flecha arriba: pasar al elemento anterior
                    current_row = self.lista_sugerencias.currentRow()
                    if current_row > 0:
                        self.lista_sugerencias.setCurrentRow(current_row - 1)
                    else:
                        self.lista_sugerencias.setCurrentRow(self.lista_sugerencias.count() - 1)
                    return True
        return super().eventFilter(obj, event)

    def busqueda_tiempo_real(self):
        """Reinicia el timer de búsqueda cada vez que se escribe"""
        self.timer_busqueda.stop()
        if len(self.txt_buscar.text()) >= 3:
            self.timer_busqueda.start(300)

    def buscar_o_seleccionar(self):
        """Al presionar Enter: busca o selecciona la sugerencia actual"""
        if self.lista_sugerencias.isVisible() and self.lista_sugerencias.currentItem():
            # Si hay lista de sugerencias visible y hay un item seleccionado, seleccionarlo
            self.seleccionar_sugerencia(self.lista_sugerencias.currentItem())
        else:
            # Si no, buscar normalmente
            self.buscar_articulo()
    
    def buscar_articulo(self):
        """Busca un artículo por EAN, nombre, referencia o palabras clave"""
        texto = self.txt_buscar.text().strip()

        if not texto:
            self.lbl_sugerencia.setText("")
            self.lista_sugerencias.clear()
            self.lista_sugerencias.setVisible(False)
            return

        # Si el texto es muy corto (<3 caracteres), solo buscar en tiempo real si es un código
        if len(texto) < 3:
            self.lista_sugerencias.setVisible(False)
            return

        try:
            rows = articulos_repo.buscar_articulos_por_texto(texto, limit=10)

            if not rows:
                self.lbl_sugerencia.setText("❌ No se encontraron artículos")
                self.lista_sugerencias.setVisible(False)
                return

            # Limpiar sugerencias previas
            self.lista_sugerencias.clear()
            self.lbl_sugerencia.setText("")

            # Si se presionó Enter y hay coincidencia exacta por EAN/Ref, agregar automáticamente
            if len(rows) == 1 and (rows[0]['ean'] == texto or rows[0]['ref_proveedor'] == texto):
                self.agregar_articulo(rows[0]['id'], rows[0]['nombre'], rows[0]['u_medida'])
                self.txt_buscar.clear()
                self.lbl_sugerencia.setText(f"✅ {rows[0]['nombre']} agregado")
                self.lista_sugerencias.setVisible(False)
                return

            # Mostrar múltiples sugerencias clickeables
            for row in rows:
                texto_item = f"{row['nombre']}"
                if row['ean']:  # EAN
                    texto_item += f" | EAN: {row['ean']}"
                if row['ref_proveedor']:  # Ref
                    texto_item += f" | Ref: {row['ref_proveedor']}"
                texto_item += f" | {row['u_medida']}"

                item = QListWidgetItem(texto_item)
                # Guardar datos del artículo en el item
                item.setData(Qt.UserRole, {
                    'id': row['id'],
                    'nombre': row['nombre'],
                    'u_medida': row['u_medida']
                })
                self.lista_sugerencias.addItem(item)

            self.lista_sugerencias.setVisible(True)
            self.lbl_sugerencia.setText(f"💡 {len(rows)} sugerencias - haz click o usa ↓↑ para seleccionar")

        except Exception as e:
            self.lbl_sugerencia.setText(f"❌ Error: {e}")
            self.lista_sugerencias.setVisible(False)
    
    def agregar_desde_busqueda(self):
        """Fuerza la búsqueda y agregado del artículo"""
        self.buscar_articulo()

    def seleccionar_sugerencia(self, item):
        """Selecciona un artículo de las sugerencias y lo agrega"""
        articulo = item.data(Qt.UserRole)
        self.agregar_articulo(articulo['id'], articulo['nombre'], articulo['u_medida'])
        self.txt_buscar.clear()
        self.lista_sugerencias.clear()
        self.lista_sugerencias.setVisible(False)
        self.lbl_sugerencia.setText(f"✅ {articulo['nombre']} agregado")
        # Volver el focus al campo de búsqueda para escanear el siguiente
        self.txt_buscar.setFocus()

    def agregar_articulo(self, articulo_id, nombre, u_medida):
        """Agrega un artículo a la lista temporal"""
        cantidad = self.spin_cantidad.value()
        
        # Verificar si ya está en la lista
        for art in self.articulos_temp:
            if art['id'] == articulo_id:
                # Incrementar cantidad
                art['cantidad'] += cantidad
                self.actualizar_tabla()
                self.spin_cantidad.setValue(1)
                self.txt_buscar.setFocus()
                return
        
        # Agregar nuevo
        self.articulos_temp.append({
            'id': articulo_id,
            'nombre': nombre,
            'u_medida': u_medida,
            'cantidad': cantidad
        })
        
        self.actualizar_tabla()
        self.spin_cantidad.setValue(1)
        self.txt_buscar.setFocus()
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))
        
        for i, art in enumerate(self.articulos_temp):
            self.tabla_articulos.setItem(i, 0, QTableWidgetItem(str(art['id'])))
            self.tabla_articulos.setItem(i, 1, QTableWidgetItem(art['nombre']))
            self.tabla_articulos.setItem(i, 2, QTableWidgetItem(art['u_medida']))
            self.tabla_articulos.setItem(i, 3, QTableWidgetItem(f"{art['cantidad']:.2f}"))
            
            # Botón quitar (centrado con callback ya conectado)
            contenedor = crear_boton_quitar_centrado(lambda checked=False, idx=i: self.quitar_articulo(idx))
            self.tabla_articulos.setCellWidget(i, 4, contenedor)
    
    def quitar_articulo(self, index):
        """Quita un artículo de la lista"""
        if 0 <= index < len(self.articulos_temp):
            del self.articulos_temp[index]
            self.actualizar_tabla()
    
    @handle_db_errors("guardar_movimiento")
    def guardar_movimiento(self):
        """Guarda el movimiento en la base de datos usando el service"""
        # Validaciones
        operario_id = self.cmb_operario.currentData()
        if not validate_field("operario", operario_id, operario_id is not None,
                             "Debe seleccionar un operario", "movimientos"):
            show_warning("⚠️ Validación", "Debe seleccionar un operario.")
            return

        if not validate_field("articulos", self.articulos_temp, len(self.articulos_temp) > 0,
                             "No hay artículos en la lista", "movimientos"):
            show_warning("⚠️ Validación", "Debe agregar al menos un artículo.")
            return

        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        modo = "ENTREGAR" if self.radio_entregar.isChecked() else "RECIBIR"

        # Preparar lista de artículos para el service
        articulos_para_service = [
            {'id': art['id'], 'cantidad': art['cantidad']}
            for art in self.articulos_temp
        ]

        # Llamar al service para crear los traspasos
        exito, mensaje, ids_creados = movimientos_service.crear_traspaso_almacen_furgoneta(
            fecha=fecha,
            operario_id=operario_id,
            articulos=articulos_para_service,
            usuario=session_manager.get_usuario_actual() or "admin",
            modo=modo
        )

        if not exito:
            show_warning("⚠️ Error", mensaje)
            return

        # Guardar en historial (cada artículo individualmente)
        usuario = session_manager.get_usuario_actual()
        if usuario:
            for art in self.articulos_temp:
                historial_service.guardar_en_historial(
                    usuario=usuario,
                    tipo_operacion='movimiento',
                    articulo_id=art['id'],
                    articulo_nombre=art['nombre'],
                    cantidad=art['cantidad'],
                    u_medida=art['u_medida'],
                    datos_adicionales={'modo': modo.lower()}
                )

        # Mensaje de éxito
        modo_texto = "entregado a" if modo == "ENTREGAR" else "recibido de"
        show_info(
            "✅ Éxito",
            f"Movimiento registrado correctamente.\n\n{mensaje}"
        )

        self.limpiar_todo()

    def abrir_historial(self):
        """Abre el diálogo de historial de operaciones"""
        usuario = session_manager.get_usuario_actual()
        if not usuario:
            show_warning("⚠️ Aviso", "No hay usuario autenticado")
            return

        from src.dialogs.dialogo_historial import DialogoHistorial

        dialogo = DialogoHistorial(
            usuario=usuario,
            tipo_operacion='movimiento',
            parent=self
        )

        # Conectar señal para cuando se seleccione un artículo
        dialogo.articulo_seleccionado.connect(self.agregar_desde_historial)

        dialogo.exec()

    def agregar_desde_historial(self, datos):
        """Agrega un artículo seleccionado del historial"""
        self.agregar_articulo(
            datos['articulo_id'],
            datos['articulo_nombre'],
            datos['u_medida']
        )
        # Actualizar cantidad si viene del historial
        if 'cantidad' in datos and datos['cantidad'] > 0:
            self.spin_cantidad.setValue(datos['cantidad'])

        # Mostrar confirmación
        self.lbl_sugerencia.setText(f"✅ {datos['articulo_nombre']} agregado desde historial")
        self.txt_buscar.setFocus()

    def limpiar_todo(self):
        """Limpia todos los campos y la lista"""
        self.articulos_temp = []
        self.actualizar_tabla()
        self.txt_buscar.clear()
        self.lbl_sugerencia.setText("")
        self.spin_cantidad.setValue(1)
        self.txt_buscar.setFocus()