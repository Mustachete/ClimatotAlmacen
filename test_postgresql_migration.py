"""
Script de pruebas para verificar la migración completa a PostgreSQL
Prueba las funciones principales de cada repositorio
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.db_utils import fetch_one, fetch_all, close_all_connections

def test_function(name, func, *args, **kwargs):
    """Ejecuta una función y reporta el resultado"""
    try:
        result = func(*args, **kwargs)
        print(f"  [OK] {name}")
        return True
    except Exception as e:
        print(f"  [ERROR] {name}: {str(e)[:80]}")
        return False

def main():
    print("=" * 70)
    print("PRUEBAS DE MIGRACION A POSTGRESQL")
    print("=" * 70)

    passed = 0
    failed = 0

    # ========================================
    # 1. VERIFICAR CONEXION POSTGRESQL
    # ========================================
    print("\n[1] VERIFICANDO CONEXION POSTGRESQL...")

    try:
        result = fetch_one("SELECT version()")
        if result and 'PostgreSQL' in result['version']:
            print(f"  [OK] Conectado a: {result['version'][:60]}...")
            passed += 1
        else:
            print("  [ERROR] No se detectó PostgreSQL")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] Error de conexión: {e}")
        failed += 1

    # ========================================
    # 2. VERIFICAR SINTAXIS POSTGRESQL
    # ========================================
    print("\n[2] VERIFICANDO SINTAXIS POSTGRESQL...")

    # Placeholders %s
    try:
        test_query = fetch_one("SELECT %s as test_value", (42,))
        if test_query and test_query['test_value'] == 42:
            print("  [OK] Placeholders PostgreSQL (%s) funcionan")
            passed += 1
        else:
            print("  [ERROR] Problema con placeholders")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] Placeholders: {e}")
        failed += 1

    # Funciones de fecha
    try:
        test_pg = fetch_one("SELECT NOW() as ahora, CURRENT_DATE as hoy")
        if test_pg:
            print("  [OK] Funciones NOW() y CURRENT_DATE funcionan")
            passed += 1
        else:
            print("  [ERROR] Problema con funciones de fecha")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] Funciones de fecha: {e}")
        failed += 1

    # JSONB operators
    try:
        test_jsonb = fetch_one("SELECT '{\"key\": \"value\"}'::jsonb @> '{\"key\": \"value\"}'::jsonb as test")
        if test_jsonb and test_jsonb['test']:
            print("  [OK] Operadores JSONB (@>) funcionan")
            passed += 1
        else:
            print("  [ERROR] Problema con operadores JSONB")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] Operadores JSONB: {e}")
        failed += 1

    # ON CONFLICT
    try:
        # Crear tabla temporal
        fetch_one("CREATE TEMP TABLE test_conflict (id INT PRIMARY KEY, val TEXT)")
        fetch_one("INSERT INTO test_conflict VALUES (%s, %s)", (1, 'test'))
        fetch_one("INSERT INTO test_conflict VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET val = EXCLUDED.val", (1, 'updated'))
        result = fetch_one("SELECT val FROM test_conflict WHERE id = %s", (1,))
        if result and result['val'] == 'updated':
            print("  [OK] ON CONFLICT (reemplazo de INSERT OR REPLACE) funciona")
            passed += 1
        else:
            print("  [ERROR] Problema con ON CONFLICT")
            failed += 1
    except Exception as e:
        print(f"  [ERROR] ON CONFLICT: {e}")
        failed += 1

    # ========================================
    # 3. PROBAR REPOSITORIOS PRINCIPALES
    # ========================================
    print("\n[3] PROBANDO REPOSITORIOS...")

    from src.repos import (
        usuarios_repo, articulos_repo, familias_repo,
        proveedores_repo, operarios_repo, ubicaciones_repo,
        almacenes_repo, stock_repo, movimientos_repo,
        inventarios_repo, albaranes_repo, sesiones_repo
    )

    # Usuarios
    print("\n  Usuarios:")
    if test_function("get_by_usuario", usuarios_repo.get_by_usuario, "admin"):
        passed += 1
    else:
        failed += 1

    if test_function("get_todos", usuarios_repo.get_todos, None, None, 10):
        passed += 1
    else:
        failed += 1

    # Artículos
    print("\n  Articulos:")
    if test_function("get_by_id", articulos_repo.get_by_id, 1):
        passed += 1
    else:
        failed += 1

    if test_function("get_todos", articulos_repo.get_todos, "", None, None, 10):
        passed += 1
    else:
        failed += 1

    # Familias
    print("\n  Familias:")
    if test_function("get_by_id", familias_repo.get_by_id, 1):
        passed += 1
    else:
        failed += 1

    if test_function("listar_todas", familias_repo.listar_todas):
        passed += 1
    else:
        failed += 1

    # Proveedores
    print("\n  Proveedores:")
    if test_function("get_by_id", proveedores_repo.get_by_id, 1):
        passed += 1
    else:
        failed += 1

    # Operarios
    print("\n  Operarios:")
    if test_function("get_by_id", operarios_repo.get_by_id, 1):
        passed += 1
    else:
        failed += 1

    # Ubicaciones
    print("\n  Ubicaciones:")
    if test_function("listar_todas", ubicaciones_repo.listar_todas):
        passed += 1
    else:
        failed += 1

    # Almacenes
    print("\n  Almacenes:")
    if test_function("list_all", almacenes_repo.list_all):
        passed += 1
    else:
        failed += 1

    if test_function("get_almacen_central", almacenes_repo.get_almacen_central):
        passed += 1
    else:
        failed += 1

    # Stock
    print("\n  Stock:")
    if test_function("get_stock_total", stock_repo.get_stock_total, 1):
        passed += 1
    else:
        failed += 1

    # Movimientos
    print("\n  Movimientos:")
    if test_function("buscar_movimientos", movimientos_repo.buscar_movimientos, articulo_id=1, limit=10):
        passed += 1
    else:
        failed += 1

    # Inventarios
    print("\n  Inventarios:")
    if test_function("listar_inventarios", inventarios_repo.listar_inventarios, limit=10):
        passed += 1
    else:
        failed += 1

    # Albaranes
    print("\n  Albaranes:")
    if test_function("get_todos", albaranes_repo.get_todos, None, 10):
        passed += 1
    else:
        failed += 1

    # Sesiones
    print("\n  Sesiones:")
    if test_function("obtener_sesiones_activas", sesiones_repo.obtener_sesiones_activas):
        passed += 1
    else:
        failed += 1

    # ========================================
    # 4. VERIFICAR QUE NO HAY CODIGO SQLITE
    # ========================================
    print("\n[4] VERIFICANDO QUE NO HAY CODIGO SQLITE...")

    # Buscar imports de sqlite3
    import os
    sqlite_found = False
    for root, dirs, files in os.walk('src'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for filename in files:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'import sqlite3' in content or 'from sqlite3' in content:
                            print(f"  [ERROR] Encontrado 'import sqlite3' en {filepath}")
                            sqlite_found = True
                            failed += 1
                except:
                    pass

    if not sqlite_found:
        print("  [OK] No se encontraron imports de sqlite3")
        passed += 1

    # ========================================
    # RESUMEN
    # ========================================
    close_all_connections()

    total = passed + failed
    print("\n" + "=" * 70)
    print("RESUMEN DE PRUEBAS")
    print("=" * 70)
    print(f"Total pruebas: {total}")
    print(f"Exitosas: {passed}")
    print(f"Fallidas: {failed}")
    print(f"Porcentaje exito: {(passed/total*100):.1f}%" if total > 0 else "N/A")

    if failed == 0:
        print("\n[OK] TODAS LAS PRUEBAS PASARON - MIGRACION COMPLETA")
        return 0
    else:
        print(f"\n[ERROR] {failed} PRUEBAS FALLARON")
        return 1

if __name__ == "__main__":
    sys.exit(main())
