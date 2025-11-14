#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el sistema de timeout con advertencia y cierre automático.
NOTA: Este script usa tiempos reducidos para facilitar las pruebas.
"""
import sys
import io
from pathlib import Path

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from src.core.idle_manager import IdleManager

print("=" * 60)
print("TEST DE SISTEMA DE TIMEOUT")
print("=" * 60)
print("Tiempos de prueba:")
print("  - Advertencia: 10 segundos")
print("  - Timeout: 20 segundos")
print("=" * 60)

app = QApplication(sys.argv)

# Crear ventana de login simulada
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 150)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ventana de Login"))

# Crear ventana principal simulada
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menú Principal")
        self.setGeometry(450, 100, 400, 300)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("Ventana Principal"))
        layout.addWidget(QLabel("\nMantén el ratón QUIETO durante 20 segundos"))
        layout.addWidget(QLabel("para probar el timeout automático."))
        layout.addWidget(QLabel("\n⏱️ Advertencia a los 10 segundos"))
        layout.addWidget(QLabel("⏱️ Cierre automático a los 20 segundos"))

# Crear ventanas
login = LoginWindow()
main = MainWindow()

# Crear gestor de inactividad con tiempos de prueba reducidos
idle_manager = IdleManager(timeout_minutes=20/60, warning_minutes=10/60)  # 20 y 10 segundos

# Iniciar sistema
idle_manager.start(login, main)

# Mostrar solo la ventana principal
main.show()

print("\n🚀 Aplicación iniciada")
print("\nPrueba 1: Deja el ratón quieto durante 10 segundos")
print("  → Debería aparecer advertencia de 'quedan 5 minutos'")
print("\nPrueba 2: NO hagas clic en OK, espera otros 10 segundos")
print("  → El diálogo de advertencia debería cerrarse automáticamente")
print("  → Todas las ventanas deberían cerrarse")
print("  → Debería aparecer mensaje 'Sesión Cerrada'")
print("  → Debería volver a la ventana de login")
print("\n" + "=" * 60)

sys.exit(app.exec())
