# config_utils.py - Utilidades de Configuración
from __future__ import annotations
import sys
import time
import hashlib
import datetime
import shutil
import configparser
from pathlib import Path

# ---------- RUTAS ----------
def guess_base_dir() -> Path:
    """Detecta la carpeta base del proyecto"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Si está compilado con PyInstaller
        base = Path(sys.executable).resolve().parent
    else:
        # Si está en desarrollo
        base = Path(__file__).resolve().parent
    
    # Verificar que existen las carpetas esperadas
    if not ((base / "config").exists() or (base / "db").exists()):
        cand = base.parent
        if (cand / "config").exists() or (cand / "db").exists():
            return cand
    return base

BASE_DIR = guess_base_dir()
DB_PATH = BASE_DIR / "db" / "almacen.db"
LOG_PATH = BASE_DIR / "logs" / "log.txt"
INI_PATH = BASE_DIR / "config" / "app.ini"
LOCK_PATH = BASE_DIR / "app.lock"
EXPORT_DIR = BASE_DIR / "exports"
BACKUP_DIR = BASE_DIR / "backups"

# ---------- LOG ----------
def log_err(msg: str):
    """Registra errores en el log"""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass

# ---------- CONFIG .INI ----------
cfg = configparser.ConfigParser()
try:
    cfg.read(INI_PATH, encoding="utf-8")
except Exception:
    pass

HEARTBEAT_S = cfg.getint("app", "heartbeat_seconds", fallback=15)
SESSION_EXPIRE_S = cfg.getint("app", "session_expire_seconds", fallback=120)
IDLE_MIN = cfg.getint("app", "idle_timeout_minutes", fallback=20)
EXCLUSIVE = cfg.getboolean("app", "exclusive_mode", fallback=False)

# ---------- UTILS ----------
def today_str():
    """Devuelve la fecha actual en formato YYYY-MM-DD"""
    return datetime.date.today().strftime("%Y-%m-%d")

def parse_date(s: str) -> bool:
    """Valida si una cadena es una fecha válida y no es futura"""
    try:
        d = datetime.datetime.strptime(s, "%Y-%m-%d").date()
        return d <= datetime.date.today()
    except Exception:
        return False

def hash_pwd(p: str) -> str:
    """Genera hash SHA256 de una contraseña"""
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

def timestamp_str():
    """Devuelve timestamp actual para nombres de archivo"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_db(keep_last: int = 10):
    """Crea backup de la base de datos"""
    try:
        if not DB_PATH.exists():
            return
        
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = BACKUP_DIR / f"almacen_{ts}.db"
        shutil.copy2(DB_PATH, dst)
        
        # Limpiar backups antiguos
        files = sorted(BACKUP_DIR.glob("almacen_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[keep_last:]:
            try:
                f.unlink()
            except Exception:
                pass
    except Exception as e:
        log_err(f"backup_db(): {e}")

# ---------- FILE LOCK (solo Windows) ----------
try:
    import msvcrt
    
    class FileLock:
        def __init__(self, path: Path):
            self.path = path
            self._fh = None

        def acquire(self, info_text: str) -> bool:
            try:
                self._fh = open(self.path, 'a+')
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
                self._fh.seek(0)
                self._fh.truncate(0)
                self._fh.write(info_text)
                self._fh.flush()
                return True
            except (OSError, IOError):
                return False

        def read_holder(self) -> str:
            try:
                with open(self.path, 'r') as f:
                    return f.read().strip()
            except Exception:
                return ""

        def release(self):
            try:
                if self._fh:
                    try:
                        msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
                    except (OSError, IOError):
                        pass
                    self._fh.close()
                self._fh = None
            except Exception:
                pass
                
except ImportError:
    # Si no está en Windows, FileLock no estará disponible
    class FileLock:
        def __init__(self, path: Path):
            pass
        def acquire(self, info_text: str) -> bool:
            return True
        def read_holder(self) -> str:
            return ""
        def release(self):
            pass