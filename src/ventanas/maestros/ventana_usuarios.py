# ventana_usuarios.py - Gestión de Usuarios del Sistema
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import usuarios_service
from src.core.session_manager import session_manager


# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR USUARIO
# ========================================
class DialogoUsuario(QDialog):
    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario  # Nombre de usuario a editar (None si es nuevo)
        self.setWindowTitle("✏️ Editar Usuario" if usuario else "➕ Nuevo Usuario")
        self.setMinimumSize(450, 300)
        self.resize(500, 350)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Formulario
        form = QFormLayout()

        # Usuario
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Mínimo 3 caracteres (a-z, 0-9, _, -)")
        if self.usuario:
            self.txt_usuario.setText(self.usuario)
            self.txt_usuario.setEnabled(False)  # No se puede cambiar el usuario
        form.addRow("👤 Usuario *:", self.txt_usuario)

        # Contraseña
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        if self.usuario:
            self.txt_password.setPlaceholderText("Dejar vacío para no cambiar")
        else:
            self.txt_password.setPlaceholderText("Mínimo 4 caracteres")
        form.addRow("🔒 Contraseña" + (" *:" if not self.usuario else ":"), self.txt_password)

        # Confirmar contraseña
        self.txt_password_confirm = QLineEdit()
        self.txt_password_confirm.setEchoMode(QLineEdit.Password)
        self.txt_password_confirm.setPlaceholderText("Repetir contraseña")
        form.addRow("🔒 Confirmar Contraseña:", self.txt_password_confirm)

        # Rol
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["admin", "almacen", "operario"])
        form.addRow("👔 Rol *:", self.cmb_rol)

        # Activo
        self.chk_activo = QCheckBox("Usuario activo")
        self.chk_activo.setChecked(True)
        form.addRow("", self.chk_activo)

        layout.addLayout(form)

        # Nota obligatorio
        nota = QLabel("* Campos obligatorios")
        nota.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(nota)

        # Advertencia de edición
        if self.usuario:
            advertencia = QLabel(
                "⚠️ El nombre de usuario no se puede modificar.\n"
                "Para cambiar contraseña, ingrese la nueva contraseña."
            )
            advertencia.setStyleSheet("color: #f97316; font-size: 11px; margin: 5px;")
            advertencia.setWordWrap(True)
            layout.addWidget(advertencia)

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
        if self.usuario:
            self.cargar_datos()

        # Focus en el campo apropiado
        if self.usuario:
            self.txt_password.setFocus()
        else:
            self.txt_usuario.setFocus()

        # Conectar teclas Esc y Return
        self.btn_guardar.setDefault(True)  # Return = Guardar
        self.btn_cancelar.setShortcut("Esc")  # Esc = Cancelar

    def cargar_datos(self):
        """Carga los datos del usuario a editar"""
        try:
            user_data = usuarios_service.obtener_usuario(self.usuario)
            if user_data:
                # Rol
                index = self.cmb_rol.findText(user_data['rol'])
                if index >= 0:
                    self.cmb_rol.setCurrentIndex(index)

                # Activo
                self.chk_activo.setChecked(bool(user_data['activo']))
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")

    def guardar(self):
        """Guarda el usuario (nuevo o editado)"""
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text()
        password_confirm = self.txt_password_confirm.text()
        rol = self.cmb_rol.currentText()
        activo = self.chk_activo.isChecked()

        # Validar contraseña
        if password or password_confirm:
            if password != password_confirm:
                QMessageBox.warning(self, "⚠️ Error", "Las contraseñas no coinciden")
                self.txt_password_confirm.setFocus()
                return

        # Usuario actual
        usuario_actual = session_manager.get_usuario_actual() or "admin"

        if self.usuario:
            # Actualizar usuario existente
            # Verificar que no se esté desactivando a sí mismo
            if self.usuario == usuario_actual and not activo:
                QMessageBox.warning(
                    self,
                    "⚠️ No Permitido",
                    "No puede desactivar su propio usuario.\n\n"
                    "Use otra cuenta de administrador para realizar esta acción."
                )
                return

            exito, mensaje = usuarios_service.actualizar_usuario(
                usuario=self.usuario,
                password=password if password else None,
                rol=rol,
                activo=activo,
                usuario_modificador=usuario_actual
            )
        else:
            # Crear nuevo usuario
            if not password:
                QMessageBox.warning(self, "⚠️ Error", "La contraseña es obligatoria para usuarios nuevos")
                self.txt_password.setFocus()
                return

            exito, mensaje = usuarios_service.crear_usuario(
                usuario=usuario,
                password=password,
                rol=rol,
                activo=activo,
                usuario_creador=usuario_actual
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()


# ========================================
# VENTANA PRINCIPAL DE USUARIOS
# ========================================
class VentanaUsuarios(VentanaMaestroBase):
    def __init__(self, parent=None):
        # Verificar que el usuario actual es admin ANTES de llamar a super()
        if not session_manager.is_admin():
            # Crear widget temporal para mostrar mensaje
            from PySide6.QtWidgets import QWidget
            temp = QWidget(parent)
            QMessageBox.critical(
                temp,
                "❌ Acceso Denegado",
                "Solo los administradores pueden gestionar usuarios.\n\n"
                "Contacte a un administrador del sistema."
            )
            # No podemos continuar, lanzar excepción
            raise PermissionError("Solo administradores pueden acceder a gestión de usuarios")

        super().__init__(
            titulo="👥 Gestión de Usuarios del Sistema",
            descripcion="Administre los usuarios que tienen acceso al sistema. Solo usuarios con rol 'admin' pueden acceder a esta funcionalidad.",
            icono_nuevo="➕",
            texto_nuevo="Nuevo Usuario",
            parent=parent
        )

        # Añadir información de sesión actual al final
        self._agregar_info_sesion()

    def _agregar_info_sesion(self):
        """Añade información de la sesión actual debajo de la tabla"""
        layout_principal = self.layout()

        # Insertar antes del botón volver (que está al final)
        info_layout = QHBoxLayout()
        usuario_actual = session_manager.get_usuario_actual() or "desconocido"
        rol_actual = session_manager.get_rol_actual() or "desconocido"

        info_label = QLabel(f"ℹ️ Sesión actual: {usuario_actual} ({rol_actual})")
        info_label.setStyleSheet("color: #64748b; font-size: 11px;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()

        # Insertar antes del último widget (botón volver)
        layout_principal.insertLayout(layout_principal.count() - 1, info_layout)

    def _crear_interfaz(self):
        """Sobrescribe para añadir botón Refrescar"""
        super()._crear_interfaz()

        # Añadir botón Refrescar a la barra superior
        layout_principal = self.layout()
        top_layout = layout_principal.itemAt(2).layout()

        btn_refrescar = QPushButton("🔄 Refrescar")
        btn_refrescar.clicked.connect(lambda: self.cargar_datos())
        top_layout.addWidget(btn_refrescar)

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(900, 550)
        self.setMinimumSize(700, 450)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de usuarios"""
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Rol", "Estado", "ID_Hidden"])
        self.tabla.setColumnHidden(3, True)  # Columna oculta con usuario

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Usuario
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Rol
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Estado

    def get_service(self):
        """Retorna el service de usuarios"""
        return usuarios_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar un usuario"""
        # En usuarios, el item_id es el nombre de usuario (string)
        return DialogoUsuario(self, item_id)

    def get_nombre_item(self, fila):
        """Retorna el nombre de usuario para mostrar en mensajes"""
        return self.tabla.item(fila, 0).text()  # Columna 0 = Usuario

    def editar_item(self):
        """Sobrescribe para usar columna 3 (usuario) en lugar de columna 0 (ID)"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return

        usuario = self.tabla.item(seleccion, 3).text()  # Columna oculta con usuario
        dialogo = self.crear_dialogo(usuario)
        if dialogo.exec():
            self.cargar_datos()

    def eliminar_item(self):
        """Sobrescribe para validar que no se elimine a sí mismo"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return

        usuario = self.tabla.item(seleccion, 3).text()
        nombre_mostrar = self.tabla.item(seleccion, 0).text()
        rol = self.tabla.item(seleccion, 1).text()

        # Verificar que no se esté eliminando a sí mismo
        usuario_actual = session_manager.get_usuario_actual()
        if usuario == usuario_actual:
            QMessageBox.warning(
                self,
                "⚠️ No Permitido",
                "No puede eliminar su propio usuario.\n\n"
                "Use otra cuenta de administrador para realizar esta acción."
            )
            return

        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar el usuario '{nombre_mostrar}'?\n\n"
            f"Rol: {rol}\n\n"
            "Esta acción no se puede deshacer.\n"
            "Si este usuario tiene operaciones registradas, no se podrá eliminar.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Eliminar
        exito, mensaje = usuarios_service.eliminar_usuario(
            usuario=usuario,
            usuario_eliminador=usuario_actual or "admin"
        )

        if not exito:
            QMessageBox.warning(self, "⚠️ No se puede eliminar", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.cargar_datos()

    def cargar_datos_en_tabla(self, datos):
        """Carga los usuarios en la tabla con formato especial"""
        self.tabla.setRowCount(len(datos))

        for i, user in enumerate(datos):
            # Usuario
            self.tabla.setItem(i, 0, QTableWidgetItem(user['usuario'] or ""))

            # Rol (con color azul para admin)
            rol_text = user['rol'] or ""
            rol_item = QTableWidgetItem(rol_text.capitalize())
            if rol_text == "admin":
                rol_item.setForeground(Qt.blue)
            self.tabla.setItem(i, 1, rol_item)

            # Estado (con color rojo para inactivos)
            activo = bool(user['activo'])
            estado_text = "✅ Activo" if activo else "❌ Inactivo"
            estado_item = QTableWidgetItem(estado_text)
            if not activo:
                estado_item.setForeground(Qt.red)
            self.tabla.setItem(i, 2, estado_item)

            # ID oculto (usuario)
            self.tabla.setItem(i, 3, QTableWidgetItem(user['usuario'] or ""))
