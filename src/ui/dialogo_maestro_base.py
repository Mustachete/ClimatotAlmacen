"""
dialogo_maestro_base.py - Clase base abstracta para todos los diálogos de maestros

Esta clase encapsula toda la lógica común de los diálogos de edición/creación de maestros:
- Estructura visual: título + formulario + botones guardar/cancelar
- Lógica de carga de datos (si edición)
- Lógica de guardado (llamada al service)
- Validaciones comunes
- Manejo de errores

Las clases hijas solo necesitan:
1. Definir el formulario específico (campos del maestro)
2. Especificar el service a usar
3. Opcionalmente: validaciones adicionales

Ejemplo de uso:
    class DialogoFamilia(DialogoMaestroBase):
        def __init__(self, parent=None, item_id=None):
            super().__init__(
                parent=parent,
                item_id=item_id,
                titulo_nuevo="➕ Nueva Familia",
                titulo_editar="✏️ Editar Familia",
                service=familias_service,
                nombre_item="familia"
            )

        def crear_formulario(self, form_layout):
            self.txt_nombre = QLineEdit()
            self.txt_nombre.setPlaceholderText("Ej: Calefacción, Climatización...")
            form_layout.addRow("📂 Nombre *:", self.txt_nombre)

        def obtener_datos_formulario(self):
            return {'nombre': self.txt_nombre.text().strip()}

Reducción esperada: ~60-80 líneas por diálogo (de ~90 líneas a ~30 líneas)
"""

from abc import ABCMeta, abstractmethod
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt

from src.ui.estilos import ESTILO_DIALOGO
from src.core.session_manager import session_manager
from src.utils import validaciones


# Metaclass que combina QDialog y ABCMeta
class QDialogABCMeta(type(QDialog), ABCMeta):
    pass


class DialogoMaestroBase(QDialog, metaclass=QDialogABCMeta):
    """
    Clase base abstracta para todos los diálogos de edición/creación de maestros.

    Proporciona:
    - Estructura visual estándar (título, formulario, botones)
    - Lógica de carga de datos automática
    - Lógica de guardado con validaciones
    - Manejo de errores consistente

    Métodos abstractos que DEBEN implementar las clases hijas:
    - crear_formulario(form_layout): Define los campos específicos del formulario
    - obtener_datos_formulario(): Retorna dict con los datos del formulario

    Métodos opcionales que PUEDEN sobrescribir las clases hijas:
    - validar_datos(datos): Validaciones adicionales específicas
    - configurar_dimensiones(): Personaliza tamaño del diálogo
    - cargar_datos_en_formulario(item_data): Personaliza cómo se cargan los datos
    """

    def __init__(
        self,
        parent=None,
        item_id=None,
        titulo_nuevo: str = "➕ Nuevo",
        titulo_editar: str = "✏️ Editar",
        service=None,
        nombre_item: str = "item",
        mostrar_nota_obligatorios: bool = True
    ):
        """
        Inicializa el diálogo maestro.

        Args:
            parent: Widget padre
            item_id: ID del item a editar, None si es nuevo
            titulo_nuevo (str): Título para modo crear
            titulo_editar (str): Título para modo editar
            service: Service que maneja la lógica de negocio
            nombre_item (str): Nombre del item (para mensajes)
            mostrar_nota_obligatorios (bool): Si muestra "* Campos obligatorios"
        """
        super().__init__(parent)

        self.item_id = item_id
        self.service = service
        self.nombre_item = nombre_item
        self.mostrar_nota_obligatorios = mostrar_nota_obligatorios

        # Configurar diálogo
        self.setWindowTitle(titulo_editar if item_id else titulo_nuevo)
        self.setStyleSheet(ESTILO_DIALOGO)
        self.setModal(True)

        # Dimensiones (pueden sobrescribirse en hijas)
        self.configurar_dimensiones()

        # Crear interfaz
        self._crear_interfaz()

        # Si estamos editando, cargar datos
        if self.item_id:
            self.cargar_datos()

        # Focus inicial en primer campo
        self._set_focus_inicial()

    def configurar_dimensiones(self):
        """
        Configura las dimensiones del diálogo.
        Las clases hijas pueden sobrescribir este método para personalizar.
        """
        self.setMinimumSize(400, 200)
        self.resize(450, 250)

    def _crear_interfaz(self):
        """Crea toda la estructura de la interfaz"""
        layout = QVBoxLayout(self)

        # Formulario (abstracto - implementado en hijas)
        self.form_layout = QFormLayout()
        self.crear_formulario(self.form_layout)
        layout.addLayout(self.form_layout)

        # Nota de campos obligatorios
        if self.mostrar_nota_obligatorios:
            nota = QLabel("* Campos obligatorios")
            nota.setStyleSheet("color: gray; font-size: 12px;")
            layout.addWidget(nota)

        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_guardar.setDefault(True)  # Enter = Guardar

        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_cancelar.setShortcut("Esc")  # Esc = Cancelar

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    @abstractmethod
    def crear_formulario(self, form_layout):
        """
        Crea los campos específicos del formulario.
        DEBE ser implementado por las clases hijas.

        Args:
            form_layout (QFormLayout): Layout donde agregar los campos

        Ejemplo:
            self.txt_nombre = QLineEdit()
            self.txt_nombre.setPlaceholderText("Nombre del item")
            form_layout.addRow("📛 Nombre *:", self.txt_nombre)
        """
        pass

    @abstractmethod
    def obtener_datos_formulario(self):
        """
        Obtiene los datos del formulario como diccionario.
        DEBE ser implementado por las clases hijas.

        Returns:
            dict: Diccionario con los datos del formulario

        Ejemplo:
            return {
                'nombre': self.txt_nombre.text().strip(),
                'telefono': self.txt_telefono.text().strip() or None
            }
        """
        pass

    def validar_datos(self, datos):
        """
        Validaciones adicionales específicas del diálogo.
        Las clases hijas pueden sobrescribir para validaciones adicionales.

        Args:
            datos (dict): Datos del formulario

        Returns:
            tuple (bool, str): (válido, mensaje_error)

        Ejemplo:
            if not datos.get('nombre'):
                return False, "El nombre es obligatorio"
            return True, ""
        """
        return True, ""

    def _set_focus_inicial(self):
        """Establece el focus en el primer campo del formulario"""
        # Intenta encontrar el primer QLineEdit o similar
        for i in range(self.form_layout.rowCount()):
            widget = self.form_layout.itemAt(i, QFormLayout.FieldRole)
            if widget and widget.widget():
                widget.widget().setFocus()
                break

    def cargar_datos(self):
        """Carga los datos del item a editar"""
        if not self.service or not self.item_id:
            return

        try:
            # Obtener método de obtención del service
            # Intentar primero el patrón exacto: obtener_<nombre_item>
            metodo_nombre = f"obtener_{self.nombre_item}"
            metodo_obtener = None

            if hasattr(self.service, metodo_nombre):
                metodo_obtener = getattr(self.service, metodo_nombre)

            # Si no existe, buscar métodos que terminen con el nombre_item
            if not metodo_obtener:
                for attr_name in dir(self.service):
                    # Buscar exactamente "obtener_X" donde X es nombre_item
                    if attr_name == metodo_nombre:
                        attr = getattr(self.service, attr_name)
                        if callable(attr):
                            metodo_obtener = attr
                            break

            if not metodo_obtener:
                raise Exception(f"No se encontró método {metodo_nombre} en el service")

            # Obtener datos del item
            item_data = metodo_obtener(self.item_id)

            if item_data:
                self.cargar_datos_en_formulario(item_data)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")

    def cargar_datos_en_formulario(self, item_data):
        """
        Carga los datos del item en el formulario.
        Las clases hijas pueden sobrescribir para personalizar.

        Por defecto, intenta setear automáticamente los campos que coincidan
        con las claves del diccionario.

        Args:
            item_data (dict): Datos del item
        """
        # Auto-carga: busca widgets que coincidan con las claves del dict
        for key, value in item_data.items():
            widget_name = f"txt_{key}"
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if hasattr(widget, 'setText'):
                    widget.setText(str(value) if value is not None else "")
                elif hasattr(widget, 'setPlainText'):
                    widget.setPlainText(str(value) if value is not None else "")

    def guardar(self):
        """Guarda el item (nuevo o editado)"""
        # Obtener datos del formulario
        datos = self.obtener_datos_formulario()

        # Validar
        valido, mensaje_error = self.validar_datos(datos)
        if not valido:
            QMessageBox.warning(self, "⚠️ Validación", mensaje_error)
            return

        # Determinar si es crear o actualizar
        if self.item_id:
            exito, mensaje = self._actualizar_item(datos)
        else:
            exito, mensaje = self._crear_item(datos)

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

    def _crear_item(self, datos):
        """
        Crea un nuevo item usando el service.

        Args:
            datos (dict): Datos del formulario

        Returns:
            tuple (bool, str): (éxito, mensaje)
        """
        if not self.service:
            return False, "No hay service configurado"

        try:
            # Buscar método crear
            metodo_crear = None
            for attr_name in dir(self.service):
                if attr_name.startswith('crear_'):
                    attr = getattr(self.service, attr_name)
                    if callable(attr):
                        metodo_crear = attr
                        break

            if not metodo_crear:
                return False, "No se encontró método de creación en el service"

            # Agregar usuario
            datos['usuario'] = session_manager.get_usuario_actual() or "admin"

            # Ejecutar creación
            resultado = metodo_crear(**datos)

            # El resultado puede ser (exito, mensaje, id) o (exito, mensaje)
            if isinstance(resultado, tuple) and len(resultado) >= 2:
                return resultado[0], resultado[1]
            else:
                return False, "Respuesta inválida del service"

        except Exception as e:
            return False, f"Error al crear:\n{e}"

    def _actualizar_item(self, datos):
        """
        Actualiza un item existente usando el service.

        Args:
            datos (dict): Datos del formulario

        Returns:
            tuple (bool, str): (éxito, mensaje)
        """
        if not self.service:
            return False, "No hay service configurado"

        try:
            # Buscar método actualizar
            metodo_actualizar = None
            for attr_name in dir(self.service):
                if attr_name.startswith('actualizar_'):
                    attr = getattr(self.service, attr_name)
                    if callable(attr):
                        metodo_actualizar = attr
                        break

            if not metodo_actualizar:
                return False, "No se encontró método de actualización en el service"

            # Agregar ID y usuario
            # El nombre del parámetro ID varía: familia_id, proveedor_id, etc.
            import inspect
            sig = inspect.signature(metodo_actualizar)
            param_id = None
            for param_name in sig.parameters:
                if param_name.endswith('_id'):
                    param_id = param_name
                    break

            if not param_id:
                param_id = 'id'

            datos[param_id] = self.item_id
            datos['usuario'] = session_manager.get_usuario_actual() or "admin"

            # Ejecutar actualización
            resultado = metodo_actualizar(**datos)

            # El resultado es (exito, mensaje)
            if isinstance(resultado, tuple) and len(resultado) >= 2:
                return resultado[0], resultado[1]
            else:
                return False, "Respuesta inválida del service"

        except Exception as e:
            return False, f"Error al actualizar:\n{e}"
