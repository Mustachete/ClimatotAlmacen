"""
ventana_maestro_base.py - Clase base abstracta para todas las ventanas maestro

Esta clase encapsula toda la lógica común de las ventanas de gestión de maestros:
- Estructura visual: título + descripción + buscador + tabla + botones
- Funcionalidad CRUD: crear, editar, eliminar
- Buscador con filtrado en tiempo real
- Manejo de selección en tabla
- Diálogo de edición integrado

Las clases hijas solo necesitan:
1. Definir las columnas de la tabla
2. Crear el diálogo de edición
3. Especificar el service a usar
4. Configurar tamaños/dimensiones si es necesario

Ejemplo de uso:
    class VentanaFamilias(VentanaMaestroBase):
        def __init__(self, parent=None):
            super().__init__(
                titulo="📂 Gestión de Familias de Artículos",
                descripcion="Las familias sirven para categorizar y organizar los artículos",
                parent=parent
            )

        def configurar_tabla(self):
            self.tabla.setColumnCount(2)
            self.tabla.setHorizontalHeaderLabels(["ID", "Nombre"])
            self.tabla.setColumnHidden(0, True)

        def get_service(self):
            return familias_service

        def crear_dialogo(self, item_id=None):
            return DialogoFamilia(self, item_id)

Reducción esperada: ~150 líneas por ventana maestro (de ~220 líneas a ~70 líneas)
"""

from abc import ABC, abstractmethod
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_base import TituloVentana, DescripcionVentana, TablaEstandar
from src.core.session_manager import session_manager


class VentanaMaestroBase(QWidget, ABC):
    """
    Clase base abstracta para todas las ventanas de gestión de maestros.

    Proporciona:
    - Estructura visual estándar (título, descripción, buscador, tabla, botones)
    - Funcionalidad CRUD completa
    - Buscador con filtrado en tiempo real
    - Gestión de selección en tabla
    - Botones habilitados/deshabilitados según selección

    Métodos abstractos que DEBEN implementar las clases hijas:
    - configurar_tabla(): Define las columnas y configuración de la tabla
    - get_service(): Retorna el service que maneja la lógica de negocio
    - crear_dialogo(item_id): Crea el diálogo para crear/editar items

    Métodos opcionales que PUEDEN sobrescribir las clases hijas:
    - configurar_dimensiones(): Personaliza tamaño de ventana
    - cargar_datos_en_tabla(datos): Personaliza cómo se muestran los datos
    - get_nombre_item(fila): Define qué nombre mostrar al eliminar (default: columna 1)
    """

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        icono_nuevo: str = "➕",
        texto_nuevo: str = "Nuevo",
        parent=None
    ):
        """
        Inicializa la ventana maestro.

        Args:
            titulo (str): Título de la ventana (ej: "📂 Gestión de Familias")
            descripcion (str): Descripción/subtítulo (ej: "Administra las familias...")
            icono_nuevo (str): Icono para botón nuevo (default: "➕")
            texto_nuevo (str): Texto para botón nuevo (default: "Nuevo")
            parent: Widget padre
        """
        super().__init__(parent)

        self.titulo_texto = titulo
        self.descripcion_texto = descripcion
        self.icono_nuevo = icono_nuevo
        self.texto_nuevo = texto_nuevo

        # Configurar ventana
        self.setWindowTitle(titulo)
        self.setStyleSheet(ESTILO_VENTANA)

        # Dimensiones (pueden sobrescribirse en hijas)
        self.configurar_dimensiones()

        # Crear interfaz
        self._crear_interfaz()

        # Cargar datos iniciales
        self.cargar_datos()

    def configurar_dimensiones(self):
        """
        Configura las dimensiones de la ventana.
        Las clases hijas pueden sobrescribir este método para personalizar.
        """
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

    def _crear_interfaz(self):
        """Crea toda la estructura de la interfaz"""
        layout = QVBoxLayout(self)

        # Título y descripción
        titulo = TituloVentana(self.titulo_texto)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        descripcion = DescripcionVentana(self.descripcion_texto)
        descripcion.setAlignment(Qt.AlignCenter)
        layout.addWidget(descripcion)

        # Barra de búsqueda y botones superiores
        top_layout = QHBoxLayout()

        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escriba para buscar...")
        self.txt_buscar.textChanged.connect(self.buscar)

        self.btn_nuevo = QPushButton(f"{self.icono_nuevo} {self.texto_nuevo}")
        self.btn_nuevo.clicked.connect(self.nuevo_item)

        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_item)
        self.btn_editar.setEnabled(False)

        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_item)
        self.btn_eliminar.setEnabled(False)

        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar)
        top_layout.addWidget(self.btn_nuevo)
        top_layout.addWidget(self.btn_editar)
        top_layout.addWidget(self.btn_eliminar)

        layout.addLayout(top_layout)

        # Tabla
        self.tabla = TablaEstandar()
        self.configurar_tabla()  # Método abstracto - implementado en hijas
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_item)

        layout.addWidget(self.tabla)

        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

    @abstractmethod
    def configurar_tabla(self):
        """
        Configura las columnas de la tabla.
        DEBE ser implementado por las clases hijas.

        Ejemplo:
            self.tabla.setColumnCount(3)
            self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción"])
            self.tabla.setColumnHidden(0, True)  # Ocultar ID

            header = self.tabla.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
        """
        pass

    @abstractmethod
    def get_service(self):
        """
        Retorna el service que maneja la lógica de negocio.
        DEBE ser implementado por las clases hijas.

        Ejemplo:
            return familias_service
        """
        pass

    @abstractmethod
    def crear_dialogo(self, item_id=None):
        """
        Crea el diálogo para crear/editar un item.
        DEBE ser implementado por las clases hijas.

        Args:
            item_id: ID del item a editar, None si es nuevo

        Returns:
            QDialog: Instancia del diálogo

        Ejemplo:
            return DialogoFamilia(self, item_id)
        """
        pass

    def cargar_datos(self, filtro=""):
        """
        Carga los datos en la tabla usando el service.

        Args:
            filtro (str): Texto para filtrar los resultados
        """
        try:
            filtro_texto = filtro if filtro else None
            service = self.get_service()

            # Obtener método de listado del service
            # Los services pueden tener diferentes métodos:
            # - obtener_familias(), obtener_proveedores(), etc.
            # Buscamos el método que empiece con 'obtener_' o 'listar_'
            metodo_listar = None
            for attr_name in dir(service):
                if attr_name.startswith('obtener_') or attr_name.startswith('listar_'):
                    attr = getattr(service, attr_name)
                    if callable(attr):
                        metodo_listar = attr
                        break

            if not metodo_listar:
                raise Exception("No se encontró método de listado en el service")

            # Llamar al método con filtro
            try:
                datos = metodo_listar(filtro_texto=filtro_texto, limit=1000)
            except TypeError:
                # Si el método no acepta estos parámetros, intentar sin ellos
                datos = metodo_listar()

            # Cargar datos en tabla
            self.cargar_datos_en_tabla(datos)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")

    def cargar_datos_en_tabla(self, datos):
        """
        Carga los datos en la tabla.
        Las clases hijas pueden sobrescribir este método para personalizar.

        Por defecto, asume que los datos son una lista de diccionarios
        y los carga en el orden de las columnas de la tabla.

        Args:
            datos (list): Lista de diccionarios con los datos
        """
        self.tabla.setRowCount(len(datos))

        num_columnas = self.tabla.columnCount()
        headers = [self.tabla.horizontalHeaderItem(i).text()
                   for i in range(num_columnas)]

        for i, item_data in enumerate(datos):
            for j, header in enumerate(headers):
                # Convertir header a nombre de campo (minúsculas, sin espacios)
                campo = header.lower().replace(" ", "_")

                # Casos especiales comunes
                if "nombre" in campo and "nombre_de_la_familia" in headers[j].lower():
                    campo = "nombre"
                elif campo == "id":
                    campo = "id"

                # Obtener valor del diccionario
                valor = item_data.get(campo, item_data.get(header.lower(), ""))

                # Convertir a string
                valor_str = str(valor) if valor is not None else ""

                self.tabla.setItem(i, j, QTableWidgetItem(valor_str))

    def buscar(self):
        """Filtra la tabla según el texto de búsqueda"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_datos(filtro)

    def seleccion_cambiada(self):
        """Activa/desactiva botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)

    def nuevo_item(self):
        """Abre el diálogo para crear un nuevo item"""
        dialogo = self.crear_dialogo(None)
        if dialogo.exec():
            self.cargar_datos()

    def editar_item(self):
        """Abre el diálogo para editar el item seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return

        item_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = self.crear_dialogo(item_id)
        if dialogo.exec():
            self.cargar_datos()

    def get_nombre_item(self, fila):
        """
        Obtiene el nombre del item para mostrar en mensajes.
        Por defecto, retorna el valor de la columna 1.
        Las clases hijas pueden sobrescribir para personalizar.

        Args:
            fila (int): Número de fila

        Returns:
            str: Nombre del item
        """
        return self.tabla.item(fila, 1).text()

    def eliminar_item(self):
        """Elimina el item seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return

        item_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.get_nombre_item(seleccion)

        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        # Llamar al service
        service = self.get_service()
        usuario = session_manager.get_usuario_actual() or "admin"

        # Buscar método eliminar
        metodo_eliminar = None
        for attr_name in dir(service):
            if attr_name.startswith('eliminar_'):
                attr = getattr(service, attr_name)
                if callable(attr):
                    metodo_eliminar = attr
                    break

        if not metodo_eliminar:
            QMessageBox.critical(self, "❌ Error", "No se encontró método de eliminación en el service")
            return

        # Determinar el nombre del parámetro ID
        # Puede ser: familia_id, proveedor_id, operario_id, etc.
        import inspect
        sig = inspect.signature(metodo_eliminar)
        param_id = None
        for param_name in sig.parameters:
            if param_name.endswith('_id'):
                param_id = param_name
                break

        if not param_id:
            # Intentar con 'id' genérico
            param_id = 'id'

        # Ejecutar eliminación
        try:
            kwargs = {param_id: item_id, 'usuario': usuario}
            exito, mensaje = metodo_eliminar(**kwargs)

            if not exito:
                QMessageBox.warning(self, "⚠️ No se puede eliminar", mensaje)
                return

            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.cargar_datos()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")
