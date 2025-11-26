# ventana_ficha_articulo.py - Ficha Completa de Artículo
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QGroupBox, QHeaderView, QFormLayout, QTextEdit, QTabWidget,
    QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from pathlib import Path
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.services import articulos_service, stock_service, movimientos_service
from src.repos import articulos_repo, stock_repo, movimientos_repo

class VentanaFichaArticulo(QWidget):
    def __init__(self, parent=None, articulo_id=None):
        super().__init__(parent)
        self.articulo_id = articulo_id
        self.setWindowTitle("📦 Ficha de Artículo")
        self.resize(1200, 800)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título y buscador
        header_layout = QHBoxLayout()
        
        titulo = QLabel("📦 Ficha Completa de Artículo")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        lbl_buscar = QLabel("🔍 Buscar artículo:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(400)
        self.cmb_articulo.setEditable(True)
        self.cmb_articulo.setPlaceholderText("Escribe para buscar...")
        self.cmb_articulo.currentIndexChanged.connect(self.cargar_articulo)
        self.cargar_articulos_combo()
        
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_buscar)
        header_layout.addWidget(self.cmb_articulo)
        
        layout.addLayout(header_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Información General
        self.tab_info = QWidget()
        self.crear_tab_informacion()
        self.tabs.addTab(self.tab_info, "ℹ️ Información General")
        
        # Tab 2: Stock por Almacén
        self.tab_stock = QWidget()
        self.crear_tab_stock()
        self.tabs.addTab(self.tab_stock, "📊 Stock por Almacén")
        
        # Tab 3: Historial de Movimientos
        self.tab_historial = QWidget()
        self.crear_tab_historial()
        self.tabs.addTab(self.tab_historial, "📋 Historial de Movimientos")
        
        # Tab 4: Estadísticas
        self.tab_stats = QWidget()
        self.crear_tab_estadisticas()
        self.tabs.addTab(self.tab_stats, "📈 Estadísticas")

        # Tab 5: Últimas Entradas
        self.tab_entradas = QWidget()
        self.crear_tab_entradas()
        self.tabs.addTab(self.tab_entradas, "📦 Últimas Entradas")

        layout.addWidget(self.tabs)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Si se pasó un ID, cargarlo
        if self.articulo_id:
            self.seleccionar_articulo_por_id(self.articulo_id)
    
    def cargar_articulos_combo(self):
        """Carga todos los artículos en el combo"""
        try:
            articulos = articulos_repo.get_todos(solo_activos=True, limit=10000)

            self.cmb_articulo.addItem("(Seleccione un artículo)", None)

            for art in articulos:
                # Texto: Nombre [EAN] [REF]
                texto = art['nombre']
                if art['ean']:
                    texto += f" [EAN: {art['ean']}]"
                if art['ref_proveedor']:
                    texto += f" [REF: {art['ref_proveedor']}]"

                self.cmb_articulo.addItem(texto, art['id'])

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def seleccionar_articulo_por_id(self, articulo_id):
        """Selecciona un artículo en el combo por su ID"""
        for i in range(self.cmb_articulo.count()):
            if self.cmb_articulo.itemData(i) == articulo_id:
                self.cmb_articulo.setCurrentIndex(i)
                break
    
    def cargar_articulo(self):
        """Carga la información del artículo seleccionado"""
        self.articulo_id = self.cmb_articulo.currentData()
        
        if not self.articulo_id:
            return
        
        # Actualizar todos los tabs
        self.actualizar_info_general()
        self.actualizar_stock_almacenes()
        self.actualizar_historial()
        self.actualizar_estadisticas()
        self.actualizar_ultimas_entradas()
    
    # ========================================
    # TAB 1: INFORMACIÓN GENERAL
    # ========================================
    def crear_tab_informacion(self):
        """Crea el tab de información general"""
        layout = QVBoxLayout(self.tab_info)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Grupo: Datos básicos
        grupo_basico = QGroupBox("📋 Datos Básicos")
        form_basico = QFormLayout()
        
        self.lbl_nombre = QLabel()
        self.lbl_ean = QLabel()
        self.lbl_ref = QLabel()
        self.lbl_familia = QLabel()
        self.lbl_ubicacion = QLabel()
        
        form_basico.addRow("📦 Nombre:", self.lbl_nombre)
        form_basico.addRow("🔢 EAN:", self.lbl_ean)
        form_basico.addRow("🏷️ Referencia:", self.lbl_ref)
        form_basico.addRow("📂 Familia:", self.lbl_familia)
        form_basico.addRow("📍 Ubicación:", self.lbl_ubicacion)
        
        grupo_basico.setLayout(form_basico)
        content_layout.addWidget(grupo_basico)
        
        # Grupo: Proveedor y marca
        grupo_prov = QGroupBox("🏭 Proveedor y Marca")
        form_prov = QFormLayout()
        
        self.lbl_proveedor = QLabel()
        self.lbl_marca = QLabel()
        
        form_prov.addRow("🏭 Proveedor:", self.lbl_proveedor)
        form_prov.addRow("🏢 Marca:", self.lbl_marca)
        
        grupo_prov.setLayout(form_prov)
        content_layout.addWidget(grupo_prov)
        
        # Grupo: Stock y unidades
        grupo_stock = QGroupBox("📊 Stock y Unidades")
        form_stock = QFormLayout()
        
        self.lbl_u_medida = QLabel()
        self.lbl_stock_total = QLabel()
        self.lbl_min_alerta = QLabel()
        self.lbl_estado_stock = QLabel()
        
        form_stock.addRow("📏 Unidad de medida:", self.lbl_u_medida)
        form_stock.addRow("📦 Stock total:", self.lbl_stock_total)
        form_stock.addRow("⚠️ Mínimo alerta:", self.lbl_min_alerta)
        form_stock.addRow("🚦 Estado:", self.lbl_estado_stock)
        
        grupo_stock.setLayout(form_stock)
        content_layout.addWidget(grupo_stock)
        
        # Grupo: Precios
        grupo_precios = QGroupBox("💰 Precios")
        form_precios = QFormLayout()
        
        self.lbl_coste = QLabel()
        self.lbl_pvp = QLabel()
        self.lbl_iva = QLabel()
        self.lbl_pvp_iva = QLabel()
        
        form_precios.addRow("💵 Coste:", self.lbl_coste)
        form_precios.addRow("💶 PVP sin IVA:", self.lbl_pvp)
        form_precios.addRow("📈 IVA:", self.lbl_iva)
        form_precios.addRow("💷 PVP con IVA:", self.lbl_pvp_iva)
        
        grupo_precios.setLayout(form_precios)
        content_layout.addWidget(grupo_precios)
        
        # Grupo: Palabras clave
        grupo_palabras = QGroupBox("🔍 Palabras Clave para Búsquedas")
        layout_palabras = QVBoxLayout()
        
        self.txt_palabras = QTextEdit()
        self.txt_palabras.setMaximumHeight(60)
        self.txt_palabras.setReadOnly(True)
        
        layout_palabras.addWidget(self.txt_palabras)
        grupo_palabras.setLayout(layout_palabras)
        content_layout.addWidget(grupo_palabras)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def actualizar_info_general(self):
        """Actualiza la información general del artículo"""
        try:
            # Obtener info del artículo
            articulo = articulos_repo.get_by_id(self.articulo_id)
            if not articulo:
                return

            # Obtener stock total
            stock_total = stock_repo.get_stock_total_articulo(self.articulo_id)

            # Datos básicos
            self.lbl_nombre.setText(f"<b>{articulo['nombre']}</b>")
            self.lbl_ean.setText(articulo['ean'] or "-")
            self.lbl_ref.setText(articulo['ref_proveedor'] or "-")
            self.lbl_familia.setText(articulo['familia_nombre'] or "-")
            self.lbl_ubicacion.setText(articulo['ubicacion_nombre'] or "-")

            # Proveedor y marca
            self.lbl_proveedor.setText(articulo['proveedor_nombre'] or "-")
            self.lbl_marca.setText(articulo['marca'] or "-")

            # Stock y unidades
            u_medida = articulo['u_medida'] or "unidad"
            min_alerta = articulo['min_alerta']

            self.lbl_u_medida.setText(u_medida)
            self.lbl_stock_total.setText(f"<b>{stock_total:.2f}</b> {u_medida}")
            self.lbl_min_alerta.setText(f"{min_alerta:.2f} {u_medida}")

            # Estado del stock con color
            if stock_total < min_alerta:
                estado = "<span style='color: #dc2626; font-weight: bold;'>⚠️ BAJO MÍNIMO</span>"
            elif stock_total == 0:
                estado = "<span style='color: #dc2626; font-weight: bold;'>❌ SIN STOCK</span>"
            else:
                estado = "<span style='color: #059669; font-weight: bold;'>✅ OK</span>"
            self.lbl_estado_stock.setText(estado)

            # Precios
            coste = articulo['coste'] or 0
            pvp_sin = articulo['pvp_sin'] or 0
            iva = articulo['iva'] or 21
            pvp_con = pvp_sin * (1 + iva / 100)

            self.lbl_coste.setText(f"€ {coste:.2f}")
            self.lbl_pvp.setText(f"€ {pvp_sin:.2f}")
            self.lbl_iva.setText(f"{iva:.0f}%")
            self.lbl_pvp_iva.setText(f"<b>€ {pvp_con:.2f}</b>")

            # Palabras clave
            self.txt_palabras.setPlainText(articulo['palabras_clave'] or "(Sin palabras clave)")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar información:\n{e}")
    
    # ========================================
    # TAB 2: STOCK POR ALMACÉN
    # ========================================
    def crear_tab_stock(self):
        """Crea el tab de stock por almacén"""
        layout = QVBoxLayout(self.tab_stock)
        
        lbl_titulo = QLabel("📊 Stock Actual por Almacén/Furgoneta")
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(lbl_titulo)
        
        self.tabla_stock = QTableWidget()
        self.tabla_stock.setColumnCount(3)
        self.tabla_stock.setHorizontalHeaderLabels(["Almacén/Furgoneta", "Stock", "Estado"])
        self.tabla_stock.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.tabla_stock.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla_stock)
    
    def actualizar_stock_almacenes(self):
        """Actualiza el stock por almacén"""
        try:
            almacenes = stock_repo.get_stock_articulo_por_almacen(self.articulo_id)

            self.tabla_stock.setRowCount(len(almacenes))

            for i, alm in enumerate(almacenes):
                # Almacén
                self.tabla_stock.setItem(i, 0, QTableWidgetItem(alm['almacen']))

                # Stock
                stock = alm['stock']
                item_stock = QTableWidgetItem(f"{stock:.2f}")
                item_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_stock.setItem(i, 1, item_stock)

                # Estado visual
                if stock > 0:
                    estado = "✅ Disponible"
                    color = QColor("#d1fae5")
                else:
                    estado = "❌ Vacío"
                    color = QColor("#fee2e2")

                item_estado = QTableWidgetItem(estado)
                item_estado.setBackground(color)
                item_estado.setTextAlignment(Qt.AlignCenter)
                self.tabla_stock.setItem(i, 2, item_estado)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar stock:\n{e}")
    
    # ========================================
    # TAB 3: HISTORIAL DE MOVIMIENTOS
    # ========================================
    def crear_tab_historial(self):
        """Crea el tab de historial"""
        layout = QVBoxLayout(self.tab_historial)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        lbl_limite = QLabel("Mostrar últimos:")
        self.cmb_limite = QComboBox()
        self.cmb_limite.addItems(["20", "50", "100", "Todos"])
        self.cmb_limite.setCurrentIndex(1)
        self.cmb_limite.currentTextChanged.connect(self.actualizar_historial)
        
        lbl_tipo = QLabel("Tipo:")
        self.cmb_tipo_hist = QComboBox()
        self.cmb_tipo_hist.addItems(["Todos", "ENTRADA", "TRASPASO", "IMPUTACION", "PERDIDA", "DEVOLUCION"])
        self.cmb_tipo_hist.currentTextChanged.connect(self.actualizar_historial)
        
        filtros_layout.addWidget(lbl_limite)
        filtros_layout.addWidget(self.cmb_limite)
        filtros_layout.addWidget(lbl_tipo)
        filtros_layout.addWidget(self.cmb_tipo_hist)
        filtros_layout.addStretch()
        
        layout.addLayout(filtros_layout)
        
        # Tabla
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(8)
        self.tabla_historial.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Origen", "Destino", "Cantidad", "OT", "Responsable", "Motivo"
        ])
        self.tabla_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.tabla_historial.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        layout.addWidget(self.tabla_historial)
    
    def actualizar_historial(self):
        """Actualiza el historial de movimientos"""
        try:
            # Determinar filtros
            tipo_filtro = None
            if self.cmb_tipo_hist.currentIndex() > 0:
                tipo_filtro = self.cmb_tipo_hist.currentText()

            # Determinar límite
            limite_str = self.cmb_limite.currentText()
            limite = 10000 if limite_str == "Todos" else int(limite_str)

            # Obtener movimientos
            movimientos = movimientos_repo.get_movimientos_articulo(
                articulo_id=self.articulo_id,
                tipo=tipo_filtro,
                limit=limite
            )

            self.tabla_historial.setRowCount(len(movimientos))

            for i, mov in enumerate(movimientos):
                # Fecha
                try:
                    fecha_obj = datetime.datetime.strptime(mov['fecha'], "%Y-%m-%d")
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    fecha_str = mov['fecha']
                self.tabla_historial.setItem(i, 0, QTableWidgetItem(fecha_str))

                # Tipo con color
                tipo = mov['tipo']
                item_tipo = QTableWidgetItem(tipo)
                if tipo == "ENTRADA":
                    item_tipo.setBackground(QColor("#d1fae5"))
                elif tipo == "TRASPASO":
                    item_tipo.setBackground(QColor("#dbeafe"))
                elif tipo == "IMPUTACION":
                    item_tipo.setBackground(QColor("#fef3c7"))
                elif tipo == "PERDIDA":
                    item_tipo.setBackground(QColor("#fee2e2"))
                elif tipo == "DEVOLUCION":
                    item_tipo.setBackground(QColor("#fce7f3"))
                self.tabla_historial.setItem(i, 1, item_tipo)

                # Origen
                self.tabla_historial.setItem(i, 2, QTableWidgetItem(mov['origen_nombre'] or "-"))

                # Destino
                self.tabla_historial.setItem(i, 3, QTableWidgetItem(mov['destino_nombre'] or "-"))

                # Cantidad
                item_cant = QTableWidgetItem(f"{mov['cantidad']:.2f}")
                item_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_historial.setItem(i, 4, item_cant)

                # OT
                self.tabla_historial.setItem(i, 5, QTableWidgetItem(mov['ot'] or "-"))

                # Responsable
                self.tabla_historial.setItem(i, 6, QTableWidgetItem(mov['responsable'] or "-"))

                # Motivo
                self.tabla_historial.setItem(i, 7, QTableWidgetItem(mov['motivo'] or "-"))
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar historial:\n{e}")
    
    # ========================================
    # TAB 4: ESTADÍSTICAS
    # ========================================
    def crear_tab_estadisticas(self):
        """Crea el tab de estadísticas"""
        layout = QVBoxLayout(self.tab_stats)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Grupo: Resumen de movimientos
        grupo_resumen = QGroupBox("📊 Resumen de Movimientos")
        form_resumen = QFormLayout()
        
        self.lbl_total_entradas = QLabel()
        self.lbl_total_salidas = QLabel()
        self.lbl_total_traspasos = QLabel()
        self.lbl_total_imputaciones = QLabel()
        self.lbl_total_perdidas = QLabel()
        
        form_resumen.addRow("📥 Total entradas:", self.lbl_total_entradas)
        form_resumen.addRow("📤 Total salidas:", self.lbl_total_salidas)
        form_resumen.addRow("🔄 Total traspasos:", self.lbl_total_traspasos)
        form_resumen.addRow("📝 Total imputaciones:", self.lbl_total_imputaciones)
        form_resumen.addRow("⚠️ Total perdidas:", self.lbl_total_perdidas)
        
        grupo_resumen.setLayout(form_resumen)
        content_layout.addWidget(grupo_resumen)
        
        # Grupo: Últimos 30 días
        grupo_30d = QGroupBox("📅 Últimos 30 Días")
        form_30d = QFormLayout()
        
        self.lbl_entradas_30d = QLabel()
        self.lbl_consumo_30d = QLabel()
        
        form_30d.addRow("📥 Entradas:", self.lbl_entradas_30d)
        form_30d.addRow("📤 Consumo total:", self.lbl_consumo_30d)
        
        grupo_30d.setLayout(form_30d)
        content_layout.addWidget(grupo_30d)
        
        # Grupo: Top OTs
        grupo_ots = QGroupBox("🏆 Top 5 OTs con más consumo")
        layout_ots = QVBoxLayout()
        
        self.tabla_top_ots = QTableWidget()
        self.tabla_top_ots.setColumnCount(2)
        self.tabla_top_ots.setHorizontalHeaderLabels(["OT", "Cantidad"])
        self.tabla_top_ots.setMaximumHeight(200)
        self.tabla_top_ots.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout_ots.addWidget(self.tabla_top_ots)
        grupo_ots.setLayout(layout_ots)
        content_layout.addWidget(grupo_ots)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas del artículo"""
        try:
            stats = movimientos_repo.get_estadisticas_articulo(self.articulo_id)

            # Resumen total
            totales = stats['totales']
            self.lbl_total_entradas.setText(f"<b>{totales.get('entradas') or 0:.2f}</b>")
            self.lbl_total_salidas.setText(f"<b>{totales.get('salidas') or 0:.2f}</b>")
            self.lbl_total_traspasos.setText(f"<b>{totales.get('traspasos') or 0:.2f}</b>")
            self.lbl_total_imputaciones.setText(f"<b>{totales.get('imputaciones') or 0:.2f}</b>")
            self.lbl_total_perdidas.setText(f"<b>{totales.get('perdidas') or 0:.2f}</b>")

            # Últimos 30 días
            stats_30d = stats['stats_30d']
            self.lbl_entradas_30d.setText(f"<b>{stats_30d.get('entradas') or 0:.2f}</b>")
            self.lbl_consumo_30d.setText(f"<b>{stats_30d.get('consumo') or 0:.2f}</b>")

            # Top OTs
            top_ots = stats['top_ots']
            self.tabla_top_ots.setRowCount(len(top_ots))

            for i, ot in enumerate(top_ots):
                self.tabla_top_ots.setItem(i, 0, QTableWidgetItem(ot['ot'] or ''))
                item_cant = QTableWidgetItem(f"{ot.get('total') or 0:.2f}")
                item_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_top_ots.setItem(i, 1, item_cant)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar estadísticas:\n{e}")

    # ========================================
    # TAB 5: ÚLTIMAS ENTRADAS
    # ========================================
    def crear_tab_entradas(self):
        """Crea el tab de últimas entradas desde proveedores"""
        layout = QVBoxLayout(self.tab_entradas)

        # Título
        titulo = QLabel("📦 Últimas 50 Entradas desde Proveedores")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(titulo)

        # Tabla de entradas
        self.tabla_entradas = QTableWidget()
        self.tabla_entradas.setColumnCount(5)
        self.tabla_entradas.setHorizontalHeaderLabels([
            "Fecha", "Cantidad", "Proveedor", "Albarán", "Coste Unit."
        ])

        # Configurar tabla
        self.tabla_entradas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_entradas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_entradas.setAlternatingRowColors(True)

        # Hacer la tabla ordenable por columnas
        self.tabla_entradas.setSortingEnabled(True)

        # Ajustar columnas
        header = self.tabla_entradas.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(2, QHeaderView.Stretch)            # Proveedor
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Albarán
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Coste

        layout.addWidget(self.tabla_entradas)

    def actualizar_ultimas_entradas(self):
        """Actualiza la tabla de últimas entradas"""
        try:
            # Obtener últimas entradas del repositorio
            entradas = articulos_repo.get_ultimas_entradas(self.articulo_id, limit=50)

            # Limpiar tabla
            self.tabla_entradas.setRowCount(0)
            self.tabla_entradas.setSortingEnabled(False)  # Deshabilitar ordenación temporalmente

            # Llenar tabla
            self.tabla_entradas.setRowCount(len(entradas))

            for i, entrada in enumerate(entradas):
                # Fecha (formato dd/mm/yyyy)
                fecha_str = entrada['fecha']
                try:
                    from datetime import datetime
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
                    fecha_mostrar = fecha_obj.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    fecha_mostrar = fecha_str

                item_fecha = QTableWidgetItem(fecha_mostrar)
                item_fecha.setTextAlignment(Qt.AlignCenter)
                self.tabla_entradas.setItem(i, 0, item_fecha)

                # Cantidad
                item_cant = QTableWidgetItem(f"{entrada['cantidad']:.2f}")
                item_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_entradas.setItem(i, 1, item_cant)

                # Proveedor
                proveedor = entrada['proveedor'] or 'Sin proveedor'
                self.tabla_entradas.setItem(i, 2, QTableWidgetItem(proveedor))

                # Albarán
                albaran = entrada['albaran'] or '-'
                item_albaran = QTableWidgetItem(albaran)
                item_albaran.setTextAlignment(Qt.AlignCenter)
                self.tabla_entradas.setItem(i, 3, item_albaran)

                # Coste unitario
                coste = entrada['coste_unit']
                if coste:
                    item_coste = QTableWidgetItem(f"{coste:.2f} €")
                else:
                    item_coste = QTableWidgetItem('-')
                item_coste.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_entradas.setItem(i, 4, item_coste)

            # Reactivar ordenación (por defecto ordenará por fecha descendente)
            self.tabla_entradas.setSortingEnabled(True)

            # Ordenar por fecha descendente (más recientes primero)
            self.tabla_entradas.sortItems(0, Qt.DescendingOrder)

        except Exception as e:
            logger.exception(f"Error al cargar últimas entradas: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al cargar últimas entradas:\n{e}")
