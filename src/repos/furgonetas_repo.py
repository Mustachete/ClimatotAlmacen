from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date
from pathlib import Path

from src.core.db_utils import execute_query, fetch_all, fetch_one, get_con, release_connection


# -----------------------------
# REPOS CRUD FURGONETAS
# -----------------------------
# Nota: Las tablas furgonetas y furgonetas_asignaciones deben existir en PostgreSQL


def list_furgonetas(include_inactive: bool = True) -> List[Dict[str, Any]]:
    """Lista furgonetas desde la tabla furgonetas."""
    sql = "SELECT * FROM furgonetas"
    if not include_inactive:
        sql += " WHERE activa = 1"
    sql += " ORDER BY numero, matricula"
    return fetch_all(sql)


def get_furgoneta(fid: int) -> Optional[Dict[str, Any]]:
    """Obtiene una furgoneta por ID."""
    return fetch_one("SELECT * FROM furgonetas WHERE id = %s", (fid,))


def create_furgoneta(matricula: str, marca: str = None, modelo: str = None, anio: int = None, notas: str = None, numero: int = None) -> int:
    """Crea una nueva furgoneta y su almacén correspondiente."""
    conn = get_con()
    cur = conn.cursor()

    try:
        # Crear furgoneta en tabla furgonetas
        cur.execute(
            "INSERT INTO furgonetas(numero, matricula, marca, modelo, anio, notas) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
            (numero, matricula.strip().upper(), marca, modelo, anio, notas)
        )
        furgoneta_id = cur.fetchone()[0]

        # Crear almacén correspondiente
        cur.execute(
            "INSERT INTO almacenes(nombre, tipo) VALUES(%s, 'furgoneta')",
            (matricula.strip().upper(),)
        )

        conn.commit()
        return furgoneta_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def update_furgoneta(fid: int, matricula: str, marca: str = None, modelo: str = None, anio: int = None, activa: int = 1, notas: str = None, numero: int = None) -> None:
    """Actualiza una furgoneta y su almacén correspondiente."""
    conn = get_con()
    cur = conn.cursor()

    try:
        # Obtener matrícula anterior
        cur.execute("SELECT matricula FROM furgonetas WHERE id = %s", (fid,))
        row = cur.fetchone()
        matricula_anterior = row[0] if row else None

        # Actualizar furgoneta
        cur.execute(
            "UPDATE furgonetas SET numero=%s, matricula=%s, marca=%s, modelo=%s, anio=%s, activa=%s, notas=%s WHERE id = %s",
            (numero, matricula.strip().upper(), marca, modelo, anio, int(bool(activa)), notas, fid)
        )

        # Actualizar almacén correspondiente
        if matricula_anterior:
            cur.execute(
                "UPDATE almacenes SET nombre=%s WHERE nombre=%s AND tipo='furgoneta'",
                (matricula.strip().upper(), matricula_anterior)
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def delete_furgoneta(fid: int) -> None:
    """Elimina una furgoneta y su almacén correspondiente."""
    conn = get_con()
    cur = conn.cursor()

    try:
        # Obtener matrícula
        cur.execute("SELECT matricula FROM furgonetas WHERE id = %s", (fid,))
        row = cur.fetchone()
        matricula = row[0] if row else None

        # Eliminar furgoneta
        cur.execute("DELETE FROM furgonetas WHERE id = %s", (fid,))

        # Eliminar almacén correspondiente
        if matricula:
            cur.execute("DELETE FROM almacenes WHERE nombre=%s AND tipo='furgoneta'", (matricula,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def list_asignaciones(fid: int) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM furgonetas_asignaciones WHERE furgoneta_id = %s ORDER BY desde DESC, id DESC",
        (fid,)
    )


def asignacion_actual(fid: int) -> Optional[Dict[str, Any]]:
    return fetch_one(
        "SELECT * FROM furgonetas_asignaciones WHERE furgoneta_id = %s AND hasta IS NULL ORDER BY desde DESC LIMIT 1",
        (fid,)
    )


def crear_asignacion(fid: int, operario: str, desde_iso: str, notas: str | None = None) -> int:
    conn = get_con()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO furgonetas_asignaciones(furgoneta_id, operario, desde, notas) VALUES(%s,%s,%s,%s) RETURNING id",
            (fid, operario.strip(), desde_iso, notas)
        )
        asignacion_id = cur.fetchone()[0]
        conn.commit()
        return asignacion_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def cerrar_asignacion(aid: int, hasta_iso: str) -> None:
    execute_query("UPDATE furgonetas_asignaciones SET hasta = %s WHERE id = %s", (hasta_iso, aid))


def estado_actual() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM vw_furgonetas_estado_actual ORDER BY matricula")
