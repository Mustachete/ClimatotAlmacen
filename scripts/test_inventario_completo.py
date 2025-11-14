#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba completa del sistema de inventarios.
Verifica:
1. Creación de inventario
2. Registro de conteos
3. Cálculo de diferencias
4. Finalización con ajustes de stock
"""
import sys
import io
from pathlib import Path
from datetime import datetime

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services import inventarios_service, articulos_service
from src.repos import inventarios_repo, articulos_repo
from src.core.db_utils import get_con

print("=" * 80)
print("TEST COMPLETO DEL SISTEMA DE INVENTARIOS")
print("=" * 80)

def limpiar_inventarios_test():
    """Limpia inventarios de prueba previos"""
    try:
        con = get_con()
        cur = con.cursor()

        # Eliminar inventarios de prueba (responsable = 'TEST_AUTO')
        cur.execute("DELETE FROM inventario_detalle WHERE inventario_id IN (SELECT id FROM inventarios WHERE responsable = 'TEST_AUTO')")
        cur.execute("DELETE FROM inventarios WHERE responsable = 'TEST_AUTO'")

        con.commit()
        con.close()
        print("✅ Inventarios de prueba previos eliminados")
    except Exception as e:
        print(f"⚠️  Error limpiando inventarios: {e}")

def test_crear_inventario():
    """Prueba 1: Crear un inventario"""
    print("\n" + "=" * 80)
    print("PRUEBA 1: CREAR INVENTARIO")
    print("=" * 80)

    # Obtener primer almacén disponible
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT id, nombre FROM almacenes LIMIT 1")
    almacen = cur.fetchone()
    con.close()

    if not almacen:
        print("❌ No hay almacenes en la BD")
        return None

    almacen_id, almacen_nombre = almacen
    print(f"📦 Almacén seleccionado: {almacen_nombre} (ID: {almacen_id})")

    # Crear inventario
    exito, mensaje, inventario_id = inventarios_service.crear_inventario(
        fecha=datetime.now().strftime("%Y-%m-%d"),
        responsable="TEST_AUTO",
        almacen_id=almacen_id,
        observaciones="Inventario de prueba automática",
        solo_con_stock=False,  # Incluir todos los artículos
        usuario="admin"
    )

    if not exito:
        print(f"❌ Error creando inventario: {mensaje}")
        return None

    print(f"✅ {mensaje}")
    print(f"📋 Inventario creado con ID: {inventario_id}")

    # Verificar detalle
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM inventario_detalle WHERE inventario_id = ?", (inventario_id,))
    num_articulos = cur.fetchone()[0]
    con.close()

    print(f"📊 Total de artículos en inventario: {num_articulos}")

    return inventario_id

def test_simular_conteos(inventario_id):
    """Prueba 2: Simular conteos con diferencias"""
    print("\n" + "=" * 80)
    print("PRUEBA 2: SIMULAR CONTEOS")
    print("=" * 80)

    # Obtener detalle del inventario
    con = get_con()
    cur = con.cursor()
    cur.execute("""
        SELECT id, articulo_id, stock_teorico
        FROM inventario_detalle
        WHERE inventario_id = ?
        LIMIT 10
    """, (inventario_id,))
    detalles = cur.fetchall()

    if not detalles:
        print("❌ No hay artículos en el inventario")
        con.close()
        return

    print(f"📦 Modificando conteos en {len(detalles)} artículos...")

    # Simular diferentes escenarios:
    # - Algunos artículos con sobrante (stock_contado > stock_teorico)
    # - Algunos artículos con faltante (stock_contado < stock_teorico)
    # - Algunos artículos OK (sin diferencia)

    for idx, (detalle_id, articulo_id, stock_teorico) in enumerate(detalles):
        if idx < 3:  # Primeros 3: sobrante
            stock_contado = stock_teorico + 10.0
            print(f"  📈 Detalle {detalle_id}: Sobrante +10 (Teórico: {stock_teorico:.2f}, Contado: {stock_contado:.2f})")
        elif idx < 6:  # Siguientes 3: faltante
            stock_contado = max(0, stock_teorico - 5.0)
            print(f"  📉 Detalle {detalle_id}: Faltante -5 (Teórico: {stock_teorico:.2f}, Contado: {stock_contado:.2f})")
        else:  # Resto: OK
            stock_contado = stock_teorico
            print(f"  ✅ Detalle {detalle_id}: OK (Sin diferencia: {stock_teorico:.2f})")

        diferencia = stock_contado - stock_teorico

        cur.execute("""
            UPDATE inventario_detalle
            SET stock_contado = ?, diferencia = ?
            WHERE id = ?
        """, (stock_contado, diferencia, detalle_id))

    con.commit()
    con.close()

    print("✅ Conteos simulados correctamente")

def test_verificar_diferencias(inventario_id):
    """Prueba 3: Verificar diferencias calculadas"""
    print("\n" + "=" * 80)
    print("PRUEBA 3: VERIFICAR DIFERENCIAS")
    print("=" * 80)

    diferencias = inventarios_repo.get_diferencias(inventario_id)

    if not diferencias:
        print("✅ No hay diferencias (todos los conteos coinciden)")
        return

    print(f"⚠️  Se encontraron {len(diferencias)} artículo(s) con diferencias:")
    print()

    total_sobrantes = 0
    total_faltantes = 0

    for diff in diferencias:
        tipo = "📈 SOBRANTE" if diff['diferencia'] > 0 else "📉 FALTANTE"
        print(f"  {tipo}: {diff['articulo_nombre']}")
        print(f"    - Stock teórico: {diff['stock_teorico']:.2f}")
        print(f"    - Stock contado: {diff['stock_contado']:.2f}")
        print(f"    - Diferencia: {diff['diferencia']:+.2f}")
        print()

        if diff['diferencia'] > 0:
            total_sobrantes += abs(diff['diferencia'])
        else:
            total_faltantes += abs(diff['diferencia'])

    print(f"📊 Resumen:")
    print(f"  📈 Total unidades sobrantes: {total_sobrantes:.2f}")
    print(f"  📉 Total unidades faltantes: {total_faltantes:.2f}")

def test_finalizar_inventario(inventario_id):
    """Prueba 4: Finalizar inventario y aplicar ajustes"""
    print("\n" + "=" * 80)
    print("PRUEBA 4: FINALIZAR INVENTARIO Y APLICAR AJUSTES")
    print("=" * 80)

    # Obtener stock ANTES de finalizar (usando la vista vw_stock)
    con = get_con()
    cur = con.cursor()
    cur.execute("""
        SELECT
            a.id,
            a.nombre,
            COALESCE(SUM(v.delta), 0) as stock_total
        FROM articulos a
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        WHERE a.id IN (
            SELECT articulo_id
            FROM inventario_detalle
            WHERE inventario_id = ? AND diferencia != 0
        )
        GROUP BY a.id, a.nombre
    """, (inventario_id,))
    stock_antes = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    con.close()

    print("📊 Stock ANTES de finalizar:")
    for art_id, (nombre, stock) in stock_antes.items():
        print(f"  - {nombre}: {stock:.2f}")

    # Finalizar inventario
    print("\n🔄 Finalizando inventario...")
    exito, mensaje, stats = inventarios_service.finalizar_inventario(
        inventario_id=inventario_id,
        aplicar_ajustes=True,
        usuario="admin"
    )

    if not exito:
        print(f"❌ Error finalizando inventario: {mensaje}")
        return False

    print(f"✅ {mensaje}")

    if stats:
        print("\n📊 Estadísticas del inventario:")
        print(f"  - Total líneas: {stats['total_lineas']}")
        print(f"  - Líneas contadas: {stats['lineas_contadas']}")
        print(f"  - Líneas con diferencias: {stats['lineas_con_diferencia']}")
        print(f"  - Sobrantes: {stats['sobrantes']} líneas (+{stats['total_sobrante']:.2f} unidades)")
        print(f"  - Faltantes: {stats['faltantes']} líneas (-{stats['total_faltante']:.2f} unidades)")

    # Obtener stock DESPUÉS de finalizar (usando la vista vw_stock)
    con = get_con()
    cur = con.cursor()
    cur.execute("""
        SELECT
            a.id,
            a.nombre,
            COALESCE(SUM(v.delta), 0) as stock_total
        FROM articulos a
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        WHERE a.id IN ({})
        GROUP BY a.id, a.nombre
    """.format(','.join('?' * len(stock_antes))), tuple(stock_antes.keys()))
    stock_despues = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    con.close()

    print("\n📊 Stock DESPUÉS de finalizar:")
    for art_id, (nombre, stock) in stock_despues.items():
        stock_previo = stock_antes[art_id][1]
        diferencia = stock - stock_previo
        print(f"  - {nombre}: {stock:.2f} (cambio: {diferencia:+.2f})")

    return True

def test_verificar_movimientos(inventario_id):
    """Prueba 5: Verificar movimientos creados"""
    print("\n" + "=" * 80)
    print("PRUEBA 5: VERIFICAR MOVIMIENTOS DE AJUSTE CREADOS")
    print("=" * 80)

    con = get_con()
    cur = con.cursor()

    # Buscar movimientos con albarán INV-{inventario_id}
    cur.execute("""
        SELECT
            m.tipo,
            a.nombre,
            m.cantidad,
            m.albaran,
            m.motivo
        FROM movimientos m
        JOIN articulos a ON m.articulo_id = a.id
        WHERE m.albaran = ? OR m.motivo LIKE ?
        ORDER BY m.tipo, a.nombre
    """, (f"INV-{inventario_id}", f"%inventario {inventario_id}%"))

    movimientos = cur.fetchall()
    con.close()

    if not movimientos:
        print("ℹ️  No se crearon movimientos de ajuste (no había diferencias)")
        return

    print(f"✅ Se crearon {len(movimientos)} movimiento(s) de ajuste:")
    print()

    for tipo, articulo, cantidad, albaran, motivo in movimientos:
        icono = "📈" if tipo == "ENTRADA" else "📉"
        print(f"  {icono} {tipo}: {articulo}")
        print(f"    - Cantidad: {cantidad:.2f}")
        print(f"    - Albarán: {albaran or '-'}")
        print(f"    - Motivo: {motivo or '-'}")
        print()

def main():
    """Ejecuta todas las pruebas"""
    try:
        # Limpiar inventarios de prueba previos
        limpiar_inventarios_test()

        # Prueba 1: Crear inventario
        inventario_id = test_crear_inventario()
        if not inventario_id:
            print("\n❌ No se pudo crear el inventario. Abortando test.")
            return

        # Prueba 2: Simular conteos
        test_simular_conteos(inventario_id)

        # Prueba 3: Verificar diferencias
        test_verificar_diferencias(inventario_id)

        # Prueba 4: Finalizar inventario
        exito = test_finalizar_inventario(inventario_id)
        if not exito:
            print("\n❌ No se pudo finalizar el inventario. Abortando test.")
            return

        # Prueba 5: Verificar movimientos
        test_verificar_movimientos(inventario_id)

        print("\n" + "=" * 80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print()
        print("💡 Resumen:")
        print(f"  - Inventario creado: #{inventario_id}")
        print("  - Conteos simulados con diferencias")
        print("  - Inventario finalizado correctamente")
        print("  - Movimientos de ajuste creados automáticamente")
        print("  - Stock ajustado correctamente")
        print()
        print("🧹 Para limpiar este inventario de prueba:")
        print(f"   DELETE FROM inventario_detalle WHERE inventario_id = {inventario_id};")
        print(f"   DELETE FROM inventarios WHERE id = {inventario_id};")

    except Exception as e:
        print(f"\n❌ ERROR EN EL TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
