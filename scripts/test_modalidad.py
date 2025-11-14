#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el comportamiento modal de las ventanas.
Verifica que las ventanas hijas bloquean a las ventanas padre.
"""
import sys
import io
from pathlib import Path

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

print("=" * 70)
print("TEST DE MODALIDAD DE VENTANAS")
print("=" * 70)
print("\nInstrucciones de prueba:")
print("  1. Se abrirá una ventana 'Principal'")
print("  2. Haz clic en 'Abrir Hija'")
print("  3. Se abrirá una ventana 'Hija' modal")
print("  4. Intenta hacer clic en la ventana 'Principal'")
print("  5. ✅ CORRECTO: La ventana Principal debe estar bloqueada")
print("  6. ✅ CORRECTO: La ventana Hija debe 'parpadear' o destacarse")
print("  7. Cierra la ventana Hija")
print("  8. ✅ CORRECTO: Ahora puedes usar la ventana Principal de nuevo")
print("=" * 70 + "\n")

app = QApplication(sys.argv)

class VentanaHija(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔹 Ventana Hija (Modal)")
        self.setGeometry(600, 200, 400, 300)

        layout = QVBoxLayout(self)

        titulo = QLabel("🔹 Ventana Hija")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        info = QLabel(
            "\nEsta ventana es MODAL.\n\n"
            "Mientras esté abierta, la ventana principal\n"
            "debe estar bloqueada.\n\n"
            "Intenta hacer clic en la ventana principal.\n"
            "Deberías ver que esta ventana 'parpadea'\n"
            "o se destaca para avisarte que debes cerrarla."
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 12px; padding: 20px;")
        layout.addWidget(info)

        btn_cerrar = QPushButton("❌ Cerrar Ventana Hija")
        btn_cerrar.setMinimumHeight(50)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar)

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 Ventana Principal")
        self.setGeometry(150, 200, 400, 300)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        titulo = QLabel("📋 Ventana Principal")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        info = QLabel(
            "\nHaz clic en el botón para abrir\n"
            "una ventana hija modal."
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 12px; padding: 20px;")
        layout.addWidget(info)

        btn_abrir = QPushButton("🔹 Abrir Ventana Hija")
        btn_abrir.setMinimumHeight(50)
        btn_abrir.clicked.connect(self.abrir_hija)
        layout.addWidget(btn_abrir)

        layout.addStretch()

        status = QLabel(
            "Tip: Cuando la ventana hija esté abierta,\n"
            "intenta hacer clic aquí. Esta ventana debe estar bloqueada."
        )
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet("font-size: 10px; color: gray; padding: 10px;")
        layout.addWidget(status)

    def abrir_hija(self):
        """Abrir ventana hija modal"""
        self.ventana_hija = VentanaHija(parent=self)
        self.ventana_hija.setWindowModality(Qt.WindowModal)
        self.ventana_hija.show()
        print("\n✅ Ventana hija abierta con modalidad Qt.WindowModal")
        print("   → La ventana principal debe estar bloqueada")
        print("   → Intenta hacer clic en la ventana principal")

# Crear y mostrar ventana principal
ventana = VentanaPrincipal()
ventana.show()

print("\n🚀 Test iniciado - Sigue las instrucciones en la ventana\n")

sys.exit(app.exec())
