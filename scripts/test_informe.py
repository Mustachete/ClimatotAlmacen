#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para el informe de furgonetas
"""
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import fetch_all, fetch_one
from src.services import informes_furgonetas_service

print("=" * 80)
print("DIAGNÓSTICO DEL INFORME DE FURGONETAS")
print("=" * 80)

# 1. Verificar furgonetas disponibles
print("\n1. FURGONETAS DISPONIBLES:")
furgonetas = fetch_all("SELECT id, nombre FROM almacenes WHERE tipo = 'furgoneta'")
for f in furgonetas:
    print(f"   - ID: {f['id']}, Nombre: {f['nombre']}")

if not furgonetas:
    print("   ERROR: No hay furgonetas en el sistema")
    sys.exit(1)

# Usar la primera furgoneta
furgoneta_id = furgonetas[0]['id']
furgoneta_nombre = furgonetas[0]['nombre']
print(f"\n   >> Usando furgoneta: {furgoneta_nombre} (ID: {furgoneta_id})")

# 2. Verificar movimientos de la furgoneta
print(f"\n2. MOVIMIENTOS DE LA FURGONETA {furgoneta_nombre}:")
movs_total = fetch_one("""
    SELECT COUNT(*) as total
    FROM movimientos
    WHERE origen_id = ? OR destino_id = ?
""", (furgoneta_id, furgoneta_id))
print(f"   Total movimientos: {movs_total['total']}")

# Movimientos por tipo
movs_por_tipo = fetch_all("""
    SELECT tipo, COUNT(*) as cuenta
    FROM movimientos
    WHERE origen_id = ? OR destino_id = ?
    GROUP BY tipo
""", (furgoneta_id, furgoneta_id))
print("\n   Por tipo:")
for m in movs_por_tipo:
    print(f"      {m['tipo']}: {m['cuenta']}")

# 3. Verificar rango de fechas
print("\n3. RANGO DE FECHAS:")
rango = fetch_one("""
    SELECT MIN(fecha) as primera, MAX(fecha) as ultima
    FROM movimientos
    WHERE origen_id = ? OR destino_id = ?
""", (furgoneta_id, furgoneta_id))
print(f"   Primera fecha: {rango['primera']}")
print(f"   Última fecha: {rango['ultima']}")

# Calcular lunes de la semana pasada
hoy = datetime.now()
lunes_actual = hoy - timedelta(days=hoy.weekday())  # 0=Lunes
lunes_pasado = lunes_actual - timedelta(days=7)
fecha_lunes = lunes_pasado.strftime("%Y-%m-%d")

print(f"\n   >> Usando fecha (lunes de semana pasada): {fecha_lunes}")

# 4. Verificar movimientos en esa semana
viernes = lunes_pasado + timedelta(days=4)
fecha_viernes = viernes.strftime("%Y-%m-%d")

movs_semana = fetch_one("""
    SELECT COUNT(*) as total
    FROM movimientos
    WHERE (origen_id = ? OR destino_id = ?)
      AND fecha BETWEEN ? AND ?
""", (furgoneta_id, furgoneta_id, fecha_lunes, fecha_viernes))
print(f"\n4. MOVIMIENTOS EN LA SEMANA {fecha_lunes} - {fecha_viernes}:")
print(f"   Total: {movs_semana['total']}")

if movs_semana['total'] == 0:
    print("\n   ⚠️  No hay movimientos en esa semana. Probando con última semana con datos...")
    # Obtener última fecha con movimientos
    ultima = fetch_one("""
        SELECT MAX(fecha) as fecha
        FROM movimientos
        WHERE origen_id = ? OR destino_id = ?
    """, (furgoneta_id, furgoneta_id))

    if ultima and ultima['fecha']:
        fecha_ultima = datetime.strptime(ultima['fecha'], "%Y-%m-%d")
        # Calcular lunes de esa semana
        lunes_ultima = fecha_ultima - timedelta(days=fecha_ultima.weekday())
        fecha_lunes = lunes_ultima.strftime("%Y-%m-%d")
        print(f"   >> Nueva fecha a probar: {fecha_lunes}")

# 5. Generar informe
print(f"\n5. GENERANDO INFORME:")
print(f"   Furgoneta ID: {furgoneta_id}")
print(f"   Fecha lunes: {fecha_lunes}")

exito, mensaje, datos = informes_furgonetas_service.generar_datos_informe(
    furgoneta_id,
    fecha_lunes
)

print(f"\n   Éxito: {exito}")
print(f"   Mensaje: {mensaje}")

if exito and datos:
    print(f"\n6. RESULTADO DEL INFORME:")
    print(f"   Furgoneta: {datos['furgoneta_nombre']}")
    print(f"   Fecha inicio: {datos['fecha_inicio']}")
    print(f"   Fecha fin: {datos['fecha_fin']}")
    print(f"   Días en semana: {len(datos['dias_semana'])}")
    print(f"   Operarios: {', '.join(datos['operarios']) if datos['operarios'] else 'Sin operarios'}")
    print(f"   Artículos: {len(datos['articulos'])}")

    if datos['articulos']:
        print("\n   Primeros 5 artículos:")
        for i, art in enumerate(datos['articulos'][:5]):
            print(f"\n      [{i+1}] {art['articulo_nombre']} ({art['familia']})")
            print(f"          Stock inicial: {art['stock_inicial']:.2f}")
            print(f"          Total E: {art['total_e']:.2f}")
            print(f"          Total D: {art['total_d']:.2f}")
            print(f"          Total G: {art['total_g']:.2f}")
            print(f"          Stock final: {art['stock_final']:.2f}")
            print(f"          Días con movimientos: {len(art['movimientos_diarios'])}")
    else:
        print("\n   ⚠️  NO HAY ARTÍCULOS EN EL INFORME")
else:
    print("\n   ❌ ERROR AL GENERAR INFORME")

print("\n" + "=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)
