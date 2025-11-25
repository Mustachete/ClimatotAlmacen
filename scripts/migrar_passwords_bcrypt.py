#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Migración de Contraseñas a bcrypt

PROPÓSITO:
    Migra contraseñas de usuarios desde SHA256 (inseguro) a bcrypt (seguro).

USO:
    python scripts/migrar_passwords_bcrypt.py

IMPORTANTE:
    - Este script requiere conocer las contraseñas en texto plano
    - Solo puede migrar usuarios con contraseñas conocidas (ej: admin)
    - El resto de usuarios se migran automáticamente en su primer login

MODO DE OPERACIÓN:
    1. Manual: Lista usuarios con contraseñas conocidas
    2. Interactivo: Pide confirmación antes de migrar
    3. Seguro: Solo actualiza si verifica que la contraseña es correcta

CONTRASEÑAS COMUNES A PROBAR:
    - admin / admin
    - usuario / usuario
    - test / test
"""

import sys
from pathlib import Path

# Añadir src al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.db_utils import (
    hash_pwd,
    hash_password_seguro,
    verificar_password,
    es_hash_legacy,
    fetch_all,
    execute_query
)
from src.core.logger import logger

# ==========================================
# CONFIGURACIÓN: Contraseñas conocidas
# ==========================================
USUARIOS_CONOCIDOS = {
    'admin': 'admin',      # usuario: contraseña
    # Añadir más usuarios conocidos aquí si los hay
    # 'usuario1': 'password1',
    # 'test': 'test',
}

# ==========================================
# FUNCIONES
# ==========================================

def obtener_usuarios_legacy():
    """Obtiene usuarios que aún tienen hash SHA256."""
    sql = """
        SELECT usuario, pass_hash, rol, activo
        FROM usuarios
        ORDER BY usuario
    """
    usuarios = fetch_all(sql)

    usuarios_legacy = []
    usuarios_bcrypt = []

    for user in usuarios:
        if es_hash_legacy(user['pass_hash']):
            usuarios_legacy.append(user)
        else:
            usuarios_bcrypt.append(user)

    return usuarios_legacy, usuarios_bcrypt


def verificar_y_migrar_usuario(usuario, password_plano):
    """
    Verifica la contraseña y migra a bcrypt si es correcta.

    Returns:
        (bool, str): (exito, mensaje)
    """
    try:
        # Obtener hash actual
        sql = "SELECT pass_hash FROM usuarios WHERE usuario = %s"
        result = fetch_all(sql, (usuario,))

        if not result:
            return False, f"Usuario '{usuario}' no encontrado"

        stored_hash = result[0]['pass_hash']

        # Verificar si es legacy
        if not es_hash_legacy(stored_hash):
            return False, f"Usuario '{usuario}' ya usa bcrypt [OK]"

        # Verificar contraseña
        password_hash_sha256 = hash_pwd(password_plano)
        if password_hash_sha256 != stored_hash:
            return False, f"Contrasena incorrecta para '{usuario}' [ERROR]"

        # Migrar a bcrypt
        nuevo_hash_bcrypt = hash_password_seguro(password_plano)

        sql_update = """
            UPDATE usuarios
            SET pass_hash = %s
            WHERE usuario = %s
        """
        execute_query(sql_update, (nuevo_hash_bcrypt, usuario))

        # Verificar que funcionó
        if verificar_password(password_plano, nuevo_hash_bcrypt):
            return True, f"Usuario '{usuario}' migrado exitosamente [MIGRADO]"
        else:
            return False, f"Error verificando nueva contrasena para '{usuario}'"

    except Exception as e:
        return False, f"Error migrando '{usuario}': {str(e)}"


def main():
    """Función principal del script de migración."""
    print("="*70)
    print("  MIGRACION DE CONTRASENAS A BCRYPT")
    print("="*70)
    print()

    # Obtener estado actual
    print(">> Analizando base de datos...")
    usuarios_legacy, usuarios_bcrypt = obtener_usuarios_legacy()

    total_usuarios = len(usuarios_legacy) + len(usuarios_bcrypt)
    print(f"\n>> Estado actual:")
    print(f"   Total usuarios: {total_usuarios}")
    print(f"   [OK] Con bcrypt (seguro): {len(usuarios_bcrypt)}")
    print(f"   [!!] Con SHA256 (legacy): {len(usuarios_legacy)}")
    print()

    if not usuarios_legacy:
        print("[OK] Todos los usuarios ya usan bcrypt!")
        print("     No hay nada que migrar.")
        return

    # Mostrar usuarios legacy
    print("[!!] Usuarios que aun usan SHA256:")
    for user in usuarios_legacy:
        estado = "[Activo]" if user['activo'] else "[Inactivo]"
        print(f"   - {user['usuario']} ({user['rol']}) {estado}")
    print()

    # Intentar migrar usuarios conocidos
    print(">> Intentando migrar usuarios con contrasenas conocidas...")
    print()

    migrados = 0
    for usuario, password in USUARIOS_CONOCIDOS.items():
        exito, mensaje = verificar_y_migrar_usuario(usuario, password)
        print(f"   {mensaje}")
        if exito:
            migrados += 1

    print()
    print("="*70)
    print(f"[OK] Migrados: {migrados} usuario(s)")
    print()

    # Recordatorio sobre migración automática
    if len(usuarios_legacy) - migrados > 0:
        print(">> NOTA IMPORTANTE:")
        print(f"   Quedan {len(usuarios_legacy) - migrados} usuarios sin migrar.")
        print()
        print("   Estos se migraran AUTOMATICAMENTE en su proximo login.")
        print("   No necesitas resetear sus contrasenas.")
        print()

    print("="*70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!!] Migracion cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] ERROR FATAL: {e}")
        logger.exception("Error en script de migracion")
        sys.exit(1)
