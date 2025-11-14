from __future__ import annotations
from datetime import date
from typing import Optional, Dict, Any, List

from src.repos.furgonetas_repo import (
    ensure_schema,
    list_furgonetas, get_furgoneta, create_furgoneta, update_furgoneta, delete_furgoneta
)
from src.repos import asignaciones_repo


def boot() -> None:
    """Inicializa/migra el esquema si falta."""
    ensure_schema()


def alta_furgoneta(matricula: str, marca: str = None, modelo: str = None, anio: int = None, notas: str = None, numero: int = None) -> int:
    return create_furgoneta(matricula, marca, modelo, anio, notas, numero)


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
        numero=kwargs.get("numero"),
    )


def baja_furgoneta(fid: int) -> None:
    delete_furgoneta(fid)


def asignar_furgoneta_a_operario(
    operario_id: int,
    furgoneta_id: int,
    fecha: str,
    turno: str = 'completo'
) -> bool:
    """
    Asigna una furgoneta a un operario para una fecha y turno específicos.

    Args:
        operario_id: ID del operario
        furgoneta_id: ID de la furgoneta (almacen con tipo='furgoneta')
        fecha: Fecha en formato YYYY-MM-DD
        turno: 'manana', 'tarde' o 'completo' (default)

    Returns:
        True si se asignó correctamente
    """
    return asignaciones_repo.asignar_furgoneta(operario_id, fecha, furgoneta_id, turno)


def obtener_furgoneta_operario(
    operario_id: int,
    fecha: str,
    turno: str = 'completo'
) -> Optional[Dict[str, Any]]:
    """
    Obtiene la furgoneta asignada a un operario en una fecha y turno.

    Args:
        operario_id: ID del operario
        fecha: Fecha en formato YYYY-MM-DD
        turno: 'manana', 'tarde' o 'completo'

    Returns:
        Dict con furgoneta_id y furgoneta_nombre, o None
    """
    return asignaciones_repo.get_furgoneta_asignada(operario_id, fecha, turno)


def listar_asignaciones_operario(
    operario_id: int,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todas las asignaciones de un operario en un rango de fechas.

    Args:
        operario_id: ID del operario
        fecha_desde: Fecha inicial (opcional)
        fecha_hasta: Fecha final (opcional)

    Returns:
        Lista de asignaciones
    """
    return asignaciones_repo.get_asignaciones_operario(operario_id, fecha_desde, fecha_hasta)
