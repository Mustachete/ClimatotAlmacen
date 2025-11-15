# ventana_usuarios.py - Gestión de Usuarios del Sistema
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox,
    QHeaderView, QComboBox, QCheckBox
)
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import usuarios_service
from src.core.session_manager import session_manager
from src.utils import validaciones


# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR USUARIO
# ========================================
class DialogoUsuario(DialogoMaestroBase):
    def __init__(self, parent=None, usuario=None):
        # Guardar usuario antes de llamar a super (DialogoMaestroBase usa item_id)
        self.usuario_nombre = usuario

        super().__init__(
            parent=parent,
            item_id=usuario,  # Usa el nombre de usuario como ID
            titulo_nuevo="➕ Nuevo Usuario",
            titulo_editar="✏️ Editar Usuario",
            service=usuarios_service,
            nombre_item="usuario",
            mostrar_nota_obligatorios=False  # Usamos nota personalizada
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(450, 350)
        self.resize(500, 400)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        # Usuario
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Mínimo 3 caracteres (a-z, 0-9, _, -)")
        if self.usuario_nombre:
            self.txt_usuario.setText(self.usuario_nombre)
            self.txt_usuario.setEnabled(False)  # No se puede cambiar
        form_layout.addRow("👤 Usuario *:", self.txt_usuario)

        # Contraseña
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        if self.usuario_nombre:
            self.txt_password.setPlaceholderText("Dejar vacío para no cambiar")
        else:
            self.txt_password.setPlaceholderText("Mínimo 4 caracteres")
        form_layout.addRow("🔒 Contraseña" + (" *:" if not self.usuario_nombre else ":"), self.txt_password)

        # Confirmar contraseña
        self.txt_password_confirm = QLineEdit()
        self.txt_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password_confirm.setPlaceholderText("Repetir contraseña")
        form_layout.addRow("🔒 Confirmar Contraseña:", self.txt_password_confirm)

        # Rol
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["admin", "almacen", "operario"])
        form_layout.addRow("👔 Rol *:", self.cmb_rol)

        # Activo
        self.chk_activo = QCheckBox("Usuario activo")
        self.chk_activo.setChecked(True)
        form_layout.addRow("", self.chk_activo)

        # Nota personalizada
        nota = QLabel("* Campos obligatorios")
        nota.setStyleSheet("color: gray; font-size: 12px;")
        form_layout.addRow("", nota)

        # Advertencia de edición
        if self.usuario_nombre:
            advertencia = QLabel(
                "⚠️ El nombre de usuario no se puede modificar.\n"
                "Para cambiar contraseña, ingrese la nueva contraseña."
            )
            advertencia.setStyleSheet("color: #f97316; font-size: 11px; margin: 5px;")
            advertencia.setWordWrap(True)
            form_layout.addRow("", advertencia)

    def _set_focus_inicial(self):
        """Focus en el campo apropiado según modo"""
        if self.usuario_nombre:
            self.txt_password.setFocus()
        else:
            self.txt_usuario.setFocus()

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        password = self.txt_password.text()
        return {
            'usuario': self.txt_usuario.text().strip(),
            'password': password if password else None,
            'rol': self.cmb_rol.currentText(),
            'activo': self.chk_activo.isChecked()
        }

    def validar_datos(self, datos):
        """Valida los datos del formulario"""
        # Validar usuario obligatorio
        valido, mensaje = validaciones.validar_campo_obligatorio(datos.get('usuario', ''), 'usuario')
        if not valido:
            return False, mensaje

        # Validar nombre de usuario (formato)
        valido, mensaje = validaciones.validar_nombre_usuario(datos['usuario'])
        if not valido:
            return False, mensaje

        # Validar contraseñas coincidan
        password = self.txt_password.text()
        password_confirm = self.txt_password_confirm.text()
        if password or password_confirm:
            if password != password_confirm:
                return False, "Las contraseñas no coinciden"

        # Validar contraseña obligatoria en creación
        if not self.usuario_nombre and not password:
            return False, "La contraseña es obligatoria para usuarios nuevos"

        # Validar password seguro si se proporciona
        if password:
            valido, mensaje = validaciones.validar_password_seguro(password, minimo_caracteres=4)
            if not valido:
                return False, mensaje

        # Validar que no se desactive a sí mismo
        if self.usuario_nombre:
            usuario_actual = session_manager.get_usuario_actual()
            if self.usuario_nombre == usuario_actual and not datos['activo']:
                return False, "No puede desactivar su propio usuario"

        return True, ""

    def cargar_datos_en_formulario(self, item_data):
        """Personaliza carga de datos"""
        # No cargar usuario (ya está seteado y deshabilitado)
        # No cargar password (nunca se muestra)

        # Cargar rol
        if 'rol' in item_data:
            index = self.cmb_rol.findText(item_data['rol'])
            if index >= 0:
                self.cmb_rol.setCurrentIndex(index)

        # Cargar activo
        if 'activo' in item_data:
            self.chk_activo.setChecked(bool(item_data['activo']))

    def _crear_item(self, datos):
        """Sobrescribe para usar usuario_creador en vez de usuario"""
        try:
            datos['usuario_creador'] = session_manager.get_usuario_actual() or "admin"
            resultado = self.service.crear_usuario(**datos)

            if isinstance(resultado, tuple) and len(resultado) >= 2:
                return resultado[0], resultado[1]
            else:
                return False, "Respuesta inválida del service"
        except Exception as e:
            return False, f"Error al crear:\n{e}"

    def _actualizar_item(self, datos):
        """Sobrescribe para usar usuario_modificador en vez de usuario"""
        try:
            datos['usuario_modificador'] = session_manager.get_usuario_actual() or "admin"
            resultado = self.service.actualizar_usuario(**datos)

            if isinstance(resultado, tuple) and len(resultado) >= 2:
                return resultado[0], resultado[1]
            else:
                return False, "Respuesta inválida del service"
        except Exception as e:
            return False, f"Error al actualizar:\n{e}"


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
