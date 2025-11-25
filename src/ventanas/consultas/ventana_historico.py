# ventana_historico.py - Histórico de Movimientos
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QLineEdit,
    QLabel, QMessageBox, QComboBox, QDateEdit, QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from pathlib import Path
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_base import (
    TituloVentana, PanelFiltros, TablaEstandar, BotonPrimario, BotonSecundario
)
from src.ui.combo_loaders import ComboLoader
from src.services import almacenes_service, movimientos_service

class VentanaHistorico(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Histórico de Movimientos")
        self.resize(1300, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)

        # Título
        titulo = TituloVentana("📋 Histórico Completo de Movimientos")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # ========== FILTROS ==========
        grupo_filtros = PanelFiltros("🔍 Filtros de Búsqueda")
        filtros_layout = QVBoxLayout()
        
        # Fila 1: Fechas
        fila1 = QHBoxLayout()
        
        self.chk_fecha = QCheckBox("Rango de fechas:")
        self.chk_fecha.stateChanged.connect(self.toggle_fechas)
        
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setEnabled(False)
        
        lbl_hasta = QLabel("hasta")
        
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setEnabled(False)
        
        fila1.addWidget(self.chk_fecha)
        fila1.addWidget(self.date_desde)
        fila1.addWidget(lbl_hasta)
        fila1.addWidget(self.date_hasta)
        fila1.addStretch()
        
        filtros_layout.addLayout(fila1)
        
        # Fila 2: Tipo, Almacén, Artículo
        fila2 = QHBoxLayout()
        
        lbl_tipo = QLabel("Tipo:")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Todos", "ENTRADA", "TRASPASO", "IMPUTACION", "PERDIDA", "DEVOLUCION"])
        self.cmb_tipo.setMinimumWidth(120)
        
        lbl_almacen = QLabel("Almacén/Furgoneta:")
        self.cmb_almacen = QComboBox()
        self.cmb_almacen.setMinimumWidth(120)
        self.cargar_almacenes()
        
        lbl_articulo = QLabel("Buscar artículo:")
        self.txt_articulo = QLineEdit()
        self.txt_articulo.setPlaceholderText("Nombre, EAN o referencia...")
        self.txt_articulo.setMinimumWidth(200)
        
        fila2.addWidget(lbl_tipo)
        fila2.addWidget(self.cmb_tipo)
        fila2.addWidget(lbl_almacen)
        fila2.addWidget(self.cmb_almacen)
        fila2.addWidget(lbl_articulo)
        fila2.addWidget(self.txt_articulo, 2)
        
        filtros_layout.addLayout(fila2)
        
        # Fila 3: OT, Operario
        fila3 = QHBoxLayout()
        
        lbl_ot = QLabel("OT:")
        self.txt_ot = QLineEdit()
        self.txt_ot.setPlaceholderText("Nº Orden de Trabajo...")
        self.txt_ot.setMinimumWidth(150)
        
        lbl_responsable = QLabel("Responsable:")
        self.txt_responsable = QLineEdit()
        self.txt_responsable.setPlaceholderText("Operario o responsable...")
        self.txt_responsable.setMinimumWidth(150)
        
        self.btn_buscar = BotonPrimario("🔍 BUSCAR")
        self.btn_buscar.clicked.connect(self.buscar)

        self.btn_limpiar = BotonSecundario("🗑️ Limpiar Filtros")
        self.btn_limpiar.clicked.connect(self.limpiar_filtros)
        
        fila3.addWidget(lbl_ot)
        fila3.addWidget(self.txt_ot)
        fila3.addWidget(lbl_responsable)
        fila3.addWidget(self.txt_responsable)
        fila3.addStretch()
        fila3.addWidget(self.btn_buscar)
        fila3.addWidget(self.btn_limpiar)
        
        filtros_layout.addLayout(fila3)
        
        grupo_filtros.setLayout(filtros_layout)
        layout.addWidget(grupo_filtros)
        
        # ========== TABLA ==========
        self.tabla = TablaEstandar(0, 11)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Fecha", "Tipo", "Origen", "Destino", "Artículo",
            "Cantidad", "Coste", "OT", "Responsable", "Motivo"
        ])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setEditTriggers(TablaEstandar.NoEditTriggers)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Origen
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Destino
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # Artículo
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Coste
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # OT
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Responsable
        header.setSectionResizeMode(10, QHeaderView.Stretch)          # Motivo
        
        layout.addWidget(self.tabla)
        
        # ========== RESUMEN Y BOTONES ==========
        footer_layout = QHBoxLayout()
        
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-weight: bold; margin: 5px;")

        self.btn_exportar = BotonPrimario("📊 Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_excel)

        self.btn_volver = BotonSecundario("⬅️ Volver")
        self.btn_volver.clicked.connect(self.close)
        
        footer_layout.addWidget(self.lbl_resumen)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_exportar)
        footer_layout.addWidget(self.btn_volver)
        
        layout.addLayout(footer_layout)
        
        # Cargar últimos 100 movimientos por defecto
        self.buscar()
    
    def cargar_almacenes(self):
        """Carga almacenes en el combo usando ComboLoader"""
        ComboLoader.cargar_almacenes(
            self.cmb_almacen,
            almacenes_service.obtener_almacenes,
            opcion_vacia=True,
            texto_vacio="Todos"
        )
    
    def toggle_fechas(self):
        """Habilita/deshabilita filtro de fechas"""
        habilitado = self.chk_fecha.isChecked()
        self.date_desde.setEnabled(habilitado)
        self.date_hasta.setEnabled(habilitado)
    
    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.chk_fecha.setChecked(False)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_hasta.setDate(QDate.currentDate())
        self.cmb_tipo.setCurrentIndex(0)
        self.cmb_almacen.setCurrentIndex(0)
        self.txt_articulo.clear()
        self.txt_ot.clear()
        self.txt_responsable.clear()
        self.buscar()
    
    def buscar(self):
        """Busca movimientos según filtros"""
        try:
            # Preparar filtros
            filtros = {}

            # Filtro de fechas
            if self.chk_fecha.isChecked():
                filtros['fecha_desde'] = self.date_desde.date().toString("yyyy-MM-dd")
                filtros['fecha_hasta'] = self.date_hasta.date().toString("yyyy-MM-dd")

            # Filtro de tipo
            if self.cmb_tipo.currentIndex() > 0:
                filtros['tipo'] = self.cmb_tipo.currentText()

            # Filtro de almacén (origen o destino)
            almacen_id = self.cmb_almacen.currentData()
            if almacen_id:
                filtros['almacen_id'] = almacen_id

            # Filtro de artículo por texto (nombre, EAN o referencia)
            texto_articulo = self.txt_articulo.text().strip()
            if texto_articulo:
                filtros['articulo_texto'] = texto_articulo

            # Filtro de OT
            ot = self.txt_ot.text().strip()
            if ot:
                filtros['ot'] = ot

            # Filtro de responsable
            responsable = self.txt_responsable.text().strip()
            if responsable:
                filtros['responsable'] = responsable

            # Usar movimientos_service en lugar de SQL directo
            rows = movimientos_service.obtener_movimientos_filtrados(**filtros)


            # Mostrar en tabla
            self.tabla.setRowCount(len(rows))

            for i, row in enumerate(rows):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row['id'])))

                # Fecha
                try:
                    fecha_obj = datetime.datetime.strptime(row['fecha'], "%Y-%m-%d")
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    fecha_str = row['fecha']
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))

                # Tipo con color
                tipo = row['tipo']
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
                self.tabla.setItem(i, 2, item_tipo)

                # Origen
                self.tabla.setItem(i, 3, QTableWidgetItem(row.get('origen_nombre') or "-"))

                # Destino
                self.tabla.setItem(i, 4, QTableWidgetItem(row.get('destino_nombre') or "-"))

                # Artículo
                self.tabla.setItem(i, 5, QTableWidgetItem(row.get('articulo_nombre', '')))

                # Cantidad
                item_cant = QTableWidgetItem(f"{row['cantidad']:.2f}")
                item_cant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(i, 6, item_cant)

                # Coste
                if row.get('coste_unit'):
                    item_coste = QTableWidgetItem(f"€ {row['coste_unit']:.2f}")
                    item_coste.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.tabla.setItem(i, 7, item_coste)
                else:
                    self.tabla.setItem(i, 7, QTableWidgetItem("-"))

                # OT
                self.tabla.setItem(i, 8, QTableWidgetItem(row.get('ot') or "-"))

                # Responsable
                self.tabla.setItem(i, 9, QTableWidgetItem(row.get('responsable') or "-"))

                # Motivo
                self.tabla.setItem(i, 10, QTableWidgetItem(row.get('motivo') or "-"))
            
            # Actualizar resumen
            self.lbl_resumen.setText(f"📋 Mostrando {len(rows)} movimiento(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al buscar movimientos:\n{e}")
    
    def exportar_excel(self):
        """Exporta los resultados a Excel"""
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
            columnas = ["Fecha", "Tipo", "Origen", "Destino", "Artículo", 
                       "Cantidad", "Coste", "OT", "Responsable", "Motivo"]
            df = pd.DataFrame(datos, columns=columnas)
            
            # Crear carpeta exports
            export_dir = BASE / "exports"
            export_dir.mkdir(exist_ok=True)
            
            # Nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"movimientos_{timestamp}.xlsx"
            
            # Exportar
            df.to_excel(filename, index=False, sheet_name="Movimientos")
            
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Movimientos exportados correctamente:\n\n{filename}"
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
