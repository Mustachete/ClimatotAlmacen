# ventana_recepcion.py - Recepción de Albaranes
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QGroupBox, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
import datetime
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.ui.widgets_personalizados import SpinBoxClimatot, crear_boton_quitar_centrado
from src.core.db_utils import get_con
from src.core.logger import logger
from src.dialogs.buscador_articulos import BuscadorArticulos
from src.services import movimientos_service, historial_service
from src.core.session_manager import session_manager
from src.repos import movimientos_repo

def today_str():
    """Devuelve fecha actual en formato YYYY-MM-DD"""
    return datetime.date.today().strftime("%Y-%m-%d")

# ========================================
# DIÁLOGO PARA REGISTRAR ALBARÁN
# ========================================
class DialogoRecepcion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Recepción de Albarán")
        self.setMinimumSize(800, 600)
        self.resize(950, 700)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        # Lista temporal de artículos a recibir
        self.articulos_temp = []
        self.articulo_actual = None
        
        layout = QVBoxLayout(self)
        
        # ========== GRUPO 1: DATOS DEL ALBARÁN ==========
        grupo_albaran = QGroupBox("📄 Datos del Albarán")
        form_albaran = QFormLayout()
        
        self.txt_num_albaran = QLineEdit()
        self.txt_num_albaran.setPlaceholderText("Número de albarán del proveedor")
        
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())  # No permitir fechas futuras
        
        self.cmb_proveedor = QComboBox()
        self.cargar_proveedores()
        self.cmb_proveedor.currentIndexChanged.connect(self.actualizar_filtro_proveedor)
        
        # Botón para crear proveedor
        layout_prov = QHBoxLayout()
        layout_prov.addWidget(self.cmb_proveedor, stretch=1)  # El combo ocupa el espacio disponible
        btn_nuevo_prov = QPushButton("➕ Nuevo")
        btn_nuevo_prov.setMinimumWidth(100)  # Ancho mínimo suficiente para el texto
        btn_nuevo_prov.setToolTip("Crear nuevo proveedor")
        btn_nuevo_prov.clicked.connect(self.crear_proveedor)
        layout_prov.addWidget(btn_nuevo_prov, stretch=0)  # El botón mantiene su tamaño
        
        form_albaran.addRow("📋 Nº Albarán *:", self.txt_num_albaran)
        form_albaran.addRow("📅 Fecha:", self.date_fecha)
        form_albaran.addRow("🏭 Proveedor:", layout_prov)
        
        grupo_albaran.setLayout(form_albaran)
        layout.addWidget(grupo_albaran)
        
        # ========== GRUPO 2: AÑADIR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Añadir Artículos al Albarán")
        layout_articulos = QVBoxLayout()
        
        # Selector de artículo
        h1 = QHBoxLayout()
        lbl_art = QLabel("Artículo:")
        
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
        
        lbl_coste = QLabel("Coste unit.:")
        self.spin_coste = SpinBoxClimatot()
        self.spin_coste.setRange(0, 999999)
        self.spin_coste.setDecimals(2)
        self.spin_coste.setPrefix("€ ")
        self.spin_coste.setMinimumWidth(150)
        
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.clicked.connect(self.agregar_articulo)

        h1.addWidget(lbl_art)
        h1.addWidget(self.buscador, 3)
        h1.addWidget(lbl_cant)
        h1.addWidget(self.spin_cantidad, 1)
        h1.addWidget(lbl_coste)
        h1.addWidget(self.spin_coste, 1)
        h1.addWidget(self.btn_agregar)

        layout_articulos.addLayout(h1)

        # Modo escaneo rápido
        h_modo = QHBoxLayout()
        self.chk_escaneo_rapido = QCheckBox("⚡ Modo Escaneo Rápido")
        self.chk_escaneo_rapido.setToolTip(
            "Al escanear un código, se añade automáticamente sin necesidad de hacer click en Agregar"
        )
        self.chk_escaneo_rapido.setStyleSheet("font-weight: bold; color: #1e3a8a;")

        self.chk_recordar_coste = QCheckBox("💰 Recordar último coste")
        self.chk_recordar_coste.setChecked(True)
        self.chk_recordar_coste.setToolTip("Usa el coste del artículo anterior para los siguientes")

        h_modo.addWidget(self.chk_escaneo_rapido)
        h_modo.addSpacing(20)
        h_modo.addWidget(self.chk_recordar_coste)
        h_modo.addStretch()
        layout_articulos.addLayout(h_modo)
        
        # Tabla de artículos agregados
        self.tabla_articulos = QTableWidget()
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels(["ID", "Artículo", "Cantidad", "Coste Unit.", "Acciones"])
        self.tabla_articulos.setColumnHidden(0, True)
        self.tabla_articulos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_articulos.setMaximumHeight(250)
        
        layout_articulos.addWidget(self.tabla_articulos)

        # Panel de resumen
        self.lbl_resumen = QLabel("📊 Total: 0 artículos | Coste total: € 0.00")
        self.lbl_resumen.setStyleSheet(
            "background-color: #f0f9ff; border: 2px solid #1e3a8a; "
            "border-radius: 5px; padding: 10px; font-size: 14px; font-weight: bold; "
            "color: #1e40af; margin-top: 5px;"
        )
        self.lbl_resumen.setAlignment(Qt.AlignCenter)
        layout_articulos.addWidget(self.lbl_resumen)

        grupo_articulos.setLayout(layout_articulos)
        layout.addWidget(grupo_articulos)

        # Nota
        nota = QLabel("* El número de albarán es obligatorio. Si ya existe, se preguntará si desea continuar.")
        nota.setStyleSheet("color: gray; font-size: 11px; margin: 5px;")
        layout.addWidget(nota)
        
        # Botones finales
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Recepción")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        # Configurar teclas rápidas
        self.btn_guardar.setShortcut("Ctrl+Return")
        self.btn_cancelar.setShortcut("Esc")

        # Focus inicial
        self.txt_num_albaran.setFocus()
    
    def on_articulo_seleccionado(self, articulo):
        """Cuando se selecciona un artículo, autocompletar el coste"""
        self.articulo_actual = articulo

        # Autocompletar coste si existe
        if articulo['coste'] > 0:
            self.spin_coste.setValue(articulo['coste'])
        elif self.chk_recordar_coste.isChecked() and hasattr(self, 'ultimo_coste'):
            # Usar el último coste si está activado recordar
            self.spin_coste.setValue(self.ultimo_coste)

        # Si está en modo escaneo rápido, agregar automáticamente
        if self.chk_escaneo_rapido.isChecked():
            self.agregar_articulo()
    
    def actualizar_filtro_proveedor(self):
        """Filtra artículos por el proveedor seleccionado"""
        proveedor_id = self.cmb_proveedor.currentData()
        if proveedor_id:
            self.buscador.filtrar_por_proveedor(proveedor_id)
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
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_proveedor.addItem("(Sin proveedor)", None)
            for row in rows:
                self.cmb_proveedor.addItem(row[1], row[0])
        except Exception:
            pass
    
    def agregar_articulo(self):
        '''Agrega un artículo a la lista temporal'''

        # Si hay texto en el buscador pero no hay artículo seleccionado, forzar búsqueda
        if not self.articulo_actual and self.buscador.txt_buscar.text().strip():
            self.buscador.buscar_exacto()
            # Esperar un momento para que se procese la búsqueda
            # Si aún no hay artículo después de la búsqueda, significa que no existe
            if not self.articulo_actual:
                return  # La búsqueda ya habrá mostrado el diálogo de crear

        # Verificar que haya un artículo seleccionado
        if not self.articulo_actual:
             QMessageBox.warning(self, "⚠️ Aviso", "Debe buscar y seleccionar un artículo primero.")
             self.buscador.txt_buscar.setFocus()
             return
        
        articulo = self.articulo_actual
        cantidad = self.spin_cantidad.value()
        coste = self.spin_coste.value()
        
        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['id'] == articulo['id']:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.\\nEdite la cantidad si es necesario.")
                return
       
        # Agregar a lista temporal
        self.articulos_temp.append({
            'id': articulo['id'],
            'nombre': articulo['nombre'],
            'cantidad': cantidad,
            'coste': coste,
            'u_medida': articulo['u_medida']
        })

        # Guardar último coste para recordar
        self.ultimo_coste = coste

        self.actualizar_tabla_articulos()

        # Resetear campos
        self.buscador.limpiar()
        self.spin_cantidad.setValue(1)

        # Solo resetear coste si NO está marcado recordar
        if not self.chk_recordar_coste.isChecked():
            self.spin_coste.setValue(0)

        self.buscador.txt_buscar.setFocus()
        self.articulo_actual = None
    
    def actualizar_tabla_articulos(self):
        """Actualiza la tabla con los artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))

        total_articulos = 0
        coste_total = 0.0

        for i, art in enumerate(self.articulos_temp):
            # ID
            self.tabla_articulos.setItem(i, 0, QTableWidgetItem(str(art['id'])))
            # Artículo
            self.tabla_articulos.setItem(i, 1, QTableWidgetItem(art['nombre']))
            # Cantidad
            self.tabla_articulos.setItem(i, 2, QTableWidgetItem(f"{art['cantidad']:.2f}"))
            # Coste
            self.tabla_articulos.setItem(i, 3, QTableWidgetItem(f"€ {art['coste']:.2f}"))

            # Botón quitar (centrado)
            contenedor, btn_quitar = crear_boton_quitar_centrado()
            btn_quitar.clicked.connect(lambda checked, idx=i: self.quitar_articulo(idx))
            self.tabla_articulos.setCellWidget(i, 4, contenedor)

            # Acumular totales
            total_articulos += art['cantidad']
            coste_total += art['cantidad'] * art['coste']

        # Actualizar panel de resumen
        self.lbl_resumen.setText(
            f"📊 Total: {len(self.articulos_temp)} artículos ({total_articulos:.2f} unidades) | "
            f"Coste total: € {coste_total:,.2f}"
        )
    
    def quitar_articulo(self, index):
        """Quita un artículo de la lista temporal"""
        if 0 <= index < len(self.articulos_temp):
            del self.articulos_temp[index]
            self.actualizar_tabla_articulos()
   
    def actualizar_filtro_proveedor(self):
        '''Filtra artículos por el proveedor seleccionado'''
        proveedor_id = self.cmb_proveedor.currentData()
        if proveedor_id:
            self.buscador.filtrar_por_proveedor(proveedor_id)
        else:
            self.buscador.limpiar_filtros()
    
    def guardar(self):
        """Guarda la recepción del albarán"""
        num_albaran = self.txt_num_albaran.text().strip()
        
        if not num_albaran:
            QMessageBox.warning(self, "⚠️ Aviso", "El número de albarán es obligatorio.")
            self.txt_num_albaran.setFocus()
            return
        
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe agregar al menos un artículo al albarán.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        proveedor_id = self.cmb_proveedor.currentData()

        try:
            con = get_con()
            cur = con.cursor()

            # Verificar si el albarán ya existe (mismo proveedor + número + fecha)
            cur.execute("""
                SELECT albaran FROM albaranes
                WHERE albaran=? AND proveedor_id=? AND fecha=?
            """, (num_albaran, proveedor_id, fecha))
            if cur.fetchone():
                QMessageBox.warning(
                    self,
                    "⚠️ Albarán duplicado",
                    f"Ya existe un albarán con el mismo número '{num_albaran}'\n"
                    f"del mismo proveedor en la fecha {self.date_fecha.date().toString('dd/MM/yyyy')}.\n\n"
                    "No se pueden registrar albaranes duplicados.\n"
                    "Si necesita modificarlo, contacte al administrador."
                )
                self.txt_num_albaran.setFocus()
                con.close()
                return

            # Advertencia si existe el mismo número pero de otro proveedor o fecha diferente
            cur.execute("SELECT proveedor_id, fecha FROM albaranes WHERE albaran=?", (num_albaran,))
            alb_existente = cur.fetchone()
            if alb_existente:
                respuesta = QMessageBox.question(
                    self,
                    "⚠️ Albarán con número similar",
                    f"Ya existe un albarán con el número '{num_albaran}'\n"
                    "pero de otro proveedor o fecha diferente.\n\n"
                    "¿Desea continuar de todos modos?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if respuesta != QMessageBox.Yes:
                    con.close()
                    return

            # Registrar el albarán
            cur.execute(
                "INSERT INTO albaranes(albaran, proveedor_id, fecha) VALUES(?,?,?)",
                (num_albaran, proveedor_id, fecha)
            )

            con.commit()
            con.close()

            # Preparar datos para el service
            articulos = [
                {
                    'articulo_id': art['id'],
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
                usuario=session_manager.get_usuario_actual() or "admin"
            )

            if not exito:
                QMessageBox.critical(self, "❌ Error", f"Error al guardar:\\n{mensaje}")
                return

            # Guardar en historial
            usuario = session_manager.get_usuario_actual()
            if usuario:
                for art in self.articulos_temp:
                    historial_service.guardar_en_historial(
                        usuario=usuario,
                        tipo_operacion='recepcion',
                        articulo_id=art['id'],
                        articulo_nombre=art['nombre'],
                        cantidad=art['cantidad'],
                        u_medida=art['u_medida'],
                        datos_adicionales={'albaran': num_albaran, 'coste': art['coste']}
                    )

            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Albarán '{num_albaran}' registrado correctamente.\\n\\n{mensaje}"
            )
            self.accept()

        except Exception as e:
            logger.error(f"Error en recepción: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\\n{e}")

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
            con = get_con()
            cur = con.cursor()
            
            if filtro:
                cur.execute("""
                    SELECT a.albaran, p.nombre, a.fecha,
                           (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_arts
                    FROM albaranes a
                    LEFT JOIN proveedores p ON a.proveedor_id = p.id
                    WHERE a.albaran LIKE ? OR p.nombre LIKE ?
                    ORDER BY a.fecha DESC, a.albaran
                """, (f"%{filtro}%", f"%{filtro}%"))
            else:
                cur.execute("""
                    SELECT a.albaran, p.nombre, a.fecha,
                           (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_arts
                    FROM albaranes a
                    LEFT JOIN proveedores p ON a.proveedor_id = p.id
                    ORDER BY a.fecha DESC, a.albaran
                """)
            
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tabla.setItem(i, 0, QTableWidgetItem(row[0]))
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1] or "(Sin proveedor)"))
                # Convertir fecha a formato dd/MM/yyyy
                try:
                    fecha_obj = datetime.datetime.strptime(row[2], "%Y-%m-%d")
                    fecha_mostrar = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_mostrar = row[2]
                self.tabla.setItem(i, 2, QTableWidgetItem(fecha_mostrar))
                self.tabla.setItem(i, 3, QTableWidgetItem(f"{row[3]} artículo(s)"))
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar albaranes:\n{e}")
    
    def buscar(self):
        """Filtra la tabla"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_albaranes(filtro)
    
    def nueva_recepcion(self):
        """Abre el diálogo para nueva recepción"""
        dialogo = DialogoRecepcion(self)
        if dialogo.exec():
            self.cargar_albaranes()