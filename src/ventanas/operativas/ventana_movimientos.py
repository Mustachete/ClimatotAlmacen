# ventana_movimientos.py - Hacer Movimientos (Supermercado)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QRadioButton, QButtonGroup, QGroupBox, QHeaderView,
    QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, QTimer
from pathlib import Path
import sqlite3
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_personalizados import SpinBoxClimatot
from src.core.db_utils import get_con

# ========================================
# VENTANA DE HACER MOVIMIENTOS
# ========================================
class VentanaMovimientos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Hacer Movimientos - Supermercado")
        self.setFixedSize(1100, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Lista temporal de artículos
        self.articulos_temp = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("🔄 Hacer Movimientos - Supermercado")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Registra entregas y devoluciones de material entre almacén y furgonetas")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DEL MOVIMIENTO ==========
        grupo_datos = QGroupBox("📋 Datos del Movimiento")
        datos_layout = QHBoxLayout()
        
        # Fecha
        lbl_fecha = QLabel("📅 Fecha:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        # Operario/Furgoneta
        lbl_operario = QLabel("👷 Operario:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(200)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)
        
        lbl_furgoneta = QLabel("🚚 Furgoneta:")
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
        
        datos_layout.addWidget(lbl_fecha)
        datos_layout.addWidget(self.date_fecha)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_operario)
        datos_layout.addWidget(self.cmb_operario)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_furgoneta)
        datos_layout.addWidget(self.lbl_furgoneta_asignada)
        datos_layout.addStretch()
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: MODO DE OPERACIÓN ==========
        grupo_modo = QGroupBox("🔀 Modo de Operación")
        modo_layout = QHBoxLayout()
        
        self.btn_group_modo = QButtonGroup()
        
        self.radio_entregar = QRadioButton("📤 ENTREGAR material (Almacén → Furgoneta)")
        self.radio_entregar.setChecked(True)
        self.radio_entregar.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.radio_recibir = QRadioButton("📥 RECIBIR material (Furgoneta → Almacén)")
        self.radio_recibir.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.btn_group_modo.addButton(self.radio_entregar, 1)
        self.btn_group_modo.addButton(self.radio_recibir, 2)
        
        modo_layout.addWidget(self.radio_entregar)
        modo_layout.addSpacing(30)
        modo_layout.addWidget(self.radio_recibir)
        modo_layout.addStretch()
        
        grupo_modo.setLayout(modo_layout)
        layout.addWidget(grupo_modo)
        
        # ========== GRUPO: BUSCAR Y AÑADIR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Buscar y Añadir Artículos")
        articulos_layout = QVBoxLayout()
        
        # Barra de búsqueda
        busqueda_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar artículo:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escanea código de barras o escribe nombre/referencia/palabras clave...")
        self.txt_buscar.returnPressed.connect(self.buscar_articulo)
        self.txt_buscar.textChanged.connect(self.busqueda_tiempo_real)
        
        # Timer para búsqueda en tiempo real (espera 300ms después de escribir)
        self.timer_busqueda = QTimer()
        self.timer_busqueda.setSingleShot(True)
        self.timer_busqueda.timeout.connect(self.buscar_articulo)
        
        lbl_cantidad = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(100)
        
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.setMinimumHeight(40)
        self.btn_agregar.clicked.connect(self.agregar_desde_busqueda)
        
        busqueda_layout.addWidget(lbl_buscar)
        busqueda_layout.addWidget(self.txt_buscar, 3)
        busqueda_layout.addWidget(lbl_cantidad)
        busqueda_layout.addWidget(self.spin_cantidad)
        busqueda_layout.addWidget(self.btn_agregar)
        
        articulos_layout.addLayout(busqueda_layout)
        
        # Sugerencias de búsqueda
        self.lbl_sugerencia = QLabel("")
        self.lbl_sugerencia.setStyleSheet("color: #1e3a8a; font-size: 12px; margin: 5px; font-style: italic;")
        articulos_layout.addWidget(self.lbl_sugerencia)
        
        grupo_articulos.setLayout(articulos_layout)
        layout.addWidget(grupo_articulos)
        
        # ========== TABLA DE ARTÍCULOS SELECCIONADOS ==========
        lbl_tabla = QLabel("📋 Artículos seleccionados:")
        lbl_tabla.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_tabla)
        
        self.tabla_articulos = QTableWidget()
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels(["ID", "Artículo", "U.Medida", "Cantidad", "Acciones"])
        self.tabla_articulos.setColumnHidden(0, True)
        
        header = self.tabla_articulos.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.tabla_articulos.setMinimumHeight(200)
        layout.addWidget(self.tabla_articulos)
        
        # ========== BOTONES FINALES ==========
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 CONFIRMAR Y GUARDAR")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_movimiento)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar_todo)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 3)
        botones_layout.addWidget(self.btn_cancelar, 1)
        botones_layout.addWidget(self.btn_volver, 1)
        
        layout.addLayout(botones_layout)
        
        # Focus inicial en búsqueda
        self.txt_buscar.setFocus()
    
    def cargar_operarios(self):
        """Carga los operarios activos"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, rol_operario 
                FROM operarios 
                WHERE activo=1 
                ORDER BY rol_operario DESC, nombre
            """)
            rows = cur.fetchall()
            con.close()
            
            self.cmb_operario.addItem("(Seleccione operario)", None)
            for row in rows:
                emoji = "👷" if row[2] == "oficial" else "🔨"
                texto = f"{emoji} {row[1]} ({row[2]})"
                self.cmb_operario.addItem(texto, row[0])
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")
    
    def cambio_operario(self):
        """Al cambiar de operario, busca su furgoneta asignada"""
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            cur.execute("""
                SELECT a.nombre 
                FROM asignaciones_furgoneta af
                JOIN almacenes a ON af.furgoneta_id = a.id
                WHERE af.operario_id=? AND af.fecha=?
            """, (operario_id, fecha_hoy))
            row = cur.fetchone()
            con.close()
            
            if row:
                self.lbl_furgoneta_asignada.setText(f"🚚 Furgoneta {row[0]}")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #1e3a8a; font-weight: bold;")
            else:
                self.lbl_furgoneta_asignada.setText("⚠️ Sin furgoneta asignada hoy")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #dc2626; font-weight: bold;")
        except Exception:
            pass
    
    def busqueda_tiempo_real(self):
        """Reinicia el timer de búsqueda cada vez que se escribe"""
        self.timer_busqueda.stop()
        if len(self.txt_buscar.text()) >= 3:
            self.timer_busqueda.start(300)
    
    def buscar_articulo(self):
        """Busca un artículo por EAN, nombre, referencia o palabras clave"""
        texto = self.txt_buscar.text().strip()
        
        if not texto:
            self.lbl_sugerencia.setText("")
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, u_medida, ean, ref_proveedor
                FROM articulos
                WHERE activo=1 AND (
                    ean LIKE ? OR
                    ref_proveedor LIKE ? OR
                    nombre LIKE ? OR
                    palabras_clave LIKE ?
                )
                ORDER BY 
                    CASE 
                        WHEN ean = ? THEN 1
                        WHEN ref_proveedor = ? THEN 2
                        WHEN nombre LIKE ? THEN 3
                        ELSE 4
                    END
                LIMIT 5
            """, (f"%{texto}%", f"%{texto}%", f"%{texto}%", f"%{texto}%", texto, texto, f"{texto}%"))
            rows = cur.fetchall()
            con.close()
            
            if not rows:
                self.lbl_sugerencia.setText("❌ No se encontraron artículos")
                return
            
            if len(rows) == 1:
                # Encontrado exacto, agregar automáticamente
                self.agregar_articulo(rows[0][0], rows[0][1], rows[0][2])
                self.txt_buscar.clear()
                self.lbl_sugerencia.setText("✅ Artículo agregado")
            else:
                # Múltiples resultados, mostrar sugerencias
                nombres = [f"• {r[1]}" for r in rows[:3]]
                self.lbl_sugerencia.setText(f"💡 Sugerencias:\n" + "\n".join(nombres))
        
        except Exception as e:
            self.lbl_sugerencia.setText(f"❌ Error: {e}")
    
    def agregar_desde_busqueda(self):
        """Fuerza la búsqueda y agregado del artículo"""
        self.buscar_articulo()
    
    def agregar_articulo(self, articulo_id, nombre, u_medida):
        """Agrega un artículo a la lista temporal"""
        cantidad = self.spin_cantidad.value()
        
        # Verificar si ya está en la lista
        for art in self.articulos_temp:
            if art['id'] == articulo_id:
                # Incrementar cantidad
                art['cantidad'] += cantidad
                self.actualizar_tabla()
                self.spin_cantidad.setValue(1)
                self.txt_buscar.setFocus()
                return
        
        # Agregar nuevo
        self.articulos_temp.append({
            'id': articulo_id,
            'nombre': nombre,
            'u_medida': u_medida,
            'cantidad': cantidad
        })
        
        self.actualizar_tabla()
        self.spin_cantidad.setValue(1)
        self.txt_buscar.setFocus()
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))
        
        for i, art in enumerate(self.articulos_temp):
            self.tabla_articulos.setItem(i, 0, QTableWidgetItem(str(art['id'])))
            self.tabla_articulos.setItem(i, 1, QTableWidgetItem(art['nombre']))
            self.tabla_articulos.setItem(i, 2, QTableWidgetItem(art['u_medida']))
            self.tabla_articulos.setItem(i, 3, QTableWidgetItem(f"{art['cantidad']:.2f}"))
            
            # Botón quitar
            btn_quitar = QPushButton("🗑️ Quitar")
            btn_quitar.clicked.connect(lambda checked, idx=i: self.quitar_articulo(idx))
            self.tabla_articulos.setCellWidget(i, 4, btn_quitar)
    
    def quitar_articulo(self, index):
        """Quita un artículo de la lista"""
        if 0 <= index < len(self.articulos_temp):
            del self.articulos_temp[index]
            self.actualizar_tabla()
    
    def guardar_movimiento(self):
        """Guarda el movimiento en la base de datos"""
        # Validaciones
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un operario.")
            return
        
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe agregar al menos un artículo.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        modo = "ENTREGAR" if self.radio_entregar.isChecked() else "RECIBIR"
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Obtener IDs de almacén y furgoneta
            cur.execute("SELECT id FROM almacenes WHERE nombre='Almacén' LIMIT 1")
            almacen_id = cur.fetchone()[0]
            
            # Obtener furgoneta del operario
            cur.execute("""
                SELECT furgoneta_id FROM asignaciones_furgoneta
                WHERE operario_id=? AND fecha=?
            """, (operario_id, fecha))
            furg_row = cur.fetchone()
            
            if not furg_row:
                QMessageBox.warning(self, "⚠️ Aviso", "El operario no tiene furgoneta asignada para esta fecha.")
                con.close()
                return
            
            furgoneta_id = furg_row[0]
            
            # Determinar origen y destino según el modo
            if modo == "ENTREGAR":
                origen_id = almacen_id
                destino_id = furgoneta_id
                tipo_mov = "TRASPASO"
            else:  # RECIBIR
                origen_id = furgoneta_id
                destino_id = almacen_id
                tipo_mov = "TRASPASO"
            
            # Obtener nombre del operario
            cur.execute("SELECT nombre FROM operarios WHERE id=?", (operario_id,))
            operario_nombre = cur.fetchone()[0]
            
            # Registrar movimientos
            for art in self.articulos_temp:
                cur.execute("""
                    INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, responsable)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (fecha, tipo_mov, origen_id, destino_id, art['id'], art['cantidad'], operario_nombre))
            
            con.commit()
            con.close()
            
            modo_texto = "entregado a" if modo == "ENTREGAR" else "recibido de"
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Movimiento registrado correctamente.\n\n"
                f"{len(self.articulos_temp)} artículo(s) {modo_texto} {operario_nombre}."
            )
            
            self.limpiar_todo()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")
    
    def limpiar_todo(self):
        """Limpia todos los campos y la lista"""
        self.articulos_temp = []
        self.actualizar_tabla()
        self.txt_buscar.clear()
        self.lbl_sugerencia.setText("")
        self.spin_cantidad.setValue(1)
        self.txt_buscar.setFocus()