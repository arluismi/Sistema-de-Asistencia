"""Registro de publicadores y suscriptores del patrón Observer."""

from .publicador import (
    EventoAsistenciaRegistrada,
    PublicadorEventosAsistencia,
    SuscriptorEventoAsistencia,
)
from .suscriptor_alertas import SuscriptorAlertasDashboard

# Instancia única usada por los servicios para publicar eventos.
publicador_eventos = PublicadorEventosAsistencia()

_observadores_registrados = False


def registrar_observadores() -> None:
    """Conecta los suscriptores al publicador una sola vez por proceso."""

    global _observadores_registrados
    if _observadores_registrados:
        return

    publicador_eventos.suscribir(SuscriptorAlertasDashboard())
    _observadores_registrados = True


__all__ = [
    "EventoAsistenciaRegistrada",
    "PublicadorEventosAsistencia",
    "SuscriptorEventoAsistencia",
    "publicador_eventos",
    "registrar_observadores",
]
