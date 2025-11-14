#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar todos los movimientos y dejar stocks en cero.
Mantiene los maestros (artículos, proveedores, operarios, furgonetas, etc.)
"""
import sys
import io
from pathlib import Path

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con

print("=" * 70)
print("LIMPIEZA DE STOCKS - ELIMINANDO TODOS LOS MOVIMIENTOS")
print("=" * 70)
print()

# Confirmar acción
print("⚠️  ADVERTENCIA: Este script va a:")
print("   1. Eliminar TODOS los movimientos")
print("   2. Eliminar TODOS los albaranes")
print("   3. Eliminar TODO el historial de operaciones")
print("   4. Mantener los maestros (artículos, proveedores, operarios, furgonetas)")
print("   5. Dejar todos los stocks en CERO")
print()

# Verificar si se pasó el argumento --force
if len(sys.argv) > 1 and sys.argv[1] == '--force':
    print("⚡ Modo --force activado, omitiendo confirmación")
    respuesta = 'SI'
else:
    respuesta = input("¿Está seguro de continuar? (escriba 'SI' para confirmar): ")

if respuesta.upper() != 'SI':
    print("\n❌ Operación cancelada por el usuario")
    sys.exit(0)

print("\n🔄 Iniciando limpieza...\n")

try:
    con = get_con()
    cur = con.cursor()

    # 1. Contar registros antes
    cur.execute("SELECT COUNT(*) FROM movimientos")
    count_movimientos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM albaranes")
    count_albaranes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM historial_operaciones")
    count_historial = cur.fetchone()[0]

    print(f"📊 Registros actuales:")
    print(f"   - Movimientos: {count_movimientos}")
    print(f"   - Albaranes: {count_albaranes}")
    print(f"   - Historial: {count_historial}")
    print()

    # 2. Eliminar movimientos
    print("🗑️  Eliminando movimientos...")
    cur.execute("DELETE FROM movimientos")
    print(f"   ✅ {count_movimientos} movimientos eliminados")

    # 3. Eliminar albaranes
    print("🗑️  Eliminando albaranes...")
    cur.execute("DELETE FROM albaranes")
    print(f"   ✅ {count_albaranes} albaranes eliminados")

    # 4. Eliminar historial
    print("🗑️  Eliminando historial de operaciones...")
    cur.execute("DELETE FROM historial_operaciones")
    print(f"   ✅ {count_historial} registros de historial eliminados")

    # 5. Reiniciar autoincrement (opcional, para que los IDs empiecen desde 1)
    print("\n🔄 Reiniciando contadores de IDs...")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('movimientos', 'albaranes', 'historial_operaciones')")
    print("   ✅ Contadores reiniciados")

    # 6. Verificar que los stocks quedaron en cero
    print("\n📊 Verificando stocks...")
    cur.execute("""
        SELECT
            a.nombre,
            al.nombre as almacen,
            COALESCE(SUM(
                CASE
                    WHEN m.tipo IN ('ENTRADA', 'AJUSTE_POSITIVO') THEN m.cantidad
                    WHEN m.destino_id = al.id THEN m.cantidad
                    WHEN m.origen_id = al.id THEN -m.cantidad
                    ELSE 0
                END
            ), 0) as stock
        FROM articulos a
        CROSS JOIN almacenes al
        LEFT JOIN movimientos m ON m.articulo_id = a.id
            AND (m.origen_id = al.id OR m.destino_id = al.id)
        WHERE a.activo = 1
        GROUP BY a.id, al.id
        HAVING stock != 0
    """)

    stocks_no_cero = cur.fetchall()

    if stocks_no_cero:
        print(f"   ⚠️  ADVERTENCIA: {len(stocks_no_cero)} registros con stock diferente de cero")
        for row in stocks_no_cero[:5]:  # Mostrar solo los primeros 5
            print(f"      - {row[0]} en {row[1]}: {row[2]}")
    else:
        print("   ✅ Todos los stocks están en CERO")

    # 7. Mostrar resumen de maestros mantenidos
    print("\n📋 Maestros mantenidos:")

    cur.execute("SELECT COUNT(*) FROM articulos WHERE activo=1")
    print(f"   - Artículos activos: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM proveedores")
    print(f"   - Proveedores: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM familias")
    print(f"   - Familias: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM operarios WHERE activo=1")
    print(f"   - Operarios activos: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM almacenes")
    print(f"   - Almacenes/Furgonetas: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM ubicaciones")
    print(f"   - Ubicaciones: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM usuarios")
    print(f"   - Usuarios: {cur.fetchone()[0]}")

    # 8. Commit
    con.commit()
    con.close()

    print("\n" + "=" * 70)
    print("✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("\n📝 Próximos pasos:")
    print("   1. Los stocks están ahora en CERO")
    print("   2. Puede empezar a registrar recepciones reales")
    print("   3. Las validaciones de stock funcionarán correctamente")
    print("   4. No habrá más stocks negativos")
    print()

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
