"""
Script para reemplazar usuario="admin" hardcodeado con session_manager en todas las ventanas
"""
import os
import re
from pathlib import Path

# Rutas de ventanas a actualizar
VENTANAS_PATHS = [
    "src/ventanas/maestros/ventana_ubicaciones.py",
    "src/ventanas/maestros/ventana_familias.py",
    "src/ventanas/maestros/ventana_operarios.py",
    "src/ventanas/maestros/ventana_proveedores.py",
    "src/ventanas/maestros/ventana_articulos.py",
    "src/ventanas/operativas/ventana_inventario.py",
    "src/ventanas/operativas/ventana_imputacion.py",
    "src/ventanas/operativas/ventana_recepcion.py",
    "src/ventanas/operativas/ventana_devolucion.py",
    "src/ventanas/operativas/ventana_material_perdido.py",
]

# Obtener raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

def actualizar_archivo(filepath):
    """Actualiza un archivo de ventana para usar session_manager"""
    full_path = PROJECT_ROOT / filepath

    if not full_path.exists():
        print(f"[X] No existe: {filepath}")
        return False

    # Leer contenido
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya tiene el import
    if 'from src.core.session_manager import session_manager' in content:
        print(f"[OK] Ya actualizado: {filepath}")
        return True

    # Agregar import después de los imports de services
    if 'from src.services import' in content:
        # Buscar el último import de services
        lines = content.split('\n')
        new_lines = []
        import_added = False

        for i, line in enumerate(lines):
            new_lines.append(line)
            # Agregar import después de la última línea de import de services
            if 'from src.services import' in line and not import_added:
                # Buscar si la siguiente línea también es un import de services
                next_is_services = False
                if i + 1 < len(lines):
                    next_is_services = 'from src.services import' in lines[i + 1]

                if not next_is_services:
                    new_lines.append('from src.core.session_manager import session_manager')
                    import_added = True

        content = '\n'.join(new_lines)

    # Reemplazar usuario="admin" con session_manager
    content = re.sub(
        r'usuario="admin"',
        'usuario=session_manager.get_usuario_actual() or "admin"',
        content
    )

    # Escribir contenido actualizado
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[+] Actualizado: {filepath}")
    return True

def main():
    print("Actualizando ventanas para usar session_manager...\n")

    exitosos = 0
    for ventana_path in VENTANAS_PATHS:
        if actualizar_archivo(ventana_path):
            exitosos += 1

    print(f"\n[+] {exitosos}/{len(VENTANAS_PATHS)} archivos actualizados correctamente")

if __name__ == "__main__":
    main()
