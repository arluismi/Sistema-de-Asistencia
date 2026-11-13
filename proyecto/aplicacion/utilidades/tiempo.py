"""Utilidades de tiempo basadas en la zona horaria institucional.

Todas las marcas de tiempo del sistema las genera el servidor. El cliente nunca
envía la hora de una firma ni la fecha de un registro automático.
"""

from datetime import date, datetime

from flask import current_app
from zoneinfo import ZoneInfo


def obtener_zona_horaria_institucional() -> ZoneInfo:
    """Devuelve la zona horaria configurada para la institución.

    `ZoneInfo` (biblioteca estándar) resuelve el identificador IANA, por ejemplo
    `America/Argentina/Buenos_Aires`, y aplica automáticamente el horario de
    verano si correspondiera.
    """

    return ZoneInfo(current_app.config["ZONA_HORARIA_INSTITUCIONAL"])


def obtener_marca_temporal_servidor() -> datetime:
    """Devuelve la fecha y hora actual del servidor en hora institucional.

    El valor se almacena sin información de zona horaria porque representa la
    hora local de la institución, que es la misma referencia usada por la grilla
    horaria. De esta manera las comparaciones de puntualidad son directas.
    """

    return datetime.now(obtener_zona_horaria_institucional()).replace(tzinfo=None)


def obtener_fecha_servidor() -> date:
    """Devuelve la fecha institucional actual según el reloj del servidor."""

    return obtener_marca_temporal_servidor().date()


def combinar_fecha_y_hora(fecha: date, hora) -> datetime:
    """Combina una fecha y una hora en un único objeto `datetime`."""

    return datetime.combine(fecha, hora)


def calcular_minutos_entre(momento_inicial: datetime, momento_final: datetime) -> int:
    """Calcula minutos completos transcurridos entre dos marcas de tiempo.

    Si el momento final es anterior al inicial, devuelve cero para evitar
    duraciones negativas en los cálculos de asistencia.
    """

    diferencia = momento_final - momento_inicial
    return max(0, int(diferencia.total_seconds() // 60))


def calcular_minutos_desde_medianoche(momento: datetime) -> int:
    """Convierte la hora de un `datetime` en minutos transcurridos desde las 00:00."""

    return momento.hour * 60 + momento.minute
