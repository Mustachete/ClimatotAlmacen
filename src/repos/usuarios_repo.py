"""
Repositorio de Usuarios - Acceso a datos de usuarios del sistema
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


def get_by_usuario(usuario: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su nombre de usuario."""
    sql = """
        SELECT usuario, pass_hash, rol, activo
        FROM usuarios
        WHERE usuario = %s
    """
    return fetch_one(sql, (usuario,))


def get_todos(filtro_texto: Optional[str] = None, solo_activos: Optional[bool] = None,
              limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtiene lista de usuarios con filtros opcionales."""
    sql = """
        SELECT usuario, rol, activo
        FROM usuarios
        WHERE 1=1
    """
    params = []

    if filtro_texto:
        sql += " AND usuario ILIKE %s"
        params.append(f"%{filtro_texto}%")

    if solo_activos is not None:
        sql += " AND activo = %s"
        params.append(1 if solo_activos else 0)

    sql += " ORDER BY usuario LIMIT %s"
    params.append(limit)

    return fetch_all(sql, tuple(params))


def crear_usuario(usuario: str, pass_hash: str, rol: str = "almacen", activo: int = 1) -> None:
    """Crea un nuevo usuario."""
    sql = """
        INSERT INTO usuarios(usuario, pass_hash, rol, activo)
        VALUES(%s, %s, %s, %s)
    """
    execute_query(sql, (usuario, pass_hash, rol, activo))


def actualizar_usuario(usuario: str, pass_hash: Optional[str] = None, rol: Optional[str] = None,
                       activo: Optional[int] = None) -> None:
    """Actualiza un usuario existente."""
    campos = []
    params = []

    if pass_hash is not None:
        campos.append("pass_hash = %s")
        params.append(pass_hash)

    if rol is not None:
        campos.append("rol = %s")
        params.append(rol)

    if activo is not None:
        campos.append("activo = %s")
        params.append(activo)

    if not campos:
        return

    sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE usuario = %s"
    params.append(usuario)
    execute_query(sql, tuple(params))


def eliminar_usuario(usuario: str) -> None:
    """Elimina un usuario."""
    sql = "DELETE FROM usuarios WHERE usuario = %s"
    execute_query(sql, (usuario,))


def verificar_es_unico_usuario() -> bool:
    """Verifica si es el único usuario en el sistema."""
    sql = "SELECT COUNT(*) as total FROM usuarios"
    resultado = fetch_one(sql)
    return resultado['total'] == 1 if resultado else False
