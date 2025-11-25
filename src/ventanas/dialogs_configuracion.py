# dialogs_configuracion.py - Diálogos de configuración del sistema
"""
Diálogos para gestión de base de datos PostgreSQL, backups y restauración.
Solo accesibles por administradores.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QGroupBox, QProgressDialog
)
from PySide6.QtCore import Qt
from pathlib import Path
import subprocess
from datetime import datetime
import os

from src.ui.estilos import ESTILO_DIALOGO
from src.core.logger import logger
from src.repos import sistema_repo
from src.core.db_utils import get_con


class DialogoGestionBD(QDialog):
    """Diálogo para gestión de base de datos PostgreSQL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🗄️ Gestión de Base de Datos PostgreSQL")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("🗄️ Información de la Base de Datos")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Info de la BD (PostgreSQL)
        try:
            conn = get_con()
            info_text = f"""
🐘 Motor: PostgreSQL
🌐 Host: {os.getenv('DB_HOST', 'localhost')}
📊 Base de datos: {os.getenv('DB_NAME', 'climatot_almacen')}
👤 Usuario: {os.getenv('DB_USER', 'postgres')}
✅ Estado: Conectado
            """
            conn.close()
        except Exception as e:
            info_text = f"❌ Error de conexión: {e}"

        lbl_info = QLabel(info_text)
        lbl_info.setStyleSheet(
            "background-color: #f0f0f0; padding: 15px; "
            "border-radius: 5px; font-family: monospace;"
        )
        layout.addWidget(lbl_info)

        # Botones de acción
        layout.addSpacing(20)

        btn_verificar = QPushButton("🔍 Verificar Conexión")
        btn_verificar.clicked.connect(self.verificar_conexion)
        layout.addWidget(btn_verificar)

        btn_estadisticas = QPushButton("📊 Ver Estadísticas de la BD")
        btn_estadisticas.clicked.connect(self.ver_estadisticas)
        layout.addWidget(btn_estadisticas)

        btn_optimizar = QPushButton("⚡ Optimizar (VACUUM)")
        btn_optimizar.clicked.connect(self.optimizar_bd)
        layout.addWidget(btn_optimizar)

        # Nota informativa
        nota = QLabel(
            "ℹ️ Para backups y restauración de PostgreSQL, use la opción "
            "\"Backup y Restauración\" del menú."
        )
        nota.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        nota.setWordWrap(True)
        layout.addWidget(nota)

        # Botón cerrar
        layout.addStretch()
        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setDefault(True)
        layout.addWidget(btn_cerrar)

    def verificar_conexion(self):
        """Verifica la conexión a PostgreSQL"""
        try:
            conn = get_con()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            QMessageBox.information(
                self,
                "✅ Conexión OK",
                f"Conexión exitosa a PostgreSQL.\n\n{version}"
            )
        except Exception as e:
            logger.exception(f"Error al verificar conexión: {e}")
            QMessageBox.critical(self, "❌ Error de Conexión", f"Error:\n{e}")

    def ver_estadisticas(self):
        """Muestra estadísticas de la base de datos"""
        try:
            conn = get_con()
            cursor = conn.cursor()

            # Obtener tamaño de la BD
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size = cursor.fetchone()[0]

            # Obtener número de tablas
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            num_tablas = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            info = f"""
📊 Estadísticas de la Base de Datos

💾 Tamaño total: {size}
📋 Número de tablas: {num_tablas}
🗄️ Motor: PostgreSQL
            """

            QMessageBox.information(self, "📊 Estadísticas", info)
        except Exception as e:
            logger.exception(f"Error al obtener estadísticas: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al obtener estadísticas:\n{e}")

    def optimizar_bd(self):
        """Optimiza la base de datos con VACUUM"""
        respuesta = QMessageBox.question(
            self,
            "⚡ Optimizar Base de Datos",
            "Esta operación reorganizará la base de datos para mejorar el rendimiento.\n\n"
            "En PostgreSQL esto ejecuta VACUUM ANALYZE.\n\n"
            "Puede tardar unos segundos.\n\n"
            "¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        try:
            sistema_repo.optimizar_bd()
            logger.info("Base de datos optimizada con VACUUM ANALYZE")
            QMessageBox.information(
                self,
                "✅ Éxito",
                "Base de datos optimizada correctamente."
            )
        except Exception as e:
            logger.exception(f"Error al optimizar BD: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al optimizar:\n{e}")


class DialogoBackupRestauracion(QDialog):
    """Diálogo para backup y restauración de PostgreSQL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Backup y Restauración PostgreSQL")
        self.setMinimumSize(700, 550)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("📦 Backup y Restauración de PostgreSQL")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Advertencia
        advertencia = QLabel(
            "⚠️ IMPORTANTE: Realice copias de seguridad regularmente.\n"
            "Los backups de PostgreSQL se realizan con pg_dump.\n"
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
            "Crea un backup completo de la base de datos PostgreSQL.\n"
            "Formato: SQL dump (archivo .sql) compatible con pg_dump/pg_restore."
        )
        lbl_backup.setStyleSheet("color: #64748b; font-size: 12px;")
        lbl_backup.setWordWrap(True)
        backup_layout.addWidget(lbl_backup)

        btn_backup_manual = QPushButton("💾 Crear Backup Ahora")
        btn_backup_manual.setMinimumHeight(50)
        btn_backup_manual.clicked.connect(self.crear_backup_manual)
        backup_layout.addWidget(btn_backup_manual)

        grupo_backup.setLayout(backup_layout)
        layout.addWidget(grupo_backup)

        # Sección Restauración
        grupo_restore = QGroupBox("📥 Restaurar desde Backup")
        restore_layout = QVBoxLayout()

        lbl_restore = QLabel(
            "⚠️ La restauración sobrescribe TODOS los datos actuales.\n"
            "Asegúrese de tener un backup reciente antes de restaurar.\n\n"
            "Requiere: psql instalado y accesible en PATH."
        )
        lbl_restore.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: bold;")
        lbl_restore.setWordWrap(True)
        restore_layout.addWidget(lbl_restore)

        btn_restore = QPushButton("📂 Restaurar desde archivo SQL...")
        btn_restore.setMinimumHeight(50)
        btn_restore.setStyleSheet("background-color: #fef2f2; border-color: #dc2626;")
        btn_restore.clicked.connect(self.restaurar_backup)
        restore_layout.addWidget(btn_restore)

        grupo_restore.setLayout(restore_layout)
        layout.addWidget(grupo_restore)

        # Nota técnica
        nota = QLabel(
            "ℹ️ Nota técnica: Los backups se crean con pg_dump en formato SQL plano.\n"
            "Para restaurar, se usa psql. Asegúrese de tener PostgreSQL instalado."
        )
        nota.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic; margin-top: 10px;")
        nota.setWordWrap(True)
        layout.addWidget(nota)

        # Botón cerrar
        layout.addStretch()
        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setDefault(True)
        layout.addWidget(btn_cerrar)

    def crear_backup_manual(self):
        """Crea un backup manual usando pg_dump"""
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"climatot_backup_{fecha_str}.sql"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar backup PostgreSQL",
            nombre_sugerido,
            "SQL Files (*.sql);;All Files (*)"
        )

        if not ruta:
            return

        # Diálogo de progreso
        progress = QProgressDialog("Creando backup de PostgreSQL...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        try:
            # Obtener configuración de conexión
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'climatot_almacen')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')

            # Preparar variables de entorno para pg_dump
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password

            # Ejecutar pg_dump
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-d', db_name,
                '-f', ruta,
                '--clean',  # Incluir DROP statements
                '--if-exists',  # Usar IF EXISTS en DROP
                '--no-owner',  # No incluir comandos de ownership
                '--no-privileges'  # No incluir privilegios
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )

            progress.close()

            if result.returncode != 0:
                error_msg = result.stderr or "Error desconocido"
                raise Exception(f"pg_dump falló: {error_msg}")

            # Verificar que el archivo se creó
            if not Path(ruta).exists():
                raise Exception("El archivo de backup no se creó")

            size_mb = Path(ruta).stat().st_size / (1024 * 1024)

            logger.info(f"Backup PostgreSQL creado: {ruta} ({size_mb:.2f} MB)")

            QMessageBox.information(
                self,
                "✅ Backup Creado",
                f"Backup guardado exitosamente en:\n\n{ruta}\n\n"
                f"Tamaño: {size_mb:.2f} MB\n\n"
                f"Este archivo puede restaurarse con psql o pgAdmin."
            )

        except FileNotFoundError:
            progress.close()
            QMessageBox.critical(
                self,
                "❌ Error",
                "No se encontró pg_dump en el sistema.\n\n"
                "Asegúrese de tener PostgreSQL instalado y que pg_dump esté en el PATH."
            )
        except subprocess.TimeoutExpired:
            progress.close()
            QMessageBox.critical(
                self,
                "❌ Timeout",
                "El backup tardó demasiado tiempo (>5 minutos).\n\n"
                "La base de datos puede ser muy grande o el servidor está lento."
            )
        except Exception as e:
            progress.close()
            logger.exception(f"Error al crear backup: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al crear backup:\n\n{e}")

    def restaurar_backup(self):
        """Restaura la base de datos desde un backup SQL"""
        # Advertencia severa
        respuesta = QMessageBox.warning(
            self,
            "⚠️ ADVERTENCIA CRÍTICA",
            "⚠️ Esta operación SOBRESCRIBIRÁ todos los datos actuales.\n\n"
            "Se recomienda:\n"
            "1. Crear un backup de los datos actuales PRIMERO\n"
            "2. Cerrar todas las ventanas del sistema\n"
            "3. Verificar que el archivo SQL de backup es correcto\n"
            "4. Asegurarse de que no hay otros usuarios conectados\n\n"
            "¿Está COMPLETAMENTE SEGURO de continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Seleccionar archivo
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de backup SQL",
            "",
            "SQL Files (*.sql);;All Files (*)"
        )

        if not ruta:
            return

        # Confirmación final
        respuesta2 = QMessageBox.question(
            self,
            "⚠️ Última confirmación",
            f"Va a restaurar desde:\n{ruta}\n\n"
            "Todos los datos actuales se perderán.\n\n"
            "Esta operación puede tardar varios minutos.\n\n"
            "¿Proceder con la restauración?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta2 != QMessageBox.Yes:
            return

        # Diálogo de progreso
        progress = QProgressDialog("Restaurando base de datos...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        try:
            # Obtener configuración de conexión
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'climatot_almacen')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')

            # Preparar variables de entorno para psql
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password

            # Ejecutar psql para restaurar
            cmd = [
                'psql',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-d', db_name,
                '-f', ruta,
                '-v', 'ON_ERROR_STOP=1'  # Detener en error
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )

            progress.close()

            if result.returncode != 0:
                error_msg = result.stderr or "Error desconocido"
                raise Exception(f"psql falló: {error_msg}")

            logger.info(f"Base de datos restaurada desde: {ruta}")

            QMessageBox.information(
                self,
                "✅ Restauración Completada",
                f"Base de datos restaurada exitosamente desde:\n\n{ruta}\n\n"
                "Se recomienda:\n"
                "1. Reiniciar la aplicación\n"
                "2. Verificar que los datos se restauraron correctamente"
            )

        except FileNotFoundError:
            progress.close()
            QMessageBox.critical(
                self,
                "❌ Error",
                "No se encontró psql en el sistema.\n\n"
                "Asegúrese de tener PostgreSQL instalado y que psql esté en el PATH."
            )
        except subprocess.TimeoutExpired:
            progress.close()
            QMessageBox.critical(
                self,
                "❌ Timeout",
                "La restauración tardó demasiado tiempo (>10 minutos).\n\n"
                "El archivo puede ser muy grande o el servidor está lento."
            )
        except Exception as e:
            progress.close()
            logger.exception(f"Error al restaurar backup: {e}")
            QMessageBox.critical(
                self,
                "❌ Error Crítico",
                f"Error al restaurar backup:\n\n{e}\n\n"
                "Si la base de datos quedó en estado inconsistente,\n"
                "puede intentar restaurar desde otro backup."
            )
