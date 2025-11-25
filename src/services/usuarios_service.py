"""
Servicio de Usuarios - Lógica de negocio para gestión de usuarios y autenticación
"""
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
import re
from src.repos import usuarios_repo
from src.core.db_utils import (
    hash_pwd,  # Legacy - para compatibilidad
    hash_password_seguro,  # Nuevo - bcrypt
    verificar_password,  # Nuevo - verificación bcrypt
    es_hash_legacy  # Nuevo - detectar formato
)
from src.core.logger import logger, log_operacion, log_validacion, log_error_bd


def validar_usuario(usuario: str) -> Tuple[bool, str]:
    """Valida que el nombre de usuario sea válido."""
    if not usuario or not usuario.strip():
        log_validacion("usuarios", "usuario", "Usuario vacío")
        return False, "El nombre de usuario es obligatorio"

    usuario = usuario.strip()

    if len(usuario) < 3:
        log_validacion("usuarios", "usuario", f"Usuario muy corto: {usuario}")
        return False, "El usuario debe tener al menos 3 caracteres"

    if len(usuario) > 50:
        log_validacion("usuarios", "usuario", f"Usuario muy largo: {len(usuario)}")
        return False, "El usuario no puede exceder 50 caracteres"

    # Solo letras, números, guiones y guiones bajos
    patron = re.compile(r'^[a-zA-Z0-9_-]+$')
    if not patron.match(usuario):
        log_validacion("usuarios", "usuario", f"Usuario con caracteres inválidos: {usuario}")
        return False, "El usuario solo puede contener letras, números, guiones y guiones bajos"

    return True, ""


def validar_password(password: str) -> Tuple[bool, str]:
    """Valida que la contraseña sea segura."""
    if not password:
        log_validacion("usuarios", "password", "Contraseña vacía")
        return False, "La contraseña es obligatoria"

    if len(password) < 4:
        log_validacion("usuarios", "password", "Contraseña muy corta")
        return False, "La contraseña debe tener al menos 4 caracteres"

    if len(password) > 100:
        log_validacion("usuarios", "password", "Contraseña muy larga")
        return False, "La contraseña no puede exceder 100 caracteres"

    return True, ""


def validar_rol(rol: str) -> Tuple[bool, str]:
    """Valida que el rol sea válido."""
    roles_validos = ["admin", "almacen", "operario"]
    rol = rol.strip().lower()

    if rol not in roles_validos:
        log_validacion("usuarios", "rol", f"Rol inválido: {rol}")
        return False, f"El rol debe ser uno de: {', '.join(roles_validos)}"

    return True, ""


def validar_usuario_unico(usuario: str) -> Tuple[bool, str]:
    """Valida que el nombre de usuario sea único."""
    existente = usuarios_repo.get_by_usuario(usuario)
    if existente:
        log_validacion("usuarios", "usuario", f"Usuario duplicado: {usuario}")
        return False, f"Ya existe un usuario con el nombre '{usuario}'"
    return True, ""


def autenticar_usuario(usuario: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Autentica un usuario verificando usuario y contraseña.

    Sistema HÍBRIDO que soporta:
    - Hashes legacy (SHA256) - para compatibilidad
    - Hashes modernos (bcrypt) - seguro

    MIGRACIÓN AUTOMÁTICA:
    Si el login es exitoso con hash legacy, automáticamente re-hashea
    con bcrypt para migrar progresivamente sin resetear contraseñas.
    """
    try:
        if not usuario or not password:
            return False, "Usuario y contraseña son obligatorios", None

        usuario = usuario.strip()
        user_data = usuarios_repo.get_by_usuario(usuario)

        if not user_data:
            log_validacion("usuarios", "autenticar", f"Usuario no encontrado: {usuario}")
            return False, "Usuario o contraseña incorrectos", None

        if not user_data['activo']:
            log_validacion("usuarios", "autenticar", f"Usuario inactivo: {usuario}")
            return False, "El usuario está desactivado", None

        stored_hash = user_data['pass_hash']
        password_correcta = False

        # Detectar tipo de hash y verificar
        if es_hash_legacy(stored_hash):
            # Hash legacy (SHA256) - verificar con método antiguo
            password_hash_sha256 = hash_pwd(password)
            password_correcta = (password_hash_sha256 == stored_hash)

            # ✨ MIGRACIÓN AUTOMÁTICA ✨
            # Si la contraseña es correcta, re-hashear con bcrypt
            if password_correcta:
                try:
                    nuevo_hash_bcrypt = hash_password_seguro(password)
                    usuarios_repo.actualizar_usuario(
                        usuario,
                        nuevo_hash_bcrypt,
                        None,  # No cambiar rol
                        None   # No cambiar estado activo
                    )
                    logger.info(f"🔐 Contraseña migrada a bcrypt | {usuario}")
                    log_operacion("usuarios", "migrar_password", usuario,
                                "Contraseña migrada de SHA256 a bcrypt")
                except Exception as e:
                    # Si falla la migración, continuar (login sigue siendo válido)
                    logger.warning(f"⚠️ Falló migración de contraseña | {usuario} | {e}")

        else:
            # Hash moderno (bcrypt) - verificar con bcrypt
            password_correcta = verificar_password(password, stored_hash)

        # Resultado de autenticación
        if not password_correcta:
            log_validacion("usuarios", "autenticar", f"Contraseña incorrecta: {usuario}")
            return False, "Usuario o contraseña incorrectos", None

        log_operacion("usuarios", "login", usuario, f"Inicio de sesión exitoso")
        logger.info(f"✅ Usuario autenticado | {usuario} | Rol: {user_data['rol']}")

        return True, "Inicio de sesión exitoso", {
            'usuario': user_data['usuario'],
            'rol': user_data['rol']
        }

    except Exception as e:
        log_error_bd("usuarios", "autenticar_usuario", e)
        return False, f"Error al autenticar: {str(e)}", None


def crear_usuario(usuario: str, password: str, rol: str = "almacen",
                  activo: bool = True, usuario_creador: str = "admin") -> Tuple[bool, str]:
    """Crea un nuevo usuario con validaciones."""
    try:
        # Validaciones
        valido, error = validar_usuario(usuario)
        if not valido:
            return False, error

        valido, error = validar_usuario_unico(usuario)
        if not valido:
            return False, error

        valido, error = validar_password(password)
        if not valido:
            return False, error

        valido, error = validar_rol(rol)
        if not valido:
            return False, error

        # Normalizar y crear
        usuario = usuario.strip()
        rol = rol.strip().lower()
        # ✅ USAR BCRYPT para nuevos usuarios
        password_hash = hash_password_seguro(password)

        usuarios_repo.crear_usuario(usuario, password_hash, rol, 1 if activo else 0)

        log_operacion("usuarios", "crear", usuario_creador,
                     f"Usuario: {usuario}, Rol: {rol}, Activo: {activo}")
        logger.info(f"Usuario creado | {usuario} | Rol: {rol}")

        return True, f"Usuario '{usuario}' creado correctamente"

    except psycopg2.IntegrityError:
        return False, f"Ya existe un usuario con el nombre '{usuario}'"
    except Exception as e:
        log_error_bd("usuarios", "crear_usuario", e)
        return False, f"Error al crear usuario: {str(e)}"


def actualizar_usuario(usuario: str, password: Optional[str] = None,
                      rol: Optional[str] = None, activo: Optional[bool] = None,
                      usuario_modificador: str = "admin") -> Tuple[bool, str]:
    """Actualiza un usuario existente con validaciones."""
    try:
        user_data = usuarios_repo.get_by_usuario(usuario)
        if not user_data:
            return False, f"No se encontró el usuario '{usuario}'"

        # Validar nueva contraseña si se proporciona
        password_hash = None
        if password:
            valido, error = validar_password(password)
            if not valido:
                return False, error
            # ✅ USAR BCRYPT para actualización de contraseña
            password_hash = hash_password_seguro(password)

        # Validar nuevo rol si se proporciona
        if rol:
            valido, error = validar_rol(rol)
            if not valido:
                return False, error
            rol = rol.strip().lower()

        # Actualizar
        activo_int = None if activo is None else (1 if activo else 0)
        usuarios_repo.actualizar_usuario(usuario, password_hash, rol, activo_int)

        cambios = []
        if password_hash:
            cambios.append("contraseña")
        if rol:
            cambios.append(f"rol: {rol}")
        if activo is not None:
            cambios.append(f"activo: {activo}")

        log_operacion("usuarios", "actualizar", usuario_modificador,
                     f"Usuario: {usuario}, Cambios: {', '.join(cambios)}")
        logger.info(f"Usuario actualizado | {usuario} | {', '.join(cambios)}")

        return True, f"Usuario '{usuario}' actualizado correctamente"

    except Exception as e:
        log_error_bd("usuarios", "actualizar_usuario", e)
        return False, f"Error al actualizar usuario: {str(e)}"


def eliminar_usuario(usuario: str, usuario_eliminador: str = "admin") -> Tuple[bool, str]:
    """Elimina un usuario del sistema."""
    try:
        user_data = usuarios_repo.get_by_usuario(usuario)
        if not user_data:
            return False, f"No se encontró el usuario '{usuario}'"

        # Verificar que no sea el único usuario
        if usuarios_repo.verificar_es_unico_usuario():
            return False, (
                "No se puede eliminar el único usuario del sistema.\n\n"
                "Debe haber al menos un usuario activo."
            )

        # Verificar que no se esté eliminando a sí mismo
        if usuario == usuario_eliminador:
            return False, "No puede eliminar su propio usuario"

        usuarios_repo.eliminar_usuario(usuario)

        log_operacion("usuarios", "eliminar", usuario_eliminador, f"Usuario: {usuario}")
        logger.info(f"Usuario eliminado | {usuario}")

        return True, f"Usuario '{usuario}' eliminado correctamente"

    except psycopg2.IntegrityError:
        return False, "No se puede eliminar el usuario debido a referencias en el sistema"
    except Exception as e:
        log_error_bd("usuarios", "eliminar_usuario", e)
        return False, f"Error al eliminar usuario: {str(e)}"


def obtener_usuarios(filtro_texto: Optional[str] = None,
                     solo_activos: Optional[bool] = None,
                     limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtiene lista de usuarios con filtros."""
    try:
        return usuarios_repo.get_todos(filtro_texto=filtro_texto,
                                       solo_activos=solo_activos,
                                       limit=limit)
    except Exception as e:
        log_error_bd("usuarios", "obtener_usuarios", e)
        return []


def obtener_usuario(usuario: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario específico por nombre de usuario."""
    try:
        user_data = usuarios_repo.get_by_usuario(usuario)
        if user_data:
            # No devolver el hash de la contraseña
            return {
                'usuario': user_data['usuario'],
                'rol': user_data['rol'],
                'activo': user_data['activo']
            }
        return None
    except Exception as e:
        log_error_bd("usuarios", "obtener_usuario", e)
        return None


def cambiar_password_propia(usuario: str, password_actual: str, password_nueva: str) -> Tuple[bool, str]:
    """Permite a un usuario cambiar su propia contraseña validando la actual."""
    try:
        # Verificar que el usuario existe
        user_data = usuarios_repo.get_by_usuario(usuario)
        if not user_data:
            return False, f"No se encontró el usuario '{usuario}'"

        # Verificar que el usuario está activo
        if not user_data['activo']:
            return False, "El usuario está desactivado"

        # Verificar contraseña actual (soportar ambos formatos)
        stored_hash = user_data['pass_hash']
        password_actual_correcta = False

        if es_hash_legacy(stored_hash):
            # Hash legacy
            password_hash_actual = hash_pwd(password_actual)
            password_actual_correcta = (password_hash_actual == stored_hash)
        else:
            # Hash bcrypt
            password_actual_correcta = verificar_password(password_actual, stored_hash)

        if not password_actual_correcta:
            log_validacion("usuarios", "cambiar_password", f"Contraseña actual incorrecta: {usuario}")
            return False, "La contraseña actual es incorrecta"

        # Validar nueva contraseña
        valido, error = validar_password(password_nueva)
        if not valido:
            return False, error

        # Verificar que la nueva contraseña sea diferente de la actual
        if password_nueva == password_actual:
            return False, "La nueva contraseña debe ser diferente a la actual"

        # ✅ Hashear nueva contraseña con BCRYPT
        password_hash_nueva = hash_password_seguro(password_nueva)

        # Actualizar contraseña
        usuarios_repo.actualizar_usuario(usuario, password_hash_nueva, None, None)

        log_operacion("usuarios", "cambiar_password", usuario, "Cambio de contraseña propia exitoso")
        logger.info(f"Contraseña cambiada | {usuario}")

        return True, "Contraseña cambiada correctamente"

    except Exception as e:
        log_error_bd("usuarios", "cambiar_password_propia", e)
        return False, f"Error al cambiar contraseña: {str(e)}"
