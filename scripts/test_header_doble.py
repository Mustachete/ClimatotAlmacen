#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el nuevo header de dos niveles
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from src.ventanas.consultas.ventana_informe_furgonetas import VentanaInformeFurgonetas

print("=" * 60)
print("TEST DE HEADER DE DOS NIVELES")
print("=" * 60)

app = QApplication(sys.argv)

ventana = VentanaInformeFurgonetas()

# Simular la selección de una furgoneta
if ventana.cmb_furgoneta.count() > 1:
    ventana.cmb_furgoneta.setCurrentIndex(1)
    print(f"Furgoneta seleccionada: {ventana.cmb_furgoneta.currentText()}")

# Ajustar la fecha a la semana pasada
hoy = datetime.now()
lunes_actual = hoy - timedelta(days=hoy.weekday())
lunes_pasado = lunes_actual - timedelta(days=7)

fecha_qt = QDate(lunes_pasado.year, lunes_pasado.month, lunes_pasado.day)
ventana.date_semana.setDate(fecha_qt)
print(f"Fecha seleccionada: {ventana.date_semana.date().toString('yyyy-MM-dd')}")

# Generar informe
print("\nGenerando informe...")
ventana.generar_informe()

# Mostrar ventana
ventana.show()
print("\nVentana mostrada con header de dos niveles.")
print("Verifica que:")
print("  1. La fecha aparece UNA sola vez abarcando E, D, G")
print("  2. Las letras E, D, G aparecen debajo de cada fecha")
print("  3. El título dice 'Informe Semanal de Consumo - Furgoneta XX'")
print("=" * 60)

sys.exit(app.exec())
