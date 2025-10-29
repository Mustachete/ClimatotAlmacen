# ventana_inventario.py - Gestión de Inventario Físico
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QGroupBox, QHeaderView, QTextEdit, QDialog, QFormLayout,
    QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from pathlib import Path
import sqlite3
import datetime
from src.ui.estilos import ESTILO_VENTANA, ESTILO_DIALOGO
from src.ui.widgets_personalizados import SpinBoxClimatot
from src.core.db_utils import get_con

# ========================================
# DIÁLOGO: NUEVO INVENTARIO
# ========================================
class DialogoNuevoInventario(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Crear Nuevo Inventario")
        self.setFixedSize(600, 600)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📋 Crear Nuevo Inventario Físico")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Grupo: Datos básicos
        grupo = QGroupBox("Datos del Inventario")
        form = QFormLayout()
        
        # Fecha
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        form.addRow("📅 Fecha:", self.date_fecha)
        
        # Responsable
        self.txt_responsable = QLineEdit()
        self.txt_responsable.setPlaceholderText("Nombre del responsable del conteo")
        form.addRow("👤 Responsable *:", self.txt_responsable)
        
        # Almacén
        self.cmb_almacen = QComboBox()
        self.cargar_almacenes()
        form.addRow("🏢 Almacén *:", self.cmb_almacen)
        
        # Observaciones
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setPlaceholderText("Observaciones opcionales sobre este inventario...")
        self.txt_observaciones.setMaximumHeight(80)
        form.addRow("📝 Observaciones:", self.txt_observaciones)
        
        grupo.setLayout(form)
        layout.addWidget(grupo)
        
        # Opciones de filtrado
        grupo_filtros = QGroupBox("¿Qué artículos incluir?")
        filtros_layout = QVBoxLayout()
        
        self.radio_todos = QCheckBox("Todos los artículos activos")
        self.radio_todos.setChecked(True)
        
        self.radio_con_stock = QCheckBox("Solo artículos con stock en este almacén")
        
        filtros_layout.addWidget(self.radio_todos)
        filtros_layout.addWidget(self.radio_con_stock)
        
        grupo_filtros.setLayout(filtros_layout)
        layout.addWidget(grupo_filtros)
        
        # Nota
        nota = QLabel(
            "💡 Tras crear el inventario, podrás registrar los conteos físicos.\n"
            "El sistema calculará automáticamente las diferencias con el stock teórico."
        )
        nota.setStyleSheet("color: #64748b; font-size: 11px; margin: 10px; padding: 8px; "
                          "background-color: #dbeafe; border-radius: 5px;")
        layout.addWidget(nota)
        
        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.btn_crear = QPushButton("✅ Crear Inventario")
        self.btn_crear.clicked.connect(self.crear_inventario)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_crear)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        self.inventario_id = None
    
    def cargar_almacenes(self):
        """Carga los almacenes"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM almacenes ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            for row in rows:
                self.cmb_almacen.addItem(row[1], row[0])
        except Exception:
            pass
    
    def crear_inventario(self):
        """Crea el inventario y genera las líneas de detalle"""
        responsable = self.txt_responsable.text().strip()
        
        if not responsable:
            QMessageBox.warning(self, "⚠️ Aviso", "El responsable es obligatorio.")
            return
        
        almacen_id = self.cmb_almacen.currentData()
        if not almacen_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un almacén.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        observaciones = self.txt_observaciones.toPlainText().strip()
        solo_con_stock = self.radio_con_stock.isChecked()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Crear cabecera del inventario
            cur.execute("""
                INSERT INTO inventarios(fecha, responsable, almacen_id, observaciones, estado)
                VALUES(?, ?, ?, ?, 'EN_PROCESO')
            """, (fecha, responsable, almacen_id, observaciones))
            
            inventario_id = cur.lastrowid
            
            # Obtener artículos a inventariar
            if solo_con_stock:
                query = """
                    SELECT DISTINCT a.id, a.nombre, a.u_medida, COALESCE(SUM(v.delta), 0) as stock
                    FROM articulos a
                    LEFT JOIN vw_stock v ON a.id = v.articulo_id AND v.almacen_id = ?
                    WHERE a.activo = 1
                    GROUP BY a.id
                    HAVING stock > 0
                    ORDER BY a.nombre
                """
                cur.execute(query, (almacen_id,))
            else:
                query = """
                    SELECT a.id, a.nombre, a.u_medida, COALESCE(SUM(v.delta), 0) as stock
                    FROM articulos a
                    LEFT JOIN vw_stock v ON a.id = v.articulo_id AND v.almacen_id = ?
                    WHERE a.activo = 1
                    GROUP BY a.id
                    ORDER BY a.nombre
                """
                cur.execute(query, (almacen_id,))
            
            articulos = cur.fetchall()
            
            if not articulos:
                con.close()
                QMessageBox.warning(self, "⚠️ Aviso", "No hay artículos para inventariar.")
                return
            
            # Crear líneas de detalle
            for art in articulos:
                cur.execute("""
                    INSERT INTO inventario_detalle(inventario_id, articulo_id, stock_teorico, stock_contado, diferencia)
                    VALUES(?, ?, ?, 0, ?)
                """, (inventario_id, art[0], art[3], -art[3]))
            
            con.commit()
            con.close()
            
            self.inventario_id = inventario_id
            
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Inventario creado correctamente.\n\n"
                f"Artículos a contar: {len(articulos)}\n\n"
                f"Ahora puede registrar los conteos físicos."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al crear inventario:\n{e}")

# ========================================
# VENTANA: REGISTRAR CONTEOS
# ========================================
class VentanaConteo(QWidget):
    def __init__(self, inventario_id, parent=None):
        super().__init__(parent)
        self.inventario_id = inventario_id
        self.setWindowTitle(f"📦 Registrar Conteos - Inventario #{inventario_id}")
        self.resize(1100, 700)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Cargar info del inventario
        self.cargar_info_inventario()
        
        # Título
        titulo = QLabel(f"📦 Registrar Conteos Físicos - Inventario #{inventario_id}")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Info del inventario
        info_layout = QHBoxLayout()
        
        lbl_info = QLabel(
            f"📅 Fecha: {self.info_inv['fecha']} | "
            f"👤 Responsable: {self.info_inv['responsable']} | "
            f"🏢 Almacén: {self.info_inv['almacen']}"
        )
        lbl_info.setStyleSheet("font-size: 13px; margin: 5px;")
        
        info_layout.addWidget(lbl_info)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Buscador rápido
        busqueda_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar artículo:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escanea código de barras o busca por nombre...")
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        
        busqueda_layout.addWidget(lbl_buscar)
        busqueda_layout.addWidget(self.txt_buscar, 2)
        
        layout.addLayout(busqueda_layout)
        
        # Filtros rápidos
        filtros_layout = QHBoxLayout()
        
        self.chk_solo_pendientes = QCheckBox("Solo pendientes (sin contar)")
        self.chk_solo_pendientes.stateChanged.connect(self.filtrar_tabla)
        
        self.chk_solo_diferencias = QCheckBox("Solo con diferencias")
        self.chk_solo_diferencias.stateChanged.connect(self.filtrar_tabla)
        
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.cargar_detalle)
        
        filtros_layout.addWidget(self.chk_solo_pendientes)
        filtros_layout.addWidget(self.chk_solo_diferencias)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.btn_actualizar)
        
        layout.addLayout(filtros_layout)
        
        # Tabla de conteos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Artículo", "U.Medida", "Stock Teórico", "Stock Contado", "Diferencia", "Estado"
        ])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.doubleClicked.connect(self.editar_conteo)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla)
        
        # Resumen
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(self.lbl_resumen)
        
        # Botones
        botones_layout = QHBoxLayout()
        
        self.btn_finalizar = QPushButton("✅ FINALIZAR INVENTARIO Y AJUSTAR STOCK")
        self.btn_finalizar.setMinimumHeight(50)
        self.btn_finalizar.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.btn_finalizar.clicked.connect(self.finalizar_inventario)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_finalizar, 3)
        botones_layout.addWidget(self.btn_volver, 1)
        
        layout.addLayout(botones_layout)
        
        # Cargar datos
        self.cargar_detalle()
    
    def cargar_info_inventario(self):
        """Carga la información del inventario"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT i.fecha, i.responsable, a.nombre, i.estado
                FROM inventarios i
                JOIN almacenes a ON i.almacen_id = a.id
                WHERE i.id = ?
            """, (self.inventario_id,))
            row = cur.fetchone()
            con.close()
            
            if row:
                # Formatear fecha
                try:
                    fecha_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d")
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_str = row[0]
                
                self.info_inv = {
                    'fecha': fecha_str,
                    'responsable': row[1],
                    'almacen': row[2],
                    'estado': row[3]
                }
                
                if row[3] == 'FINALIZADO':
                    QMessageBox.information(
                        self,
                        "ℹ️ Inventario Finalizado",
                        "Este inventario ya está finalizado.\n"
                        "No se pueden modificar los conteos."
                    )
                    self.btn_finalizar.setEnabled(False)
            
        except Exception:
            self.info_inv = {'fecha': '', 'responsable': '', 'almacen': '', 'estado': ''}
    
    def cargar_detalle(self):
        """Carga el detalle del inventario"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT 
                    d.id,
                    a.nombre,
                    a.u_medida,
                    d.stock_teorico,
                    d.stock_contado,
                    d.diferencia
                FROM inventario_detalle d
                JOIN articulos a ON d.articulo_id = a.id
                WHERE d.inventario_id = ?
                ORDER BY a.nombre
            """, (self.inventario_id,))
            self.rows = cur.fetchall()
            con.close()
            
            self.filtrar_tabla()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar detalle:\n{e}")
    
    def filtrar_tabla(self):
        """Filtra y muestra los datos en la tabla"""
        texto_buscar = self.txt_buscar.text().strip().lower()
        solo_pendientes = self.chk_solo_pendientes.isChecked()
        solo_diferencias = self.chk_solo_diferencias.isChecked()
        
        rows_filtradas = []
        
        for row in self.rows:
            # Filtro de búsqueda
            if texto_buscar and texto_buscar not in row[1].lower():
                continue
            
            # Filtro pendientes (sin contar aún)
            if solo_pendientes and row[4] != 0:
                continue
            
            # Filtro diferencias
            if solo_diferencias and row[5] == 0:
                continue
            
            rows_filtradas.append(row)
        
        # Mostrar en tabla
        self.tabla.setRowCount(len(rows_filtradas))
        
        total = len(self.rows)
        contados = sum(1 for r in self.rows if r[4] != 0)
        con_diferencias = sum(1 for r in self.rows if r[5] != 0)
        
        for i, row in enumerate(rows_filtradas):
            # ID
            self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
            # Artículo
            self.tabla.setItem(i, 1, QTableWidgetItem(row[1]))
            # U.Medida
            self.tabla.setItem(i, 2, QTableWidgetItem(row[2]))
            # Stock Teórico
            item_teorico = QTableWidgetItem(f"{row[3]:.2f}")
            item_teorico.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(i, 3, item_teorico)
            # Stock Contado
            item_contado = QTableWidgetItem(f"{row[4]:.2f}")
            item_contado.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[4] == 0:
                item_contado.setForeground(QColor("#94a3b8"))
            self.tabla.setItem(i, 4, item_contado)
            # Diferencia
            item_diff = QTableWidgetItem(f"{row[5]:+.2f}")
            item_diff.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if row[5] > 0:
                item_diff.setBackground(QColor("#d1fae5"))
                item_diff.setForeground(QColor("#065f46"))
            elif row[5] < 0:
                item_diff.setBackground(QColor("#fee2e2"))
                item_diff.setForeground(QColor("#991b1b"))
            self.tabla.setItem(i, 5, item_diff)
            # Estado
            if row[4] == 0:
                estado = "⏳ Pendiente"
                color = QColor("#fef3c7")
            elif row[5] == 0:
                estado = "✅ OK"
                color = QColor("#d1fae5")
            elif row[5] > 0:
                estado = "📈 Sobra"
                color = QColor("#dbeafe")
            else:
                estado = "📉 Falta"
                color = QColor("#fecaca")
            
            item_estado = QTableWidgetItem(estado)
            item_estado.setBackground(color)
            item_estado.setTextAlignment(Qt.AlignCenter)
            self.tabla.setItem(i, 6, item_estado)
        
        # Actualizar resumen
        self.lbl_resumen.setText(
            f"📦 Total artículos: {total} | "
            f"✅ Contados: {contados} | "
            f"⏳ Pendientes: {total - contados} | "
            f"⚠️ Con diferencias: {con_diferencias}"
        )
    
    def editar_conteo(self):
        """Abre diálogo para editar el conteo de un artículo"""
        if self.info_inv['estado'] == 'FINALIZADO':
            QMessageBox.warning(self, "⚠️ Aviso", "El inventario ya está finalizado.")
            return
        
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        
        detalle_id = int(self.tabla.item(fila, 0).text())
        articulo = self.tabla.item(fila, 1).text()
        stock_teorico = float(self.tabla.item(fila, 3).text())
        stock_contado_actual = float(self.tabla.item(fila, 4).text())
        
        # Diálogo simple para introducir conteo
        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"📦 Contar: {articulo}")
        dialogo.setFixedSize(400, 200)
        dialogo.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(dialogo)
        
        lbl_titulo = QLabel(f"📦 {articulo}")
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(lbl_titulo)
        
        lbl_teorico = QLabel(f"Stock teórico en sistema: {stock_teorico:.2f}")
        lbl_teorico.setStyleSheet("color: #64748b;")
        layout.addWidget(lbl_teorico)
        
        form = QFormLayout()
        
        spin_contado = SpinBoxClimatot()
        spin_contado.setRange(0, 999999)
        spin_contado.setDecimals(2)
        spin_contado.setValue(stock_contado_actual if stock_contado_actual > 0 else stock_teorico)
        spin_contado.setMinimumWidth(150)
        
        form.addRow("📊 Cantidad contada *:", spin_contado)
        
        layout.addLayout(form)
        
        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        btn_guardar = QPushButton("💾 Guardar")
        btn_cancelar = QPushButton("❌ Cancelar")
        
        btn_layout.addWidget(btn_guardar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        
        # Conectar botones
        btn_cancelar.clicked.connect(dialogo.reject)
        
        def guardar_conteo():
            contado = spin_contado.value()
            diferencia = contado - stock_teorico
            
            try:
                con = get_con()
                cur = con.cursor()
                cur.execute("""
                    UPDATE inventario_detalle
                    SET stock_contado = ?, diferencia = ?
                    WHERE id = ?
                """, (contado, diferencia, detalle_id))
                con.commit()
                con.close()
                
                dialogo.accept()
                self.cargar_detalle()
                
            except Exception as e:
                QMessageBox.critical(dialogo, "❌ Error", f"Error al guardar:\n{e}")
        
        btn_guardar.clicked.connect(guardar_conteo)
        
        dialogo.exec()
    
    def finalizar_inventario(self):
        """Finaliza el inventario y genera los ajustes de stock"""
        # Verificar si hay pendientes
        pendientes = sum(1 for r in self.rows if r[4] == 0)
        
        if pendientes > 0:
            respuesta = QMessageBox.question(
                self,
                "⚠️ Artículos pendientes",
                f"Hay {pendientes} artículo(s) sin contar.\n\n"
                f"¿Desea finalizar de todos modos?\n"
                f"(Los artículos sin contar mantendrán su stock actual)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta != QMessageBox.Yes:
                return
        
        # Confirmar finalización
        respuesta = QMessageBox.question(
            self,
            "✅ Finalizar Inventario",
            "¿Está seguro de finalizar este inventario?\n\n"
            "Se generarán automáticamente los ajustes de stock necesarios.\n\n"
            "Esta acción NO se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Obtener almacén del inventario
            cur.execute("SELECT almacen_id FROM inventarios WHERE id = ?", (self.inventario_id,))
            almacen_id = cur.fetchone()[0]
            
            # Obtener todas las diferencias
            cur.execute("""
                SELECT articulo_id, diferencia
                FROM inventario_detalle
                WHERE inventario_id = ? AND diferencia != 0
            """, (self.inventario_id,))
            diferencias = cur.fetchall()
            
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            
            # Generar movimientos de ajuste
            ajustes_positivos = 0
            ajustes_negativos = 0
            
            for articulo_id, diferencia in diferencias:
                if diferencia > 0:
                    # Sobra material - Entrada
                    cur.execute("""
                        INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, motivo)
                        VALUES(?, 'ENTRADA', NULL, ?, ?, ?, ?)
                    """, (fecha_hoy, almacen_id, articulo_id, diferencia, 
                          f"Ajuste inventario #{self.inventario_id}"))
                    ajustes_positivos += 1
                else:
                    # Falta material - Pérdida
                    cur.execute("""
                        INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, motivo, responsable)
                        VALUES(?, 'PERDIDA', ?, NULL, ?, ?, ?, ?)
                    """, (fecha_hoy, almacen_id, articulo_id, abs(diferencia),
                          f"Ajuste inventario #{self.inventario_id}", 
                          self.info_inv['responsable']))
                    ajustes_negativos += 1
            
            # Marcar inventario como finalizado
            cur.execute("""
                UPDATE inventarios
                SET estado = 'FINALIZADO', fecha_cierre = ?
                WHERE id = ?
            """, (fecha_hoy, self.inventario_id))
            
            con.commit()
            con.close()
            
            QMessageBox.information(
                self,
                "✅ Inventario Finalizado",
                f"Inventario finalizado correctamente.\n\n"
                f"Ajustes generados:\n"
                f"  • Entradas (sobra): {ajustes_positivos}\n"
                f"  • Salidas (falta): {ajustes_negativos}\n\n"
                f"El stock ha sido actualizado automáticamente."
            )
            
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al finalizar inventario:\n{e}")

# ========================================
# VENTANA PRINCIPAL: INVENTARIO FÍSICO
# ========================================
class VentanaInventario(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Inventario Físico")
        self.resize(1000, 650)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📊 Gestión de Inventario Físico")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel(
            "Controla el stock físico real y ajusta diferencias con el sistema.\n"
            "Crea inventarios, registra conteos y aplica ajustes automáticos."
        )
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Botones superiores
        botones_top = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("➕ Nuevo Inventario")
        self.btn_nuevo.setMinimumHeight(45)
        self.btn_nuevo.clicked.connect(self.nuevo_inventario)
        
        self.btn_continuar = QPushButton("📝 Continuar Inventario")
        self.btn_continuar.setMinimumHeight(45)
        self.btn_continuar.clicked.connect(self.continuar_inventario)
        self.btn_continuar.setEnabled(False)
        
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.setMinimumHeight(45)
        self.btn_actualizar.clicked.connect(self.cargar_inventarios)
        
        botones_top.addWidget(self.btn_nuevo, 2)
        botones_top.addWidget(self.btn_continuar, 2)
        botones_top.addWidget(self.btn_actualizar, 1)
        
        layout.addLayout(botones_top)
        
        # Filtros
        filtros_layout = QHBoxLayout()
        
        lbl_filtro = QLabel("Mostrar:")
        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(["Todos", "Solo en proceso", "Solo finalizados"])
        self.cmb_filtro.currentTextChanged.connect(self.cargar_inventarios)
        
        filtros_layout.addWidget(lbl_filtro)
        filtros_layout.addWidget(self.cmb_filtro)
        filtros_layout.addStretch()
        
        layout.addLayout(filtros_layout)
        
        # Tabla de inventarios
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Fecha", "Responsable", "Almacén", "Artículos", "Estado", "Fecha Cierre"
        ])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.continuar_inventario)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(45)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos
        self.cargar_inventarios()
    
    def cargar_inventarios(self):
        """Carga el histórico de inventarios"""
        filtro = self.cmb_filtro.currentText()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            query = """
                SELECT 
                    i.id,
                    i.fecha,
                    i.responsable,
                    a.nombre as almacen,
                    (SELECT COUNT(*) FROM inventario_detalle WHERE inventario_id = i.id) as num_arts,
                    i.estado,
                    i.fecha_cierre
                FROM inventarios i
                JOIN almacenes a ON i.almacen_id = a.id
                WHERE 1=1
            """
            
            if filtro == "Solo en proceso":
                query += " AND i.estado = 'EN_PROCESO'"
            elif filtro == "Solo finalizados":
                query += " AND i.estado = 'FINALIZADO'"
            
            query += " ORDER BY i.id DESC"
            
            cur.execute(query)
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
                
                # Fecha
                try:
                    fecha_obj = datetime.datetime.strptime(row[1], "%Y-%m-%d")
                    fecha_str = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_str = row[1]
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
                
                # Responsable
                self.tabla.setItem(i, 2, QTableWidgetItem(row[2]))
                
                # Almacén
                self.tabla.setItem(i, 3, QTableWidgetItem(row[3]))
                
                # Artículos
                item_arts = QTableWidgetItem(f"{row[4]} artículos")
                item_arts.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(i, 4, item_arts)
                
                # Estado
                if row[5] == 'EN_PROCESO':
                    estado_txt = "⏳ En Proceso"
                    color = QColor("#fef3c7")
                else:
                    estado_txt = "✅ Finalizado"
                    color = QColor("#d1fae5")
                
                item_estado = QTableWidgetItem(estado_txt)
                item_estado.setBackground(color)
                item_estado.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(i, 5, item_estado)
                
                # Fecha cierre
                if row[6]:
                    try:
                        fecha_cierre_obj = datetime.datetime.strptime(row[6], "%Y-%m-%d")
                        fecha_cierre_str = fecha_cierre_obj.strftime("%d/%m/%Y")
                    except:
                        fecha_cierre_str = row[6]
                else:
                    fecha_cierre_str = "-"
                self.tabla.setItem(i, 6, QTableWidgetItem(fecha_cierre_str))
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar inventarios:\n{e}")
    
    def seleccion_cambiada(self):
        """Habilita/deshabilita botón continuar"""
        self.btn_continuar.setEnabled(len(self.tabla.selectedItems()) > 0)
    
    def nuevo_inventario(self):
        """Abre diálogo para crear nuevo inventario"""
        dialogo = DialogoNuevoInventario(self)
        if dialogo.exec() and dialogo.inventario_id:
            # Abrir directamente la ventana de conteo
            self.ventana_conteo = VentanaConteo(dialogo.inventario_id)
            self.ventana_conteo.show()
            self.cargar_inventarios()
    
    def continuar_inventario(self):
        """Abre la ventana de conteo del inventario seleccionado"""
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        
        inventario_id = int(self.tabla.item(fila, 0).text())
        
        self.ventana_conteo = VentanaConteo(inventario_id)
        self.ventana_conteo.show()