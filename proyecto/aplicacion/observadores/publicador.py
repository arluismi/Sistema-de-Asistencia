"""Infraestructura del patrón Observer (publicador / suscriptores)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..modelos.enumeraciones import EstadoAsistencia


@dataclass(frozen=True)
class EventoAsistenciaRegistrada:
    """Evento emitido cuando se registra o actualiza una asistencia."""

    estudiante_id: int
    curso_id: int
    materia_id: int
    fecha: date
    estado: EstadoAsistencia


class SuscriptorEventoAsistencia(ABC):
    """Contrato que deben cumplir los interesados en eventos de asistencia."""

    @abstractmethod
    def actualizar(self, evento: EventoAsistenciaRegistrada) -> None:
        """Reacciona al evento publicado; no debe confirmar ni revertir la transacción."""


class PublicadorEventosAsistencia:
    """Publicador que notifica eventos a todos los suscriptores registrados."""

    def __init__(self):
        self._suscriptores: list[SuscriptorEventoAsistencia] = []

    def suscribir(self, suscriptor: SuscriptorEventoAsistencia) -> None:
        """Agrega un suscriptor si aún no está registrado."""

        if suscriptor not in self._suscriptores:
            self._suscriptores.append(suscriptor)

    def publicar(self, evento: EventoAsistenciaRegistrada) -> None:
        """Entrega el evento a cada suscriptor en el orden de registro."""

        for suscriptor in list(self._suscriptores):
            suscriptor.actualizar(evento)
