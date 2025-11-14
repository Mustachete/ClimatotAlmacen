#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para limpiar TODOs obsoletos del código"""

import re
import sys
import io
from pathlib import Path

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Patrón a buscar y reemplazar (más flexible)
PATRON = r'  # TODO: obtener usuario real de sesión'
REEMPLAZO = r''

archivos_modificados = []
total_reemplazos = 0

# Buscar en src/
for archivo in Path('src').rglob('*.py'):
    contenido_original = archivo.read_text(encoding='utf-8')
    contenido_nuevo, num_reemplazos = re.subn(PATRON, REEMPLAZO, contenido_original)

    if num_reemplazos > 0:
        archivo.write_text(contenido_nuevo, encoding='utf-8')
        archivos_modificados.append((str(archivo), num_reemplazos))
        total_reemplazos += num_reemplazos

# Mostrar resultados
print("=" * 60)
print("LIMPIEZA DE TODOs OBSOLETOS")
print("=" * 60)
print()

if archivos_modificados:
    print(f"✅ {len(archivos_modificados)} archivos modificados:")
    for archivo, num in archivos_modificados:
        print(f"   - {archivo}: {num} reemplazo(s)")
    print()
    print(f"📊 Total de TODOs eliminados: {total_reemplazos}")
else:
    print("ℹ️  No se encontraron TODOs para limpiar")

print()
print("=" * 60)
