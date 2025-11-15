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


# ========================================
# WRAPPER PARA COMPATIBILIDAD CON DialogoMaestroBase
# ========================================
class _FurgonetasServiceWrapper:
    """
    Wrapper para adaptar furgonetas_service (basado en funciones)
    al patrón esperado por DialogoMaestroBase (basado en métodos de clase).
    """

    def obtener_furgonetas(self, filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Lista todas las furgonetas"""
        return list_furgonetas(include_inactive=True)

    def obtener_furgoneta(self, furgoneta_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una furgoneta por ID"""
        return get_furgoneta(furgoneta_id)

    def crear_furgoneta(self, matricula: str, numero: int = None, marca: str = None,
                       modelo: str = None, anio: int = None, activa: bool = True,
                       notas: str = None, usuario: str = None) -> tuple:
        """
        Crea una nueva furgoneta.

        Returns:
            Tupla (exito, mensaje, furgoneta_id)
        """
        try:
            # Validar matrícula obligatoria
            if not matricula or not matricula.strip():
                return False, "La matrícula es obligatoria", None

            # Validar número único si se proporciona
            if numero is not None:
                furgonetas = list_furgonetas()
                for f in furgonetas:
                    if f.get('numero') == numero:
                        return False, f"El número {numero} ya está asignado a otra furgoneta", None

            # Crear furgoneta
            furgoneta_id = alta_furgoneta(
                matricula=matricula,
                marca=marca,
                modelo=modelo,
                anio=anio,
                notas=notas,
                numero=numero
            )

            return True, "Furgoneta creada correctamente", furgoneta_id

        except Exception as e:
            return False, f"Error al crear furgoneta: {str(e)}", None

    def actualizar_furgoneta(self, furgoneta_id: int, matricula: str,
                            numero: int = None, marca: str = None, modelo: str = None,
                            anio: int = None, activa: bool = True, notas: str = None,
                            usuario: str = None) -> tuple:
        """
        Actualiza una furgoneta existente.

        Returns:
            Tupla (exito, mensaje)
        """
        try:
            # Validar matrícula obligatoria
            if not matricula or not matricula.strip():
                return False, "La matrícula es obligatoria"

            # Validar número único si se proporciona
            if numero is not None:
                furgonetas = list_furgonetas()
                for f in furgonetas:
                    if f['id'] != furgoneta_id and f.get('numero') == numero:
                        return False, f"El número {numero} ya está asignado a otra furgoneta"

            # Actualizar furgoneta
            modificar_furgoneta(
                furgoneta_id,
                matricula=matricula,
                numero=numero,
                marca=marca,
                modelo=modelo,
                anio=anio,
                activa=1 if activa else 0,
                notas=notas
            )

            return True, "Furgoneta actualizada correctamente"

        except Exception as e:
            return False, f"Error al actualizar furgoneta: {str(e)}"

    def eliminar_furgoneta(self, furgoneta_id: int, usuario: str = None) -> tuple:
        """
        Elimina una furgoneta.

        Args:
            furgoneta_id: ID de la furgoneta a eliminar
            usuario: Usuario que realiza la acción (opcional)

        Returns:
            Tupla (exito, mensaje)
        """
        try:
            baja_furgoneta(furgoneta_id)
            return True, "Furgoneta eliminada correctamente"
        except Exception as e:
            return False, f"Error al eliminar furgoneta: {str(e)}"


# Instancia singleton del wrapper
furgonetas_service_wrapper = _FurgonetasServiceWrapper()
