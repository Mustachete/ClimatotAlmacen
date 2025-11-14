# ventana_operarios.py - Gestión de Operarios
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import operarios_service
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR OPERARIO
# ========================================
class DialogoOperario(QDialog):
    def __init__(self, parent=None, operario_id=None):
        super().__init__(parent)
        self.operario_id = operario_id
        self.setWindowTitle("✏️ Editar Operario" if operario_id else "➕ Nuevo Operario")
        self.setMinimumSize(450, 250)
        self.resize(500, 280)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: José Martínez")
        
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["oficial", "ayudante"])
        
        self.chk_activo = QCheckBox("Operario activo")
        self.chk_activo.setChecked(True)
        
        form.addRow("👤 Nombre completo *:", self.txt_nombre)
        form.addRow("🔧 Rol *:", self.cmb_rol)
        form.addRow("", self.chk_activo)
        
        layout.addLayout(form)
        
        # Nota
        nota = QLabel("* Campos obligatorios\n\n"
                     "👷 Oficial: Responsable de la furgoneta y trabajos\n"
                     "🔨 Ayudante: Asiste al oficial")
        nota.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(nota)
        
        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        # Si estamos editando, cargar datos
        if self.operario_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos del operario a editar"""
        try:
            operario = operarios_service.obtener_operario(self.operario_id)

            if operario:
                self.txt_nombre.setText(operario['nombre'] or "")
                # Buscar el índice del rol
                idx = self.cmb_rol.findText(operario['rol_operario'])
                if idx >= 0:
                    self.cmb_rol.setCurrentIndex(idx)
                self.chk_activo.setChecked(operario['activo'] == 1)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el operario (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()
        rol = self.cmb_rol.currentText()
        activo = self.chk_activo.isChecked()

        # Llamar al service
        if self.operario_id:
            # Editar existente
            exito, mensaje = operarios_service.actualizar_operario(
                operario_id=self.operario_id,
                nombre=nombre,
                rol_operario=rol,
                activo=activo,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            # Crear nuevo
            exito, mensaje, operario_id = operarios_service.crear_operario(
                nombre=nombre,
                rol_operario=rol,
                activo=activo,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

# ========================================
# VENTANA PRINCIPAL DE OPERARIOS
# ========================================
class VentanaOperarios(VentanaMaestroBase):
    def __init__(self, parent=None):
        # Crear ComboBox de filtros antes de llamar a super()
        self.cmb_filtro = None

        super().__init__(
            titulo="👷 Gestión de Operarios",
            descripcion="Gestiona los técnicos que trabajan en campo (oficiales y ayudantes)",
            icono_nuevo="➕",
            texto_nuevo="Nuevo Operario",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(850, 600)
        self.setMinimumSize(750, 500)

    def _crear_interfaz(self):
        """Crea la interfaz con filtros adicionales"""
        # Primero llamamos al método padre para crear la estructura base
        super()._crear_interfaz()

        # Ahora agregamos el filtro adicional en la barra superior
        # Necesitamos acceder al layout superior que ya creó el padre
        # Lo insertamos antes de los botones

        # Obtener el layout principal
        layout_principal = self.layout()

        # El top_layout es el segundo widget (después del título y descripción)
        # Usamos itemAt para acceder a los layouts
        top_layout = layout_principal.itemAt(2).layout()  # Índice 2 = barra superior

        # Insertar el combo de filtros antes del botón "Nuevo"
        lbl_filtro = QLabel("Filtrar:")
        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(["Todos", "Solo Oficiales", "Solo Ayudantes", "Solo Activos", "Solo Inactivos"])
        self.cmb_filtro.currentTextChanged.connect(self.buscar)

        # Insertar en la posición 2 (después de lbl_buscar y txt_buscar)
        top_layout.insertWidget(2, lbl_filtro)
        top_layout.insertWidget(3, self.cmb_filtro)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de operarios"""
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Rol", "Estado"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Rol
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Estado

    def get_service(self):
        """Retorna el service de operarios"""
        return operarios_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar un operario"""
        return DialogoOperario(self, item_id)

    def cargar_datos(self, filtro=""):
        """Sobrescribe para manejar filtros adicionales"""
        filtro_tipo = self.cmb_filtro.currentText() if self.cmb_filtro else "Todos"

        # Preparar filtros
        filtro_texto_param = filtro if filtro else None

        solo_rol = None
        if filtro_tipo == "Solo Oficiales":
            solo_rol = "oficial"
        elif filtro_tipo == "Solo Ayudantes":
            solo_rol = "ayudante"

        solo_activos = None
        if filtro_tipo == "Solo Activos":
            solo_activos = True
        elif filtro_tipo == "Solo Inactivos":
            solo_activos = False

        # Obtener operarios con filtros
        try:
            operarios = operarios_service.obtener_operarios(
                filtro_texto=filtro_texto_param,
                solo_rol=solo_rol,
                solo_activos=solo_activos,
                limit=1000
            )
            self.cargar_datos_en_tabla(operarios)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")

    def cargar_datos_en_tabla(self, datos):
        """Carga los operarios en la tabla con formato especial"""
        self.tabla.setRowCount(len(datos))

        for i, oper in enumerate(datos):
            # ID
            self.tabla.setItem(i, 0, QTableWidgetItem(str(oper['id'])))
            # Nombre
            self.tabla.setItem(i, 1, QTableWidgetItem(oper['nombre']))
            # Rol con emoji
            rol_texto = "👷 Oficial" if oper['rol_operario'] == "oficial" else "🔨 Ayudante"
            item_rol = QTableWidgetItem(rol_texto)
            self.tabla.setItem(i, 2, item_rol)
            # Estado
            estado_texto = "✅ Activo" if oper['activo'] == 1 else "❌ Inactivo"
            item_estado = QTableWidgetItem(estado_texto)
            if oper['activo'] == 0:
                item_estado.setForeground(Qt.gray)
            self.tabla.setItem(i, 3, item_estado)