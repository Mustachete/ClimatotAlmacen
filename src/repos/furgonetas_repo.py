from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date
from pathlib import Path

from src.core.db_utils import get_connection, execute_query, fetch_all, fetch_one, DB_PATH


# -----------------------------
# SCHEMA / MIGRATIONS LIGERAS
# -----------------------------

SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS furgonetas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero      INTEGER UNIQUE,
    matricula   TEXT NOT NULL UNIQUE,
    marca       TEXT,
    modelo      TEXT,
    anio        INTEGER,
    activa      INTEGER NOT NULL DEFAULT 1,
    notas       TEXT
);

CREATE TABLE IF NOT EXISTS furgonetas_asignaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    furgoneta_id INTEGER NOT NULL,
    operario     TEXT NOT NULL,          -- guardamos nombre/alias (evita dependencia dura si aún no tenéis tabla operarios consolidada)
    desde        TEXT NOT NULL,          -- ISO yyyy-mm-dd
    hasta        TEXT,                   -- NULL = asignación actual
    notas        TEXT,
    FOREIGN KEY (furgoneta_id) REFERENCES furgonetas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_furgonetas_asignaciones_furgoneta ON furgonetas_asignaciones(furgoneta_id);
CREATE INDEX IF NOT EXISTS idx_furgonetas_asignaciones_actual ON furgonetas_asignaciones(furgoneta_id, hasta);

-- Vista de estado actual por furgoneta (una fila por furgoneta)
CREATE VIEW IF NOT EXISTS vw_furgonetas_estado_actual AS
SELECT f.id AS furgoneta_id,
       f.matricula,
       f.marca,
       f.modelo,
       f.anio,
       f.activa,
       (SELECT a.operario
          FROM furgonetas_asignaciones a
         WHERE a.furgoneta_id = f.id AND a.hasta IS NULL
         ORDER BY a.desde DESC
         LIMIT 1) AS operario_actual,
       (SELECT a.desde
          FROM furgonetas_asignaciones a
         WHERE a.furgoneta_id = f.id AND a.hasta IS NULL
         ORDER BY a.desde DESC
         LIMIT 1) AS desde
  FROM furgonetas f;
"""

def ensure_schema() -> None:
    """Crea tablas y vista si no existen."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

        # Migración: añadir columna 'numero' si no existe
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(furgonetas)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'numero' not in columns:
            # SQLite no permite añadir columna UNIQUE con ALTER TABLE si hay datos
            # Por eso añadimos sin restricción UNIQUE
            conn.execute("ALTER TABLE furgonetas ADD COLUMN numero INTEGER")
            conn.commit()
            # Nota: La restricción UNIQUE se aplicará en nuevas inserciones mediante la lógica de la aplicación


# -----------------------------
# REPOS CRUD FURGONETAS
# -----------------------------

def list_furgonetas(include_inactive: bool = True) -> List[Dict[str, Any]]:
    """
    Lista furgonetas desde la tabla almacenes (tipo='furgoneta').
    IMPORTANTE: No usa la tabla 'furgonetas' antigua.
    """
    sql = """
        SELECT id, nombre as matricula, NULL as marca, NULL as modelo,
               NULL as anio, 1 as activa, NULL as notas, NULL as numero
        FROM almacenes
        WHERE tipo = 'furgoneta'
    """
    if not include_inactive:
        sql += " AND activa = 1"
    sql += " ORDER BY nombre"
    return fetch_all(sql)


def get_furgoneta(fid: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene una furgoneta por ID desde la tabla almacenes.
    Retorna datos compatibles con el formato esperado por el diálogo.
    """
    result = fetch_one("SELECT id, nombre as matricula FROM almacenes WHERE id = ? AND tipo = 'furgoneta'", (fid,))
    if result:
        # Añadir campos adicionales como None para compatibilidad
        result['marca'] = None
        result['modelo'] = None
        result['anio'] = None
        result['activa'] = 1
        result['notas'] = None
        result['numero'] = None
    return result


def create_furgoneta(matricula: str, marca: str = None, modelo: str = None, anio: int = None, notas: str = None, numero: int = None) -> int:
    """
    Crea una nueva furgoneta en la tabla almacenes (tipo='furgoneta').
    Solo usa el campo 'nombre' para guardar la matrícula.
    Otros campos (marca, modelo, año) se ignoran por ahora ya que almacenes no los tiene.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO almacenes(nombre, tipo) VALUES(?, 'furgoneta')",
            (matricula.strip().upper(),)
        )
        conn.commit()
        return cur.lastrowid


def update_furgoneta(fid: int, matricula: str, marca: str = None, modelo: str = None, anio: int = None, activa: int = 1, notas: str = None, numero: int = None) -> None:
    """
    Actualiza una furgoneta en la tabla almacenes.
    Solo actualiza el campo 'nombre' (matrícula).
    Otros campos se ignoran ya que almacenes no los tiene.
    """
    execute_query(
        "UPDATE almacenes SET nombre = ? WHERE id = ? AND tipo = 'furgoneta'",
        (matricula.strip().upper(), fid)
    )


def delete_furgoneta(fid: int) -> None:
    """
    Elimina una furgoneta de la tabla almacenes.
    """
    execute_query("DELETE FROM almacenes WHERE id = ? AND tipo = 'furgoneta'", (fid,))


# -----------------------------
# REPOS ASIGNACIONES
# -----------------------------

def list_asignaciones(fid: int) -> List[Dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM furgonetas_asignaciones WHERE furgoneta_id = ? ORDER BY desde DESC, id DESC",
        (fid,)
    )


def asignacion_actual(fid: int) -> Optional[Dict[str, Any]]:
    return fetch_one(
        "SELECT * FROM furgonetas_asignaciones WHERE furgoneta_id = ? AND hasta IS NULL ORDER BY desde DESC LIMIT 1",
        (fid,)
    )


def crear_asignacion(fid: int, operario: str, desde_iso: str, notas: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO furgonetas_asignaciones(furgoneta_id, operario, desde, notas) VALUES(?,?,?,?)",
            (fid, operario.strip(), desde_iso, notas)
        )
        conn.commit()
        return cur.lastrowid


def cerrar_asignacion(aid: int, hasta_iso: str) -> None:
    execute_query("UPDATE furgonetas_asignaciones SET hasta = ? WHERE id = ?", (hasta_iso, aid))


def estado_actual() -> List[Dict[str, Any]]:
    return fetch_all("SELECT * FROM vw_furgonetas_estado_actual ORDER BY matricula")
