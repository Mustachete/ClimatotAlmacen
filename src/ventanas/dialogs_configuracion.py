# dialogs_configuracion.py - Diálogos de configuración del sistema
"""
Diálogos para gestión de base de datos, backups y restauración.
Solo accesibles por administradores.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import shutil
from datetime import datetime

from src.ui.estilos import ESTILO_DIALOGO
from src.core.db_utils import DB_PATH
from src.core.logger import logger
from src.repos import sistema_repo


class DialogoGestionBD(QDialog):
    """Diálogo para gestión de base de datos"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🗄️ Gestión de Base de Datos")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("🗄️ Información de la Base de Datos")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Info de la BD
        db_path = Path(DB_PATH)

        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            info_text = f"""
📁 Ubicación: {DB_PATH}
📊 Tamaño: {size_mb:.2f} MB
✅ Estado: Operativa
            """
        else:
            info_text = "❌ Base de datos no encontrada"

        lbl_info = QLabel(info_text)
        lbl_info.setStyleSheet(
            "background-color: #f0f0f0; padding: 15px; "
            "border-radius: 5px; font-family: monospace;"
        )
        layout.addWidget(lbl_info)

        # Botones de acción
        layout.addSpacing(20)

        btn_verificar = QPushButton("🔍 Verificar Integridad")
        btn_verificar.clicked.connect(self.verificar_integridad)
        layout.addWidget(btn_verificar)

        btn_optimizar = QPushButton("⚡ Optimizar (VACUUM)")
        btn_optimizar.clicked.connect(self.optimizar_bd)
        layout.addWidget(btn_optimizar)

        btn_exportar = QPushButton("📤 Exportar copia de la BD")
        btn_exportar.clicked.connect(self.exportar_bd)
        layout.addWidget(btn_exportar)

        # Botón cerrar
        layout.addStretch()
        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setDefault(True)
        layout.addWidget(btn_cerrar)

    def verificar_integridad(self):
        """Verifica la integridad de la base de datos"""
        try:
            resultado = sistema_repo.verificar_integridad_bd()

            if resultado['ok']:
                QMessageBox.information(
                    self,
                    "✅ Integridad OK",
                    "La base de datos está en perfecto estado."
                )
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Problema detectado",
                    f"Resultado: {resultado['resultado']}"
                )
        except Exception as e:
            logger.exception(f"Error al verificar integridad: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al verificar:\n{e}")

    def optimizar_bd(self):
        """Optimiza la base de datos con VACUUM"""
        respuesta = QMessageBox.question(
            self,
            "⚡ Optimizar Base de Datos",
            "Esta operación reorganizará la base de datos para mejorar el rendimiento.\n\n"
            "Puede tardar unos segundos.\n\n"
            "¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        try:
            sistema_repo.optimizar_bd()
            logger.info("Base de datos optimizada con VACUUM")
            QMessageBox.information(
                self,
                "✅ Éxito",
                "Base de datos optimizada correctamente."
            )
        except Exception as e:
            logger.exception(f"Error al optimizar BD: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al optimizar:\n{e}")

    def exportar_bd(self):
        """Exporta una copia de la base de datos"""
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"almacen_backup_{fecha_str}.db"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar copia de la base de datos",
            nombre_sugerido,
            "Database Files (*.db);;All Files (*)"
        )

        if not ruta:
            return

        try:
            shutil.copy2(DB_PATH, ruta)
            logger.info(f"BD exportada a: {ruta}")
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Copia de seguridad creada en:\n\n{ruta}"
            )
        except Exception as e:
            logger.exception(f"Error al exportar BD: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al copiar:\n{e}")


class DialogoBackupRestauracion(QDialog):
    """Diálogo para backup y restauración"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Backup y Restauración")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("📦 Backup y Restauración de Datos")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Advertencia
        advertencia = QLabel(
            "⚠️ IMPORTANTE: Realice copias de seguridad regularmente.\n"
            "Las restauraciones sobrescriben todos los datos actuales."
        )
        advertencia.setStyleSheet(
            "background-color: #fff3cd; color: #856404; padding: 10px; "
            "border-radius: 5px; border: 1px solid #ffc107;"
        )
        advertencia.setWordWrap(True)
        layout.addWidget(advertencia)

        layout.addSpacing(20)

        # Sección Backup
        grupo_backup = QGroupBox("📤 Crear Backup")
        backup_layout = QVBoxLayout()

        lbl_backup = QLabel(
            "Crea una copia de seguridad completa de la base de datos.\n"
            "Incluye: artículos, movimientos, inventarios, usuarios, etc."
        )
        lbl_backup.setStyleSheet("color: #64748b; font-size: 12px;")
        backup_layout.addWidget(lbl_backup)

        btn_backup_manual = QPushButton("💾 Crear Backup Ahora")
        btn_backup_manual.setMinimumHeight(50)
        btn_backup_manual.clicked.connect(self.crear_backup_manual)
        backup_layout.addWidget(btn_backup_manual)

        # Botón de configuración
        btn_config_backup = QPushButton("⚙️ Configurar Backups...")
        btn_config_backup.setMinimumHeight(40)
        btn_config_backup.setStyleSheet("background-color: #f3f4f6;")
        btn_config_backup.clicked.connect(self.abrir_config_backups)
        backup_layout.addWidget(btn_config_backup)

        grupo_backup.setLayout(backup_layout)
        layout.addWidget(grupo_backup)

        # Sección Restauración
        grupo_restore = QGroupBox("📥 Restaurar desde Backup")
        restore_layout = QVBoxLayout()

        lbl_restore = QLabel(
            "⚠️ La restauración sobrescribe TODOS los datos actuales.\n"
            "Asegúrese de tener un backup reciente antes de restaurar."
        )
        lbl_restore.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: bold;")
        restore_layout.addWidget(lbl_restore)

        btn_restore = QPushButton("📂 Restaurar desde archivo...")
        btn_restore.setMinimumHeight(50)
        btn_restore.setStyleSheet("background-color: #fef2f2; border-color: #dc2626;")
        btn_restore.clicked.connect(self.restaurar_backup)
        restore_layout.addWidget(btn_restore)

        grupo_restore.setLayout(restore_layout)
        layout.addWidget(grupo_restore)

        # Botón cerrar
        layout.addStretch()
        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setDefault(True)
        layout.addWidget(btn_cerrar)

    def abrir_config_backups(self):
        """Abre el diálogo de configuración de backups"""
        from src.ventanas.dialogo_config_backups import DialogoConfigBackups

        dialogo = DialogoConfigBackups(self)
        dialogo.exec()

    def crear_backup_manual(self):
        """Crea un backup manual"""
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"climatot_backup_{fecha_str}.db"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar backup",
            nombre_sugerido,
            "Database Files (*.db);;All Files (*)"
        )

        if not ruta:
            return

        try:
            # Crear directorio si no existe
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)

            # Copiar base de datos
            shutil.copy2(DB_PATH, ruta)

            # Registrar en log
            logger.info(f"Backup manual creado: {ruta}")

            QMessageBox.information(
                self,
                "✅ Backup Creado",
                f"Backup guardado exitosamente en:\n\n{ruta}\n\n"
                f"Tamaño: {Path(ruta).stat().st_size / (1024*1024):.2f} MB"
            )
        except Exception as e:
            logger.exception(f"Error al crear backup: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al crear backup:\n{e}")

    def restaurar_backup(self):
        """Restaura la base de datos desde un backup"""
        # Advertencia severa
        respuesta = QMessageBox.warning(
            self,
            "⚠️ ADVERTENCIA CRÍTICA",
            "⚠️ Esta operación SOBRESCRIBIRÁ todos los datos actuales.\n\n"
            "Se recomienda:\n"
            "1. Crear un backup de los datos actuales\n"
            "2. Cerrar todas las ventanas del sistema\n"
            "3. Verificar que el archivo de backup es correcto\n\n"
            "¿Está COMPLETAMENTE SEGURO de continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Seleccionar archivo
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de backup",
            "",
            "Database Files (*.db);;All Files (*)"
        )

        if not ruta:
            return

        # Confirmación final
        respuesta2 = QMessageBox.question(
            self,
            "⚠️ Última confirmación",
            f"Va a restaurar desde:\n{ruta}\n\n"
            "Todos los datos actuales se perderán.\n\n"
            "¿Proceder con la restauración?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta2 != QMessageBox.Yes:
            return

        try:
            # Crear backup de seguridad antes de sobrescribir
            backup_seguridad = DB_PATH.replace(
                '.db',
                f'_pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            )
            shutil.copy2(DB_PATH, backup_seguridad)
            logger.info(f"Backup de seguridad creado antes de restaurar: {backup_seguridad}")

            # Restaurar
            shutil.copy2(ruta, DB_PATH)
            logger.info(f"Base de datos restaurada desde: {ruta}")

            QMessageBox.information(
                self,
                "✅ Restauración Completada",
                f"Base de datos restaurada exitosamente desde:\n\n{ruta}\n\n"
                f"Se creó un backup de seguridad en:\n{backup_seguridad}\n\n"
                "Se recomienda reiniciar la aplicación."
            )

        except Exception as e:
            logger.exception(f"Error al restaurar backup: {e}")
            QMessageBox.critical(
                self,
                "❌ Error Crítico",
                f"Error al restaurar backup:\n{e}\n\n"
                f"Si la base de datos quedó corrupta, puede restaurar desde:\n{backup_seguridad}"
            )
