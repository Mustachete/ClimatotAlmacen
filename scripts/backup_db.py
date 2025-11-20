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

# Configuración (valores por defecto, se sobreescriben desde BD)
MAX_BACKUPS = 20  # Número máximo de backups a mantener (por defecto)

def obtener_config_backups():
    """Obtiene la configuración de backups desde la BD"""
    try:
        from src.services.backup_config_service import obtener_configuracion
        return obtener_configuracion()
    except Exception as e:
        logger.warning(f"No se pudo cargar configuración desde BD, usando valores por defecto: {e}")
        # Retornar valores por defecto si falla
        class ConfigDefault:
            max_backups = 20
            permitir_multiples_diarios = True
            retencion_dias = None
            ruta_backups = None
        return ConfigDefault()

# ========================================
# FUNCIONES PRINCIPALES
# ========================================

def crear_backup(mostrar_log: bool = True, forzar: bool = False) -> bool:
    """
    Crea un backup de la base de datos

    Args:
        mostrar_log: Si True, registra en logs
        forzar: Si True, ignora la restricción de múltiples backups diarios

    Returns:
        True si el backup se creó exitosamente, False en caso contrario
    """
    try:
        # Obtener configuración
        config = obtener_config_backups()

        # Verificar si se permiten múltiples backups diarios
        if not forzar and not config.permitir_multiples_diarios:
            if hay_backup_hoy():
                if mostrar_log:
                    logger.info("BACKUP | Ya existe un backup del día de hoy, operación omitida")
                return False

        # Verificar que existe la BD
        if not DB_PATH.exists():
            if mostrar_log:
                logger.error(f"BACKUP | Base de datos no encontrada: {DB_PATH}")
            return False

        # Obtener directorio de backups desde config
        backup_dir = Path(config.ruta_backups) if config.ruta_backups else BACKUP_DIR

        # Crear carpeta de backups si no existe
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo de backup con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"almacen_{timestamp}.zip"
        backup_path = backup_dir / backup_filename
        
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
        limpiar_backups_antiguos(backup_dir, config, mostrar_log)

        return True
        
    except Exception as e:
        if mostrar_log:
            logger.error(f"BACKUP | Error al crear backup: {type(e).__name__}: {str(e)}")
        return False

def limpiar_backups_antiguos(backup_dir: Path, config, mostrar_log: bool = True):
    """
    Elimina backups antiguos según la configuración

    Args:
        backup_dir: Directorio de backups
        config: Configuración de backups
        mostrar_log: Si True, registra en logs
    """
    try:
        # Obtener lista de backups ordenados por fecha (más recientes primero)
        backups = sorted(
            backup_dir.glob("almacen_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        backups_a_eliminar = []

        # Criterio 1: Limitar por número máximo
        if len(backups) > config.max_backups:
            backups_a_eliminar.extend(backups[config.max_backups:])

        # Criterio 2: Eliminar backups más antiguos que retencion_dias
        if config.retencion_dias is not None:
            from datetime import datetime, timedelta
            fecha_limite = datetime.now() - timedelta(days=config.retencion_dias)

            for backup in backups:
                if backup not in backups_a_eliminar:
                    fecha_backup = datetime.fromtimestamp(backup.stat().st_mtime)
                    if fecha_backup < fecha_limite:
                        backups_a_eliminar.append(backup)

        # Eliminar backups
        for backup in set(backups_a_eliminar):  # Usar set para evitar duplicados
            backup.unlink()
            if mostrar_log:
                logger.info(f"BACKUP | Backup antiguo eliminado: {backup.name}")

        if backups_a_eliminar and mostrar_log:
            logger.info(f"BACKUP | Se eliminaron {len(set(backups_a_eliminar))} backup(s) antiguo(s)")

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

def hay_backup_hoy(backup_dir: Path = None) -> bool:
    """
    Verifica si ya existe un backup del día de hoy

    Args:
        backup_dir: Directorio de backups (opcional, usa el por defecto si no se especifica)

    Returns:
        True si existe backup de hoy, False en caso contrario
    """
    try:
        if backup_dir is None:
            config = obtener_config_backups()
            backup_dir = Path(config.ruta_backups) if config.ruta_backups else BACKUP_DIR

        if not backup_dir.exists():
            return False

        fecha_hoy = datetime.now().strftime("%Y%m%d")

        # Buscar archivos que empiecen con la fecha de hoy
        backups_hoy = list(backup_dir.glob(f"almacen_{fecha_hoy}_*.zip"))

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

def listar_backups(backup_dir: Path = None) -> list:
    """
    Lista todos los backups disponibles

    Args:
        backup_dir: Directorio de backups (opcional, usa el por defecto si no se especifica)

    Returns:
        Lista de tuplas (nombre_archivo, fecha_modificacion, tamaño_mb)
    """
    try:
        if backup_dir is None:
            config = obtener_config_backups()
            backup_dir = Path(config.ruta_backups) if config.ruta_backups else BACKUP_DIR

        if not backup_dir.exists():
            return []

        backups = []
        for backup_path in sorted(backup_dir.glob("almacen_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
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