"""
Script para verificar que todos los imports del proyecto funcionan correctamente
"""
import sys
from pathlib import Path

# Anadir el directorio raiz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

print("=" * 60)
print("VERIFICACION DE IMPORTS DEL SISTEMA CLIMATOT ALMACEN")
print("=" * 60)

errores = []
exitosos = []

# ========================================
# VERIFICAR MODULOS CORE
# ========================================
print("\n[CORE] Verificando modulos CORE...")
modulos_core = [
    "src.core.db_utils",
    "src.core.session_manager",
    "src.core.logger",
    "src.core.error_handler",
    "src.core.idle_manager",
]

for modulo in modulos_core:
    try:
        __import__(modulo)
        exitosos.append(modulo)
        print(f"  [OK] {modulo}")
    except Exception as e:
        errores.append((modulo, str(e)))
        print(f"  [ERROR] {modulo}: {e}")

# ========================================
# VERIFICAR REPOSITORIOS
# ========================================
print("\n[REPOS] Verificando REPOSITORIOS...")
repos = [
    "src.repos.articulos_repo",
    "src.repos.consumos_repo",
    "src.repos.familias_repo",
    "src.repos.furgonetas_repo",
    "src.repos.inventarios_repo",
    "src.repos.movimientos_repo",
    "src.repos.operarios_repo",
    "src.repos.pedido_ideal_repo",
    "src.repos.proveedores_repo",
    "src.repos.ubicaciones_repo",
    "src.repos.usuarios_repo",
]

for repo in repos:
    try:
        __import__(repo)
        exitosos.append(repo)
        print(f"  [OK] {repo}")
    except Exception as e:
        errores.append((repo, str(e)))
        print(f"  [ERROR] {repo}: {e}")

# ========================================
# VERIFICAR SERVICIOS
# ========================================
print("\n[SERVICES] Verificando SERVICIOS...")
servicios = [
    "src.services.articulos_service",
    "src.services.consumos_service",
    "src.services.familias_service",
    "src.services.furgonetas_service",
    "src.services.inventarios_service",
    "src.services.movimientos_service",
    "src.services.operarios_service",
    "src.services.pedido_ideal_service",
    "src.services.proveedores_service",
    "src.services.ubicaciones_service",
    "src.services.usuarios_service",
]

for servicio in servicios:
    try:
        __import__(servicio)
        exitosos.append(servicio)
        print(f"  [OK] {servicio}")
    except Exception as e:
        errores.append((servicio, str(e)))
        print(f"  [ERROR] {servicio}: {e}")

# ========================================
# VERIFICAR UI
# ========================================
print("\n[UI] Verificando UI...")
ui_modules = [
    "src.ui.estilos",
    "src.ui.widgets_personalizados",
]

for modulo in ui_modules:
    try:
        __import__(modulo)
        exitosos.append(modulo)
        print(f"  [OK] {modulo}")
    except Exception as e:
        errores.append((modulo, str(e)))
        print(f"  [ERROR] {modulo}: {e}")

# ========================================
# VERIFICAR VENTANAS MAESTROS
# ========================================
print("\n[MAESTROS] Verificando VENTANAS MAESTROS...")
ventanas_maestros = [
    "src.ventanas.maestros.ventana_articulos",
    "src.ventanas.maestros.ventana_familias",
    "src.ventanas.maestros.ventana_furgonetas",
    "src.ventanas.maestros.ventana_operarios",
    "src.ventanas.maestros.ventana_proveedores",
    "src.ventanas.maestros.ventana_ubicaciones",
    "src.ventanas.maestros.ventana_usuarios",
]

for ventana in ventanas_maestros:
    try:
        __import__(ventana)
        exitosos.append(ventana)
        print(f"  [OK] {ventana}")
    except Exception as e:
        errores.append((ventana, str(e)))
        print(f"  [ERROR] {ventana}: {e}")

# ========================================
# VERIFICAR VENTANAS OPERATIVAS
# ========================================
print("\n[OPERATIVAS] Verificando VENTANAS OPERATIVAS...")
ventanas_operativas = [
    "src.ventanas.operativas.ventana_recepcion",
    "src.ventanas.operativas.ventana_movimientos",
    "src.ventanas.operativas.ventana_imputacion",
    "src.ventanas.operativas.ventana_devolucion",
    "src.ventanas.operativas.ventana_material_perdido",
    "src.ventanas.operativas.ventana_inventario",
]

for ventana in ventanas_operativas:
    try:
        __import__(ventana)
        exitosos.append(ventana)
        print(f"  [OK] {ventana}")
    except Exception as e:
        errores.append((ventana, str(e)))
        print(f"  [ERROR] {ventana}: {e}")

# ========================================
# VERIFICAR VENTANAS CONSULTAS
# ========================================
print("\n[CONSULTAS] Verificando VENTANAS CONSULTAS...")
ventanas_consultas = [
    "src.ventanas.consultas.ventana_stock",
    "src.ventanas.consultas.ventana_historico",
    "src.ventanas.consultas.ventana_consumos",
    "src.ventanas.consultas.ventana_pedido_ideal",
    "src.ventanas.consultas.ventana_ficha_articulo",
]

for ventana in ventanas_consultas:
    try:
        __import__(ventana)
        exitosos.append(ventana)
        print(f"  [OK] {ventana}")
    except Exception as e:
        errores.append((ventana, str(e)))
        print(f"  [ERROR] {ventana}: {e}")

# ========================================
# VERIFICAR VENTANAS ADICIONALES
# ========================================
print("\n[ADICIONALES] Verificando VENTANAS ADICIONALES...")
ventanas_adicionales = [
    "src.ventanas.ventana_login",
    "src.ventanas.dialogo_cambiar_password",
]

for ventana in ventanas_adicionales:
    try:
        __import__(ventana)
        exitosos.append(ventana)
        print(f"  [OK] {ventana}")
    except Exception as e:
        errores.append((ventana, str(e)))
        print(f"  [ERROR] {ventana}: {e}")

# ========================================
# VERIFICAR DIALOGOS
# ========================================
print("\n[DIALOGOS] Verificando DIALOGOS...")
dialogos = [
    "src.dialogs.buscador_articulos",
]

for dialogo in dialogos:
    try:
        __import__(dialogo)
        exitosos.append(dialogo)
        print(f"  [OK] {dialogo}")
    except Exception as e:
        errores.append((dialogo, str(e)))
        print(f"  [ERROR] {dialogo}: {e}")

# ========================================
# RESUMEN
# ========================================
print("\n" + "=" * 60)
print("RESUMEN DE LA VERIFICACION")
print("=" * 60)
print(f"[OK] Modulos exitosos: {len(exitosos)}")
print(f"[ERROR] Modulos con errores: {len(errores)}")

if errores:
    print("\n[!] ERRORES ENCONTRADOS:")
    for modulo, error in errores:
        print(f"\n  [ERROR] {modulo}")
        print(f"     Error: {error}")
    sys.exit(1)
else:
    print("\n[OK] TODOS LOS IMPORTS FUNCIONAN CORRECTAMENTE!")
    sys.exit(0)
