#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con datos de prueba realistas.
Crea proveedores, artículos, y movimientos desde el 27/10 hasta hoy.
"""
import sys
import io
import random
from pathlib import Path
from datetime import datetime, timedelta

# Configurar encoding UTF-8 para la salida
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.db_utils import get_con, execute_query, fetch_all, fetch_one
from src.repos import proveedores_repo, articulos_repo, familias_repo
from src.repos.furgonetas_repo import list_furgonetas
from src.repos.operarios_repo import get_todos as get_operarios

print("=" * 60)
print("POBLANDO BASE DE DATOS CON DATOS DE PRUEBA")
print("=" * 60)

# ==================== PROVEEDORES ====================
print("\n[1/5] Creando proveedores...")
proveedores_data = [
    {
        'nombre': 'Suministros Climáticos SL',
        'cif': 'B12345678',
        'direccion': 'Calle Mayor 123, Madrid',
        'telefono': '915551234',
        'email': 'ventas@sumclimaticos.es',
        'contacto': 'Juan García'
    },
    {
        'nombre': 'Distribuciones Frío Total',
        'cif': 'B23456789',
        'direccion': 'Av. Industria 45, Barcelona',
        'telefono': '934442233',
        'email': 'pedidos@friototal.com',
        'contacto': 'María López'
    },
    {
        'nombre': 'Repuestos Airtech SA',
        'cif': 'A34567890',
        'direccion': 'Polígono Sur, Nave 12, Valencia',
        'telefono': '963338899',
        'email': 'info@airtech.es',
        'contacto': 'Pedro Martínez'
    },
    {
        'nombre': 'Climatización Profesional',
        'cif': 'B45678901',
        'direccion': 'C/ Comercio 78, Sevilla',
        'telefono': '954447788',
        'email': 'comercial@climapro.es',
        'contacto': 'Ana Fernández'
    },
    {
        'nombre': 'Mayorista HVAC Solutions',
        'cif': 'B56789012',
        'direccion': 'Ronda Norte 234, Zaragoza',
        'telefono': '976665544',
        'email': 'ventas@hvacsolutions.es',
        'contacto': 'Carlos Ruiz'
    },
    {
        'nombre': 'Componentes Clima Express',
        'cif': 'B67890123',
        'direccion': 'C/ Innovación 56, Bilbao',
        'telefono': '944332211',
        'email': 'pedidos@climaexpress.com',
        'contacto': 'Laura Sánchez'
    }
]

proveedores_ids = []
for prov in proveedores_data:
    # Intentar obtener existente primero
    existente = proveedores_repo.get_by_nombre(prov['nombre'])
    if existente:
        proveedores_ids.append(existente['id'])
        print(f"  OK Usando existente: {prov['nombre']} (ID: {existente['id']})")
    else:
        try:
            # crear_proveedor solo acepta: nombre, telefono, contacto, email, notas
            notas = f"CIF: {prov['cif']}\nDirección: {prov['direccion']}"
            prov_id = proveedores_repo.crear_proveedor(
                nombre=prov['nombre'],
                telefono=prov['telefono'],
                email=prov['email'],
                contacto=prov['contacto'],
                notas=notas
            )
            proveedores_ids.append(prov_id)
            print(f"  OK Creado: {prov['nombre']}")
        except Exception as e:
            print(f"  ADVERTENCIA Error al crear {prov['nombre']}: {e}")

print(f"  Total proveedores creados: {len(proveedores_ids)}")

# ==================== FAMILIAS ====================
print("\n[2/5] Verificando familias...")
familias = fetch_all("SELECT id, nombre FROM familias")
print(f"  Familias disponibles: {len(familias)}")
for fam in familias:
    print(f"    - {fam['nombre']} (ID: {fam['id']})")

# Si no hay familias, crear algunas
if len(familias) == 0:
    print("  Creando familias básicas...")
    familias_crear = [
        'Tubería de Cobre',
        'Gases Refrigerantes',
        'Válvulas y Conexiones',
        'Aislamiento',
        'Herramientas',
        'Consumibles'
    ]
    for nombre in familias_crear:
        try:
            fam_id = familias_repo.crear_familia(nombre=nombre, descripcion=f"Familia de {nombre}")
            print(f"    OK Creada familia: {nombre}")
        except Exception as e:
            print(f"    ADVERTENCIA Error: {e}")

    # Recargar familias
    familias = fetch_all("SELECT id, nombre FROM familias")

familia_ids = [f['id'] for f in familias]

# ==================== ARTÍCULOS ====================
print("\n[3/5] Creando artículos...")

articulos_data = [
    {
        'codigo': 'TUB-CU-15',
        'nombre': 'Tubo Cobre 1/2" x 15m',
        'u_medida': 'rollo',
        'familia_id': familia_ids[0] if len(familia_ids) > 0 else None,
        'proveedor_id': proveedores_ids[0] if proveedores_ids else None,
        'precio_compra': 45.50,
        'stock_minimo': 10.0,
        'stock_optimo': 30.0
    },
    {
        'codigo': 'TUB-CU-25',
        'nombre': 'Tubo Cobre 3/4" x 25m',
        'u_medida': 'rollo',
        'familia_id': familia_ids[0] if len(familia_ids) > 0 else None,
        'proveedor_id': proveedores_ids[0] if proveedores_ids else None,
        'precio_compra': 78.90,
        'stock_minimo': 8.0,
        'stock_optimo': 25.0
    },
    {
        'codigo': 'GAS-R32-5',
        'nombre': 'Gas R32 Botella 5kg',
        'u_medida': 'kg',
        'familia_id': familia_ids[1] if len(familia_ids) > 1 else None,
        'proveedor_id': proveedores_ids[1] if len(proveedores_ids) > 1 else proveedores_ids[0],
        'precio_compra': 125.00,
        'stock_minimo': 20.0,
        'stock_optimo': 50.0
    },
    {
        'codigo': 'GAS-R410-10',
        'nombre': 'Gas R410A Botella 10kg',
        'u_medida': 'kg',
        'familia_id': familia_ids[1] if len(familia_ids) > 1 else None,
        'proveedor_id': proveedores_ids[1] if len(proveedores_ids) > 1 else proveedores_ids[0],
        'precio_compra': 215.00,
        'stock_minimo': 15.0,
        'stock_optimo': 40.0
    },
    {
        'codigo': 'VAL-SF-12',
        'nombre': 'Válvula Esfera 1/2"',
        'u_medida': 'unidad',
        'familia_id': familia_ids[2] if len(familia_ids) > 2 else None,
        'proveedor_id': proveedores_ids[2] if len(proveedores_ids) > 2 else proveedores_ids[0],
        'precio_compra': 8.50,
        'stock_minimo': 50.0,
        'stock_optimo': 150.0
    },
    {
        'codigo': 'VAL-SF-34',
        'nombre': 'Válvula Esfera 3/4"',
        'u_medida': 'unidad',
        'familia_id': familia_ids[2] if len(familia_ids) > 2 else None,
        'proveedor_id': proveedores_ids[2] if len(proveedores_ids) > 2 else proveedores_ids[0],
        'precio_compra': 12.75,
        'stock_minimo': 40.0,
        'stock_optimo': 120.0
    },
    {
        'codigo': 'AISL-TUBO-15',
        'nombre': 'Aislamiento Tubo 1/2" x 2m',
        'u_medida': 'metro',
        'familia_id': familia_ids[3] if len(familia_ids) > 3 else None,
        'proveedor_id': proveedores_ids[3] if len(proveedores_ids) > 3 else proveedores_ids[0],
        'precio_compra': 3.20,
        'stock_minimo': 100.0,
        'stock_optimo': 300.0
    },
    {
        'codigo': 'AISL-TUBO-25',
        'nombre': 'Aislamiento Tubo 3/4" x 2m',
        'u_medida': 'metro',
        'familia_id': familia_ids[3] if len(familia_ids) > 3 else None,
        'proveedor_id': proveedores_ids[3] if len(proveedores_ids) > 3 else proveedores_ids[0],
        'precio_compra': 4.50,
        'stock_minimo': 80.0,
        'stock_optimo': 250.0
    },
    {
        'codigo': 'HERR-CORTA',
        'nombre': 'Cortador de Tubo 1/4"-1"',
        'u_medida': 'unidad',
        'familia_id': familia_ids[4] if len(familia_ids) > 4 else None,
        'proveedor_id': proveedores_ids[4] if len(proveedores_ids) > 4 else proveedores_ids[0],
        'precio_compra': 28.90,
        'stock_minimo': 5.0,
        'stock_optimo': 15.0
    },
    {
        'codigo': 'CONS-CINT',
        'nombre': 'Cinta Aislante 19mm x 20m',
        'u_medida': 'rollo',
        'familia_id': familia_ids[5] if len(familia_ids) > 5 else None,
        'proveedor_id': proveedores_ids[5] if len(proveedores_ids) > 5 else proveedores_ids[0],
        'precio_compra': 2.80,
        'stock_minimo': 80.0,
        'stock_optimo': 200.0
    }
]

articulos_ids = []
for art in articulos_data:
    # Intentar obtener por ref_proveedor
    existente = fetch_one("SELECT id FROM articulos WHERE ref_proveedor = ?", (art['codigo'],))
    if existente:
        articulos_ids.append(existente['id'])
        print(f"  OK Usando existente: {art['nombre']} ({art['codigo']}) ID:{existente['id']}")
    else:
        try:
            # crear_articulo params: nombre, ean, ref_proveedor, palabras_clave, u_medida,
            # min_alerta, ubicacion_id, proveedor_id, familia_id, marca, coste, pvp_sin, iva, activo
            art_id = articulos_repo.crear_articulo(
                nombre=art['nombre'],
                ref_proveedor=art['codigo'],
                u_medida=art['u_medida'],
                familia_id=art['familia_id'],
                proveedor_id=art['proveedor_id'],
                coste=art['precio_compra'],
                min_alerta=art['stock_minimo']
            )
            articulos_ids.append(art_id)
            print(f"  OK Creado: {art['nombre']} ({art['codigo']})")
        except Exception as e:
            print(f"  ADVERTENCIA Error al crear {art['nombre']}: {e}")

print(f"  Total artículos creados: {len(articulos_ids)}")

# ==================== OPERARIOS Y FURGONETAS ====================
print("\n[4/5] Verificando operarios y furgonetas...")

operarios = get_operarios()
print(f"  Operarios disponibles: {len(operarios)}")
for op in operarios[:5]:  # Mostrar solo los primeros 5
    print(f"    - {op.get('nombre', 'Sin nombre')} (ID: {op['id']})")

furgonetas = list_furgonetas(include_inactive=False)
print(f"  Furgonetas disponibles: {len(furgonetas)}")
for furg in furgonetas:
    print(f"    - {furg.get('nombre', 'Sin nombre')} (ID: {furg['id']})")

if len(operarios) == 0 or len(furgonetas) == 0:
    print("  ADVERTENCIA: Necesitas operarios y furgonetas para generar movimientos")
    print("     Continuando sin generar movimientos...")
else:
    # ==================== ASIGNACIONES Y MOVIMIENTOS ====================
    print("\n[5/5] Generando asignaciones y movimientos...")

    # Obtener ID del almacén principal
    almacen_principal = fetch_one("SELECT id FROM almacenes WHERE tipo = 'almacen' LIMIT 1")
    if not almacen_principal:
        print("  ADVERTENCIA: No se encontro almacen principal. Creando...")
        execute_query("INSERT INTO almacenes (nombre, tipo) VALUES ('Almacen Principal', 'almacen')")
        almacen_principal = fetch_one("SELECT id FROM almacenes WHERE tipo = 'almacen' LIMIT 1")

    almacen_id = almacen_principal['id']
    print(f"  Almacén Principal ID: {almacen_id}")

    # Fechas: del 27/10/2024 hasta hoy
    fecha_inicio = datetime(2024, 10, 27)
    fecha_fin = datetime.now()

    # Crear asignaciones para cada operario en cada furgoneta (rotación)
    print("\n  Creando asignaciones...")
    asignaciones_creadas = 0

    # Estrategia: asignar operarios a furgonetas por semanas
    fecha_actual = fecha_inicio
    op_idx = 0

    while fecha_actual <= fecha_fin:
        # Calcular lunes de esta semana
        dias_desde_lunes = fecha_actual.weekday()
        lunes = fecha_actual - timedelta(days=dias_desde_lunes)

        # Asignar cada furgoneta a un operario diferente para esta semana
        for i, furgoneta in enumerate(furgonetas):
            operario = operarios[(op_idx + i) % len(operarios)]

            # Crear asignación para días laborables de la semana
            for dia_offset in range(5):  # Lunes a Viernes
                fecha_asig = lunes + timedelta(days=dia_offset)

                if fecha_asig > fecha_fin:
                    break

                fecha_str = fecha_asig.strftime("%Y-%m-%d")

                # Verificar si ya existe asignación
                existe = fetch_one(
                    "SELECT COUNT(*) as count FROM asignaciones_furgoneta WHERE operario_id = ? AND furgoneta_id = ? AND fecha = ?",
                    (operario['id'], furgoneta['id'], fecha_str)
                )

                if not existe or existe['count'] == 0:
                    try:
                        execute_query(
                            "INSERT INTO asignaciones_furgoneta (operario_id, furgoneta_id, fecha, turno) VALUES (?, ?, ?, ?)",
                            (operario['id'], furgoneta['id'], fecha_str, 'completo')
                        )
                        asignaciones_creadas += 1
                    except Exception as e:
                        pass  # Ignorar duplicados

        # Avanzar a la siguiente semana y rotar operarios
        fecha_actual += timedelta(days=7)
        op_idx = (op_idx + 1) % len(operarios)

    print(f"  OK Asignaciones creadas: {asignaciones_creadas}")

    # Generar movimientos realistas
    print("\n  Generando movimientos...")
    movimientos_creados = 0

    # 1. RECEPCIONES al almacén principal (2-3 veces por semana)
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        # 2-3 recepciones por semana
        for _ in range(random.randint(2, 3)):
            fecha_recep = fecha_actual + timedelta(days=random.randint(0, 6))

            if fecha_recep > fecha_fin:
                break

            fecha_str = fecha_recep.strftime("%Y-%m-%d")

            # Recibir varios artículos
            num_articulos = random.randint(3, 6)
            articulos_recibir = random.sample(articulos_ids, min(num_articulos, len(articulos_ids)))

            for art_id in articulos_recibir:
                # Obtener datos del artículo para cantidad realista
                articulo = fetch_one("SELECT u_medida FROM articulos WHERE id = ?", (art_id,))

                if articulo:
                    # Cantidad realista por tipo
                    if articulo['u_medida'] in ['kg', 'metro']:
                        cantidad = random.randint(10, 50)
                    elif articulo['u_medida'] == 'rollo':
                        cantidad = random.randint(5, 15)
                    else:  # unidad
                        cantidad = random.randint(20, 100)

                    try:
                        execute_query(
                            """
                            INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id)
                            VALUES (?, 'ENTRADA', ?, ?, NULL, ?, ?)
                            """,
                            (fecha_str, art_id, cantidad, almacen_id, operarios[0]['id'])
                        )
                        movimientos_creados += 1
                    except Exception as e:
                        pass

        fecha_actual += timedelta(days=7)

    print(f"  OK Recepciones creadas: {movimientos_creados}")

    # 2. ENTREGAS a furgonetas (diarias)
    print("  Generando entregas a furgonetas...")
    entregas_creadas = 0

    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        # Solo días laborables
        if fecha_actual.weekday() < 5:  # Lunes a Viernes
            fecha_str = fecha_actual.strftime("%Y-%m-%d")

            # Obtener asignaciones de ese día
            asignaciones_dia = fetch_all(
                "SELECT * FROM asignaciones_furgoneta WHERE fecha = ?",
                (fecha_str,)
            )

            for asig in asignaciones_dia:
                # Cada furgoneta recibe material (2-4 artículos diferentes)
                num_articulos = random.randint(2, 4)
                articulos_entregar = random.sample(articulos_ids, min(num_articulos, len(articulos_ids)))

                for art_id in articulos_entregar:
                    articulo = fetch_one("SELECT u_medida FROM articulos WHERE id = ?", (art_id,))

                    if articulo:
                        # Cantidades pequeñas para entregas diarias
                        if articulo['u_medida'] in ['kg', 'metro']:
                            cantidad = random.randint(2, 10)
                        elif articulo['u_medida'] == 'rollo':
                            cantidad = random.randint(1, 3)
                        else:  # unidad
                            cantidad = random.randint(5, 20)

                        try:
                            execute_query(
                                """
                                INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id)
                                VALUES (?, 'SALIDA', ?, ?, ?, ?, ?)
                                """,
                                (fecha_str, art_id, cantidad, almacen_id, asig['furgoneta_id'], asig['operario_id'])
                            )
                            entregas_creadas += 1
                        except Exception as e:
                            pass

        fecha_actual += timedelta(days=1)

    print(f"  OK Entregas creadas: {entregas_creadas}")

    # 3. IMPUTACIONES (gastos en OTs)
    print("  Generando imputaciones...")
    imputaciones_creadas = 0

    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() < 5:
            fecha_str = fecha_actual.strftime("%Y-%m-%d")

            asignaciones_dia = fetch_all(
                "SELECT * FROM asignaciones_furgoneta WHERE fecha = ?",
                (fecha_str,)
            )

            for asig in asignaciones_dia:
                # 30% de probabilidad de imputación ese día
                if random.random() < 0.3:
                    # 1-2 artículos imputados
                    num_articulos = random.randint(1, 2)
                    articulos_imputar = random.sample(articulos_ids, min(num_articulos, len(articulos_ids)))

                    ot = f"OT{random.randint(1000, 9999)}"

                    for art_id in articulos_imputar:
                        articulo = fetch_one("SELECT u_medida FROM articulos WHERE id = ?", (art_id,))

                        if articulo:
                            if articulo['u_medida'] in ['kg', 'metro']:
                                cantidad = random.uniform(0.5, 5.0)
                            elif articulo['u_medida'] == 'rollo':
                                cantidad = random.uniform(0.1, 1.0)
                            else:
                                cantidad = random.randint(1, 5)

                            try:
                                execute_query(
                                    """
                                    INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id, ot)
                                    VALUES (?, 'SALIDA', ?, ?, ?, NULL, ?, ?)
                                    """,
                                    (fecha_str, art_id, cantidad, asig['furgoneta_id'], asig['operario_id'], ot)
                                )
                                imputaciones_creadas += 1
                            except Exception as e:
                                pass

        fecha_actual += timedelta(days=1)

    print(f"  OK Imputaciones creadas: {imputaciones_creadas}")

    # 4. DEVOLUCIONES (ocasionales)
    print("  Generando devoluciones...")
    devoluciones_creadas = 0

    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() < 5:
            fecha_str = fecha_actual.strftime("%Y-%m-%d")

            asignaciones_dia = fetch_all(
                "SELECT * FROM asignaciones_furgoneta WHERE fecha = ?",
                (fecha_str,)
            )

            for asig in asignaciones_dia:
                # 10% de probabilidad de devolución
                if random.random() < 0.1:
                    art_id = random.choice(articulos_ids)
                    articulo = fetch_one("SELECT u_medida FROM articulos WHERE id = ?", (art_id,))

                    if articulo:
                        if articulo['u_medida'] in ['kg', 'metro']:
                            cantidad = random.uniform(1.0, 5.0)
                        elif articulo['u_medida'] == 'rollo':
                            cantidad = 1.0
                        else:
                            cantidad = random.randint(1, 10)

                        try:
                            execute_query(
                                """
                                INSERT INTO movimientos (fecha, tipo, articulo_id, cantidad, origen_id, destino_id, operario_id)
                                VALUES (?, 'SALIDA', ?, ?, ?, ?, ?)
                                """,
                                (fecha_str, art_id, cantidad, asig['furgoneta_id'], almacen_id, asig['operario_id'])
                            )
                            devoluciones_creadas += 1
                        except Exception as e:
                            pass

        fecha_actual += timedelta(days=1)

    print(f"  OK Devoluciones creadas: {devoluciones_creadas}")

    print(f"\n  TOTAL MOVIMIENTOS: {movimientos_creados + entregas_creadas + imputaciones_creadas + devoluciones_creadas}")

print("\n" + "=" * 60)
print("PROCESO COMPLETADO")
print("=" * 60)
print("\nResumen:")
print(f"  OK Proveedores: {len(proveedores_ids)}")
print(f"  OK Articulos: {len(articulos_ids)}")
print(f"  OK Familias: {len(familias)}")
print(f"  OK Operarios: {len(operarios)}")
print(f"  OK Furgonetas: {len(furgonetas)}")
if len(operarios) > 0 and len(furgonetas) > 0:
    print(f"  OK Asignaciones: {asignaciones_creadas}")
    print(f"  OK Movimientos totales: {movimientos_creados + entregas_creadas + imputaciones_creadas + devoluciones_creadas}")
print("\nBase de datos lista para pruebas!\n")
