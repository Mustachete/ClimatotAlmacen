# ventana_familias.py - Gestión de Familias de Artículos
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView
)
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import familias_service
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR FAMILIA
# ========================================
class DialogoFamilia(QDialog):
    def __init__(self, parent=None, familia_id=None):
        super().__init__(parent)
        self.familia_id = familia_id
        self.setWindowTitle("✏️ Editar Familia" if familia_id else "➕ Nueva Familia")
        self.setMinimumSize(400, 180)
        self.resize(450, 200)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Calefacción, Climatización...")
        form.addRow("📂 Nombre de la Familia *:", self.txt_nombre)
        
        layout.addLayout(form)
        
        # Nota obligatorio
        nota = QLabel("* Campo obligatorio")
        nota.setStyleSheet("color: gray; font-size: 12px;")
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
        if self.familia_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos de la familia a editar"""
        try:
            familia = familias_service.obtener_familia(self.familia_id)
            if familia:
                self.txt_nombre.setText(familia['nombre'] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda la familia (nueva o editada)"""
        nombre = self.txt_nombre.text().strip()

        if self.familia_id:
            exito, mensaje = familias_service.actualizar_familia(
                familia_id=self.familia_id,
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            exito, mensaje, familia_id = familias_service.crear_familia(
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

# ========================================
# VENTANA PRINCIPAL DE FAMILIAS
# ========================================
class VentanaFamilias(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="📂 Gestión de Familias de Artículos",
            descripcion="Las familias sirven para categorizar y organizar los artículos del almacén",
            icono_nuevo="➕",
            texto_nuevo="Nueva Familia",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(700, 500)
        self.setMinimumSize(600, 400)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de familias"""
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def get_service(self):
        """Retorna el service de familias"""
        return familias_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar una familia"""
        return DialogoFamilia(self, item_id)

    def cargar_datos_en_tabla(self, datos):
        """Carga las familias en la tabla"""
        self.tabla.setRowCount(len(datos))
        for i, fam in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(fam['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(fam['nombre'] or ""))