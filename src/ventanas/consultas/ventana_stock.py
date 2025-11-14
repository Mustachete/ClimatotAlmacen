# ventana_stock.py - Consulta de Stock
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from pathlib import Path
import sqlite3
from src.ui.estilos import ESTILO_VENTANA
from src.core.db_utils import get_con

# ========================================
# VENTANA DE CONSULTA DE STOCK
# ========================================
class VentanaStock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Consulta de Stock")
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("📊 Consulta de Stock de Almacén")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Visualiza el stock actual de todos los artículos por almacén y furgoneta")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ========== PANEL DE ALERTAS ==========
        self.panel_alertas = QLabel("")
        self.panel_alertas.setStyleSheet(
            "background-color: #fef2f2; border: 2px solid #dc2626; "
            "border-radius: 5px; padding: 10px; color: #dc2626; font-weight: bold;"
        )
        self.panel_alertas.setAlignment(Qt.AlignCenter)
        self.panel_alertas.setVisible(False)  # Oculto por defecto
        layout.addWidget(self.panel_alertas)

        # ========== FILTROS ==========
        filtros_layout = QHBoxLayout()
        
        # Búsqueda
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, EAN o referencia...")
        self.txt_buscar.textChanged.connect(self.aplicar_filtros)
        
        # Familia
        lbl_familia = QLabel("Familia:")
        self.cmb_familia = QComboBox()
        self.cmb_familia.setMinimumWidth(150)
        self.cargar_familias()
        self.cmb_familia.currentTextChanged.connect(self.aplicar_filtros)
        
        # Almacén
        lbl_almacen = QLabel("Almacén:")
        self.cmb_almacen = QComboBox()
        self.cmb_almacen.setMinimumWidth(120)
        self.cargar_almacenes()
        self.cmb_almacen.currentTextChanged.connect(self.aplicar_filtros)
        
        # Checkbox solo con stock
        self.chk_con_stock = QCheckBox("Solo con stock")
        self.chk_con_stock.setChecked(True)
        self.chk_con_stock.stateChanged.connect(self.aplicar_filtros)
        
        # Checkbox alertas
        self.chk_alertas = QCheckBox("Solo alertas (< mínimo)")
        self.chk_alertas.stateChanged.connect(self.aplicar_filtros)
        
        filtros_layout.addWidget(lbl_buscar)
        filtros_layout.addWidget(self.txt_buscar, 2)
        filtros_layout.addWidget(lbl_familia)
        filtros_layout.addWidget(self.cmb_familia, 1)
        filtros_layout.addWidget(lbl_almacen)
        filtros_layout.addWidget(self.cmb_almacen, 1)
        filtros_layout.addWidget(self.chk_con_stock)
        filtros_layout.addWidget(self.chk_alertas)
        
        layout.addLayout(filtros_layout)
        
        # ========== BOTONES ==========
        botones_layout = QHBoxLayout()
        
        self.btn_exportar = QPushButton("📊 Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_excel)
        
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.aplicar_filtros)
        
        botones_layout.addWidget(self.btn_exportar)
        botones_layout.addWidget(self.btn_actualizar)
        botones_layout.addStretch()
        
        layout.addLayout(botones_layout)
        
        # ========== TABLA ==========
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Artículo", "EAN", "Familia", "Almacén", "Stock", "Mín", "Estado"
        ])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Artículo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # EAN
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Familia
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Almacén
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Stock
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Mín
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Estado
        
        layout.addWidget(self.tabla)
        
        # ========== RESUMEN ==========
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.lbl_resumen)
        
        # ========== BOTÓN VOLVER ==========
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.aplicar_filtros()
    
    def cargar_familias(self):
        """Carga las familias en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT nombre FROM familias ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_familia.addItem("Todas", None)
            for row in rows:
                self.cmb_familia.addItem(row[0], row[0])
        except Exception:
            pass
    
    def cargar_almacenes(self):
        """Carga los almacenes en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT nombre FROM almacenes ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_almacen.addItem("Todos", None)
            for row in rows:
                self.cmb_almacen.addItem(row[0], row[0])
        except Exception:
            pass
    
    def aplicar_filtros(self):
        """Aplica los filtros y carga los datos"""
        texto_buscar = self.txt_buscar.text().strip()
        familia = self.cmb_familia.currentData()
        almacen = self.cmb_almacen.currentData()
        solo_con_stock = self.chk_con_stock.isChecked()
        solo_alertas = self.chk_alertas.isChecked()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            query = """
                SELECT 
                    a.id,
                    a.nombre,
                    a.ean,
                    f.nombre as familia,
                    alm.nombre as almacen,
                    COALESCE(SUM(v.delta), 0) as stock,
                    a.min_alerta,
                    a.u_medida
                FROM articulos a
                LEFT JOIN familias f ON a.familia_id = f.id
                LEFT JOIN vw_stock v ON a.id = v.articulo_id
                LEFT JOIN almacenes alm ON v.almacen_id = alm.id
                WHERE a.activo = 1
            """
            
            params = []
            
            # Filtro de búsqueda
            if texto_buscar:
                query += " AND (a.nombre LIKE ? OR a.ean LIKE ? OR a.ref_proveedor LIKE ?)"
                params.extend([f"%{texto_buscar}%"] * 3)
            
            # Filtro de familia
            if familia:
                query += " AND f.nombre = ?"
                params.append(familia)
            
            # Filtro de almacén
            if almacen:
                query += " AND alm.nombre = ?"
                params.append(almacen)
            
            query += " GROUP BY a.id, a.nombre, a.ean, f.nombre, alm.nombre, a.min_alerta, a.u_medida"
            
            # Filtro de solo con stock
            if solo_con_stock:
                query += " HAVING stock > 0"
            
            # Filtro de solo alertas
            if solo_alertas:
                if solo_con_stock:
                    query += " AND stock < a.min_alerta"
                else:
                    query += " HAVING stock < a.min_alerta"
            
            query += " ORDER BY a.nombre, alm.nombre"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            total_articulos = 0
            alertas = 0
            
            for i, row in enumerate(rows):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
                # Artículo
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1]))
                # EAN
                self.tabla.setItem(i, 2, QTableWidgetItem(row[2] or "-"))
                # Familia
                self.tabla.setItem(i, 3, QTableWidgetItem(row[3] or "-"))
                # Almacén
                self.tabla.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                # Stock
                stock = row[5]
                u_medida = row[7] or "unidad"
                item_stock = QTableWidgetItem(f"{stock:.2f} {u_medida}")
                item_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(i, 5, item_stock)
                # Mínimo
                min_alerta = row[6]
                item_min = QTableWidgetItem(f"{min_alerta:.2f}")
                item_min.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(i, 6, item_min)
                # Estado
                if stock < min_alerta:
                    estado = "⚠️ BAJO"
                    color = QColor("#fee2e2")
                    alertas += 1
                elif stock == 0:
                    estado = "❌ VACÍO"
                    color = QColor("#fecaca")
                else:
                    estado = "✅ OK"
                    color = QColor("#d1fae5")
                
                item_estado = QTableWidgetItem(estado)
                item_estado.setBackground(color)
                item_estado.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(i, 7, item_estado)
                
                total_articulos += 1
            
            # Actualizar resumen
            self.lbl_resumen.setText(
                f"📦 Total registros: {total_articulos} | "
                f"⚠️ Alertas (stock bajo): {alertas}"
            )

            # Mostrar panel de alertas si hay artículos críticos
            if alertas > 0 and not solo_alertas:
                self.panel_alertas.setText(
                    f"⚠️ ATENCIÓN: {alertas} artículo(s) con stock bajo el mínimo. "
                    f"Marca 'Solo alertas' para ver solo estos artículos."
                )
                self.panel_alertas.setVisible(True)
            else:
                self.panel_alertas.setVisible(False)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar stock:\n{e}")
    
    def exportar_excel(self):
        """Exporta el stock actual a Excel"""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Obtener datos de la tabla
            datos = []
            for row in range(self.tabla.rowCount()):
                fila = []
                for col in range(1, self.tabla.columnCount()):  # Omitir ID
                    item = self.tabla.item(row, col)
                    fila.append(item.text() if item else "")
                datos.append(fila)
            
            if not datos:
                QMessageBox.warning(self, "⚠️ Aviso", "No hay datos para exportar.")
                return
            
            # Crear DataFrame
            columnas = ["Artículo", "EAN", "Familia", "Almacén", "Stock", "Mínimo", "Estado"]
            df = pd.DataFrame(datos, columns=columnas)
            
            # Crear carpeta exports si no existe
            export_dir = BASE / "exports"
            export_dir.mkdir(exist_ok=True)
            
            # Nombre del archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"stock_{timestamp}.xlsx"
            
            # Exportar
            df.to_excel(filename, index=False, sheet_name="Stock")
            
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Stock exportado correctamente:\n\n{filename}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self,
                "⚠️ Aviso",
                "No se puede exportar a Excel.\n\n"
                "Instala las librerías necesarias:\n"
                "pip install pandas openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al exportar:\n{e}")