"""
Ventana de Análisis de Consumos - Vista con 5 tabs
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QDateEdit,
    QComboBox, QTextEdit, QGroupBox, QMessageBox, QCompleter
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from datetime import date, datetime
from typing import List, Dict, Any

from src.services import consumos_service
from src.ui.estilos import (
    ESTILO_VENTANA,
    ESTILO_TITULO_VENTANA,
    ESTILO_TABS,
    ESTILO_ALERTA_INFO
)


class VentanaConsumos(QWidget):
    """
    Ventana principal de análisis de consumos con 5 tabs:
    - Por OT
    - Por Operario
    - Por Furgoneta
    - Por Período
    - Por Artículo
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Análisis de Consumos")
        self.resize(1100, 700)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📊 ANÁLISIS DE CONSUMOS")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(ESTILO_TITULO_VENTANA)
        layout.addWidget(titulo)
        
        # Tabs principales
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(ESTILO_TABS)
        
        # Crear cada tab
        self.tab_ot = self._crear_tab_ot()
        self.tab_operario = self._crear_tab_operario()
        self.tab_furgoneta = self._crear_tab_furgoneta()
        self.tab_periodo = self._crear_tab_periodo()
        self.tab_articulo = self._crear_tab_articulo()
        
        # Agregar tabs
        self.tabs.addTab(self.tab_ot, "📋 Por OT")
        self.tabs.addTab(self.tab_operario, "👷 Por Operario")
        self.tabs.addTab(self.tab_furgoneta, "🚐 Por Furgoneta")
        self.tabs.addTab(self.tab_periodo, "📅 Por Período")
        self.tabs.addTab(self.tab_articulo, "📦 Por Artículo")
        
        layout.addWidget(self.tabs)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
    
    # ========================================
    # TAB 1: CONSUMOS POR OT
    # ========================================
    
    def _crear_tab_ot(self) -> QWidget:
        """Crea el tab de consumos por OT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Panel de búsqueda
        panel_busqueda = QGroupBox("Buscar OT")
        panel_layout = QHBoxLayout()
        
        self.ot_input = QLineEdit()
        self.ot_input.setPlaceholderText("Número de OT...")
        self.ot_input.returnPressed.connect(self._buscar_ot)
        
        btn_buscar = QPushButton("🔍 Consultar")
        btn_buscar.clicked.connect(self._buscar_ot)
        
        btn_ots_recientes = QPushButton("📋 OTs Recientes")
        btn_ots_recientes.clicked.connect(self._mostrar_ots_recientes)
        
        panel_layout.addWidget(QLabel("OT:"))
        panel_layout.addWidget(self.ot_input)
        panel_layout.addWidget(btn_buscar)
        panel_layout.addWidget(btn_ots_recientes)
        panel_busqueda.setLayout(panel_layout)
        layout.addWidget(panel_busqueda)
        
        # Panel de resumen
        self.ot_resumen = QLabel("Seleccione una OT para ver el detalle")
        self.ot_resumen.setStyleSheet(ESTILO_ALERTA_INFO)
        layout.addWidget(self.ot_resumen)
        
        # Tabla de detalle
        self.tabla_ot = QTableWidget(0, 7)
        self.tabla_ot.setHorizontalHeaderLabels([
            "Artículo", "Unidad", "Cantidad", "Coste Unit.", "Coste Total", "Fecha", "Operario"
        ])
        self.tabla_ot.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_ot.setAlternatingRowColors(True)
        layout.addWidget(self.tabla_ot)
        
        # Botones de acción
        botones = QHBoxLayout()
        btn_exportar_ot = QPushButton("📄 Exportar a Excel")
        btn_exportar_ot.clicked.connect(self._exportar_ot)
        btn_imprimir_ot = QPushButton("🖨️ Imprimir")
        btn_imprimir_ot.clicked.connect(self._imprimir_ot)
        botones.addStretch()
        botones.addWidget(btn_exportar_ot)
        botones.addWidget(btn_imprimir_ot)
        layout.addLayout(botones)
        
        return widget
    
    def _buscar_ot(self):
        """Busca y muestra el detalle de una OT"""
        ot = self.ot_input.text().strip()
        
        if not ot:
            QMessageBox.warning(self, "Aviso", "Por favor, introduce un número de OT")
            return
        
        try:
            datos = consumos_service.obtener_consumos_ot(ot)
            
            if not datos['detalle']:
                QMessageBox.information(self, "Sin resultados", 
                    f"No se encontraron consumos para la OT: {ot}")
                return
            
            # Actualizar resumen
            resumen = datos['resumen']
            texto_resumen = f"""
<b>OT: {ot}</b><br>
<br>
<b>Artículos diferentes:</b> {resumen.get('total_articulos', 0)}<br>
<b>Total imputaciones:</b> {resumen.get('total_imputaciones', 0)}<br>
<b>Coste total:</b> <span style='font-size:16px; color:#dc2626;'><b>{consumos_service.formatear_coste(resumen.get('coste_total', 0))}</b></span><br>
<b>Primera imputación:</b> {resumen.get('fecha_primera', 'N/A')}<br>
<b>Última imputación:</b> {resumen.get('fecha_ultima', 'N/A')}
            """
            self.ot_resumen.setText(texto_resumen)
            
            # Actualizar tabla
            self.tabla_ot.setRowCount(0)
            for row in datos['detalle']:
                r = self.tabla_ot.rowCount()
                self.tabla_ot.insertRow(r)
                
                self.tabla_ot.setItem(r, 0, QTableWidgetItem(row.get('articulo', '')))
                self.tabla_ot.setItem(r, 1, QTableWidgetItem(row.get('unidad', '')))
                self.tabla_ot.setItem(r, 2, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad', 0), row.get('unidad', ''))
                ))
                self.tabla_ot.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_unit', 0))
                ))
                self.tabla_ot.setItem(r, 4, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
                self.tabla_ot.setItem(r, 5, QTableWidgetItem(row.get('fecha', '')))
                self.tabla_ot.setItem(r, 6, QTableWidgetItem(row.get('operario', '')))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar OT:\n{e}")
    
    def _mostrar_ots_recientes(self):
        """Muestra diálogo con OTs recientes"""
        try:
            ots = consumos_service.obtener_ots_recientes(20)
            
            if not ots:
                QMessageBox.information(self, "Sin datos", "No hay OTs con consumos registrados")
                return
            
            # Crear diálogo simple con lista de OTs
            from PySide6.QtWidgets import QDialog, QListWidget
            
            dialogo = QDialog(self)
            dialogo.setWindowTitle("OTs Recientes")
            dialogo.resize(500, 400)
            
            layout = QVBoxLayout(dialogo)
            layout.addWidget(QLabel("Selecciona una OT para ver su detalle:"))
            
            lista = QListWidget()
            for ot_data in ots:
                texto = f"OT {ot_data['ot']} - {ot_data['fecha_ultima']} - " \
                        f"{ot_data['total_imputaciones']} imputaciones - " \
                        f"{consumos_service.formatear_coste(ot_data.get('coste_total', 0))}"
                lista.addItem(texto)
            
            lista.itemDoubleClicked.connect(lambda item: self._seleccionar_ot_reciente(item, dialogo))
            layout.addWidget(lista)
            
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.clicked.connect(dialogo.close)
            layout.addWidget(btn_cerrar)
            
            dialogo.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar OTs:\n{e}")
    
    def _seleccionar_ot_reciente(self, item, dialogo):
        """Selecciona una OT de la lista de recientes"""
        texto = item.text()
        # Extraer número de OT del texto "OT 12345 - ..."
        ot = texto.split(" - ")[0].replace("OT ", "").strip()
        self.ot_input.setText(ot)
        dialogo.close()
        self._buscar_ot()
    
    def _exportar_ot(self):
        """Exporta el detalle de OT a Excel"""
        QMessageBox.information(self, "Próximamente", 
            "La exportación a Excel estará disponible próximamente")
    
    def _imprimir_ot(self):
        """Imprime el detalle de OT"""
        QMessageBox.information(self, "Próximamente", 
            "La impresión estará disponible próximamente")
    
    # ========================================
    # TAB 2: CONSUMOS POR OPERARIO
    # ========================================
    
    def _crear_tab_operario(self) -> QWidget:
        """Crea el tab de consumos por operario"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Panel de filtros
        panel_filtros = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        # Selector de operario
        filtros_layout.addWidget(QLabel("Operario:"))
        self.combo_operario = QComboBox()
        self.combo_operario.setMinimumWidth(200)
        filtros_layout.addWidget(self.combo_operario)
        
        # Rango de fechas
        filtros_layout.addWidget(QLabel("Desde:"))
        self.operario_fecha_desde = QDateEdit()
        self.operario_fecha_desde.setCalendarPopup(True)
        self.operario_fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        filtros_layout.addWidget(self.operario_fecha_desde)
        
        filtros_layout.addWidget(QLabel("Hasta:"))
        self.operario_fecha_hasta = QDateEdit()
        self.operario_fecha_hasta.setCalendarPopup(True)
        self.operario_fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.operario_fecha_hasta)
        
        # Botón consultar
        btn_consultar_operario = QPushButton("🔍 Consultar")
        btn_consultar_operario.clicked.connect(self._consultar_operario)
        filtros_layout.addWidget(btn_consultar_operario)
        
        panel_filtros.setLayout(filtros_layout)
        layout.addWidget(panel_filtros)
        
        # Panel de resumen
        self.operario_resumen = QLabel("Seleccione un operario y período")
        self.operario_resumen.setStyleSheet(ESTILO_ALERTA_INFO)
        layout.addWidget(self.operario_resumen)
        
        # Layout horizontal: tabla de detalle + top artículos
        h_layout = QHBoxLayout()
        
        # Tabla de detalle (izquierda)
        v_left = QVBoxLayout()
        v_left.addWidget(QLabel("<b>Detalle de Imputaciones:</b>"))
        self.tabla_operario_detalle = QTableWidget(0, 6)
        self.tabla_operario_detalle.setHorizontalHeaderLabels([
            "Fecha", "OT", "Artículo", "Cantidad", "Coste Unit.", "Coste Total"
        ])
        self.tabla_operario_detalle.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_operario_detalle.setAlternatingRowColors(True)
        v_left.addWidget(self.tabla_operario_detalle)
        h_layout.addLayout(v_left, 2)
        
        # Top artículos (derecha)
        v_right = QVBoxLayout()
        v_right.addWidget(QLabel("<b>Top 10 Artículos Más Usados:</b>"))
        self.tabla_operario_top = QTableWidget(0, 4)
        self.tabla_operario_top.setHorizontalHeaderLabels([
            "Artículo", "Cantidad", "Veces", "Coste"
        ])
        self.tabla_operario_top.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_operario_top.setAlternatingRowColors(True)
        v_right.addWidget(self.tabla_operario_top)
        h_layout.addLayout(v_right, 1)
        
        layout.addLayout(h_layout)
        
        # Botones de acción
        botones = QHBoxLayout()
        btn_exportar_op = QPushButton("📄 Exportar a Excel")
        btn_exportar_op.clicked.connect(lambda: QMessageBox.information(
            self, "Próximamente", "Exportación disponible próximamente"))
        botones.addStretch()
        botones.addWidget(btn_exportar_op)
        layout.addLayout(botones)
        
        # Cargar lista de operarios
        self._cargar_operarios()
        
        return widget
    
    def _cargar_operarios(self):
        """Carga la lista de operarios en el combo"""
        try:
            self.combo_operario.clear()
            self.combo_operario.addItem("Seleccione un operario...", None)
            
            operarios = consumos_service.obtener_operarios_con_consumos()
            for op in operarios:
                self.combo_operario.addItem(op['nombre'], op['id'])
                
        except Exception as e:
            print(f"Error al cargar operarios: {e}")
    
    def _consultar_operario(self):
        """Consulta los consumos de un operario"""
        operario_id = self.combo_operario.currentData()
        
        if not operario_id:
            QMessageBox.warning(self, "Aviso", "Por favor, seleccione un operario")
            return
        
        try:
            fecha_desde = self.operario_fecha_desde.date().toPython()
            fecha_hasta = self.operario_fecha_hasta.date().toPython()
            
            datos = consumos_service.obtener_consumos_operario(operario_id, fecha_desde, fecha_hasta)
            
            if not datos['detalle']:
                QMessageBox.information(self, "Sin resultados",
                    "No se encontraron imputaciones para este operario en el período seleccionado")
                return
            
            # Actualizar resumen
            resumen = datos['resumen']
            texto_resumen = f"""
<b>Operario: {resumen.get('operario_nombre', 'N/A')}</b><br>
<b>Período:</b> {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}<br>
<br>
<b>Total imputaciones:</b> {resumen.get('total_imputaciones', 0)}<br>
<b>OTs trabajadas:</b> {resumen.get('total_ots', 0)}<br>
<b>Coste total material:</b> <span style='font-size:16px; color:#dc2626;'><b>{consumos_service.formatear_coste(resumen.get('coste_total', 0))}</b></span>
            """
            self.operario_resumen.setText(texto_resumen)
            
            # Actualizar tabla de detalle
            self.tabla_operario_detalle.setRowCount(0)
            for row in datos['detalle']:
                r = self.tabla_operario_detalle.rowCount()
                self.tabla_operario_detalle.insertRow(r)
                
                self.tabla_operario_detalle.setItem(r, 0, QTableWidgetItem(row.get('fecha', '')))
                self.tabla_operario_detalle.setItem(r, 1, QTableWidgetItem(row.get('ot', '')))
                self.tabla_operario_detalle.setItem(r, 2, QTableWidgetItem(row.get('articulo', '')))
                self.tabla_operario_detalle.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad', 0), row.get('unidad', ''))
                ))
                self.tabla_operario_detalle.setItem(r, 4, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_unit', 0))
                ))
                self.tabla_operario_detalle.setItem(r, 5, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
            
            # Actualizar top artículos
            self.tabla_operario_top.setRowCount(0)
            for row in datos['top_articulos']:
                r = self.tabla_operario_top.rowCount()
                self.tabla_operario_top.insertRow(r)
                
                self.tabla_operario_top.setItem(r, 0, QTableWidgetItem(row.get('articulo', '')))
                self.tabla_operario_top.setItem(r, 1, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad_total', 0), row.get('unidad', ''))
                ))
                self.tabla_operario_top.setItem(r, 2, QTableWidgetItem(str(row.get('veces_usado', 0))))
                self.tabla_operario_top.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar operario:\n{e}")
    
    # ========================================
    # TAB 3: CONSUMOS POR FURGONETA
    # ========================================
    
    def _crear_tab_furgoneta(self) -> QWidget:
        """Crea el tab de consumos por furgoneta"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Panel de filtros
        panel_filtros = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        filtros_layout.addWidget(QLabel("Furgoneta:"))
        self.combo_furgoneta = QComboBox()
        self.combo_furgoneta.setMinimumWidth(200)
        filtros_layout.addWidget(self.combo_furgoneta)
        
        filtros_layout.addWidget(QLabel("Desde:"))
        self.furgoneta_fecha_desde = QDateEdit()
        self.furgoneta_fecha_desde.setCalendarPopup(True)
        self.furgoneta_fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        filtros_layout.addWidget(self.furgoneta_fecha_desde)
        
        filtros_layout.addWidget(QLabel("Hasta:"))
        self.furgoneta_fecha_hasta = QDateEdit()
        self.furgoneta_fecha_hasta.setCalendarPopup(True)
        self.furgoneta_fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.furgoneta_fecha_hasta)
        
        btn_consultar_furg = QPushButton("🔍 Consultar")
        btn_consultar_furg.clicked.connect(self._consultar_furgoneta)
        filtros_layout.addWidget(btn_consultar_furg)
        
        panel_filtros.setLayout(filtros_layout)
        layout.addWidget(panel_filtros)
        
        # Panel de resumen
        self.furgoneta_resumen = QLabel("Seleccione una furgoneta y período")
        self.furgoneta_resumen.setStyleSheet(ESTILO_ALERTA_INFO)
        layout.addWidget(self.furgoneta_resumen)
        
        # Tabla de detalle
        layout.addWidget(QLabel("<b>Material Imputado desde esta Furgoneta:</b>"))
        self.tabla_furgoneta = QTableWidget(0, 7)
        self.tabla_furgoneta.setHorizontalHeaderLabels([
            "Fecha", "OT", "Artículo", "Cantidad", "Operario", "Coste Total", "Unidad"
        ])
        self.tabla_furgoneta.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_furgoneta.setAlternatingRowColors(True)
        layout.addWidget(self.tabla_furgoneta)
        
        # Botones
        botones = QHBoxLayout()
        btn_exportar = QPushButton("📄 Exportar a Excel")
        btn_exportar.clicked.connect(lambda: QMessageBox.information(
            self, "Próximamente", "Exportación disponible próximamente"))
        botones.addStretch()
        botones.addWidget(btn_exportar)
        layout.addLayout(botones)
        
        # Cargar furgonetas
        self._cargar_furgonetas()
        
        return widget
    
    def _cargar_furgonetas(self):
        """Carga la lista de furgonetas"""
        try:
            self.combo_furgoneta.clear()
            self.combo_furgoneta.addItem("Seleccione una furgoneta...", None)
            
            furgonetas = consumos_service.obtener_lista_furgonetas()
            for f in furgonetas:
                self.combo_furgoneta.addItem(f['nombre'], f['id'])
                
        except Exception as e:
            print(f"Error al cargar furgonetas: {e}")
    
    def _consultar_furgoneta(self):
        """Consulta consumos de una furgoneta"""
        furgoneta_id = self.combo_furgoneta.currentData()
        
        if not furgoneta_id:
            QMessageBox.warning(self, "Aviso", "Por favor, seleccione una furgoneta")
            return
        
        try:
            fecha_desde = self.furgoneta_fecha_desde.date().toPython()
            fecha_hasta = self.furgoneta_fecha_hasta.date().toPython()
            
            datos = consumos_service.obtener_consumos_furgoneta(furgoneta_id, fecha_desde, fecha_hasta)
            
            if not datos['detalle']:
                QMessageBox.information(self, "Sin resultados",
                    "No se encontraron imputaciones desde esta furgoneta en el período")
                return
            
            # Actualizar resumen
            resumen = datos['resumen']
            texto_resumen = f"""
<b>Furgoneta: {resumen.get('furgoneta_nombre', 'N/A')}</b><br>
<b>Período:</b> {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}<br>
<br>
<b>Total imputaciones:</b> {resumen.get('total_imputaciones', 0)}<br>
<b>Coste total consumido:</b> <span style='font-size:16px; color:#dc2626;'><b>{consumos_service.formatear_coste(resumen.get('coste_total', 0))}</b></span>
            """
            self.furgoneta_resumen.setText(texto_resumen)
            
            # Actualizar tabla
            self.tabla_furgoneta.setRowCount(0)
            for row in datos['detalle']:
                r = self.tabla_furgoneta.rowCount()
                self.tabla_furgoneta.insertRow(r)
                
                self.tabla_furgoneta.setItem(r, 0, QTableWidgetItem(row.get('fecha', '')))
                self.tabla_furgoneta.setItem(r, 1, QTableWidgetItem(row.get('ot', '')))
                self.tabla_furgoneta.setItem(r, 2, QTableWidgetItem(row.get('articulo', '')))
                self.tabla_furgoneta.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad', 0), row.get('unidad', ''))
                ))
                self.tabla_furgoneta.setItem(r, 4, QTableWidgetItem(row.get('operario', '')))
                self.tabla_furgoneta.setItem(r, 5, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
                self.tabla_furgoneta.setItem(r, 6, QTableWidgetItem(row.get('unidad', '')))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar furgoneta:\n{e}")
    
    # ========================================
    # TAB 4: CONSUMOS POR PERÍODO
    # ========================================
    
    def _crear_tab_periodo(self) -> QWidget:
        """Crea el tab de análisis por período"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Panel de filtros
        panel_filtros = QGroupBox("Seleccionar Período")
        filtros_layout = QHBoxLayout()
        
        filtros_layout.addWidget(QLabel("Desde:"))
        self.periodo_fecha_desde = QDateEdit()
        self.periodo_fecha_desde.setCalendarPopup(True)
        # Inicio del mes actual
        hoy = QDate.currentDate()
        self.periodo_fecha_desde.setDate(QDate(hoy.year(), hoy.month(), 1))
        filtros_layout.addWidget(self.periodo_fecha_desde)
        
        filtros_layout.addWidget(QLabel("Hasta:"))
        self.periodo_fecha_hasta = QDateEdit()
        self.periodo_fecha_hasta.setCalendarPopup(True)
        self.periodo_fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.periodo_fecha_hasta)
        
        # Botones rápidos
        btn_mes_actual = QPushButton("📅 Mes Actual")
        btn_mes_actual.clicked.connect(self._periodo_mes_actual)
        filtros_layout.addWidget(btn_mes_actual)
        
        btn_mes_anterior = QPushButton("📅 Mes Anterior")
        btn_mes_anterior.clicked.connect(self._periodo_mes_anterior)
        filtros_layout.addWidget(btn_mes_anterior)
        
        btn_consultar_periodo = QPushButton("🔍 Consultar")
        btn_consultar_periodo.clicked.connect(self._consultar_periodo)
        filtros_layout.addWidget(btn_consultar_periodo)
        
        panel_filtros.setLayout(filtros_layout)
        layout.addWidget(panel_filtros)
        
        # Panel de resumen general
        self.periodo_resumen = QLabel("Seleccione un período para ver el análisis")
        self.periodo_resumen.setStyleSheet(ESTILO_ALERTA_INFO)
        layout.addWidget(self.periodo_resumen)
        
        # Layout horizontal: Top artículos + Top operarios
        h_layout = QHBoxLayout()
        
        # Top artículos (izquierda)
        v_left = QVBoxLayout()
        v_left.addWidget(QLabel("<b>Top 10 Artículos Más Consumidos:</b>"))
        self.tabla_periodo_articulos = QTableWidget(0, 4)
        self.tabla_periodo_articulos.setHorizontalHeaderLabels([
            "Artículo", "Cantidad", "Veces", "Coste"
        ])
        self.tabla_periodo_articulos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_periodo_articulos.setAlternatingRowColors(True)
        v_left.addWidget(self.tabla_periodo_articulos)
        h_layout.addLayout(v_left)
        
        # Top operarios (derecha)
        v_right = QVBoxLayout()
        v_right.addWidget(QLabel("<b>Operarios Más Activos:</b>"))
        self.tabla_periodo_operarios = QTableWidget(0, 3)
        self.tabla_periodo_operarios.setHorizontalHeaderLabels([
            "Operario", "Imputaciones", "Coste"
        ])
        self.tabla_periodo_operarios.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_periodo_operarios.setAlternatingRowColors(True)
        v_right.addWidget(self.tabla_periodo_operarios)
        h_layout.addLayout(v_right)
        
        layout.addLayout(h_layout)
        
        # Botones
        botones = QHBoxLayout()
        btn_exportar = QPushButton("📄 Exportar a Excel")
        btn_exportar.clicked.connect(lambda: QMessageBox.information(
            self, "Próximamente", "Exportación disponible próximamente"))
        botones.addStretch()
        botones.addWidget(btn_exportar)
        layout.addLayout(botones)
        
        return widget
    
    def _periodo_mes_actual(self):
        """Establece el período al mes actual"""
        inicio, fin = consumos_service.obtener_periodo_mes_actual()
        self.periodo_fecha_desde.setDate(QDate(inicio.year, inicio.month, inicio.day))
        self.periodo_fecha_hasta.setDate(QDate(fin.year, fin.month, fin.day))
    
    def _periodo_mes_anterior(self):
        """Establece el período al mes anterior"""
        inicio, fin = consumos_service.obtener_periodo_mes_anterior()
        self.periodo_fecha_desde.setDate(QDate(inicio.year, inicio.month, inicio.day))
        self.periodo_fecha_hasta.setDate(QDate(fin.year, fin.month, fin.day))
    
    def _consultar_periodo(self):
        """Consulta el análisis de un período"""
        try:
            fecha_desde = self.periodo_fecha_desde.date().toPython()
            fecha_hasta = self.periodo_fecha_hasta.date().toPython()
            
            datos = consumos_service.obtener_analisis_periodo(fecha_desde, fecha_hasta)
            
            # Actualizar resumen
            resumen = datos['resumen']
            texto_resumen = f"""
<b>RESUMEN DEL PERÍODO: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}</b><br>
<br>
<b>MOVIMIENTOS:</b><br>
• Entradas: {consumos_service.formatear_coste(resumen.get('total_entradas', 0))}<br>
• Imputaciones: {consumos_service.formatear_coste(resumen.get('total_imputaciones', 0))}<br>
• Pérdidas: {consumos_service.formatear_coste(resumen.get('total_perdidas', 0))}<br>
• Devoluciones: {consumos_service.formatear_coste(resumen.get('total_devoluciones', 0))}<br>
<br>
<b>OTs trabajadas:</b> {resumen.get('total_ots', 0)}<br>
<b>Total movimientos:</b> {resumen.get('total_movimientos', 0)}
            """
            self.periodo_resumen.setText(texto_resumen)
            
            # Actualizar top artículos
            self.tabla_periodo_articulos.setRowCount(0)
            for row in datos['articulos_top']:
                r = self.tabla_periodo_articulos.rowCount()
                self.tabla_periodo_articulos.insertRow(r)
                
                self.tabla_periodo_articulos.setItem(r, 0, QTableWidgetItem(row.get('articulo', '')))
                self.tabla_periodo_articulos.setItem(r, 1, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad_total', 0), row.get('unidad', ''))
                ))
                self.tabla_periodo_articulos.setItem(r, 2, QTableWidgetItem(str(row.get('veces_usado', 0))))
                self.tabla_periodo_articulos.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
            
            # Actualizar top operarios
            self.tabla_periodo_operarios.setRowCount(0)
            for row in datos['operarios_top']:
                r = self.tabla_periodo_operarios.rowCount()
                self.tabla_periodo_operarios.insertRow(r)
                
                self.tabla_periodo_operarios.setItem(r, 0, QTableWidgetItem(row.get('operario', '')))
                self.tabla_periodo_operarios.setItem(r, 1, QTableWidgetItem(str(row.get('total_imputaciones', 0))))
                self.tabla_periodo_operarios.setItem(r, 2, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar período:\n{e}")
    
    # ========================================
    # TAB 5: CONSUMOS POR ARTÍCULO
    # ========================================
    
    def _crear_tab_articulo(self) -> QWidget:
        """Crea el tab de consumos por artículo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Panel de búsqueda
        panel_busqueda = QGroupBox("Buscar Artículo")
        busqueda_layout = QHBoxLayout()
        
        busqueda_layout.addWidget(QLabel("Artículo:"))
        self.articulo_buscar = QLineEdit()
        self.articulo_buscar.setPlaceholderText("Buscar por nombre, EAN o referencia...")
        self.articulo_buscar.textChanged.connect(self._buscar_articulos_autocompletar)
        busqueda_layout.addWidget(self.articulo_buscar)
        
        btn_buscar_art = QPushButton("🔍 Buscar")
        btn_buscar_art.clicked.connect(self._mostrar_selector_articulos)
        busqueda_layout.addWidget(btn_buscar_art)
        
        panel_busqueda.setLayout(busqueda_layout)
        layout.addWidget(panel_busqueda)
        
        # Panel de fechas
        panel_filtros = QGroupBox("Período")
        filtros_layout = QHBoxLayout()
        
        filtros_layout.addWidget(QLabel("Desde:"))
        self.articulo_fecha_desde = QDateEdit()
        self.articulo_fecha_desde.setCalendarPopup(True)
        self.articulo_fecha_desde.setDate(QDate.currentDate().addMonths(-3))
        filtros_layout.addWidget(self.articulo_fecha_desde)
        
        filtros_layout.addWidget(QLabel("Hasta:"))
        self.articulo_fecha_hasta = QDateEdit()
        self.articulo_fecha_hasta.setCalendarPopup(True)
        self.articulo_fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.articulo_fecha_hasta)
        
        btn_consultar_art = QPushButton("🔍 Consultar")
        btn_consultar_art.clicked.connect(self._consultar_articulo)
        filtros_layout.addWidget(btn_consultar_art)
        
        panel_filtros.setLayout(filtros_layout)
        layout.addWidget(panel_filtros)
        
        # Panel de resumen
        self.articulo_resumen = QLabel("Busque un artículo para ver su análisis de consumos")
        self.articulo_resumen.setStyleSheet(ESTILO_ALERTA_INFO)
        layout.addWidget(self.articulo_resumen)
        
        # Tabla de histórico
        layout.addWidget(QLabel("<b>Histórico de Consumos:</b>"))
        self.tabla_articulo = QTableWidget(0, 6)
        self.tabla_articulo.setHorizontalHeaderLabels([
            "Fecha", "OT", "Operario", "Cantidad", "Coste Total", "Unidad"
        ])
        self.tabla_articulo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_articulo.setAlternatingRowColors(True)
        layout.addWidget(self.tabla_articulo)
        
        # Botones
        botones = QHBoxLayout()
        btn_exportar = QPushButton("📄 Exportar a Excel")
        btn_exportar.clicked.connect(lambda: QMessageBox.information(
            self, "Próximamente", "Exportación disponible próximamente"))
        botones.addStretch()
        botones.addWidget(btn_exportar)
        layout.addLayout(botones)
        
        # Variable para almacenar el ID del artículo seleccionado
        self.articulo_seleccionado_id = None
        
        return widget
    
    def _buscar_articulos_autocompletar(self):
        """Busca artículos mientras el usuario escribe (autocompletar simple)"""
        # Esta función podría implementar autocompletado en el futuro
        pass
    
    def _mostrar_selector_articulos(self):
        """Muestra un diálogo para seleccionar un artículo"""
        texto_busqueda = self.articulo_buscar.text().strip()
        
        if not texto_busqueda or len(texto_busqueda) < 2:
            QMessageBox.warning(self, "Aviso", "Escriba al menos 2 caracteres para buscar")
            return
        
        try:
            articulos = consumos_service.buscar_articulos(texto_busqueda)
            
            if not articulos:
                QMessageBox.information(self, "Sin resultados", 
                    "No se encontraron artículos que coincidan con la búsqueda")
                return
            
            # Crear diálogo de selección
            from PySide6.QtWidgets import QDialog, QListWidget
            
            dialogo = QDialog(self)
            dialogo.setWindowTitle("Seleccionar Artículo")
            dialogo.resize(600, 400)
            
            layout = QVBoxLayout(dialogo)
            layout.addWidget(QLabel(f"Resultados para: <b>{texto_busqueda}</b>"))
            
            lista = QListWidget()
            for art in articulos:
                texto = f"{art['nombre']}"
                if art.get('ean'):
                    texto += f" (EAN: {art['ean']})"
                if art.get('ref_proveedor'):
                    texto += f" (Ref: {art['ref_proveedor']})"
                
                item = lista.addItem(texto)
                # Guardar el ID en el item
                lista.item(lista.count() - 1).setData(Qt.UserRole, art['id'])
            
            lista.itemDoubleClicked.connect(lambda item: self._seleccionar_articulo(item, dialogo))
            layout.addWidget(lista)
            
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.clicked.connect(dialogo.close)
            layout.addWidget(btn_cerrar)
            
            dialogo.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar artículos:\n{e}")
    
    def _seleccionar_articulo(self, item, dialogo):
        """Selecciona un artículo del diálogo"""
        self.articulo_seleccionado_id = item.data(Qt.UserRole)
        self.articulo_buscar.setText(item.text().split(" (")[0])  # Solo el nombre
        dialogo.close()
        self._consultar_articulo()
    
    def _consultar_articulo(self):
        """Consulta los consumos de un artículo"""
        if not self.articulo_seleccionado_id:
            QMessageBox.warning(self, "Aviso", "Por favor, busque y seleccione un artículo primero")
            return
        
        try:
            fecha_desde = self.articulo_fecha_desde.date().toPython()
            fecha_hasta = self.articulo_fecha_hasta.date().toPython()
            
            datos = consumos_service.obtener_consumos_articulo(
                self.articulo_seleccionado_id, fecha_desde, fecha_hasta
            )
            
            if not datos['detalle']:
                QMessageBox.information(self, "Sin resultados",
                    "No se encontraron consumos de este artículo en el período")
                return
            
            # Actualizar resumen
            resumen = datos['resumen']
            texto_resumen = f"""
<b>Artículo: {resumen.get('articulo_nombre', 'N/A')}</b><br>
<b>Período:</b> {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}<br>
<br>
<b>Total consumido:</b> {consumos_service.formatear_cantidad(resumen.get('cantidad_total', 0), resumen.get('unidad', ''))}<br>
<b>Número de imputaciones:</b> {resumen.get('veces_usado', 0)}<br>
<b>Coste total:</b> <span style='font-size:16px; color:#dc2626;'><b>{consumos_service.formatear_coste(resumen.get('coste_total', 0))}</b></span>
            """
            self.articulo_resumen.setText(texto_resumen)
            
            # Actualizar tabla
            self.tabla_articulo.setRowCount(0)
            for row in datos['detalle']:
                r = self.tabla_articulo.rowCount()
                self.tabla_articulo.insertRow(r)
                
                self.tabla_articulo.setItem(r, 0, QTableWidgetItem(row.get('fecha', '')))
                self.tabla_articulo.setItem(r, 1, QTableWidgetItem(row.get('ot', '')))
                self.tabla_articulo.setItem(r, 2, QTableWidgetItem(row.get('operario', '')))
                self.tabla_articulo.setItem(r, 3, QTableWidgetItem(
                    consumos_service.formatear_cantidad(row.get('cantidad', 0), row.get('unidad', ''))
                ))
                self.tabla_articulo.setItem(r, 4, QTableWidgetItem(
                    consumos_service.formatear_coste(row.get('coste_total', 0))
                ))
                self.tabla_articulo.setItem(r, 5, QTableWidgetItem(row.get('unidad', '')))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar artículo:\n{e}")
