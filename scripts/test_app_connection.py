#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rápido de la conexión de la aplicación
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.db_utils import get_connection, fetch_all, release_connection

print(f"Motor configurado: PostgreSQL")
print(f"Probando conexión...")

conn = get_connection()
print("Conexión establecida!")

# Test básico
usuarios = fetch_all('SELECT * FROM usuarios')
print(f"\nUsuarios encontrados: {len(usuarios)}")
for u in usuarios:
    print(f"  - {u['usuario']} (rol: {u['rol']}, activo: {u['activo']})")

articulos = fetch_all('SELECT COUNT(*) as total FROM articulos WHERE activo = 1')
print(f"\nArtículos activos: {articulos[0]['total']}")

movimientos = fetch_all('SELECT COUNT(*) as total FROM movimientos')
print(f"Movimientos registrados: {movimientos[0]['total']}")

release_connection(conn)
print("\n¡TODO FUNCIONA CORRECTAMENTE!")
