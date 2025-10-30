"""
Sistema de Backups Automáticos de Base de Datos
Crea copias de seguridad comprimidas y mantiene solo las últimas 20
"""
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import hashlib

# Agregar la ruta raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger

# ========================================
# CONFIGURACIÓN
# ========================================
# Rutas
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "db" / "almacen.db"
BACKUP_DIR = ROOT_DIR / "db" / "backups"

# Configuración
MAX_BACKUPS = 20  # Número máximo de backups a mantener

# ========================================
# FUNCIONES PRINCIPALES
# ========================================

def crear_backup(mostrar_log: bool = True) -> bool:
    """
    Crea un backup de la base de datos
    
    Args:
        mostrar_log: Si True, registra en logs
    
    Returns:
        True si el backup se creó exitosamente, False en caso contrario
    """
    try:
        # Verificar que existe la BD
        if not DB_PATH.exists():
            if mostrar_log:
                logger.error(f"BACKUP | Base de datos no encontrada: {DB_PATH}")
            return False
        
        # Crear carpeta de backups si no existe
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo de backup con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"almacen_{timestamp}.zip"
        backup_path = BACKUP_DIR / backup_filename
        
        # Calcular hash SHA256 de la BD original (para verificación)
        hash_original = calcular_hash(DB_PATH)
        
        # Crear ZIP con la base de datos
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_PATH, arcname="almacen.db")
            # Agregar archivo con el hash para verificación
            zipf.writestr("hash.txt", hash_original)
        
        # Verificar que el backup se creó correctamente
        if not backup_path.exists():
            if mostrar_log:
                logger.error(f"BACKUP | Error: El archivo de backup no se creó")
            return False
        
        tamanio_mb = backup_path.stat().st_size / (1024 * 1024)
        
        if mostrar_log:
            logger.info(f"BACKUP | Backup creado exitosamente: {backup_filename} ({tamanio_mb:.2f} MB)")
            logger.info(f"BACKUP | Hash SHA256: {hash_original}")
        
        # Limpiar backups antiguos
        limpiar_backups_antiguos(mostrar_log)
        
        return True
        
    except Exception as e:
        if mostrar_log:
            logger.error(f"BACKUP | Error al crear backup: {type(e).__name__}: {str(e)}")
        return False

def limpiar_backups_antiguos(mostrar_log: bool = True):
    """
    Elimina backups antiguos, manteniendo solo los últimos MAX_BACKUPS
    
    Args:
        mostrar_log: Si True, registra en logs
    """
    try:
        # Obtener lista de backups ordenados por fecha (más recientes primero)
        backups = sorted(
            BACKUP_DIR.glob("almacen_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Si hay más de MAX_BACKUPS, eliminar los antiguos
        if len(backups) > MAX_BACKUPS:
            backups_a_eliminar = backups[MAX_BACKUPS:]
            
            for backup in backups_a_eliminar:
                backup.unlink()
                if mostrar_log:
                    logger.info(f"BACKUP | Backup antiguo eliminado: {backup.name}")
            
            if mostrar_log:
                logger.info(f"BACKUP | Se eliminaron {len(backups_a_eliminar)} backup(s) antiguo(s)")
        
    except Exception as e:
        if mostrar_log:
            logger.error(f"BACKUP | Error al limpiar backups antiguos: {str(e)}")

def verificar_backup(backup_path: Path) -> bool:
    """
    Verifica la integridad de un backup
    
    Args:
        backup_path: Ruta al archivo de backup
    
    Returns:
        True si el backup es válido, False en caso contrario
    """
    try:
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Verificar que contiene almacen.db
            if "almacen.db" not in zipf.namelist():
                return False
            
            # Si tiene hash, verificarlo
            if "hash.txt" in zipf.namelist():
                hash_almacenado = zipf.read("hash.txt").decode('utf-8').strip()
                # Extraer temporalmente para verificar
                with zipf.open("almacen.db") as db_file:
                    contenido = db_file.read()
                    hash_actual = hashlib.sha256(contenido).hexdigest()
                    return hash_actual == hash_almacenado
            
            return True
            
    except Exception as e:
        logger.error(f"BACKUP | Error al verificar backup: {str(e)}")
        return False

def calcular_hash(file_path: Path) -> str:
    """
    Calcula el hash SHA256 de un archivo
    
    Args:
        file_path: Ruta al archivo
    
    Returns:
        Hash SHA256 en hexadecimal
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Leer en bloques de 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hay_backup_hoy() -> bool:
    """
    Verifica si ya existe un backup del día de hoy
    
    Returns:
        True si existe backup de hoy, False en caso contrario
    """
    try:
        if not BACKUP_DIR.exists():
            return False
        
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        
        # Buscar archivos que empiecen con la fecha de hoy
        backups_hoy = list(BACKUP_DIR.glob(f"almacen_{fecha_hoy}_*.zip"))
        
        return len(backups_hoy) > 0
        
    except Exception as e:
        logger.error(f"BACKUP | Error al verificar backup de hoy: {str(e)}")
        return False

def restaurar_backup(backup_path: Path) -> bool:
    """
    Restaura una base de datos desde un backup
    
    Args:
        backup_path: Ruta al archivo de backup
    
    Returns:
        True si se restauró exitosamente, False en caso contrario
    """
    try:
        # Verificar que el backup es válido
        if not verificar_backup(backup_path):
            logger.error(f"BACKUP | El backup no es válido: {backup_path}")
            return False
        
        # Hacer backup de la BD actual antes de restaurar
        backup_actual = DB_PATH.parent / f"almacen_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_actual)
        logger.info(f"BACKUP | BD actual respaldada en: {backup_actual.name}")
        
        # Extraer el backup
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extract("almacen.db", path=DB_PATH.parent)
        
        logger.info(f"BACKUP | Base de datos restaurada desde: {backup_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"BACKUP | Error al restaurar backup: {str(e)}")
        return False

def listar_backups() -> list:
    """
    Lista todos los backups disponibles
    
    Returns:
        Lista de tuplas (nombre_archivo, fecha_modificacion, tamaño_mb)
    """
    try:
        if not BACKUP_DIR.exists():
            return []
        
        backups = []
        for backup_path in sorted(BACKUP_DIR.glob("almacen_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = backup_path.stat()
            fecha = datetime.fromtimestamp(stat.st_mtime)
            tamanio_mb = stat.st_size / (1024 * 1024)
            backups.append((backup_path.name, fecha, tamanio_mb))
        
        return backups
        
    except Exception as e:
        logger.error(f"BACKUP | Error al listar backups: {str(e)}")
        return []

# ========================================
# EJECUCIÓN DIRECTA
# ========================================
if __name__ == "__main__":
    print("🔄 Iniciando backup de base de datos...")
    print(f"📁 Base de datos: {DB_PATH}")
    print(f"💾 Carpeta de backups: {BACKUP_DIR}")
    print("-" * 50)
    
    if crear_backup(mostrar_log=True):
        print("✅ Backup creado exitosamente")
        
        print("\n📋 Backups disponibles:")
        for nombre, fecha, tamanio in listar_backups():
            print(f"  • {nombre} - {fecha.strftime('%Y-%m-%d %H:%M:%S')} - {tamanio:.2f} MB")
    else:
        print("❌ Error al crear backup")