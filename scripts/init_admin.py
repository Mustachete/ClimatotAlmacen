"""
Script para crear el primer usuario administrador en el sistema.
Se ejecuta una sola vez al inicializar la base de datos.
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services import usuarios_service
from src.core.db_utils import DB_PATH


def main():
    print("=" * 60)
    print("CREAR USUARIO ADMINISTRADOR INICIAL")
    print("=" * 60)
    print()

    # Verificar que existe la base de datos
    if not DB_PATH.exists():
        print(f"[ERROR] No se encuentra la base de datos en: {DB_PATH}")
        print("Ejecuta primero: python init_db.py")
        return 1

    # Verificar si ya existen usuarios
    usuarios_existentes = usuarios_service.obtener_usuarios()
    if usuarios_existentes:
        print("[INFO] Ya existen usuarios en el sistema:")
        for usuario in usuarios_existentes:
            activo_str = "ACTIVO" if usuario['activo'] else "INACTIVO"
            print(f"  - {usuario['usuario']} (Rol: {usuario['rol']}, Estado: {activo_str})")
        print()
        respuesta = input("¿Desea crear un nuevo usuario administrador de todos modos? (s/N): ")
        if respuesta.lower() != 's':
            print("Operación cancelada.")
            return 0

    print()
    print("Ingrese los datos del nuevo administrador:")
    print()

    # Solicitar datos
    while True:
        usuario = input("Usuario (min 3 caracteres): ").strip()
        if len(usuario) >= 3:
            break
        print("[ERROR] El usuario debe tener al menos 3 caracteres")

    while True:
        password = input("Contraseña (min 4 caracteres): ").strip()
        if len(password) >= 4:
            break
        print("[ERROR] La contraseña debe tener al menos 4 caracteres")

    password_confirm = input("Confirmar contraseña: ").strip()
    if password != password_confirm:
        print("[ERROR] Las contraseñas no coinciden")
        return 1

    # Crear el usuario
    print()
    print("Creando usuario administrador...")

    exito, mensaje = usuarios_service.crear_usuario(
        usuario=usuario,
        password=password,
        rol="admin",
        activo=True,
        usuario_creador="system"
    )

    if not exito:
        print(f"[ERROR] {mensaje}")
        return 1

    print(f"[OK] {mensaje}")
    print()
    print("=" * 60)
    print("Usuario administrador creado correctamente")
    print("=" * 60)
    print()
    print("Ahora puede ejecutar la aplicación con: python app.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
