from __future__ import annotations
from PySide6.QtWidgets import QStyledItemDelegate, QPushButton
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import QObject, QEvent

class NumericDelegate(QStyledItemDelegate):
    def __init__(self, decimals: int = 2, allow_zero: bool = True, parent=None):
        super().__init__(parent)
        self.decimals = decimals
        self.allow_zero = allow_zero

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if hasattr(editor, "setValidator"):
            v = QDoubleValidator(parent)
            v.setDecimals(self.decimals)
            v.setNotation(QDoubleValidator.StandardNotation)
            v.setBottom(0.0 if self.allow_zero else 0.0000001)
            editor.setValidator(v)
        return editor

class ActivityWatcher(QObject):
    """Detecta actividad global (ratón/teclado) para reiniciar el temporizador de inactividad."""
    def __init__(self, on_activity):
        super().__init__()
        self.on_activity = on_activity

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress):
            self.on_activity()
        return False

class BackButton(QPushButton):
    """Botón estandarizado de 'Atrás' con texto/emoji; úsalo en todas las ventanas hijas."""
    def __init__(self, parent=None, text="⟵ Volver"):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
