# ========================================
# DB UTILS — GESTIÓN DE BASE DE DATOS POSTGRESQL
# ========================================
import sys
import hashlib
import configparser
from pathlib import Path
from typing import List, Dict, Any, Optional

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
# CONFIGURACIÓN DE POSTGRESQL
# ----------------------------------------
config = configparser.ConfigParser()
config_path = PROJECT_ROOT / "config.ini"

if not config_path.exists():
    raise FileNotFoundError(
        f"No se encontró config.ini en {config_path}\n"
        "Debe existir para configurar la conexión PostgreSQL"
    )

config.read(config_path)

LOG_PATH = PROJECT_ROOT / "logs" / "app.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------
# POOL DE CONEXIONES POSTGRESQL
# ----------------------------------------
try:
    import psycopg2
    import psycopg2.pool
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    print(f"[DB] ERROR: psycopg2 no está instalado. Ejecuta: pip install psycopg2-binary")
    print(f"[DB] Detalles: {e}")
    sys.exit(1)

# Pool de conexiones global
_connection_pool = None

def _init_pool():
    """Inicializa el pool de conexiones PostgreSQL"""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=2,
                maxconn=20,
                host=config.get('database', 'HOST', fallback='localhost'),
                port=config.getint('database', 'PORT', fallback=5432),
                database=config.get('database', 'NAME', fallback='climatot_almacen'),
                user=config.get('database', 'USER', fallback='climatot'),
                password=config.get('database', 'PASSWORD', fallback='')
            )
            print(f"[DB] Pool de conexiones PostgreSQL inicializado (host: {config.get('database', 'HOST')})")
        except Exception as e:
            print(f"[DB] ERROR al inicializar pool PostgreSQL: {e}")
            raise

def get_connection():
    """
    Obtiene una conexión del pool PostgreSQL.
    IMPORTANTE: Debe liberarse con release_connection()
    """
    global _connection_pool
    if _connection_pool is None:
        _init_pool()
    try:
        conn = _connection_pool.getconn()
        return conn
    except Exception as e:
        log_error(f"Error al obtener conexión del pool: {e}")
        raise

def release_connection(conn):
    """Devuelve una conexión al pool"""
    if _connection_pool and conn:
        _connection_pool.putconn(conn)

def close_all_connections():
    """Cierra todas las conexiones del pool"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None

# ----------------------------------------
# ALIAS DE COMPATIBILIDAD
# ----------------------------------------
def get_con():
    """Alias de compatibilidad para código antiguo"""
    return get_connection()

# ----------------------------------------
# FUNCIONES DE CONSULTA
# ----------------------------------------
def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SELECT y devuelve todas las filas como lista de diccionarios.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_error(f"Error ejecutando fetch_all: {e}\n{query}\nParams: {params}")
        raise
    finally:
        release_connection(conn)


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Ejecuta una consulta SELECT y devuelve una sola fila (o None).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_error(f"Error ejecutando fetch_one: {e}\n{query}\nParams: {params}")
        raise
    finally:
        release_connection(conn)


def execute_query(query: str, params: tuple = ()) -> int:
    """
    Ejecuta una consulta de escritura (INSERT, UPDATE, DELETE)
    y confirma automáticamente.

    Returns:
        Para INSERT con RETURNING: el ID del registro insertado
        Para UPDATE/DELETE: número de filas afectadas
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()

            # PostgreSQL: Si es INSERT con RETURNING, obtener el ID
            if query.strip().upper().startswith('INSERT'):
                try:
                    result = cur.fetchone()
                    if result:
                        return result[0]
                except:
                    pass
                return 0
            else:
                # UPDATE/DELETE: devolver rowcount
                return cur.rowcount
    except Exception as e:
        conn.rollback()
        log_error(f"Error ejecutando query: {e}\n{query}\nParams: {params}")
        raise
    finally:
        release_connection(conn)


# Alias de compatibilidad
fetchall = fetch_all
fetchone = fetch_one
exec_query = execute_query

# ----------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS
# ----------------------------------------
def init_db_if_missing(schema_file: str = "schema_postgres.sql") -> None:
    """
    Crea la base de datos PostgreSQL si no existe, aplicando el esquema.

    Args:
        schema_file: Nombre del archivo de schema (por defecto: schema_postgres.sql)
    """
    # Verificar si hay tablas
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            table_count = cur.fetchone()[0]
        release_connection(conn)

        if table_count > 0:
            print(f"[DB] Base de datos PostgreSQL ya tiene {table_count} tablas")
            return
    except Exception as e:
        print(f"[DB] Error al verificar tablas PostgreSQL: {e}")
        return

    # Inicializar con schema_postgres.sql
    schema_path = PROJECT_ROOT / "db" / schema_file

    if not schema_path.exists():
        raise FileNotFoundError(f"No se encontró el esquema: {schema_path}")

    print(f"[DB] Inicializando PostgreSQL con {schema_file}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
        print("[DB] Base de datos PostgreSQL inicializada correctamente")
    except Exception as e:
        conn.rollback()
        print(f"[DB] Error al inicializar PostgreSQL: {e}")
        raise
    finally:
        release_connection(conn)


# ----------------------------------------
# LOGGING BÁSICO
# ----------------------------------------
def log_error(message: str) -> None:
    """
    Registra errores o eventos en /logs/app.log
    """
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [ERROR] {message}\n")
    except Exception:
        pass  # evitar bucles si hay fallo en logging


# ----------------------------------------
# UTILIDAD DE HASH DE CONTRASEÑAS
# ----------------------------------------
def hash_pwd(password: str) -> str:
    """
    Devuelve el hash SHA256 en formato hexadecimal de la contraseña indicada.
    Uso: hash_pwd("mi_clave") -> '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd...'
    """
    if password is None:
        return ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ----------------------------------------
# TEST MANUAL
# ----------------------------------------
if __name__ == "__main__":
    print(f"Motor BD: PostgreSQL")
    print(f"Host: {config.get('database', 'HOST')}")
    print(f"Base de datos: {config.get('database', 'NAME')}")
    print(f"Ruta LOG: {LOG_PATH}")

    try:
        conn = get_connection()
        print("✅ Conexión abierta correctamente.")
        release_connection(conn)
        close_all_connections()
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
