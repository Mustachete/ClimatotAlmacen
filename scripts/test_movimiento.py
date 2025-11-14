#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import execute_query

try:
    result = execute_query(
        "INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id) VALUES (?, 'SALIDA', ?, ?, ?, ?, ?)",
        ('2024-10-28', 6, 5.0, 1, 2, 1)
    )
    print(f"OK - Insert funciona. ID: {result}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
