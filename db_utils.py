# db_utils.py - Utilidades centralizadas para Base de Datos
from __future__ import annotations
import sqlite3
import hashlib
import time
import datetime
from pathlib import Path

# ========================================
# RUTAS Y CONFIGURACIÓN
# ========================================
BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "db" / "almacen.db"
LOG_PATH = BASE / "logs" / "log.txt"

# ========================================
# FUNCIONES DE BASE DE DATOS
# ========================================
def get_con():
    """
    Devuelve conexión SQLite con configuraciones optimizadas.
    
    Equivalente en VBA:
        Set conn = New ADODB.Connection
        conn.Open "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=..."
    """
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("PRAGMA foreign_keys=ON;")
        return con
    except Exception as e:
        log_err(f"Error al abrir BD: {e} | Ruta: {DB_PATH}")
        raise

# ========================================
# FUNCIONES DE LOG
# ========================================
def log_err(msg: str):
    r"""
    Registra errores en el archivo de log.
    
    Equivalente en VBA:
        Open "C:\log.txt" For Append As #1
        Print #1, Now & " - " & mensaje
        Close #1
    """
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
            f.write(f"{timestamp} {msg}\n")
    except Exception:
        pass  # Si falla el log, no queremos que pare el programa

# ========================================
# FUNCIONES DE UTILIDAD
# ========================================
def hash_pwd(password: str) -> str:
    """
    Genera hash SHA256 de una contraseña.
    Nunca guardamos contraseñas en texto plano por seguridad.
    
    Equivalente en VBA:
        ' No hay equivalente directo, necesitarías una DLL externa
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def today_str() -> str:
    """
    Devuelve la fecha actual en formato YYYY-MM-DD.
    
    Equivalente en VBA:
        Format(Date, "yyyy-mm-dd")
    """
    return datetime.date.today().strftime("%Y-%m-%d")

def parse_date(fecha_str: str) -> bool:
    """
    Valida si una cadena es una fecha válida y no es futura.
    
    Equivalente en VBA:
        If IsDate(texto) And CDate(texto) <= Date Then
            parse_date = True
        End If
    """
    try:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        return fecha <= datetime.date.today()
    except Exception:
        return False

def timestamp_str() -> str:
    """
    Devuelve timestamp para nombres de archivos.
    Ejemplo: 20250125_143022
    
    Equivalente en VBA:
        Format(Now, "yyyymmdd_hhnnss")
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# ========================================
# FUNCIONES DE VALIDACIÓN
# ========================================
def validar_stock_disponible(articulo_id: int, almacen_id: int, cantidad: float) -> bool:
    """
    Verifica si hay stock suficiente antes de hacer un movimiento.
    Devuelve True si hay stock, False si no hay.
    
    Equivalente en VBA:
        Function HayStock(art As Long, alm As Long, cant As Double) As Boolean
            Dim rs As Recordset
            Set rs = conn.Execute("SELECT SUM(cantidad) FROM movimientos WHERE...")
            HayStock = (rs(0) >= cant)
        End Function
    """
    try:
        con = get_con()
        cur = con.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(delta), 0)
            FROM vw_stock
            WHERE articulo_id = ? AND almacen_id = ?
        """, (articulo_id, almacen_id))
        stock_actual = cur.fetchone()[0]
        con.close()
        return stock_actual >= cantidad
    except Exception as e:
        log_err(f"Error al validar stock: {e}")
        return False

def obtener_stock_articulo(articulo_id: int, almacen_id: int = None) -> float:
    """
    Obtiene el stock actual de un artículo.
    Si se especifica almacen_id, devuelve el stock de ese almacén.
    Si no, devuelve el stock total.
    
    Equivalente en VBA:
        Function StockArticulo(art As Long, Optional alm As Long) As Double
            ...
        End Function
    """
    try:
        con = get_con()
        cur = con.cursor()
        
        if almacen_id:
            cur.execute("""
                SELECT COALESCE(SUM(delta), 0)
                FROM vw_stock
                WHERE articulo_id = ? AND almacen_id = ?
            """, (articulo_id, almacen_id))
        else:
            cur.execute("""
                SELECT COALESCE(stock_total, 0)
                FROM vw_stock_total
                WHERE articulo_id = ?
            """, (articulo_id,))
        
        stock = cur.fetchone()[0]
        con.close()
        return stock
    except Exception as e:
        log_err(f"Error al obtener stock: {e}")
        return 0.0

# ========================================
# FUNCIONES DE CONSULTA RÁPIDA
# ========================================
def buscar_articulo_por_ean(ean: str):
    """
    Busca un artículo por su código EAN (código de barras).
    Devuelve None si no existe.
    
    Equivalente en VBA:
        Function BuscarPorEAN(codigo As String) As Recordset
            Set BuscarPorEAN = conn.Execute("SELECT * FROM articulos WHERE ean='" & codigo & "'")
        End Function
    """
    try:
        con = get_con()
        cur = con.cursor()
        cur.execute("SELECT * FROM articulos WHERE ean = ? AND activo = 1", (ean,))
        resultado = cur.fetchone()
        con.close()
        return resultado
    except Exception as e:
        log_err(f"Error al buscar por EAN: {e}")
        return None

def obtener_nombre_almacen(almacen_id: int) -> str:
    """
    Obtiene el nombre de un almacén por su ID.
    
    Equivalente en VBA:
        Function NombreAlmacen(id As Long) As String
            NombreAlmacen = DLookup("nombre", "almacenes", "id=" & id)
        End Function
    """
    try:
        con = get_con()
        cur = con.cursor()
        cur.execute("SELECT nombre FROM almacenes WHERE id = ?", (almacen_id,))
        resultado = cur.fetchone()
        con.close()
        return resultado[0] if resultado else "Desconocido"
    except Exception as e:
        log_err(f"Error al obtener nombre de almacén: {e}")
        return "Desconocido"

def obtener_nombre_articulo(articulo_id: int) -> str:
    """
    Obtiene el nombre de un artículo por su ID.
    
    Equivalente en VBA:
        Function NombreArticulo(id As Long) As String
            NombreArticulo = DLookup("nombre", "articulos", "id=" & id)
        End Function
    """
    try:
        con = get_con()
        cur = con.cursor()
        cur.execute("SELECT nombre FROM articulos WHERE id = ?", (articulo_id,))
        resultado = cur.fetchone()
        con.close()
        return resultado[0] if resultado else "Desconocido"
    except Exception as e:
        log_err(f"Error al obtener nombre de artículo: {e}")
        return "Desconocido"

# ========================================
# FUNCIÓN DE VERIFICACIÓN DE BD
# ========================================
def verificar_bd() -> bool:
    """
    Verifica que la base de datos existe y es accesible.
    
    Equivalente en VBA:
        Function ExisteBD() As Boolean
            ExisteBD = (Dir("C:\almacen.db") <> "")
        End Function
    """
    if not DB_PATH.exists():
        return False
    
    try:
        con = get_con()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios")
        con.close()
        return True
    except Exception:
        return False
