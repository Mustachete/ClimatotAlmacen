# buscador_articulos.py - Buscador Inteligente de Artículos
"""
Widget reutilizable para buscar artículos por EAN, referencia o nombre.
Incluye autocompletado, detección automática y opción de crear nuevos artículos.

CARACTERÍSTICAS:
✅ Busca por EAN, referencia o nombre
✅ Autocompletado mientras escribes
✅ Detecta si el artículo existe
✅ Botón lupa para búsqueda avanzada
✅ Ofrece crear artículo nuevo si no existe
✅ Filtra por almacén/proveedor si se especifica
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QListWidget,
    QLabel, QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit,
    QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon
from src.core.db_utils import get_con


class BuscadorArticulos(QWidget):
    """
    Widget de búsqueda inteligente de artículos.
    
    Señales:
        articuloSeleccionado(dict): Emite cuando se selecciona un artículo válido
            dict contiene: {'id', 'nombre', 'u_medida', 'ean', 'ref', 'coste', ...}
    
    Uso:
        buscador = BuscadorArticulos()
        buscador.articuloSeleccionado.connect(mi_funcion)
        
        # Opcional: filtrar por proveedor
        buscador.filtrar_por_proveedor(proveedor_id)
        
        # Opcional: filtrar por almacén (solo artículos con stock)
        buscador.filtrar_por_almacen(almacen_id)
    """
    
    # Señal emitida cuando se selecciona un artículo
    articuloSeleccionado = Signal(dict)
    
    def __init__(self, parent=None, mostrar_boton_lupa=True, placeholder="Buscar por EAN, referencia o nombre..."):
        super().__init__(parent)
        
        self.filtro_proveedor_id = None
        self.filtro_almacen_id = None
        self.articulo_actual = None
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # ========== BARRA DE BÚSQUEDA ==========
        busqueda_layout = QHBoxLayout()
        
        # Campo de texto
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText(placeholder)
        self.txt_buscar.setMinimumHeight(40)
        self.txt_buscar.returnPressed.connect(self.buscar_exacto)
        self.txt_buscar.textChanged.connect(self.busqueda_tiempo_real)
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1e3a8a;
                background-color: #f8fafc;
            }
        """)
        
        # Campo de búsqueda ocupa el espacio disponible
        busqueda_layout.addWidget(self.txt_buscar, stretch=1)

        # Botón lupa (búsqueda avanzada)
        if mostrar_boton_lupa:
            self.btn_lupa = QPushButton("🔍 Buscar")
            self.btn_lupa.setMinimumWidth(100)
            self.btn_lupa.setToolTip("Búsqueda avanzada")
            self.btn_lupa.clicked.connect(self.busqueda_avanzada)
            busqueda_layout.addWidget(self.btn_lupa, stretch=0)
        layout.addLayout(busqueda_layout)
        
        # ========== LISTA DE SUGERENCIAS ==========
        self.lista_sugerencias = QListWidget()
        self.lista_sugerencias.setMaximumHeight(150)
        self.lista_sugerencias.setVisible(False)
        self.lista_sugerencias.itemClicked.connect(self.seleccionar_sugerencia)
        self.lista_sugerencias.setStyleSheet("""
            QListWidget {
                border: 2px solid #1e3a8a;
                border-radius: 5px;
                background-color: white;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            QListWidget::item:hover {
                background-color: #dbeafe;
            }
            QListWidget::item:selected {
                background-color: #1e3a8a;
                color: white;
            }
        """)
        layout.addWidget(self.lista_sugerencias)
        
        # ========== LABEL DE ESTADO ==========
        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
        self.lbl_estado.setVisible(False)
        layout.addWidget(self.lbl_estado)
        
        # Timer para búsqueda en tiempo real
        self.timer_busqueda = QTimer()
        self.timer_busqueda.setSingleShot(True)
        self.timer_busqueda.timeout.connect(self.buscar_sugerencias)
    
    def filtrar_por_proveedor(self, proveedor_id):
        """Filtra resultados solo de un proveedor específico"""
        self.filtro_proveedor_id = proveedor_id
    
    def filtrar_por_almacen(self, almacen_id):
        """Filtra resultados solo con artículos que tengan stock en el almacén"""
        self.filtro_almacen_id = almacen_id
    
    def limpiar_filtros(self):
        """Elimina todos los filtros"""
        self.filtro_proveedor_id = None
        self.filtro_almacen_id = None
    
    def limpiar(self):
        """Limpia el buscador"""
        self.txt_buscar.clear()
        self.lista_sugerencias.clear()
        self.lista_sugerencias.setVisible(False)
        self.lbl_estado.setVisible(False)
        self.articulo_actual = None
    
    def busqueda_tiempo_real(self):
        """Activa el timer de búsqueda al escribir"""
        texto = self.txt_buscar.text().strip()
        
        if len(texto) < 2:
            self.lista_sugerencias.setVisible(False)
            self.lbl_estado.setVisible(False)
            return
        
        # Esperar 300ms antes de buscar (evita búsquedas excesivas)
        self.timer_busqueda.stop()
        self.timer_busqueda.start(300)
    
    def buscar_sugerencias(self):
        """Busca artículos y muestra sugerencias"""
        texto = self.txt_buscar.text().strip()
        
        if len(texto) < 2:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Construir query según filtros
            query = """
                SELECT a.id, a.nombre, a.u_medida, a.ean, a.ref_proveedor, a.coste, a.pvp_sin, 
                       a.proveedor_id, a.familia_id, a.ubicacion_id, a.marca
                FROM articulos a
                WHERE a.activo=1 AND (
                    a.ean LIKE ? OR
                    a.ref_proveedor LIKE ? OR
                    a.nombre LIKE ? OR
                    a.palabras_clave LIKE ?
                )
            """
            params = [f"%{texto}%"] * 4
            
            # Agregar filtro de proveedor si existe
            if self.filtro_proveedor_id:
                query += " AND a.proveedor_id=?"
                params.append(self.filtro_proveedor_id)
            
            # Agregar filtro de almacén (con stock) si existe
            if self.filtro_almacen_id:
                query += """ AND EXISTS (
                    SELECT 1 FROM vw_stock v 
                    WHERE v.articulo_id=a.id AND v.almacen_id=? AND v.delta > 0
                )"""
                params.append(self.filtro_almacen_id)
            
            query += """
                ORDER BY 
                    CASE 
                        WHEN a.ean = ? THEN 1
                        WHEN a.ref_proveedor = ? THEN 2
                        WHEN a.nombre LIKE ? THEN 3
                        ELSE 4
                    END
                LIMIT 10
            """
            params.extend([texto, texto, f"{texto}%"])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()
            
            # Mostrar sugerencias
            self.lista_sugerencias.clear()
            
            if not rows:
                self.lbl_estado.setText("❌ No se encontraron artículos")
                self.lbl_estado.setVisible(True)
                self.lista_sugerencias.setVisible(False)
                return
            
            self.lbl_estado.setVisible(False)
            
            for row in rows:
                texto_item = f"{row[1]}"
                if row[3]:  # EAN
                    texto_item += f" | EAN: {row[3]}"
                if row[4]:  # Ref
                    texto_item += f" | Ref: {row[4]}"
                texto_item += f" | {row[2]}"
                
                item = QListWidgetItem(texto_item)
                item.setData(Qt.UserRole, {
                    'id': row[0],
                    'nombre': row[1],
                    'u_medida': row[2],
                    'ean': row[3],
                    'ref': row[4],
                    'coste': row[5] or 0.0,
                    'pvp': row[6] or 0.0,
                    'proveedor_id': row[7],
                    'familia_id': row[8],
                    'ubicacion_id': row[9],
                    'marca': row[10]
                })
                self.lista_sugerencias.addItem(item)
            
            self.lista_sugerencias.setVisible(True)
            
        except Exception as e:
            self.lbl_estado.setText(f"❌ Error: {e}")
            self.lbl_estado.setVisible(True)
    
    def buscar_exacto(self):
        """Busca coincidencia exacta al presionar Enter"""
        texto = self.txt_buscar.text().strip()
        
        if not texto:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Buscar coincidencia EXACTA (primero por EAN, luego por ref)
            query = """
                SELECT a.id, a.nombre, a.u_medida, a.ean, a.ref_proveedor, a.coste, a.pvp_sin,
                       a.proveedor_id, a.familia_id, a.ubicacion_id, a.marca
                FROM articulos a
                WHERE a.activo=1 AND (a.ean=? OR a.ref_proveedor=?)
            """
            params = [texto, texto]
            
            if self.filtro_proveedor_id:
                query += " AND a.proveedor_id=?"
                params.append(self.filtro_proveedor_id)
            
            if self.filtro_almacen_id:
                query += """ AND EXISTS (
                    SELECT 1 FROM vw_stock v 
                    WHERE v.articulo_id=a.id AND v.almacen_id=? AND v.delta > 0
                )"""
                params.append(self.filtro_almacen_id)
            
            query += " LIMIT 1"
            
            cur.execute(query, params)
            row = cur.fetchone()
            con.close()
            
            if row:
                # ✅ ENCONTRADO - Emitir señal
                articulo = {
                    'id': row[0],
                    'nombre': row[1],
                    'u_medida': row[2],
                    'ean': row[3],
                    'ref': row[4],
                    'coste': row[5] or 0.0,
                    'pvp': row[6] or 0.0,
                    'proveedor_id': row[7],
                    'familia_id': row[8],
                    'ubicacion_id': row[9],
                    'marca': row[10]
                }
                self.articulo_actual = articulo
                self.articuloSeleccionado.emit(articulo)
                self.lbl_estado.setText(f"✅ {row[1]}")
                self.lbl_estado.setStyleSheet("color: #16a34a; font-size: 12px; font-weight: bold;")
                self.lbl_estado.setVisible(True)
                self.lista_sugerencias.setVisible(False)
            else:
                # ❌ NO ENCONTRADO - Ofrecer crear
                self.ofrecer_crear_articulo(texto)
        
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al buscar:\n{e}")
    
    def seleccionar_sugerencia(self, item):
        """Selecciona un artículo de las sugerencias"""
        articulo = item.data(Qt.UserRole)
        self.articulo_actual = articulo
        self.txt_buscar.setText(articulo['nombre'])
        self.lista_sugerencias.setVisible(False)
        self.articuloSeleccionado.emit(articulo)
        self.lbl_estado.setText(f"✅ {articulo['nombre']}")
        self.lbl_estado.setStyleSheet("color: #16a34a; font-size: 12px; font-weight: bold;")
        self.lbl_estado.setVisible(True)
    
    def ofrecer_crear_articulo(self, texto_busqueda):
        """Ofrece crear un artículo nuevo si no existe"""
        respuesta = QMessageBox.question(
            self,
            "❓ Artículo no encontrado",
            f"No se encontró ningún artículo con:\n'{texto_busqueda}'\n\n"
            "¿Desea crear un nuevo artículo?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            self.abrir_dialogo_nuevo_articulo(texto_busqueda)
        else:
            # Usuario canceló - limpiar el campo para que pueda buscar otro
            self.limpiar()
            self.txt_buscar.setFocus()
    
    def abrir_dialogo_nuevo_articulo(self, referencia_inicial=""):
        """Abre el diálogo para crear un nuevo artículo"""
        from src.ventanas.maestros.ventana_articulos import DialogoArticulo
        dialogo = DialogoArticulo(self, referencia_inicial=referencia_inicial)
        if dialogo.exec():
            # Recargar búsqueda con el nuevo artículo
            self.txt_buscar.setText(referencia_inicial)
            self.buscar_exacto()
    
    def busqueda_avanzada(self):
        """Abre diálogo de búsqueda avanzada"""
        dialogo = DialogoBusquedaAvanzada(
            self, 
            filtro_proveedor=self.filtro_proveedor_id,
            filtro_almacen=self.filtro_almacen_id
        )
        if dialogo.exec():
            articulo = dialogo.articulo_seleccionado
            if articulo:
                self.articulo_actual = articulo
                self.txt_buscar.setText(articulo['nombre'])
                self.articuloSeleccionado.emit(articulo)
                self.lbl_estado.setText(f"✅ {articulo['nombre']}")
                self.lbl_estado.setStyleSheet("color: #16a34a; font-size: 12px; font-weight: bold;")
                self.lbl_estado.setVisible(True)


class DialogoBusquedaAvanzada(QDialog):
    """Diálogo de búsqueda avanzada con filtros"""
    
    def __init__(self, parent=None, filtro_proveedor=None, filtro_almacen=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Búsqueda Avanzada de Artículos")
        self.setFixedSize(800, 600)
        
        self.filtro_proveedor = filtro_proveedor
        self.filtro_almacen = filtro_almacen
        self.articulo_seleccionado = None
        
        layout = QVBoxLayout(self)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        lbl_familia = QLabel("Familia:")
        self.cmb_familia = QComboBox()
        self.cmb_familia.addItem("(Todas)", None)
        self.cargar_familias()
        self.cmb_familia.currentIndexChanged.connect(self.filtrar)
        
        lbl_buscar = QLabel("Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Nombre, EAN, ref...")
        self.txt_buscar.textChanged.connect(self.filtrar)
        
        filtros_layout.addWidget(lbl_familia)
        filtros_layout.addWidget(self.cmb_familia)
        filtros_layout.addWidget(lbl_buscar)
        filtros_layout.addWidget(self.txt_buscar)
        
        layout.addLayout(filtros_layout)

        # Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "EAN", "Ref", "U.Medida"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self.seleccionar)
        layout.addWidget(self.tabla)
        
        # Botones
        botones_layout = QHBoxLayout()
        
        btn_seleccionar = QPushButton("✅ Seleccionar")
        btn_seleccionar.clicked.connect(self.seleccionar)
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        botones_layout.addWidget(btn_seleccionar)
        botones_layout.addWidget(btn_cancelar)
        
        layout.addLayout(botones_layout)
        
        # Cargar datos
        self.cargar_articulos()
    
    def cargar_familias(self):
        """Carga las familias disponibles"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM familias ORDER BY nombre")
            rows = cur.fetchall()
            con.close()

            for row in rows:
                self.cmb_familia.addItem(row[1], row[0])
        except Exception as e:
            from src.core.logger import logger
            logger.exception(f"Error al cargar familias en buscador avanzado: {e}")
            # Continuar sin familias - el combo tendrá solo "(Todas)"
    
    def cargar_articulos(self, filtro_texto="", filtro_familia=None):
        """Carga artículos con filtros"""
        try:
            con = get_con()
            cur = con.cursor()
            
            query = """
                SELECT a.id, a.nombre, a.ean, a.ref_proveedor, a.u_medida,
                       a.coste, a.pvp_sin, a.proveedor_id, a.familia_id, a.ubicacion_id, a.marca
                FROM articulos a
                WHERE a.activo=1
            """
            params = []
            
            if filtro_texto:
                query += """ AND (
                    a.nombre LIKE ? OR a.ean LIKE ? OR a.ref_proveedor LIKE ? OR a.palabras_clave LIKE ?
                )"""
                params.extend([f"%{filtro_texto}%"] * 4)
            
            if filtro_familia:
                query += " AND a.familia_id=?"
                params.append(filtro_familia)
            
            if self.filtro_proveedor:
                query += " AND a.proveedor_id=?"
                params.append(self.filtro_proveedor)
            
            if self.filtro_almacen:
                query += """ AND EXISTS (
                    SELECT 1 FROM vw_stock v 
                    WHERE v.articulo_id=a.id AND v.almacen_id=? AND v.delta > 0
                )"""
                params.append(self.filtro_almacen)
            
            query += " ORDER BY a.nombre LIMIT 200"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1]))
                self.tabla.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.tabla.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.tabla.setItem(i, 4, QTableWidgetItem(row[4]))
                
                # Guardar datos completos
                self.tabla.item(i, 0).setData(Qt.UserRole, {
                    'id': row[0],
                    'nombre': row[1],
                    'ean': row[2],
                    'ref': row[3],
                    'u_medida': row[4],
                    'coste': row[5] or 0.0,
                    'pvp': row[6] or 0.0,
                    'proveedor_id': row[7],
                    'familia_id': row[8],
                    'ubicacion_id': row[9],
                    'marca': row[10]
                })
        
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def filtrar(self):
        """Aplica filtros"""
        texto = self.txt_buscar.text().strip()
        familia = self.cmb_familia.currentData()
        self.cargar_articulos(texto, familia)
    
    def seleccionar(self):
        """Selecciona el artículo"""
        fila = self.tabla.currentRow()
        if fila >= 0:
            item = self.tabla.item(fila, 0)
            self.articulo_seleccionado = item.data(Qt.UserRole)
            self.accept()
