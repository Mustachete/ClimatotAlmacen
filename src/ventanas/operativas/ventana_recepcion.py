# ventana_recepcion.py - Recepción de Albaranes
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox,
    QFormLayout, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import datetime

from src.ui.estilos import ESTILO_VENTANA
from src.ui.ventana_operativa_base import VentanaOperativaBase
from src.ui.widgets_personalizados import SpinBoxClimatot, crear_boton_quitar_centrado
from src.core.logger import logger
from src.services import movimientos_service, historial_service
from src.repos import articulos_repo, albaranes_repo
from src.core.session_manager import session_manager


# ========================================
# DIÁLOGO PARA REGISTRAR ALBARÁN
# ========================================
class DialogoRecepcion(VentanaOperativaBase):
    """
    Diálogo para registrar recepciones de albaranes desde proveedores.
    Hereda de VentanaOperativaBase para aprovechar toda la estructura común.
    """

    def __init__(self, parent=None):
        self.proveedor_id = None
        self.ultimo_coste = 0.0
        super().__init__(
            titulo="📦 Recepción de Albarán",
            descripcion="Registra la entrada de material al almacén desde proveedores",
            mostrar_fecha=True,
            parent=parent
        )

        # Configurar como diálogo modal
        self.setWindowModality(Qt.WindowModal)

    def configurar_dimensiones(self):
        """Personaliza las dimensiones para el diálogo de recepción"""
        self.setMinimumSize(800, 600)
        self.resize(950, 700)

    def crear_formulario_cabecera(self, layout):
        """Crea el formulario de cabecera con número de albarán y proveedor"""
        form = QFormLayout()

        # Número de albarán
        self.txt_num_albaran = QLineEdit()
        self.txt_num_albaran.setPlaceholderText("Número de albarán del proveedor")
        form.addRow("📋 Nº Albarán *:", self.txt_num_albaran)

        # Proveedor
        layout_prov = QHBoxLayout()
        self.cmb_proveedor = QComboBox()
        self.cargar_proveedores()
        self.cmb_proveedor.currentIndexChanged.connect(self.actualizar_filtro_proveedor)

        btn_nuevo_prov = QPushButton("➕ Nuevo")
        btn_nuevo_prov.setMinimumWidth(100)
        btn_nuevo_prov.setToolTip("Crear nuevo proveedor")
        btn_nuevo_prov.clicked.connect(self.crear_proveedor)

        layout_prov.addWidget(self.cmb_proveedor, stretch=1)
        layout_prov.addWidget(btn_nuevo_prov, stretch=0)

        form.addRow("🏭 Proveedor:", layout_prov)

        layout.addLayout(form)

        # Opciones de recepción
        h_opciones = QHBoxLayout()

        self.chk_escaneo_rapido = QCheckBox("⚡ Modo Escaneo Rápido")
        self.chk_escaneo_rapido.setToolTip(
            "Al escanear un código, se añade automáticamente sin necesidad de hacer click en Agregar"
        )
        self.chk_escaneo_rapido.setStyleSheet("font-weight: bold; color: #1e3a8a;")

        self.chk_recordar_coste = QCheckBox("💰 Recordar último coste")
        self.chk_recordar_coste.setChecked(True)
        self.chk_recordar_coste.setToolTip("Usa el coste del artículo anterior para los siguientes")

        h_opciones.addWidget(self.chk_escaneo_rapido)
        h_opciones.addSpacing(20)
        h_opciones.addWidget(self.chk_recordar_coste)
        h_opciones.addStretch()

        layout.addLayout(h_opciones)

        # Nota
        nota = QLabel("* El número de albarán es obligatorio. Si ya existe, se preguntará si desea continuar.")
        nota.setStyleSheet("color: gray; font-size: 11px; margin: 5px;")
        layout.addWidget(nota)

        # Focus inicial
        self.txt_num_albaran.setFocus()

    def _crear_selector_articulos(self, layout):
        """Sobrescribe el selector para añadir campo de coste"""
        h_selector = QHBoxLayout()

        lbl_art = QLabel("Artículo:")

        from src.dialogs.buscador_articulos import BuscadorArticulos
        self.buscador = BuscadorArticulos(
            self,
            mostrar_boton_lupa=True,
            placeholder="Buscar por EAN, referencia o nombre..."
        )
        self.buscador.articuloSeleccionado.connect(self.on_articulo_seleccionado)

        lbl_cant = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(150)

        # Campo adicional: coste
        lbl_coste = QLabel("Coste unit.:")
        self.spin_coste = SpinBoxClimatot()
        self.spin_coste.setRange(0, 999999)
        self.spin_coste.setDecimals(2)
        self.spin_coste.setPrefix("€ ")
        self.spin_coste.setMinimumWidth(150)

        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.clicked.connect(self.agregar_articulo)
        self.btn_agregar.setEnabled(False)

        h_selector.addWidget(lbl_art)
        h_selector.addWidget(self.buscador, 3)
        h_selector.addWidget(lbl_cant)
        h_selector.addWidget(self.spin_cantidad, 1)
        h_selector.addWidget(lbl_coste)
        h_selector.addWidget(self.spin_coste, 1)
        h_selector.addWidget(self.btn_agregar)

        layout.addLayout(h_selector)

    def configurar_columnas_articulos(self):
        """Configura las columnas de la tabla de artículos"""
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels([
            "ID", "Artículo", "Cantidad", "Coste Unit.", "Acciones"
        ])
        self.tabla_articulos.setColumnHidden(0, True)

        header = self.tabla_articulos.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def on_articulo_seleccionado(self, articulo):
        """Cuando se selecciona un artículo, autocompletar el coste"""
        self.articulo_actual = articulo
        self.btn_agregar.setEnabled(True)

        # Autocompletar coste si existe
        if articulo['coste'] > 0:
            self.spin_coste.setValue(articulo['coste'])
        elif self.chk_recordar_coste.isChecked() and self.ultimo_coste > 0:
            # Usar el último coste si está activado recordar
            self.spin_coste.setValue(self.ultimo_coste)

        # Si está en modo escaneo rápido, agregar automáticamente
        if self.chk_escaneo_rapido.isChecked():
            self.agregar_articulo()
        else:
            self.spin_cantidad.setFocus()
            # SpinBoxClimatot usa line_edit en lugar de lineEdit
            self.spin_cantidad.line_edit.selectAll()

    def agregar_articulo(self):
        """Agrega el artículo actual a la lista temporal"""
        # Si hay texto en el buscador pero no hay artículo seleccionado, forzar búsqueda
        if not self.articulo_actual and self.buscador.txt_buscar.text().strip():
            self.buscador.buscar_exacto()
            if not self.articulo_actual:
                return  # La búsqueda ya habrá mostrado el diálogo de crear

        # Verificar que haya un artículo seleccionado
        if not self.articulo_actual:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe buscar y seleccionar un artículo primero.")
            self.buscador.txt_buscar.setFocus()
            return

        cantidad = self.spin_cantidad.value()
        coste = self.spin_coste.value()

        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['articulo_id'] == self.articulo_actual['id']:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.\nEdite la cantidad si es necesario.")
                return

        # Agregar a lista temporal con coste
        articulo_temp = {
            'articulo_id': self.articulo_actual['id'],
            'nombre': self.articulo_actual['nombre'],
            'cantidad': cantidad,
            'coste': coste,
            'u_medida': self.articulo_actual.get('u_medida', 'unidad'),
            'ref_proveedor': self.articulo_actual.get('ref_proveedor', ''),
            'ean': self.articulo_actual.get('ean', '')
        }

        self.articulos_temp.append(articulo_temp)

        # Guardar último coste para recordar
        self.ultimo_coste = coste

        self.actualizar_tabla_articulos()
        self.limpiar_selector()

        # Solo resetear coste si NO está marcado recordar
        if not self.chk_recordar_coste.isChecked():
            self.spin_coste.setValue(0)

    def llenar_fila_articulo(self, fila, articulo):
        """Llena una fila de la tabla con los datos del artículo incluyendo coste"""
        # ID (oculto)
        self.tabla_articulos.setItem(fila, 0, QTableWidgetItem(str(articulo['articulo_id'])))
        # Nombre
        self.tabla_articulos.setItem(fila, 1, QTableWidgetItem(articulo['nombre']))
        # Cantidad
        self.tabla_articulos.setItem(fila, 2, QTableWidgetItem(f"{articulo['cantidad']:.2f}"))
        # Coste
        self.tabla_articulos.setItem(fila, 3, QTableWidgetItem(f"€ {articulo['coste']:.2f}"))
        # Botón quitar se añade en actualizar_tabla_articulos de la base

    def calcular_resumen(self):
        """Calcula el resumen con coste total"""
        total_articulos = len(self.articulos_temp)
        total_cantidad = sum(art['cantidad'] for art in self.articulos_temp)
        coste_total = sum(art['cantidad'] * art['coste'] for art in self.articulos_temp)

        return (f"📊 Total: {total_articulos} artículos ({total_cantidad:.2f} unidades) | "
                f"Coste total: € {coste_total:,.2f}")

    def actualizar_filtro_proveedor(self):
        """Filtra artículos por el proveedor seleccionado"""
        self.proveedor_id = self.cmb_proveedor.currentData()
        if self.proveedor_id:
            self.buscador.filtrar_por_proveedor(self.proveedor_id)
        else:
            self.buscador.limpiar_filtros()

    def crear_proveedor(self):
        """Abre diálogo para crear un nuevo proveedor"""
        from src.ventanas.maestros.ventana_proveedores import DialogoProveedor
        dialogo = DialogoProveedor(self)
        if dialogo.exec():
            # Recargar proveedores
            self.cmb_proveedor.clear()
            self.cargar_proveedores()
            # Seleccionar el último (recién creado)
            self.cmb_proveedor.setCurrentIndex(self.cmb_proveedor.count() - 1)

    def cargar_proveedores(self):
        """Carga los proveedores en el combo"""
        try:
            proveedores = articulos_repo.get_proveedores()

            self.cmb_proveedor.addItem("(Sin proveedor)", None)
            for prov in proveedores:
                self.cmb_proveedor.addItem(prov['nombre'], prov['id'])
        except Exception:
            pass

    def validar_antes_guardar(self):
        """Valida los datos antes de guardar"""
        num_albaran = self.txt_num_albaran.text().strip()

        if not num_albaran:
            return False, "El número de albarán es obligatorio."

        if not self.articulos_temp:
            return False, "Debe agregar al menos un artículo al albarán."

        return True, ""

    def ejecutar_guardado(self):
        """Ejecuta el guardado de la recepción"""
        num_albaran = self.txt_num_albaran.text().strip()
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        proveedor_id = self.cmb_proveedor.currentData()

        try:
            # Verificar si el albarán ya existe (mismo proveedor + número + fecha)
            if albaranes_repo.verificar_duplicado(num_albaran, proveedor_id, fecha):
                return False, (
                    f"Ya existe un albarán con el mismo número '{num_albaran}'\n"
                    f"del mismo proveedor en la fecha {self.date_fecha.date().toString('dd/MM/yyyy')}.\n\n"
                    "No se pueden registrar albaranes duplicados.\n"
                    "Si necesita modificarlo, contacte al administrador."
                )

            # Advertencia si existe el mismo número pero de otro proveedor o fecha diferente
            alb_existente = albaranes_repo.get_by_numero(num_albaran)
            if alb_existente:
                # Aquí no podemos mostrar diálogo, solo advertir
                # La clase base ya preguntará confirmación antes de guardar
                pass

            # Registrar el albarán
            albaranes_repo.crear_albaran(num_albaran, proveedor_id, fecha)

            # Preparar datos para el service
            articulos = [
                {
                    'articulo_id': art['articulo_id'],
                    'cantidad': art['cantidad'],
                    'coste_unit': art['coste']
                }
                for art in self.articulos_temp
            ]

            # Llamar al service para crear la recepción
            exito, mensaje, ids_creados = movimientos_service.crear_recepcion_material(
                fecha=fecha,
                articulos=articulos,
                almacen_nombre="Almacén",
                albaran=num_albaran,
                usuario=session_manager.get_usuario_actual() or "admin",
                proveedor_id=proveedor_id  # Pasar el ID del proveedor
            )

            if not exito:
                return False, f"Error al guardar:\n{mensaje}"

            # Guardar en historial
            usuario = session_manager.get_usuario_actual()
            if usuario:
                for art in self.articulos_temp:
                    historial_service.guardar_en_historial(
                        usuario=usuario,
                        tipo_operacion='recepcion',
                        articulo_id=art['articulo_id'],
                        articulo_nombre=art['nombre'],
                        cantidad=art['cantidad'],
                        u_medida=art['u_medida'],
                        datos_adicionales={'albaran': num_albaran, 'coste': art['coste']}
                    )

            return True, f"Albarán '{num_albaran}' registrado correctamente.\n\n{mensaje}"

        except Exception as e:
            logger.error(f"Error en recepción: {e}")
            return False, f"Error al guardar:\n{e}"


# ========================================
# VENTANA PRINCIPAL DE RECEPCIÓN
# ========================================
class VentanaRecepcion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Recepción de Albaranes")
        self.resize(950, 600)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("📦 Recepción de Albaranes de Proveedores")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        desc = QLabel("Registra la entrada de material al almacén desde proveedores")
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Botón para nueva recepción
        btn_layout = QHBoxLayout()

        self.btn_nueva = QPushButton("➕ Nueva Recepción")
        self.btn_nueva.setMinimumHeight(45)
        self.btn_nueva.clicked.connect(self.nueva_recepcion)

        btn_layout.addWidget(self.btn_nueva)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Filtros
        filtro_layout = QHBoxLayout()

        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por número de albarán o proveedor...")
        self.txt_buscar.textChanged.connect(self.buscar)

        filtro_layout.addWidget(lbl_buscar)
        filtro_layout.addWidget(self.txt_buscar)

        layout.addLayout(filtro_layout)

        # Tabla de albaranes
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nº Albarán", "Proveedor", "Fecha", "Artículos"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout.addWidget(self.tabla)

        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

        # Cargar datos iniciales
        self.cargar_albaranes()

    def cargar_albaranes(self, filtro=""):
        """Carga los albaranes registrados"""
        try:
            albaranes = albaranes_repo.get_todos(filtro_texto=filtro if filtro else None, limit=500)

            self.tabla.setRowCount(len(albaranes))

            for i, alb in enumerate(albaranes):
                self.tabla.setItem(i, 0, QTableWidgetItem(alb['albaran']))
                self.tabla.setItem(i, 1, QTableWidgetItem(alb['proveedor_nombre'] or "(Sin proveedor)"))
                # Convertir fecha a formato dd/MM/yyyy
                try:
                    fecha_obj = datetime.datetime.strptime(alb['fecha'], "%Y-%m-%d")
                    fecha_mostrar = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_mostrar = alb['fecha']
                self.tabla.setItem(i, 2, QTableWidgetItem(fecha_mostrar))
                self.tabla.setItem(i, 3, QTableWidgetItem(f"{alb['num_articulos']} artículo(s)"))

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar albaranes:\n{e}")

    def buscar(self):
        """Filtra la tabla"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_albaranes(filtro)

    def nueva_recepcion(self):
        """Abre el diálogo para nueva recepción"""
        # Crear el diálogo sin parent para que sea ventana independiente
        dialogo = DialogoRecepcion()
        # Guardar referencia para evitar que se destruya prematuramente
        self.dialogo_recepcion = dialogo
        # Conectar señal cuando se cierra para recargar la lista
        dialogo.destroyed.connect(self._recargar_albaranes_seguro)
        dialogo.show()

    def _recargar_albaranes_seguro(self):
        """Recarga albaranes de forma segura, verificando que la ventana existe"""
        try:
            if self and not self.isHidden():
                self.cargar_albaranes()
        except RuntimeError:
            # La ventana padre ya fue eliminada, no hacer nada
            pass
