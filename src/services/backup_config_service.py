"""
Servicio para gestionar la configuración de backups
"""
from typing import Optional, Dict, Any
from pathlib import Path

from src.core.db_utils import fetch_one, execute_query
from src.core.logger import logger


class BackupConfig:
    """Clase para representar la configuración de backups"""

    def __init__(
        self,
        max_backups: int = 20,
        permitir_multiples_diarios: bool = True,
        backup_auto_inicio: bool = False,
        backup_auto_cierre: bool = False,
        retencion_dias: Optional[int] = None,
        ruta_backups: Optional[str] = None
    ):
        self.max_backups = max_backups
        self.permitir_multiples_diarios = permitir_multiples_diarios
        self.backup_auto_inicio = backup_auto_inicio
        self.backup_auto_cierre = backup_auto_cierre
        self.retencion_dias = retencion_dias
        self.ruta_backups = ruta_backups

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return {
            'max_backups': self.max_backups,
            'permitir_multiples_diarios': self.permitir_multiples_diarios,
            'backup_auto_inicio': self.backup_auto_inicio,
            'backup_auto_cierre': self.backup_auto_cierre,
            'retencion_dias': self.retencion_dias,
            'ruta_backups': self.ruta_backups
        }

    @staticmethod
    def from_db_row(row) -> 'BackupConfig':
        """Crea una instancia desde una fila de la BD"""
        return BackupConfig(
            max_backups=row['max_backups'],
            permitir_multiples_diarios=bool(row['permitir_multiples_diarios']),
            backup_auto_inicio=bool(row['backup_auto_inicio']),
            backup_auto_cierre=bool(row['backup_auto_cierre']),
            retencion_dias=row['retencion_dias'],
            ruta_backups=row['ruta_backups']
        )


def obtener_configuracion() -> BackupConfig:
    """
    Obtiene la configuración actual de backups desde la BD

    Returns:
        BackupConfig con la configuración actual
    """
    try:
        sql = "SELECT * FROM config_backups WHERE id = 1"
        row = fetch_one(sql)

        if row:
            return BackupConfig.from_db_row(row)
        else:
            # Si no existe configuración, crear una por defecto
            logger.warning("No existe configuración de backups, creando configuración por defecto")
            crear_configuracion_default()
            return BackupConfig()

    except Exception as e:
        logger.error(f"Error al obtener configuración de backups: {e}")
        # Retornar configuración por defecto en caso de error
        return BackupConfig()


def guardar_configuracion(config: BackupConfig) -> bool:
    """
    Guarda la configuración de backups en la BD

    Args:
        config: Configuración a guardar

    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        sql = """
            UPDATE config_backups
            SET max_backups = %s,
                permitir_multiples_diarios = %s,
                backup_auto_inicio = %s,
                backup_auto_cierre = %s,
                retencion_dias = %s,
                ruta_backups = %s,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id = 1
        """

        params = (
            config.max_backups,
            1 if config.permitir_multiples_diarios else 0,
            1 if config.backup_auto_inicio else 0,
            1 if config.backup_auto_cierre else 0,
            config.retencion_dias,
            config.ruta_backups
        )

        execute_query(sql, params)
        logger.info(f"Configuración de backups actualizada: {config.to_dict()}")
        return True

    except Exception as e:
        logger.error(f"Error al guardar configuración de backups: {e}")
        return False


def crear_configuracion_default() -> bool:
    """
    Crea la configuración por defecto en la BD

    Returns:
        True si se creó exitosamente, False en caso contrario
    """
    try:
        sql = """
            INSERT INTO config_backups (
                id,
                max_backups,
                permitir_multiples_diarios,
                backup_auto_inicio,
                backup_auto_cierre,
                retencion_dias,
                ruta_backups
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """

        execute_query(sql, (1, 20, 1, 0, 0, None, None))
        logger.info("Configuración de backups por defecto creada")
        return True

    except Exception as e:
        logger.error(f"Error al crear configuración por defecto: {e}")
        return False


def actualizar_campo(campo: str, valor: Any) -> bool:
    """
    Actualiza un campo específico de la configuración

    Args:
        campo: Nombre del campo a actualizar
        valor: Nuevo valor

    Returns:
        True si se actualizó exitosamente, False en caso contrario
    """
    campos_validos = [
        'max_backups',
        'permitir_multiples_diarios',
        'backup_auto_inicio',
        'backup_auto_cierre',
        'retencion_dias',
        'ruta_backups'
    ]

    if campo not in campos_validos:
        logger.error(f"Campo inválido: {campo}")
        return False

    try:
        sql = f"""
            UPDATE config_backups
            SET {campo} = %s,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id = 1
        """

        execute_query(sql, (valor,))
        logger.info(f"Campo '{campo}' actualizado a: {valor}")
        return True

    except Exception as e:
        logger.error(f"Error al actualizar campo '{campo}': {e}")
        return False


def obtener_ruta_backups() -> Path:
    """
    Obtiene la ruta de backups configurada o la por defecto

    Returns:
        Path con la ruta de backups
    """
    config = obtener_configuracion()

    if config.ruta_backups:
        return Path(config.ruta_backups)
    else:
        # Ruta por defecto
        from pathlib import Path as P
        return P(__file__).parent.parent.parent / "db" / "backups"
