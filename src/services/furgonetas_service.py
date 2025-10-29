from __future__ import annotations
from datetime import date
from typing import Optional, Dict, Any

from src.repos.furgonetas_repo import (
    ensure_schema,
    list_furgonetas, get_furgoneta, create_furgoneta, update_furgoneta, delete_furgoneta,
    list_asignaciones, asignacion_actual, crear_asignacion, cerrar_asignacion, estado_actual
)


def boot() -> None:
    """Inicializa/migra el esquema si falta."""
    ensure_schema()


def alta_furgoneta(matricula: str, marca: str = None, modelo: str = None, anio: int = None, notas: str = None) -> int:
    return create_furgoneta(matricula, marca, modelo, anio, notas)


def modificar_furgoneta(fid: int, **kwargs) -> None:
    # Sanitiza kwargs y delega
    matricula = kwargs.get("matricula")
    if not matricula:
        f = get_furgoneta(fid)
        matricula = f["matricula"] if f else None
    update_furgoneta(
        fid,
        matricula=matricula,
        marca=kwargs.get("marca"),
        modelo=kwargs.get("modelo"),
        anio=kwargs.get("anio"),
        activa=kwargs.get("activa", 1),
        notas=kwargs.get("notas"),
    )


def baja_furgoneta(fid: int) -> None:
    delete_furgoneta(fid)


def reasignar_furgoneta(fid: int, operario: str, fecha_desde: date) -> None:
    """
    Cierra la asignación abierta (si la hay) y crea una nueva para el operario indicado.
    """
    actual = asignacion_actual(fid)
    desde_iso = fecha_desde.isoformat()
    if actual is not None:
        # evita no-op si es mismo operario
        if actual["operario"].strip().lower() == operario.strip().lower():
            return
        # cierra anterior el día inmediatamente previo a la nueva asignación
        cerrar_asignacion(actual["id"], hasta_iso=desde_iso)
    crear_asignacion(fid, operario=operario, desde_iso=desde_iso)
