# widgets_personalizados.py - Widgets personalizados de Climatot
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QPushButton, QWidget, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator

class SpinBoxClimatot(QWidget):
    """SpinBox personalizado con botones + y - visibles"""
    
    valueChanged = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 1.0
        self._minimum = 0.01
        self._maximum = 999999.0
        self._decimals = 2
        self._single_step = 1.0
        self._prefix = ""
        self._suffix = ""
        
        # Layout horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Campo de texto
        self.line_edit = QLineEdit()
        self.line_edit.setText(f"{self._value:.{self._decimals}f}")
        self.line_edit.setAlignment(Qt.AlignRight)
        self.line_edit.editingFinished.connect(self._on_text_changed)
        
        # Validador
        validator = QDoubleValidator(self._minimum, self._maximum, self._decimals)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_edit.setValidator(validator)
        
        # Botón -
        self.btn_down = QPushButton("−")
        self.btn_down.setFixedSize(24, 20)
        self.btn_down.clicked.connect(self._decrement)
        self.btn_down.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 0;
                border: 1px solid #e2e8f0;
                border-radius: 3px;
                background-color: white;
                color: #1e3a8a;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)
        
        # Botón +
        self.btn_up = QPushButton("+")
        self.btn_up.setFixedSize(24, 20)
        self.btn_up.clicked.connect(self._increment)
        self.btn_up.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 0;
                border: 1px solid #e2e8f0;
                border-radius: 3px;
                background-color: white;
                color: #1e3a8a;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)
        
        # Añadir al layout
        layout.addWidget(self.line_edit)
        layout.addWidget(self.btn_down)
        layout.addWidget(self.btn_up)
        
        # Estilo del campo
        self.line_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                background-color: white;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 2px solid #1e3a8a;
            }
        """)
    
    def value(self):
        """Obtiene el valor actual"""
        return self._value
    
    def setValue(self, val):
        """Establece el valor"""
        val = max(self._minimum, min(self._maximum, float(val)))
        self._value = val
        self.line_edit.setText(f"{self._prefix}{val:.{self._decimals}f}{self._suffix}")
        self.valueChanged.emit(val)
    
    def setRange(self, minimum, maximum):
        """Establece el rango"""
        self._minimum = minimum
        self._maximum = maximum
        validator = QDoubleValidator(minimum, maximum, self._decimals)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_edit.setValidator(validator)
    
    def setDecimals(self, decimals):
        """Establece los decimales"""
        self._decimals = decimals
        self.setValue(self._value)
    
    def setSingleStep(self, step):
        """Establece el incremento"""
        self._single_step = step
    
    def setPrefix(self, prefix):
        """Establece el prefijo"""
        self._prefix = prefix
        self.setValue(self._value)
    
    def setSuffix(self, suffix):
        """Establece el sufijo"""
        self._suffix = suffix
        self.setValue(self._value)
    
    def setMinimumWidth(self, width):
        """Establece ancho mínimo"""
        self.line_edit.setMinimumWidth(width - 48)
    
    def _increment(self):
        """Incrementa el valor"""
        new_val = self._value + self._single_step
        self.setValue(new_val)
    
    def _decrement(self):
        """Decrementa el valor"""
        new_val = self._value - self._single_step
        self.setValue(new_val)
    
    def _on_text_changed(self):
        """Cuando el usuario edita el texto"""
        try:
            # Quitar prefijo y sufijo
            text = self.line_edit.text().replace(self._prefix, "").replace(self._suffix, "").strip()
            val = float(text)
            self.setValue(val)
        except:
            # Si hay error, restaurar valor anterior
            self.setValue(self._value)