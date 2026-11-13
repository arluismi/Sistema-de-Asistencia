"""Estrategias de cálculo intercambiables (patrón Strategy)."""

from .calculo_asistencia import (
    EstrategiaCalculoAsistencia,
    EstrategiaCalculoAsistenciaEstricta,
    EstrategiaCalculoAsistenciaInstitucional,
    ResumenAsistencia,
    obtener_estrategia_calculo_asistencia,
)
from .calculo_horas_docentes import (
    EstrategiaBalanceHorasCatedra,
    EstrategiaBalanceHorasCatedraExacta,
    EstrategiaBalanceHorasCatedraPorBloques,
    obtener_estrategia_balance_horas,
)

__all__ = [
    "EstrategiaBalanceHorasCatedra",
    "EstrategiaBalanceHorasCatedraExacta",
    "EstrategiaBalanceHorasCatedraPorBloques",
    "EstrategiaCalculoAsistencia",
    "EstrategiaCalculoAsistenciaEstricta",
    "EstrategiaCalculoAsistenciaInstitucional",
    "ResumenAsistencia",
    "obtener_estrategia_balance_horas",
    "obtener_estrategia_calculo_asistencia",
]
