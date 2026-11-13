"""Estrategias de cálculo de porcentajes de asistencia estudiantil.

Se aplica el patrón Strategy: el servicio desconoce la fórmula concreta y
delega el cálculo en una implementación intercambiable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import EstadoAsistencia


@dataclass(frozen=True)
class ResumenAsistencia:
    """Conteos y porcentajes calculados para un conjunto de registros."""

    total_registros: int
    presentes: int
    ausentes: int
    justificados: int
    tardes: int
    porcentaje_asistencia: float
    porcentaje_presentismo_efectivo: float

    def como_diccionario(self) -> dict:
        """Convierte el resumen en un diccionario serializable a JSON."""

        return {
            "total_registros": self.total_registros,
            "presentes": self.presentes,
            "ausentes": self.ausentes,
            "justificados": self.justificados,
            "tardes": self.tardes,
            "porcentaje_asistencia": self.porcentaje_asistencia,
            "porcentaje_presentismo_efectivo": self.porcentaje_presentismo_efectivo,
        }


class EstrategiaCalculoAsistencia(ABC):
    """Contrato común para los algoritmos de cálculo de asistencia."""

    nombre = "base"

    @abstractmethod
    def calcular(
        self, registros: Sequence
    ) -> ResumenAsistencia:
        """Calcula el resumen de asistencia a partir de registros del dominio."""

    @staticmethod
    def _contar_estados(registros: Sequence) -> dict:
        """Cuenta registros por estado, tolerando listas vacías."""

        conteos = {estado: 0 for estado in EstadoAsistencia}
        for registro in registros:
            conteos[registro.estado] += 1
        return conteos

    @staticmethod
    def _calcular_porcentaje(cantidad: int, total: int) -> float:
        """Calcula un porcentaje redondeado a dos decimales, sin dividir por cero."""

        if total == 0:
            return 0.0
        return round((cantidad / total) * 100, 2)


class EstrategiaCalculoAsistenciaInstitucional(EstrategiaCalculoAsistencia):
    """Criterio institucional: las faltas justificadas no afectan la regularidad.

    - Porcentaje de asistencia: (Presente + Tarde + Justificado) / total.
    - Presentismo efectivo: (Presente + Tarde) / total.
    """

    nombre = "institucional"

    def calcular(self, registros: Sequence) -> ResumenAsistencia:
        """Aplica el criterio institucional sobre los registros recibidos."""

        conteos = self._contar_estados(registros)
        total = len(registros)
        asistencias_computables = (
            conteos[EstadoAsistencia.PRESENTE]
            + conteos[EstadoAsistencia.TARDE]
            + conteos[EstadoAsistencia.JUSTIFICADO]
        )
        presentismo_efectivo = (
            conteos[EstadoAsistencia.PRESENTE] + conteos[EstadoAsistencia.TARDE]
        )

        return ResumenAsistencia(
            total_registros=total,
            presentes=conteos[EstadoAsistencia.PRESENTE],
            ausentes=conteos[EstadoAsistencia.AUSENTE],
            justificados=conteos[EstadoAsistencia.JUSTIFICADO],
            tardes=conteos[EstadoAsistencia.TARDE],
            porcentaje_asistencia=self._calcular_porcentaje(
                asistencias_computables, total
            ),
            porcentaje_presentismo_efectivo=self._calcular_porcentaje(
                presentismo_efectivo, total
            ),
        )


class EstrategiaCalculoAsistenciaEstricta(EstrategiaCalculoAsistencia):
    """Criterio estricto: las faltas justificadas no computan como asistencia.

    - Porcentaje de asistencia: (Presente + Tarde) / total.
    - Presentismo efectivo: (Presente + Tarde) / total.
    """

    nombre = "estricta"

    def calcular(self, registros: Sequence) -> ResumenAsistencia:
        """Aplica el criterio estricto sobre los registros recibidos."""

        conteos = self._contar_estados(registros)
        total = len(registros)
        asistencias_efectivas = (
            conteos[EstadoAsistencia.PRESENTE] + conteos[EstadoAsistencia.TARDE]
        )

        return ResumenAsistencia(
            total_registros=total,
            presentes=conteos[EstadoAsistencia.PRESENTE],
            ausentes=conteos[EstadoAsistencia.AUSENTE],
            justificados=conteos[EstadoAsistencia.JUSTIFICADO],
            tardes=conteos[EstadoAsistencia.TARDE],
            porcentaje_asistencia=self._calcular_porcentaje(
                asistencias_efectivas, total
            ),
            porcentaje_presentismo_efectivo=self._calcular_porcentaje(
                asistencias_efectivas, total
            ),
        )


ESTRATEGIAS_DISPONIBLES = {
    EstrategiaCalculoAsistenciaInstitucional.nombre: EstrategiaCalculoAsistenciaInstitucional,
    EstrategiaCalculoAsistenciaEstricta.nombre: EstrategiaCalculoAsistenciaEstricta,
}


def obtener_estrategia_calculo_asistencia(
    nombre_estrategia: str | None,
) -> EstrategiaCalculoAsistencia:
    """Devuelve la estrategia solicitada o falla con un mensaje explicativo."""

    nombre_normalizado = (nombre_estrategia or "institucional").strip().lower()
    clase_estrategia = ESTRATEGIAS_DISPONIBLES.get(nombre_normalizado)
    if clase_estrategia is None:
        raise ErrorValidacion(
            "Estrategia de cálculo de asistencia desconocida.",
            detalles={"estrategias_permitidas": sorted(ESTRATEGIAS_DISPONIBLES)},
        )
    return clase_estrategia()
