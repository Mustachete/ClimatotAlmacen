"""
Diálogo para configurar las opciones de backup del sistema
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QCheckBox, QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from pathlib import Path

from src.ui.estilos import ESTILO_DIALOGO
from src.services.backup_config_service import obtener_configuracion, guardar_configuracion, BackupConfig
from src.core.logger import logger


class DialogoConfigBackups(QDialog):
    """Diálogo para configurar las opciones de backup"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuracion de Backups")
        self.setMinimumSize(600, 550)
        self.setStyleSheet(ESTILO_DIALOGO)

        # Cargar configuración actual
        self.config_actual = obtener_configuracion()

        self.crear_interfaz()
        self.cargar_valores()

    def crear_interfaz(self):
        """Crea la interfaz del diálogo"""
        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("Configuracion de Backups")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Configure las opciones de backup automatico del sistema.\n"
            "Los cambios se aplican inmediatamente."
        )
        descripcion.setStyleSheet("color: #64748b; margin-bottom: 15px;")
        descripcion.setWordWrap(True)
        descripcion.setAlignment(Qt.AlignCenter)
        layout.addWidget(descripcion)

        # Grupo: Configuración General
        grupo_general = QGroupBox("Configuracion General")
        layout_general = QVBoxLayout()

        # Max backups
        layout_max = QHBoxLayout()
        lbl_max = QLabel("Numero maximo de backups:")
        lbl_max.setToolTip("Cantidad maxima de backups a mantener en disco")
        layout_max.addWidget(lbl_max)

        self.spin_max_backups = QSpinBox()
        self.spin_max_backups.setMinimum(1)
        self.spin_max_backups.setMaximum(100)
        self.spin_max_backups.setSuffix(" backups")
        self.spin_max_backups.setToolTip("Entre 1 y 100 backups")
        layout_max.addWidget(self.spin_max_backups)
        layout_max.addStretch()

        layout_general.addLayout(layout_max)

        # Retención por días
        layout_retencion = QHBoxLayout()
        lbl_retencion = QLabel("Retencion por dias (opcional):")
        lbl_retencion.setToolTip("Eliminar backups mas antiguos de X dias (0 = sin limite)")
        layout_retencion.addWidget(lbl_retencion)

        self.spin_retencion_dias = QSpinBox()
        self.spin_retencion_dias.setMinimum(0)
        self.spin_retencion_dias.setMaximum(365)
        self.spin_retencion_dias.setSuffix(" dias")
        self.spin_retencion_dias.setSpecialValueText("Sin limite")
        self.spin_retencion_dias.setToolTip("0 = sin limite de dias")
        layout_retencion.addWidget(self.spin_retencion_dias)
        layout_retencion.addStretch()

        layout_general.addLayout(layout_retencion)

        grupo_general.setLayout(layout_general)
        layout.addWidget(grupo_general)

        # Grupo: Opciones de Backup
        grupo_opciones = QGroupBox("Opciones de Backup")
        layout_opciones = QVBoxLayout()

        # Múltiples backups diarios
        self.chk_multiples_diarios = QCheckBox("Permitir multiples backups por dia")
        self.chk_multiples_diarios.setToolTip(
            "Si esta desactivado, solo se permite un backup por dia"
        )
        layout_opciones.addWidget(self.chk_multiples_diarios)

        # Backup automático al inicio
        self.chk_auto_inicio = QCheckBox("Crear backup automatico al iniciar sesion")
        self.chk_auto_inicio.setToolTip(
            "Se crea un backup cada vez que un usuario inicia sesion"
        )
        layout_opciones.addWidget(self.chk_auto_inicio)

        # Backup automático al cerrar
        self.chk_auto_cierre = QCheckBox("Crear backup automatico al cerrar la aplicacion")
        self.chk_auto_cierre.setToolTip(
            "Se crea un backup cada vez que se cierra el programa"
        )
        layout_opciones.addWidget(self.chk_auto_cierre)

        grupo_opciones.setLayout(layout_opciones)
        layout.addWidget(grupo_opciones)

        # Grupo: Ubicación (futuro)
        grupo_ubicacion = QGroupBox("Ubicacion de Backups")
        layout_ubicacion = QVBoxLayout()

        layout_ruta = QHBoxLayout()
        self.lbl_ruta = QLabel("Ruta: Por defecto (db/backups)")
        self.lbl_ruta.setStyleSheet("color: #64748b; font-family: monospace;")
        layout_ruta.addWidget(self.lbl_ruta)
        layout_ruta.addStretch()

        btn_cambiar_ruta = QPushButton("Cambiar ubicacion...")
        btn_cambiar_ruta.clicked.connect(self.cambiar_ubicacion)
        layout_ruta.addWidget(btn_cambiar_ruta)

        layout_ubicacion.addLayout(layout_ruta)

        grupo_ubicacion.setLayout(layout_ubicacion)
        layout.addWidget(grupo_ubicacion)

        # Botones
        layout.addStretch()

        layout_botones = QHBoxLayout()

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setMinimumHeight(40)
        btn_guardar.clicked.connect(self.guardar)
        btn_guardar.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        layout_botones.addWidget(btn_guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.clicked.connect(self.reject)
        layout_botones.addWidget(btn_cancelar)

        layout.addLayout(layout_botones)

    def cargar_valores(self):
        """Carga los valores actuales de la configuración"""
        self.spin_max_backups.setValue(self.config_actual.max_backups)
        self.spin_retencion_dias.setValue(
            self.config_actual.retencion_dias if self.config_actual.retencion_dias else 0
        )
        self.chk_multiples_diarios.setChecked(self.config_actual.permitir_multiples_diarios)
        self.chk_auto_inicio.setChecked(self.config_actual.backup_auto_inicio)
        self.chk_auto_cierre.setChecked(self.config_actual.backup_auto_cierre)

        if self.config_actual.ruta_backups:
            self.lbl_ruta.setText(f"Ruta: {self.config_actual.ruta_backups}")

    def cambiar_ubicacion(self):
        """Permite cambiar la ubicación de los backups"""
        ruta_actual = self.config_actual.ruta_backups if self.config_actual.ruta_backups else ""

        nueva_ruta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta para backups",
            ruta_actual,
            QFileDialog.ShowDirsOnly
        )

        if nueva_ruta:
            self.config_actual.ruta_backups = nueva_ruta
            self.lbl_ruta.setText(f"Ruta: {nueva_ruta}")

            # Preguntar si desea usar la ruta por defecto
            respuesta = QMessageBox.question(
                self,
                "Confirmar cambio",
                f"Nueva ubicacion:\n{nueva_ruta}\n\n"
                "Los backups futuros se guardaran en esta ubicacion.\n"
                "Los backups existentes en la ubicacion anterior no se moveran.\n\n"
                "Continuar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if respuesta != QMessageBox.Yes:
                # Restaurar valor anterior
                if self.config_actual.ruta_backups:
                    self.config_actual.ruta_backups = ruta_actual
                    self.lbl_ruta.setText(f"Ruta: {ruta_actual}" if ruta_actual else "Ruta: Por defecto (db/backups)")

    def guardar(self):
        """Guarda la configuración"""
        # Crear nueva configuración con los valores del formulario
        nueva_config = BackupConfig(
            max_backups=self.spin_max_backups.value(),
            permitir_multiples_diarios=self.chk_multiples_diarios.isChecked(),
            backup_auto_inicio=self.chk_auto_inicio.isChecked(),
            backup_auto_cierre=self.chk_auto_cierre.isChecked(),
            retencion_dias=self.spin_retencion_dias.value() if self.spin_retencion_dias.value() > 0 else None,
            ruta_backups=self.config_actual.ruta_backups
        )

        # Guardar en BD
        if guardar_configuracion(nueva_config):
            logger.info(f"Configuracion de backups guardada: {nueva_config.to_dict()}")
            QMessageBox.information(
                self,
                "Exito",
                "Configuracion de backups guardada correctamente.\n\n"
                "Los cambios se aplicaran en los proximos backups."
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo guardar la configuracion.\n\n"
                "Consulte el registro de errores."
            )
