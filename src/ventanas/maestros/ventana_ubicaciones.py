# ventana_ubicaciones.py - Gestión de Ubicaciones del Almacén
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView
)
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import ubicaciones_service
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR UBICACIÓN
# ========================================
class DialogoUbicacion(QDialog):
    def __init__(self, parent=None, ubicacion_id=None):
        super().__init__(parent)
        self.ubicacion_id = ubicacion_id
        self.setWindowTitle("✏️ Editar Ubicación" if ubicacion_id else "➕ Nueva Ubicación")
        self.setMinimumSize(400, 180)
        self.resize(450, 200)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: A1, B2, Estantería 5...")
        form.addRow("📍 Código/Nombre de Ubicación *:", self.txt_nombre)
        
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
        if self.ubicacion_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos de la ubicación a editar"""
        try:
            ubicacion = ubicaciones_service.obtener_ubicacion(self.ubicacion_id)
            if ubicacion:
                self.txt_nombre.setText(ubicacion['nombre'] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda la ubicación (nueva o editada)"""
        nombre = self.txt_nombre.text().strip()

        if self.ubicacion_id:
            exito, mensaje = ubicaciones_service.actualizar_ubicacion(
                ubicacion_id=self.ubicacion_id,
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            exito, mensaje, ubicacion_id = ubicaciones_service.crear_ubicacion(
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

# ========================================
# VENTANA PRINCIPAL DE UBICACIONES
# ========================================
class VentanaUbicaciones(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="📍 Gestión de Ubicaciones del Almacén",
            descripcion="Las ubicaciones sirven para identificar dónde está físicamente cada artículo en el almacén",
            icono_nuevo="➕",
            texto_nuevo="Nueva Ubicación",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(700, 500)
        self.setMinimumSize(600, 400)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de ubicaciones"""
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Ubicación"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def get_service(self):
        """Retorna el service de ubicaciones"""
        return ubicaciones_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar una ubicación"""
        return DialogoUbicacion(self, item_id)

    def cargar_datos_en_tabla(self, datos):
        """Carga las ubicaciones en la tabla"""
        self.tabla.setRowCount(len(datos))
        for i, ubi in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(ubi['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(ubi['nombre'] or ""))