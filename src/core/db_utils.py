# ========================================
# DB UTILS — GESTIÓN DE BASE DE DATOS SQLite
# ========================================
import sqlite3
from pathlib import Path
import os
import sys

# ----------------------------------------
# DETECCIÓN DE LA RAÍZ DEL PROYECTO
# ----------------------------------------
_THIS = Path(__file__).resolve()

def _find_project_root(start: Path) -> Path:
    """
    Busca hacia arriba una carpeta que contenga las carpetas 'db' y 'config'.
    Si no las encuentra, sube dos niveles como fallback.
    """
    for cand in [start, *start.parents]:
        if (cand / "db").is_dir() and (cand / "config").is_dir():
            return cand
    return start.parents[2]

PROJECT_ROOT = _find_project_root(_THIS)

# ----------------------------------------
# RUTAS DE LA BASE DE DATOS Y LOGS
# ----------------------------------------
env_db = os.getenv("CLIMATOT_DB_PATH")
DB_PATH = Path(env_db).resolve() if env_db else PROJECT_ROOT / "db" / "almacen.db"

LOG_PATH = PROJECT_ROOT / "logs" / "app.log"

# Crear carpetas si no existen
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------
# FUNCIONES DE CONEXIÓN Y UTILIDAD
# ----------------------------------------
def get_connection() -> sqlite3.Connection:
    """
    Abre una conexión con la base de datos SQLite del proyecto.
    Activa foreign_keys y row_factory para acceso tipo diccionario.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_con():
    """Compat: antes se importaba get_con; delega en get_connection()."""
    return get_connection()

def fetchall(query: str, params: tuple = ()):
    return fetch_all(query, params)

def fetchone(query: str, params: tuple = ()):
    return fetch_one(query, params)

def exec_query(query: str, params: tuple = ()):
    return execute_query(query, params)

def execute_query(query: str, params: tuple = ()) -> None:
    """
    Ejecuta una consulta de escritura (INSERT, UPDATE, DELETE)
    y confirma automáticamente.
    """
    try:
        with get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
    except Exception as e:
        log_error(f"Error ejecutando query: {e}\n{query}")
        raise


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """
    Ejecuta una consulta SELECT y devuelve todas las filas como lista de diccionarios.
    """
    try:
        with get_connection() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_error(f"Error ejecutando fetch_all: {e}\n{query}")
        raise


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """
    Ejecuta una consulta SELECT y devuelve una sola fila (o None).
    """
    try:
        with get_connection() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_error(f"Error ejecutando fetch_one: {e}\n{query}")
        raise


def init_db_if_missing(schema_file: str = "schema.sql") -> None:
    """
    Crea la base de datos si no existe, aplicando el esquema desde /db/schema.sql.
    """
    if not DB_PATH.exists():
        print(f"[DB] Creando nueva base de datos en {DB_PATH}")
        schema_path = PROJECT_ROOT / "db" / schema_file
        if not schema_path.exists():
            raise FileNotFoundError(f"No se encontró el esquema: {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with get_connection() as conn:
            conn.executescript(schema_sql)
        print("[DB] Base de datos inicializada correctamente.")


# ----------------------------------------
# LOGGING BÁSICO
# ----------------------------------------
def log_error(message: str) -> None:
    """
    Registra errores o eventos en /logs/app.log
    """
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {message}\n")
    except Exception:
        pass  # evitar bucles si hay fallo en logging


# ----------------------------------------
# TEST MANUAL
# ----------------------------------------
if __name__ == "__main__":
    print(f"Ruta DB: {DB_PATH}")
    print(f"Existe: {DB_PATH.exists()}")
    print(f"Ruta LOG: {LOG_PATH}")
    try:
        conn = get_connection()
        print("Conexión abierta correctamente.")
        conn.close()
    except Exception as e:
        print(f"Error al conectar: {e}")

# ----------------------------------------
# UTILIDAD DE HASH DE CONTRASEÑAS
# ----------------------------------------
import hashlib

def hash_pwd(password: str) -> str:
    """
    Devuelve el hash SHA256 en formato hexadecimal de la contraseña indicada.
    Uso: hash_pwd("mi_clave") -> '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd...'
    """
    if password is None:
        return ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


