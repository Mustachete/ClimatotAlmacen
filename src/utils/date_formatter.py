# -*- coding: utf-8 -*-
"""
Utilidades centralizadas para formateo de fechas.

Este módulo proporciona funciones estándar para convertir y formatear fechas
en toda la aplicación, eliminando código duplicado.

Uso:
    from src.utils.date_formatter import DateFormatter

    # Convertir de BD a formato display
    fecha_mostrar = DateFormatter.db_a_display("2025-01-15")  # "15/01/2025"

    # Convertir de display a BD
    fecha_bd = DateFormatter.display_a_db("15/01/2025")  # "2025-01-15"
"""

from datetime import datetime, date
from typing import Optional, Union


class DateFormatter:
    """Formateador de fechas estándar para la aplicación"""

    # Formatos estándar
    FORMATO_BD = "%Y-%m-%d"           # Formato en base de datos (YYYY-MM-DD)
    FORMATO_DISPLAY = "%d/%m/%Y"      # Formato para mostrar al usuario (DD/MM/YYYY)
    FORMATO_DISPLAY_HORA = "%d/%m/%Y %H:%M"  # Con hora
    FORMATO_HORA = "%H:%M"            # Solo hora
    FORMATO_ISO = "%Y-%m-%dT%H:%M:%S"  # ISO 8601

    @staticmethod
    def db_a_display(
        fecha_str: Union[str, date, None],
        con_hora: bool = False,
        fallback: str = "-"
    ) -> str:
        """
        Convierte fecha de formato BD (YYYY-MM-DD) a formato display (DD/MM/YYYY).

        Args:
            fecha_str: Fecha en formato YYYY-MM-DD, objeto date, o None
            con_hora: Si es True, incluye también la hora (HH:MM)
            fallback: Valor a retornar si la conversión falla

        Returns:
            Fecha formateada en DD/MM/YYYY o fallback si hay error

        Ejemplo:
            fecha = DateFormatter.db_a_display("2025-01-15")  # "15/01/2025"
            fecha_hora = DateFormatter.db_a_display("2025-01-15 14:30", con_hora=True)  # "15/01/2025 14:30"
        """
        if not fecha_str:
            return fallback

        try:
            # Si es un objeto date, convertir directamente
            if isinstance(fecha_str, date):
                return fecha_str.strftime(DateFormatter.FORMATO_DISPLAY)

            fecha_str_limpia = str(fecha_str).strip()

            # Intentar parsear con hora primero
            if con_hora or ' ' in fecha_str_limpia:
                try:
                    fecha_obj = datetime.strptime(fecha_str_limpia, f"{DateFormatter.FORMATO_BD} %H:%M:%S")
                    return fecha_obj.strftime(DateFormatter.FORMATO_DISPLAY_HORA)
                except ValueError:
                    try:
                        fecha_obj = datetime.strptime(fecha_str_limpia, f"{DateFormatter.FORMATO_BD} %H:%M")
                        return fecha_obj.strftime(DateFormatter.FORMATO_DISPLAY_HORA)
                    except ValueError:
                        pass

            # Intentar parsear solo fecha
            fecha_obj = datetime.strptime(fecha_str_limpia, DateFormatter.FORMATO_BD)
            formato = DateFormatter.FORMATO_DISPLAY_HORA if con_hora else DateFormatter.FORMATO_DISPLAY
            return fecha_obj.strftime(formato)

        except (ValueError, TypeError, AttributeError):
            return fallback

    @staticmethod
    def display_a_db(
        fecha_str: Union[str, date, None],
        fallback: Optional[str] = None
    ) -> Optional[str]:
        """
        Convierte fecha de formato display (DD/MM/YYYY) a formato BD (YYYY-MM-DD).

        Args:
            fecha_str: Fecha en formato DD/MM/YYYY, objeto date, o None
            fallback: Valor a retornar si la conversión falla

        Returns:
            Fecha formateada en YYYY-MM-DD o fallback si hay error

        Ejemplo:
            fecha = DateFormatter.display_a_db("15/01/2025")  # "2025-01-15"
        """
        if not fecha_str:
            return fallback

        try:
            # Si es un objeto date, convertir directamente
            if isinstance(fecha_str, date):
                return fecha_str.strftime(DateFormatter.FORMATO_BD)

            fecha_str_limpia = str(fecha_str).strip()
            fecha_obj = datetime.strptime(fecha_str_limpia, DateFormatter.FORMATO_DISPLAY)
            return fecha_obj.strftime(DateFormatter.FORMATO_BD)

        except (ValueError, TypeError, AttributeError):
            return fallback

    @staticmethod
    def normalizar_fecha(
        fecha_str: Union[str, date, None],
        formato_entrada: Optional[str] = None
    ) -> Optional[str]:
        """
        Normaliza una fecha a formato BD, intentando varios formatos si es necesario.

        Args:
            fecha_str: Fecha a normalizar (string o date)
            formato_entrada: Formato de entrada (si None, intenta detectar automáticamente)

        Returns:
            Fecha en formato YYYY-MM-DD o None si no se puede convertir

        Ejemplo:
            fecha = DateFormatter.normalizar_fecha("15-01-2025")  # "2025-01-15"
            fecha = DateFormatter.normalizar_fecha("15/01/2025")  # "2025-01-15"
            fecha = DateFormatter.normalizar_fecha("2025-01-15")  # "2025-01-15"
        """
        if not fecha_str:
            return None

        # Si es un objeto date, convertir directamente
        if isinstance(fecha_str, date):
            return fecha_str.strftime(DateFormatter.FORMATO_BD)

        fecha_str_limpia = str(fecha_str).strip()

        # Si ya está en formato BD, retornar como está
        try:
            datetime.strptime(fecha_str_limpia, DateFormatter.FORMATO_BD)
            return fecha_str_limpia
        except ValueError:
            pass

        # Si se especifica formato, intentar con ese
        if formato_entrada:
            try:
                fecha_obj = datetime.strptime(fecha_str_limpia, formato_entrada)
                return fecha_obj.strftime(DateFormatter.FORMATO_BD)
            except ValueError:
                return None

        # Intentar con formatos comunes
        formatos_intentar = [
            "%d/%m/%Y",      # DD/MM/YYYY
            "%d-%m-%Y",      # DD-MM-YYYY
            "%d.%m.%Y",      # DD.MM.YYYY
            "%Y/%m/%d",      # YYYY/MM/DD
            "%Y.%m.%d",      # YYYY.MM.DD
        ]

        for fmt in formatos_intentar:
            try:
                fecha_obj = datetime.strptime(fecha_str_limpia, fmt)
                return fecha_obj.strftime(DateFormatter.FORMATO_BD)
            except ValueError:
                continue

        return None

    @staticmethod
    def formatear_rango_fechas(
        fecha_inicio: Union[str, date, None],
        fecha_fin: Union[str, date, None]
    ) -> str:
        """
        Formatea un rango de fechas de forma legible.

        Args:
            fecha_inicio: Fecha inicio en formato BD o date
            fecha_fin: Fecha fin en formato BD o date

        Returns:
            String con formato "DD/MM/YYYY - DD/MM/YYYY"

        Ejemplo:
            rango = DateFormatter.formatear_rango_fechas("2025-01-01", "2025-01-31")
            # "01/01/2025 - 31/01/2025"
        """
        inicio = DateFormatter.db_a_display(fecha_inicio)
        fin = DateFormatter.db_a_display(fecha_fin)
        return f"{inicio} - {fin}"

    @staticmethod
    def fecha_actual() -> str:
        """
        Retorna la fecha actual en formato BD.

        Returns:
            Fecha actual en formato YYYY-MM-DD

        Ejemplo:
            hoy = DateFormatter.fecha_actual()  # "2025-01-15"
        """
        return datetime.now().strftime(DateFormatter.FORMATO_BD)

    @staticmethod
    def fecha_actual_display() -> str:
        """
        Retorna la fecha actual en formato display.

        Returns:
            Fecha actual en formato DD/MM/YYYY

        Ejemplo:
            hoy = DateFormatter.fecha_actual_display()  # "15/01/2025"
        """
        return datetime.now().strftime(DateFormatter.FORMATO_DISPLAY)

    @staticmethod
    def hora_actual() -> str:
        """
        Retorna la hora actual en formato HH:MM.

        Returns:
            Hora actual en formato HH:MM

        Ejemplo:
            ahora = DateFormatter.hora_actual()  # "14:30"
        """
        return datetime.now().strftime(DateFormatter.FORMATO_HORA)

    @staticmethod
    def es_fecha_valida(fecha_str: str, formato: Optional[str] = None) -> bool:
        """
        Verifica si una cadena es una fecha válida.

        Args:
            fecha_str: Cadena a verificar
            formato: Formato esperado (si None, intenta varios formatos)

        Returns:
            True si es una fecha válida, False en caso contrario

        Ejemplo:
            valida = DateFormatter.es_fecha_valida("15/01/2025")  # True
            valida = DateFormatter.es_fecha_valida("32/01/2025")  # False
        """
        if not fecha_str:
            return False

        if formato:
            try:
                datetime.strptime(str(fecha_str).strip(), formato)
                return True
            except (ValueError, TypeError):
                return False

        # Intentar con formatos comunes
        formatos = [
            DateFormatter.FORMATO_BD,
            DateFormatter.FORMATO_DISPLAY,
            "%d-%m-%Y",
            "%d.%m.%Y",
        ]

        for fmt in formatos:
            try:
                datetime.strptime(str(fecha_str).strip(), fmt)
                return True
            except (ValueError, TypeError):
                continue

        return False

    @staticmethod
    def comparar_fechas(
        fecha1: Union[str, date],
        fecha2: Union[str, date]
    ) -> int:
        """
        Compara dos fechas.

        Args:
            fecha1: Primera fecha
            fecha2: Segunda fecha

        Returns:
            -1 si fecha1 < fecha2
             0 si fecha1 == fecha2
             1 si fecha1 > fecha2
            None si alguna fecha es inválida

        Ejemplo:
            resultado = DateFormatter.comparar_fechas("2025-01-15", "2025-01-20")  # -1
        """
        try:
            # Normalizar ambas fechas
            f1_norm = DateFormatter.normalizar_fecha(fecha1)
            f2_norm = DateFormatter.normalizar_fecha(fecha2)

            if f1_norm is None or f2_norm is None:
                return None

            if f1_norm < f2_norm:
                return -1
            elif f1_norm > f2_norm:
                return 1
            else:
                return 0

        except (ValueError, TypeError, AttributeError):
            return None

    @staticmethod
    def dias_entre_fechas(
        fecha_inicio: Union[str, date],
        fecha_fin: Union[str, date]
    ) -> Optional[int]:
        """
        Calcula el número de días entre dos fechas.

        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin

        Returns:
            Número de días (puede ser negativo) o None si hay error

        Ejemplo:
            dias = DateFormatter.dias_entre_fechas("2025-01-01", "2025-01-10")  # 9
        """
        try:
            f1_norm = DateFormatter.normalizar_fecha(fecha_inicio)
            f2_norm = DateFormatter.normalizar_fecha(fecha_fin)

            if f1_norm is None or f2_norm is None:
                return None

            fecha1_obj = datetime.strptime(f1_norm, DateFormatter.FORMATO_BD)
            fecha2_obj = datetime.strptime(f2_norm, DateFormatter.FORMATO_BD)

            diferencia = fecha2_obj - fecha1_obj
            return diferencia.days

        except (ValueError, TypeError, AttributeError):
            return None
