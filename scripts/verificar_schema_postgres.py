#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar que el schema de PostgreSQL sea correcto.
Compara las constraints actuales contra lo esperado.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.db_utils import fetch_all, fetch_one
from src.core.logger import logger


def verificar_primary_keys():
    """Verifica que todas las PRIMARY KEYs sean correctas"""
    print("\n" + "=" * 60)
    print("VERIFICANDO PRIMARY KEYS")
    print("=" * 60)

    # Definir las PKs esperadas
    pks_esperadas = {
        'usuarios': ['usuario'],
        'sesiones': ['usuario', 'hostname'],
        'proveedores': ['id'],
        'operarios': ['id'],
        'familias': ['id'],
        'ubicaciones': ['id'],
        'almacenes': ['id'],
        'articulos': ['id'],
        'movimientos': ['id'],
        'albaranes': ['albaran'],
        'asignaciones_furgoneta': ['fecha', 'turno', 'furgoneta_id'],
        'inventarios': ['id'],
        'inventario_detalle': ['id'],
        'furgonetas': ['id'],
        'notificaciones': ['id'],
        'historial': ['id']
    }

    problemas = []

    for tabla, columnas_esperadas in pks_esperadas.items():
        # Obtener el nombre de la constraint
        sql_constraint = """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = %s
              AND constraint_type = 'PRIMARY KEY'
        """
        result = fetch_one(sql_constraint, (tabla,))

        if not result:
            print(f"\n[ERROR] {tabla}: No tiene PRIMARY KEY")
            problemas.append(f"{tabla}: No tiene PRIMARY KEY")
            continue

        constraint_name = result['constraint_name']

        # Obtener las columnas de la constraint
        sql_columnas = """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
              AND constraint_name = %s
            ORDER BY ordinal_position
        """
        columnas_result = fetch_all(sql_columnas, (tabla, constraint_name))
        columnas_actuales = [col['column_name'] for col in columnas_result]

        # Comparar
        if columnas_actuales == columnas_esperadas:
            print(f"[OK] {tabla}: {', '.join(columnas_actuales)}")
        else:
            print(f"[ERROR] {tabla}:")
            print(f"   Esperado: {', '.join(columnas_esperadas)}")
            print(f"   Actual:   {', '.join(columnas_actuales)}")
            problemas.append(
                f"{tabla}: PK incorrecta. "
                f"Esperado {columnas_esperadas}, Actual {columnas_actuales}"
            )

    return problemas


def verificar_foreign_keys():
    """Verifica que existan todas las FKs importantes"""
    print("\n" + "=" * 60)
    print("VERIFICANDO FOREIGN KEYS")
    print("=" * 60)

    # Definir las FKs esperadas (tabla -> [(columna, tabla_referenciada)])
    fks_esperadas = {
        'articulos': [
            ('ubicacion_id', 'ubicaciones'),
            ('proveedor_id', 'proveedores'),
            ('familia_id', 'familias')
        ],
        'movimientos': [
            ('origen_id', 'almacenes'),
            ('destino_id', 'almacenes'),
            ('articulo_id', 'articulos'),
            ('operario_id', 'operarios')
        ],
        'albaranes': [
            ('proveedor_id', 'proveedores')
        ],
        'asignaciones_furgoneta': [
            ('operario_id', 'operarios'),
            ('furgoneta_id', 'almacenes')
        ],
        'inventarios': [
            ('almacen_id', 'almacenes')
        ],
        'inventario_detalle': [
            ('inventario_id', 'inventarios'),
            ('articulo_id', 'articulos')
        ],
        'furgonetas': [
            ('almacen_id', 'almacenes')
        ],
        'notificaciones': [
            ('usuario', 'usuarios')
        ]
    }

    problemas = []

    for tabla, fks in fks_esperadas.items():
        # Obtener FKs actuales de la tabla
        sql_fks = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = %s
        """
        fks_actuales = fetch_all(sql_fks, (tabla,))
        fks_dict = {fk['column_name']: fk['foreign_table_name'] for fk in fks_actuales}

        print(f"\n{tabla}:")
        for columna, tabla_ref in fks:
            if columna in fks_dict and fks_dict[columna] == tabla_ref:
                print(f"  [OK] {columna} -> {tabla_ref}")
            else:
                print(f"  [ERROR] {columna} -> {tabla_ref} (falta o incorrecta)")
                problemas.append(f"{tabla}.{columna}: FK incorrecta o faltante")

    return problemas


def verificar_indices():
    """Verifica que existan los índices importantes"""
    print("\n" + "=" * 60)
    print("VERIFICANDO ÍNDICES")
    print("=" * 60)

    # Índices críticos
    indices_criticos = [
        ('movimientos', 'articulo_id'),
        ('movimientos', 'fecha'),
        ('movimientos', 'tipo'),
        ('articulos', 'nombre'),
        ('articulos', 'ean')
    ]

    problemas = []

    for tabla, columna in indices_criticos:
        sql_indices = """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = %s
              AND indexdef LIKE %s
        """
        result = fetch_one(sql_indices, (tabla, f'%{columna}%'))

        if result:
            print(f"[OK] {tabla}.{columna}")
        else:
            print(f"[WARNING] {tabla}.{columna}: No hay índice")
            # No lo añadimos como problema crítico, solo warning

    return problemas


def main():
    """Ejecuta todas las verificaciones"""
    print("=" * 60)
    print("VERIFICACIÓN DE SCHEMA POSTGRESQL")
    print("=" * 60)

    todos_problemas = []

    try:
        # Verificar PKs
        problemas = verificar_primary_keys()
        todos_problemas.extend(problemas)

        # Verificar FKs
        problemas = verificar_foreign_keys()
        todos_problemas.extend(problemas)

        # Verificar índices
        problemas = verificar_indices()
        todos_problemas.extend(problemas)

        # Resumen
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)

        if todos_problemas:
            print(f"\n[ERROR] Se encontraron {len(todos_problemas)} problemas:")
            for i, problema in enumerate(todos_problemas, 1):
                print(f"  {i}. {problema}")
            print("\nRecomendación: Ejecutar scripts de corrección correspondientes.")
            sys.exit(1)
        else:
            print("\n[OK] Todas las verificaciones pasaron correctamente!")
            print("El schema de PostgreSQL está correcto.")

    except Exception as e:
        logger.exception(f"Error en verificación: {e}")
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
