# db_utils.py - Utilidades de Base de Datos
from __future__ import annotations
import sqlite3
from pathlib import Path

# Ruta de la base de datos
BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "db" / "almacen.db"
LOG_PATH = BASE / "logs" / "log.txt"

def log_err(msg: str):
    """Registra errores en el archivo de log"""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            import time
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass

def db():
    """Devuelve conexión SQLite con WAL habilitado."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("PRAGMA foreign_keys=ON;")
        return con
    except Exception as e:
        log_err(f"DB open error: {e} | DB_PATH={DB_PATH}")
        raise

def ensure_schema_and_views():
    """
    Crea/actualiza las vistas de stock.
    Esta función ya NO es necesaria porque las vistas se crean en schema.sql,
    pero la dejamos por compatibilidad.
    """
    try:
        con = db()
        cur = con.cursor()
        
        # Recrear vistas de stock
        cur.executescript("""
        DROP VIEW IF EXISTS vw_stock;
        CREATE VIEW vw_stock AS
          SELECT destino_id AS almacen_id, articulo_id, SUM(cantidad) AS delta
          FROM movimientos
          WHERE tipo IN ('ENTRADA','TRASPASO')
          GROUP BY destino_id, articulo_id
          UNION ALL
          SELECT origen_id AS almacen_id, articulo_id, SUM(-cantidad) AS delta
          FROM movimientos
          WHERE tipo IN ('IMPUTACION','PERDIDA','DEVOLUCION','TRASPASO')
            AND origen_id IS NOT NULL
          GROUP BY origen_id, articulo_id;

        DROP VIEW IF EXISTS vw_stock_total;
        CREATE VIEW vw_stock_total AS
          SELECT articulo_id, SUM(delta) AS stock_total
          FROM vw_stock
          GROUP BY articulo_id;
        """)
        
        con.commit()
        con.close()
    except Exception as e:
        log_err(f"ensure_schema_and_views(): {e}")