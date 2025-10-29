"""
Ventana de Pedido Ideal - Cálculo inteligente de pedidos por proveedor
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QSpinBox, QComboBox,
    QCheckBox, QMessageBox, QTabWidget, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from typing import List, Dict, Any

from src.services import pedido_ideal_service
from src.repos import pedido_ideal_repo
from src.ui.estilos import ESTILO_VENTANA


class VentanaPedidoIdeal(QWidget):
    """
    Ventana para calcular pedidos ideales agrupados por proveedor.
    
    Características:
    - Cálculo inteligente con stock de seguridad
    - Agrupación por proveedores
    - Unidades de compra
    - Exportación por proveedor
    - Priorización automática
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Pedido Ideal Sugerido")
        self.resize(1200, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Variables de estado
        self.pedidos_calculados = []
        self.grupos_proveedores = {}
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📦 PEDIDO IDEAL SUGERIDO")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(titulo)
        
        # Panel de configuración
        layout.addWidget(self._crear_panel_configuracion())
        
        # Panel de resumen
        self.label_resumen = QLabel("Configure los parámetros y presione 'Calcular Pedido'")
        self.label_resumen.setStyleSheet("""
            background: #f8fafc;
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 13px;
        """)
        layout.addWidget(self.label_resumen)
        
        # Tabs: Vista general y por proveedor
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #f1f5f9;
                border: 1px solid #cbd5e1;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #3b82f6;
                font-weight: bold;
            }
        """)
        
        # Tab 1: Vista general
        self.tab_general = self._crear_tab_general()
        self.tabs.addTab(self.tab_general, "📊 Vista General")
        
        # Tab 2: Por proveedores (se crea dinámicamente)
        self.tab_proveedores = QWidget()
        self.tabs.addTab(self.tab_proveedores, "👥 Por Proveedores")
        
        layout.addWidget(self.tabs)
        
        # Botones inferiores
        layout.addWidget(self._crear_botones_inferiores())
    
    # ========================================
    # PANEL DE CONFIGURACIÓN
    # ========================================
    
    def _crear_panel_configuracion(self) -> QGroupBox:
        """Crea el panel de configuración de parámetros"""
        panel = QGroupBox("⚙️ Configuración del Cálculo")
        layout = QVBoxLayout()
        
        # Primera fila: Parámetros principales
        fila1 = QHBoxLayout()
        
        fila1.addWidget(QLabel("Días de cobertura:"))
        self.spin_dias_cobertura = QSpinBox()
        self.spin_dias_cobertura.setRange(5, 90)
        self.spin_dias_cobertura.setValue(20)
        self.spin_dias_cobertura.setSuffix(" días")
        self.spin_dias_cobertura.setToolTip("Días de stock que deseas mantener (ej: 20 días = 1 mes)")
        fila1.addWidget(self.spin_dias_cobertura)
        
        fila1.addWidget(QLabel("Stock de seguridad:"))
        self.spin_dias_seguridad = QSpinBox()
        self.spin_dias_seguridad.setRange(0, 30)
        self.spin_dias_seguridad.setValue(5)
        self.spin_dias_seguridad.setSuffix(" días")
        self.spin_dias_seguridad.setToolTip("Días extra de colchón por si hay picos de demanda")
        fila1.addWidget(self.spin_dias_seguridad)
        
        fila1.addWidget(QLabel("Analizar últimos:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItem("30 días", 30)
        self.combo_periodo.addItem("60 días", 60)
        self.combo_periodo.addItem("90 días", 90)
        self.combo_periodo.addItem("180 días", 180)
        self.combo_periodo.setCurrentIndex(2)  # 90 días por defecto
        self.combo_periodo.setToolTip("Período histórico para calcular consumo medio")
        fila1.addWidget(self.combo_periodo)
        
        fila1.addStretch()
        layout.addLayout(fila1)
        
        # Segunda fila: Filtros
        fila2 = QHBoxLayout()
        fila2.addWidget(QLabel("Filtros:"))
        
        self.check_bajo_alerta = QCheckBox("Solo bajo nivel de alerta")
        self.check_bajo_alerta.setChecked(True)
        fila2.addWidget(self.check_bajo_alerta)
        
        self.check_criticos = QCheckBox("Solo artículos críticos")
        fila2.addWidget(self.check_criticos)
        
        self.check_con_proveedor = QCheckBox("Solo con proveedor asignado")
        fila2.addWidget(self.check_con_proveedor)
        
        self.check_excluir_sin_consumo = QCheckBox("Excluir sin consumo")
        self.check_excluir_sin_consumo.setChecked(True)
        fila2.addWidget(self.check_excluir_sin_consumo)
        
        fila2.addStretch()
        layout.addLayout(fila2)
        
        # Botón calcular
        fila3 = QHBoxLayout()
        fila3.addStretch()
        
        btn_calcular = QPushButton("🔍 CALCULAR PEDIDO")
        btn_calcular.setMinimumHeight(40)
        btn_calcular.setMinimumWidth(200)
        btn_calcular.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        btn_calcular.clicked.connect(self._calcular_pedido)
        fila3.addWidget(btn_calcular)
        
        fila3.addStretch()
        layout.addLayout(fila3)
        
        panel.setLayout(layout)
        return panel
    
    # ========================================
    # TAB: VISTA GENERAL
    # ========================================
    
    def _crear_tab_general(self) -> QWidget:
        """Crea el tab con la vista general de todos los artículos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info superior
        info = QLabel("Vista consolidada de todos los artículos que necesitan reposición")
        info.setStyleSheet("color: #64748b; font-size: 12px; padding: 5px;")
        layout.addWidget(info)
        
        # Tabla general
        self.tabla_general = QTableWidget(0, 10)
        self.tabla_general.setHorizontalHeaderLabels([
            "Artículo", "Proveedor", "Stock", "Alerta", "Cons/día", 
            "Días Rest.", "Pedido", "Unid.", "Coste", "Prioridad"
        ])
        self.tabla_general.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_general.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_general.setAlternatingRowColors(True)
        self.tabla_general.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla_general)
        
        return widget
    
    # ========================================
    # BOTONES INFERIORES
    # ========================================
    
    def _crear_botones_inferiores(self) -> QWidget:
        """Crea la barra de botones inferior"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Información de ayuda
        btn_ayuda = QPushButton("❓ Ayuda")
        btn_ayuda.clicked.connect(self._mostrar_ayuda)
        layout.addWidget(btn_ayuda)
        
        layout.addStretch()
        
        # Exportar todo
        btn_exportar_todo = QPushButton("📄 Exportar Todo (Excel)")
        btn_exportar_todo.clicked.connect(self._exportar_todo)
        layout.addWidget(btn_exportar_todo)
        
        # Generar PDFs por proveedor
        btn_pdfs = QPushButton("📑 Generar PDFs por Proveedor")
        btn_pdfs.clicked.connect(self._generar_pdfs_proveedores)
        layout.addWidget(btn_pdfs)
        
        # Volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        return widget
    
    # ========================================
    # LÓGICA DE CÁLCULO
    # ========================================
    
    def _calcular_pedido(self):
        """Calcula el pedido ideal basado en los parámetros configurados"""
        try:
            # Obtener parámetros
            dias_cobertura = self.spin_dias_cobertura.value()
            dias_seguridad = self.spin_dias_seguridad.value()
            periodo_analisis = self.combo_periodo.currentData()
            
            # Obtener filtros
            filtros = {
                'solo_criticos': self.check_criticos.isChecked(),
                'solo_bajo_alerta': self.check_bajo_alerta.isChecked(),
                'excluir_sin_consumo': self.check_excluir_sin_consumo.isChecked(),
                'solo_con_proveedor': self.check_con_proveedor.isChecked()
            }
            
            # Mostrar progreso
            self.label_resumen.setText("⏳ Calculando pedido ideal... Analizando consumos históricos...")
            self.label_resumen.repaint()
            
            # Obtener artículos
            incluir_sin_alerta = not filtros['solo_bajo_alerta']
            articulos = pedido_ideal_repo.get_articulos_para_analizar(incluir_sin_alerta)
            
            if not articulos:
                QMessageBox.information(self, "Sin datos",
                    "No se encontraron artículos para analizar con los filtros seleccionados")
                self.label_resumen.setText("Sin artículos para analizar")
                return
            
            self.label_resumen.setText(f"⏳ Analizando {len(articulos)} artículos...")
            self.label_resumen.repaint()
            
            # Calcular pedidos
            self.pedidos_calculados = pedido_ideal_service.calcular_pedidos_multiples(
                articulos,
                dias_cobertura,
                dias_seguridad,
                periodo_analisis,
                filtros
            )
            
            # Agrupar por proveedor
            self.grupos_proveedores = pedido_ideal_service.agrupar_por_proveedor(
                self.pedidos_calculados
            )
            
            # Actualizar interfaz
            self._actualizar_resumen()
            self._actualizar_tabla_general()
            self._crear_tabs_proveedores()
            
            QMessageBox.information(self, "✅ Cálculo completado",
                f"Se ha calculado el pedido ideal para {len(self.pedidos_calculados)} artículos")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al calcular pedido:\n{e}")
            print(f"Error detallado: {e}")
            import traceback
            traceback.print_exc()
    
    def _actualizar_resumen(self):
        """Actualiza el panel de resumen con estadísticas"""
        resumen = pedido_ideal_service.calcular_resumen(self.pedidos_calculados)
        
        texto = f"""
<b>📊 RESUMEN DEL PEDIDO:</b><br>
<br>
<b>Total de artículos analizados:</b> {resumen['total_articulos']}<br>
<b>Artículos que necesitan pedido:</b> {resumen['articulos_con_pedido']}<br>
<br>
<b>Por prioridad:</b><br>
• 🔴 Críticos: {resumen['articulos_criticos']}<br>
• 🟡 Preventivos: {resumen['articulos_preventivos']}<br>
• 🟢 Normales: {resumen['articulos_normales']}<br>
<br>
<b>Coste total estimado:</b> <span style='font-size:16px; color:#dc2626;'><b>{pedido_ideal_service.formatear_coste(resumen['coste_total'])}</b></span><br>
<b>  - Críticos:</b> {pedido_ideal_service.formatear_coste(resumen['coste_criticos'])}<br>
<b>  - Preventivos:</b> {pedido_ideal_service.formatear_coste(resumen['coste_preventivos'])}<br>
<br>
<b>Proveedores involucrados:</b> {len(self.grupos_proveedores)}<br>
<b>⚠️ Artículos sin proveedor:</b> {resumen['articulos_sin_proveedor']}
        """
        self.label_resumen.setText(texto)
    
    def _actualizar_tabla_general(self):
        """Actualiza la tabla general con todos los artículos"""
        self.tabla_general.setRowCount(0)
        
        for pedido in self.pedidos_calculados:
            if not pedido.get('requiere_pedido') or pedido['pedido_sugerido'] <= 0:
                continue
            
            r = self.tabla_general.rowCount()
            self.tabla_general.insertRow(r)
            
            # Artículo
            item_nombre = QTableWidgetItem(f"{pedido['emoji']} {pedido['articulo_nombre']}")
            item_nombre.setData(Qt.UserRole, pedido)  # Guardar datos completos
            self.tabla_general.setItem(r, 0, item_nombre)
            
            # Proveedor
            self.tabla_general.setItem(r, 1, QTableWidgetItem(pedido['proveedor_nombre']))
            
            # Stock
            item_stock = QTableWidgetItem(str(int(pedido['stock_actual'])))
            item_stock.setTextAlignment(Qt.AlignCenter)
            if pedido['stock_actual'] < pedido['nivel_alerta']:
                item_stock.setBackground(QColor(254, 226, 226))  # Rojo claro
            self.tabla_general.setItem(r, 2, item_stock)
            
            # Alerta
            item_alerta = QTableWidgetItem(str(int(pedido['nivel_alerta'])))
            item_alerta.setTextAlignment(Qt.AlignCenter)
            self.tabla_general.setItem(r, 3, item_alerta)
            
            # Consumo diario
            item_cons = QTableWidgetItem(f"{pedido['consumo_diario']:.2f}")
            item_cons.setTextAlignment(Qt.AlignCenter)
            self.tabla_general.setItem(r, 4, item_cons)
            
            # Días restantes
            dias_rest = pedido['dias_restantes']
            dias_texto = f"{dias_rest:.1f}" if dias_rest < 999 else "∞"
            item_dias = QTableWidgetItem(dias_texto)
            item_dias.setTextAlignment(Qt.AlignCenter)
            if dias_rest < 7:
                item_dias.setBackground(QColor(254, 226, 226))  # Rojo
            elif dias_rest < 14:
                item_dias.setBackground(QColor(254, 243, 199))  # Amarillo
            self.tabla_general.setItem(r, 5, item_dias)
            
            # Pedido sugerido
            item_pedido = QTableWidgetItem(
                pedido_ideal_service.formatear_cantidad(
                    pedido['pedido_sugerido'], 
                    pedido['u_medida']
                )
            )
            item_pedido.setTextAlignment(Qt.AlignCenter)
            font_bold = QFont()
            font_bold.setBold(True)
            item_pedido.setFont(font_bold)
            self.tabla_general.setItem(r, 6, item_pedido)
            
            # Unidad de compra
            uc = pedido['unidad_compra']
            uc_texto = f"x{int(uc)}" if uc > 1 else "-"
            item_uc = QTableWidgetItem(uc_texto)
            item_uc.setTextAlignment(Qt.AlignCenter)
            self.tabla_general.setItem(r, 7, item_uc)
            
            # Coste
            self.tabla_general.setItem(r, 8, QTableWidgetItem(
                pedido_ideal_service.formatear_coste(pedido['coste_estimado'])
            ))
            
            # Prioridad
            item_prioridad = QTableWidgetItem(pedido['prioridad'])
            item_prioridad.setTextAlignment(Qt.AlignCenter)
            if 'CRÍTICO' in pedido['prioridad']:
                item_prioridad.setBackground(QColor(254, 226, 226))
            elif pedido['prioridad'] == 'PREVENTIVO':
                item_prioridad.setBackground(QColor(254, 243, 199))
            self.tabla_general.setItem(r, 9, item_prioridad)
    
    # ========================================
    # TABS POR PROVEEDOR
    # ========================================
    
    def _crear_tabs_proveedores(self):
        """Crea tabs dinámicos para cada proveedor"""
        # Limpiar tabs anteriores (excepto los dos primeros fijos)
        while self.tabs.count() > 2:
            self.tabs.removeTab(2)
        
        # Actualizar tab "Por Proveedores" con lista de proveedores
        self._actualizar_tab_lista_proveedores()
        
        # Crear un tab por cada proveedor
        for proveedor_id, info in self.grupos_proveedores.items():
            if info['total_articulos'] == 0:
                continue
            
            tab = self._crear_tab_proveedor(info)
            nombre_tab = f"📦 {info['proveedor_nombre'][:20]}"
            if info['total_articulos'] > 0:
                nombre_tab += f" ({info['total_articulos']})"
            
            self.tabs.addTab(tab, nombre_tab)
    
    def _actualizar_tab_lista_proveedores(self):
        """Actualiza el tab con la lista resumida de proveedores"""
        # Limpiar contenido anterior
        if self.tab_proveedores.layout():
            QWidget().setLayout(self.tab_proveedores.layout())
        
        layout = QVBoxLayout(self.tab_proveedores)
        
        # Info
        info = QLabel("Resumen por proveedor - Haz clic en un tab específico para ver el detalle")
        info.setStyleSheet("color: #64748b; font-size: 12px; padding: 5px;")
        layout.addWidget(info)
        
        # Tabla resumen de proveedores
        tabla = QTableWidget(0, 5)
        tabla.setHorizontalHeaderLabels([
            "Proveedor", "Artículos", "Coste Total", "Email", "Teléfono"
        ])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.setAlternatingRowColors(True)
        
        for proveedor_id, info in self.grupos_proveedores.items():
            if info['total_articulos'] == 0:
                continue
            
            r = tabla.rowCount()
            tabla.insertRow(r)
            
            # Nombre
            nombre = info['proveedor_nombre']
            if 'SIN PROVEEDOR' in nombre:
                nombre = "⚠️ " + nombre
            tabla.setItem(r, 0, QTableWidgetItem(nombre))
            
            # Artículos
            item_art = QTableWidgetItem(str(info['total_articulos']))
            item_art.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(r, 1, item_art)
            
            # Coste
            tabla.setItem(r, 2, QTableWidgetItem(
                pedido_ideal_service.formatear_coste(info['coste_total'])
            ))
            
            # Email
            tabla.setItem(r, 3, QTableWidgetItem(info.get('proveedor_email') or '-'))
            
            # Teléfono
            tabla.setItem(r, 4, QTableWidgetItem(info.get('proveedor_telefono') or '-'))
        
        layout.addWidget(tabla)
        
        # Botones
        botones = QHBoxLayout()
        botones.addStretch()
        
        btn_exportar_resumen = QPushButton("📄 Exportar Resumen")
        btn_exportar_resumen.clicked.connect(self._exportar_resumen_proveedores)
        botones.addWidget(btn_exportar_resumen)
        
        layout.addLayout(botones)
    
    def _crear_tab_proveedor(self, proveedor_info: Dict[str, Any]) -> QWidget:
        """Crea un tab con el detalle de pedido de un proveedor específico"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cabecera del proveedor
        header = QGroupBox(f"📦 {proveedor_info['proveedor_nombre']}")
        header_layout = QVBoxLayout()
        
        info_proveedor = f"""
<b>Total artículos:</b> {proveedor_info['total_articulos']}<br>
<b>Coste total:</b> <span style='font-size:14px; color:#dc2626;'><b>{pedido_ideal_service.formatear_coste(proveedor_info['coste_total'])}</b></span>
        """
        
        if proveedor_info.get('proveedor_email'):
            info_proveedor += f"<br><b>Email:</b> {proveedor_info['proveedor_email']}"
        if proveedor_info.get('proveedor_telefono'):
            info_proveedor += f"<br><b>Teléfono:</b> {proveedor_info['proveedor_telefono']}"
        
        label_info = QLabel(info_proveedor)
        header_layout.addWidget(label_info)
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        # Tabla de artículos del proveedor
        tabla = QTableWidget(0, 9)
        tabla.setHorizontalHeaderLabels([
            "Artículo", "Ref. Prov.", "Stock", "Alerta", "Cons/día",
            "Pedido", "Unid.Compra", "Coste Unit.", "Coste Total"
        ])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.setAlternatingRowColors(True)
        
        for articulo in proveedor_info['articulos']:
            r = tabla.rowCount()
            tabla.insertRow(r)
            
            tabla.setItem(r, 0, QTableWidgetItem(f"{articulo['emoji']} {articulo['articulo_nombre']}"))
            tabla.setItem(r, 1, QTableWidgetItem(articulo.get('ref_proveedor', '-')))
            tabla.setItem(r, 2, QTableWidgetItem(str(int(articulo['stock_actual']))))
            tabla.setItem(r, 3, QTableWidgetItem(str(int(articulo['nivel_alerta']))))
            tabla.setItem(r, 4, QTableWidgetItem(f"{articulo['consumo_diario']:.2f}"))
            
            # Pedido en negrita
            item_pedido = QTableWidgetItem(
                pedido_ideal_service.formatear_cantidad(
                    articulo['pedido_sugerido'],
                    articulo['u_medida']
                )
            )
            font_bold = QFont()
            font_bold.setBold(True)
            item_pedido.setFont(font_bold)
            tabla.setItem(r, 5, item_pedido)
            
            uc = articulo['unidad_compra']
            tabla.setItem(r, 6, QTableWidgetItem(f"x{int(uc)}" if uc > 1 else "-"))
            tabla.setItem(r, 7, QTableWidgetItem(
                pedido_ideal_service.formatear_coste(articulo['coste_unitario'])
            ))
            tabla.setItem(r, 8, QTableWidgetItem(
                pedido_ideal_service.formatear_coste(articulo['coste_estimado'])
            ))
        
        layout.addWidget(tabla)
        
        # Botones específicos del proveedor
        botones = QHBoxLayout()
        botones.addStretch()
        
        btn_excel = QPushButton(f"📄 Exportar Excel - {proveedor_info['proveedor_nombre'][:30]}")
        btn_excel.clicked.connect(lambda: self._exportar_proveedor_excel(proveedor_info))
        botones.addWidget(btn_excel)
        
        btn_pdf = QPushButton("📑 Generar PDF")
        btn_pdf.clicked.connect(lambda: self._exportar_proveedor_pdf(proveedor_info))
        botones.addWidget(btn_pdf)
        
        if proveedor_info.get('proveedor_email'):
            btn_email = QPushButton("✉️ Enviar por Email")
            btn_email.clicked.connect(lambda: self._enviar_email_proveedor(proveedor_info))
            botones.addWidget(btn_email)
        
        layout.addLayout(botones)
        
        return widget
    
    # ========================================
    # EXPORTACIÓN Y ACCIONES
    # ========================================
    
    def _exportar_todo(self):
        """Exporta todo el pedido a Excel"""
        QMessageBox.information(self, "Próximamente",
            "La exportación completa a Excel estará disponible próximamente")
    
    def _exportar_proveedor_excel(self, proveedor_info: Dict[str, Any]):
        """Exporta el pedido de un proveedor a Excel"""
        QMessageBox.information(self, "Próximamente",
            f"Se exportará el pedido de {proveedor_info['proveedor_nombre']} a Excel")
    
    def _exportar_proveedor_pdf(self, proveedor_info: Dict[str, Any]):
        """Genera PDF del pedido de un proveedor"""
        QMessageBox.information(self, "Próximamente",
            f"Se generará PDF del pedido de {proveedor_info['proveedor_nombre']}")
    
    def _generar_pdfs_proveedores(self):
        """Genera PDFs para todos los proveedores"""
        QMessageBox.information(self, "Próximamente",
            "Se generarán PDFs individuales para cada proveedor")
    
    def _exportar_resumen_proveedores(self):
        """Exporta el resumen de proveedores"""
        QMessageBox.information(self, "Próximamente",
            "Se exportará el resumen de proveedores a Excel")
    
    def _enviar_email_proveedor(self, proveedor_info: Dict[str, Any]):
        """Envía el pedido por email al proveedor"""
        QMessageBox.information(self, "Próximamente",
            f"Se enviará el pedido por email a {proveedor_info.get('proveedor_email')}")
    
    def _mostrar_ayuda(self):
        """Muestra ventana de ayuda"""
        ayuda_texto = """
<h3>📦 Ayuda - Pedido Ideal</h3>

<h4>¿Qué hace este módulo?</h4>
<p>Calcula automáticamente qué artículos necesitas reponer y en qué cantidad,
basándose en tu consumo histórico real.</p>

<h4>Parámetros:</h4>
<ul>
<li><b>Días de cobertura:</b> Cuántos días de stock quieres tener (ej: 20 = 1 mes)</li>
<li><b>Stock de seguridad:</b> Días extra de colchón por si hay picos (ej: 5 días)</li>
<li><b>Período de análisis:</b> Cuántos días hacia atrás analizar para calcular el consumo medio</li>
</ul>

<h4>Fórmula:</h4>
<p><b>Pedido = (Consumo_Diario × Días_Cobertura) + (Consumo_Diario × Días_Seguridad) - Stock_Actual</b></p>

<h4>Prioridades:</h4>
<ul>
<li>🔴 <b>CRÍTICO:</b> Stock actual por debajo del nivel de alerta</li>
<li>🟡 <b>PREVENTIVO:</b> Stock cerca del nivel de alerta</li>
<li>🟢 <b>NORMAL:</b> Stock suficiente pero conviene reponer</li>
</ul>

<h4>Unidades de Compra:</h4>
<p>Si un artículo se compra en lotes (ej: bobinas de 100m), el pedido se redondea
automáticamente al múltiplo más cercano.</p>

<h4>Agrupación por Proveedores:</h4>
<p>Los artículos se agrupan automáticamente por proveedor para que puedas
generar un pedido separado para cada uno.</p>
        """
        
        dialogo = QMessageBox(self)
        dialogo.setWindowTitle("Ayuda - Pedido Ideal")
        dialogo.setTextFormat(Qt.RichText)
        dialogo.setText(ayuda_texto)
        dialogo.setIcon(QMessageBox.Information)
        dialogo.exec()

