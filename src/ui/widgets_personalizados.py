# widgets_personalizados.py - Widgets personalizados de Climatot (CORREGIDO)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget, QSizePolicy
from src.ui.estilos import ESTILO_BOTON_QUITAR


class SpinBoxClimatot(QWidget):
    """
    SpinBox personalizado con botones + y - visibles.

    CORRECCIONES APLICADAS:
    1. ✅ Alineación vertical PERFECTA con otros campos
    2. ✅ Bug del "1000" SOLUCIONADO
    3. ✅ Altura consistente con QLineEdit estándar
    4. ✅ Campos más anchos para 4 dígitos + céntimos (9.999,99)
    """

    valueChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 1.0
        self._minimum = 0.01
        self._maximum = 999999.99
        self._decimals = 2
        self._single_step = 1.0
        self._prefix = ""
        self._suffix = ""

        # ========================================
        # ✅ CORRECCIÓN 1: SIN altura fija del widget
        # Dejamos que tome la altura natural del layout
        # ========================================

        # Layout horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)  # Pequeño espacio entre elementos

        # ========================================
        # ✅ Campo de texto - SIN altura fija
        # ========================================
        self.line_edit = QLineEdit()
        self.line_edit.setText(f"{self._value:.{self._decimals}f}")
        self.line_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ✅ ANCHO MÍNIMO para 4 dígitos + céntimos
        self.line_edit.setMinimumWidth(120)  # Más ancho para "9.999,99"

        # Conectar señales
        self.line_edit.textEdited.connect(self._on_text_editing)
        self.line_edit.editingFinished.connect(self._on_text_changed)

        # ========================================
        # ✅ Botones - y + (SIN altura fija)
        # ========================================
        self.btn_down = QPushButton("−")
        self.btn_down.setFixedWidth(32)  # Solo fijamos el ancho
        self.btn_down.clicked.connect(self._decrement)
        self.btn_down.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 5px 0px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
                color: #1e3a8a;
            }
            QPushButton:hover {
                background-color: #dbeafe;
                border-color: #1e3a8a;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
            }
        """)

        self.btn_up = QPushButton("+")
        self.btn_up.setFixedWidth(32)  # Solo fijamos el ancho
        self.btn_up.clicked.connect(self._increment)
        self.btn_up.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 5px 0px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
                color: #1e3a8a;
            }
            QPushButton:hover {
                background-color: #dbeafe;
                border-color: #1e3a8a;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
            }
        """)

        # Añadir al layout
        layout.addWidget(self.line_edit)
        layout.addWidget(self.btn_down)
        layout.addWidget(self.btn_up)

        # ========================================
        # ✅ Estilo del campo (SIN altura fija)
        # ========================================
        self.line_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
                color: #1e293b;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1e3a8a;
                background-color: #f8fafc;
            }
        """)

    def value(self):
        """Obtiene el valor actual"""
        return self._value

    def setValue(self, val):
        """Establece el valor"""
        try:
            val = float(val)
            val = max(self._minimum, min(self._maximum, val))

            # Solo actualizar si cambió realmente
            if abs(self._value - val) > 0.001:
                self._value = val
                self._update_display()
                self.valueChanged.emit(val)
        except Exception as e:
            from src.core.logger import logger
            logger.warning(f"Error al establecer valor en SpinBoxClimatot: {val} - {e}")
            # Mantener el valor anterior en caso de error

    def _update_display(self):
        """Actualiza el display con el valor actual"""
        display_text = f"{self._prefix}{self._value:.{self._decimals}f}{self._suffix}"

        # Solo actualizar si es diferente (evita cursor jumping)
        if self.line_edit.text() != display_text:
            cursor_pos = self.line_edit.cursorPosition()
            self.line_edit.setText(display_text)
            # Restaurar posición del cursor si es razonable
            if cursor_pos <= len(display_text):
                self.line_edit.setCursorPosition(cursor_pos)

    def setRange(self, minimum, maximum):
        """Establece el rango"""
        self._minimum = minimum
        self._maximum = maximum

    def setDecimals(self, decimals):
        """Establece los decimales"""
        self._decimals = decimals
        self._update_display()

    def setSingleStep(self, step):
        """Establece el incremento"""
        self._single_step = step

    def setPrefix(self, prefix):
        """Establece el prefijo"""
        self._prefix = prefix
        self._update_display()

    def setSuffix(self, suffix):
        """Establece el sufijo"""
        self._suffix = suffix
        self._update_display()

    def setMinimumWidth(self, width):
        """Establece ancho mínimo total del widget"""
        total_buttons = 64 + 6  # 2 botones de 32px + spacing
        self.line_edit.setMinimumWidth(width - total_buttons)
        super().setMinimumWidth(width)

    def _increment(self):
        """Incrementa el valor"""
        new_val = self._value + self._single_step
        self.setValue(new_val)

    def _decrement(self):
        """Decrementa el valor"""
        new_val = self._value - self._single_step
        self.setValue(new_val)

    def _on_text_editing(self, text):
        """
        ✅ CORRECCIÓN BUG "1000":
        Mientras el usuario está escribiendo, permitir escribir libremente.
        No interferir con la edición.
        """
        pass  # Dejar que escriba sin restricciones

    def _on_text_changed(self):
        """
        Cuando el usuario termina de escribir (pierde el foco o presiona Enter).
        Aquí SÍ validamos y corregimos el valor.
        """
        try:
            # Obtener el texto actual
            text = self.line_edit.text().strip()

            # Quitar prefijo si existe
            if self._prefix and text.startswith(self._prefix):
                text = text[len(self._prefix) :].strip()

            # Quitar sufijo si existe
            if self._suffix and text.endswith(self._suffix):
                text = text[: -len(self._suffix)].strip()

            # Reemplazar coma por punto (formato español → formato Python)
            text = text.replace(",", ".")

            # Quitar separadores de miles si los hay
            text = text.replace(" ", "").replace(".", "", text.count(".") - 1)

            # ✅ CORRECCIÓN: Si está vacío, usar el mínimo
            if not text:
                self.setValue(self._minimum)
                return

            # Convertir a float y validar
            val = float(text)

            # ✅ CORRECCIÓN: Aplicar límites
            if val < self._minimum:
                val = self._minimum
            elif val > self._maximum:
                val = self._maximum

            self.setValue(val)

        except ValueError:
            # Si hay error, restaurar valor anterior
            self._update_display()


class BotonQuitar(QPushButton):
    """
    Botón "Quitar" compacto y responsive para usar en filas de tabla.
    Se adapta automáticamente al tamaño del contenedor donde se coloca.

    Características:
    - Usa estilos centralizados de estilos.py
    - No tiene tamaño fijo, se adapta al espacio disponible
    - Respeta límites min/max definidos en el estilo
    - Cabe perfectamente en filas de tabla estándar (~24px)
    """

    def __init__(self, texto="🗑️", parent=None):
        super().__init__(texto, parent)

        # ========================================
        # ✅ RESPONSIVE: Sin tamaño fijo
        # El botón se adapta al contenedor
        # ========================================

        # Política de tamaño: preferir tamaño mínimo pero expandible si hay espacio
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Aplicar estilo centralizado desde estilos.py
        self.setStyleSheet(ESTILO_BOTON_QUITAR)


def crear_boton_quitar_centrado(parent=None):
    """
    Crea un botón Quitar dentro de un contenedor centrado.
    Usar este helper para insertar en celdas de tabla con setCellWidget.

    Returns:
        tuple: (widget_contenedor, boton) - El widget para setCellWidget y el botón para conectar señales
    """
    # Crear contenedor
    contenedor = QWidget(parent)
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # Añadir espaciadores para centrar
    layout.addStretch()

    # Crear botón
    boton = BotonQuitar()

    # Añadir botón al layout
    layout.addWidget(boton)

    # Añadir espaciador derecho
    layout.addStretch()

    return contenedor, boton
