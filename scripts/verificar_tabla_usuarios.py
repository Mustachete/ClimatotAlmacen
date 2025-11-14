#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura de la tabla usuarios
"""

import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con

def verificar_tabla():
    con = get_con()
    cur = con.cursor()

    # Ver estructura de la tabla
    cur.execute("PRAGMA table_info(usuarios)")
    columnas = cur.fetchall()

    print("📋 Estructura de la tabla 'usuarios':")
    print("-" * 80)
    for col in columnas:
        print(f"  {col[1]:20} {col[2]:15} {'PRIMARY KEY' if col[5] else ''}")

    print("\n" + "=" * 80)

    # Ver datos
    cur.execute("SELECT * FROM usuarios LIMIT 3")
    usuarios = cur.fetchall()

    print(f"\n👥 Usuarios encontrados: {len(usuarios)}")
    for user in usuarios:
        print(f"  - {user}")

    con.close()

if __name__ == "__main__":
    verificar_tabla()
