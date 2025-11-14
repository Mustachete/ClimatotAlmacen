#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la UI del informe de furgonetas
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from src.ventanas.consultas.ventana_informe_furgonetas import VentanaInformeFurgonetas

print("=" * 60)
print("TEST DE UI DEL INFORME")
print("=" * 60)

app = QApplication(sys.argv)

ventana = VentanaInformeFurgonetas()

# Simular la selección de una furgoneta
# Asumiendo que la furgoneta ID 2 está en el índice 1 del combo (índice 0 es "Selecciona...")
if ventana.cmb_furgoneta.count() > 1:
    ventana.cmb_furgoneta.setCurrentIndex(1)
    print(f"Furgoneta seleccionada: {ventana.cmb_furgoneta.currentText()}")
    print(f"Furgoneta ID: {ventana.cmb_furgoneta.currentData()}")

# Ajustar la fecha a la semana pasada (donde sabemos que hay datos)
hoy = datetime.now()
lunes_actual = hoy - timedelta(days=hoy.weekday())
lunes_pasado = lunes_actual - timedelta(days=7)

from PySide6.QtCore import QDate
fecha_qt = QDate(lunes_pasado.year, lunes_pasado.month, lunes_pasado.day)
ventana.date_semana.setDate(fecha_qt)
print(f"Fecha seleccionada: {ventana.date_semana.date().toString('yyyy-MM-dd')}")

# Simular el clic en "Generar Informe"
print("\nGenerando informe...")
ventana.generar_informe()

# Verificar si se generaron datos
if ventana.datos_informe:
    print(f"\n✅ Datos generados:")
    print(f"   Artículos: {len(ventana.datos_informe['articulos'])}")
    print(f"   Operarios: {', '.join(ventana.datos_informe['operarios'])}")

    # Verificar tabla
    print(f"\n   Tabla:")
    print(f"   Filas: {ventana.tabla_preview.rowCount()}")
    print(f"   Columnas: {ventana.tabla_preview.columnCount()}")

    if ventana.tabla_preview.rowCount() > 0:
        print("\n   Primera fila:")
        for col in range(min(5, ventana.tabla_preview.columnCount())):
            item = ventana.tabla_preview.item(0, col)
            if item:
                print(f"      Col {col}: {item.text()}")
    else:
        print("\n   ⚠️  LA TABLA ESTÁ VACÍA (0 filas)")
else:
    print("\n❌ No se generaron datos")

# Mostrar ventana
ventana.show()
print("\nVentana mostrada. Revisa visualmente.")
print("=" * 60)

sys.exit(app.exec())
