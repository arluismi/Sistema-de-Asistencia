"""Estrategias de cálculo de horas cátedra docentes.

El cálculo cruza la grilla horaria institucional con las firmas de ingreso y
egreso efectivamente registradas. La conversión de minutos a horas cátedra es
la parte intercambiable del algoritmo (patrón Strategy).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import TipoFirma


@dataclass(frozen=True)
class DetalleClaseEvaluada:
    """Resultado de evaluar un bloque horario en una fecha concreta."""

    grilla_horaria_id: int
    fecha: date
    curso: str
    materia: str
    hora_inicio: time
    hora_fin: time
    minutos_esperados: int
    minutos_laborados: int
    estado: str


class EstrategiaBalanceHorasCatedra(ABC):
    """Contrato común para el balance de horas cátedra."""

    nombre = "base"

    def calcular(
        self,
        grillas_horarias,
        firmas_asistencia,
        fecha_inicio: date,
        fecha_fin: date,
        minutos_hora_catedra: int,
    ) -> dict:
        """Evalúa cada clase del período y devuelve el balance consolidado."""

        if minutos_hora_catedra <= 0:
            raise ErrorValidacion("La duración de la hora cátedra debe ser mayor que cero.")
        if fecha_fin < fecha_inicio:
            raise ErrorValidacion("La fecha final no puede ser anterior a la fecha inicial.")

        firmas_por_clase = self._indexar_firmas(firmas_asistencia)
        detalles = self._evaluar_clases(
            grillas_horarias, firmas_por_clase, fecha_inicio, fecha_fin
        )

        minutos_esperados = sum(detalle.minutos_esperados for detalle in detalles)
        minutos_laborados = sum(detalle.minutos_laborados for detalle in detalles)
        horas_esperadas = self._convertir_minutos_a_horas(
            minutos_esperados, minutos_hora_catedra
        )
        horas_laboradas = self._convertir_minutos_a_horas(
            minutos_laborados, minutos_hora_catedra
        )
        saldo = round(horas_laboradas - horas_esperadas, 2)
        porcentaje_cumplimiento = (
            round((horas_laboradas / horas_esperadas) * 100, 2)
            if horas_esperadas > 0
            else 0.0
        )

        return {
            "estrategia": self.nombre,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "minutos_hora_catedra": minutos_hora_catedra,
            "clases_esperadas": len(detalles),
            "clases_completas": sum(
                1 for detalle in detalles if detalle.estado == "Completa"
            ),
            "clases_incompletas": sum(
                1 for detalle in detalles if detalle.estado == "Incompleta"
            ),
            "clases_sin_firma": sum(
                1 for detalle in detalles if detalle.estado == "Sin firma"
            ),
            "minutos_esperados": minutos_esperados,
            "minutos_laborados": minutos_laborados,
            "horas_catedra_esperadas": horas_esperadas,
            "horas_catedra_laboradas": horas_laboradas,
            "saldo_horas_catedra": saldo,
            "porcentaje_cumplimiento": porcentaje_cumplimiento,
            "detalle_clases": [
                {
                    "grilla_horaria_id": detalle.grilla_horaria_id,
                    "fecha": detalle.fecha.isoformat(),
                    "curso": detalle.curso,
                    "materia": detalle.materia,
                    "hora_inicio": detalle.hora_inicio.strftime("%H:%M"),
                    "hora_fin": detalle.hora_fin.strftime("%H:%M"),
                    "minutos_esperados": detalle.minutos_esperados,
                    "minutos_laborados": detalle.minutos_laborados,
                    "estado": detalle.estado,
                }
                for detalle in detalles
            ],
        }

    @abstractmethod
    def _convertir_minutos_a_horas(self, minutos: int, minutos_hora_catedra: int) -> float:
        """Convierte minutos a horas cátedra según la regla de la estrategia."""

    @staticmethod
    def _indexar_firmas(firmas_asistencia) -> dict:
        """Organiza las firmas por bloque horario, fecha y tipo."""

        indice = {}
        for firma in firmas_asistencia:
            clave = (firma.grilla_horaria_id, firma.fecha)
            indice.setdefault(clave, {})[firma.tipo_firma] = firma
        return indice

    def _evaluar_clases(
        self,
        grillas_horarias,
        firmas_por_clase: dict,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[DetalleClaseEvaluada]:
        """Recorre las fechas del período y evalúa cada bloque de la grilla."""

        cantidad_dias = (fecha_fin - fecha_inicio).days
        if cantidad_dias > 731:
            raise ErrorValidacion("El período de cálculo no puede superar los dos años.")

        detalles = []
        for grilla in grillas_horarias:
            for numero_dia in range(cantidad_dias + 1):
                fecha_evaluada = fecha_inicio + timedelta(days=numero_dia)
                if fecha_evaluada.isoweekday() != grilla.dia_semana:
                    continue

                inicio_programado = datetime.combine(fecha_evaluada, grilla.hora_inicio)
                fin_programado = datetime.combine(fecha_evaluada, grilla.hora_fin)
                minutos_esperados = int(
                    (fin_programado - inicio_programado).total_seconds() // 60
                )

                firmas_del_dia = firmas_por_clase.get((grilla.id, fecha_evaluada), {})
                firma_ingreso = firmas_del_dia.get(TipoFirma.INGRESO)
                firma_egreso = firmas_del_dia.get(TipoFirma.EGRESO)

                minutos_laborados = 0
                if firma_ingreso is not None and firma_egreso is not None:
                    minutos_laborados = max(
                        0,
                        int(
                            (
                                firma_egreso.marca_temporal
                                - firma_ingreso.marca_temporal
                            ).total_seconds()
                            // 60
                        ),
                    )
                    estado = "Completa"
                elif firma_ingreso is not None or firma_egreso is not None:
                    estado = "Incompleta"
                else:
                    estado = "Sin firma"

                detalles.append(
                    DetalleClaseEvaluada(
                        grilla_horaria_id=grilla.id,
                        fecha=fecha_evaluada,
                        curso=grilla.curso.nombre_completo,
                        materia=grilla.materia.nombre,
                        hora_inicio=grilla.hora_inicio,
                        hora_fin=grilla.hora_fin,
                        minutos_esperados=minutos_esperados,
                        minutos_laborados=minutos_laborados,
                        estado=estado,
                    )
                )
        return detalles


class EstrategiaBalanceHorasCatedraExacta(EstrategiaBalanceHorasCatedra):
    """Divide los minutos exactos por la duración de la hora cátedra."""

    nombre = "exacta"

    def _convertir_minutos_a_horas(self, minutos: int, minutos_hora_catedra: int) -> float:
        """Convierte minutos a horas cátedra con redondeo a dos decimales."""

        return round(minutos / minutos_hora_catedra, 2)


class EstrategiaBalanceHorasCatedraPorBloques(EstrategiaBalanceHorasCatedra):
    """Considera únicamente horas cátedra completas (división entera)."""

    nombre = "por_bloques"

    def _convertir_minutos_a_horas(self, minutos: int, minutos_hora_catedra: int) -> float:
        """Cuenta bloques completos de hora cátedra."""

        return float(minutos // minutos_hora_catedra)


ESTRATEGIAS_DISPONIBLES = {
    EstrategiaBalanceHorasCatedraExacta.nombre: EstrategiaBalanceHorasCatedraExacta,
    EstrategiaBalanceHorasCatedraPorBloques.nombre: EstrategiaBalanceHorasCatedraPorBloques,
}


def obtener_estrategia_balance_horas(nombre_estrategia: str | None) -> EstrategiaBalanceHorasCatedra:
    """Devuelve la estrategia de horas cátedra solicitada."""

    nombre_normalizado = (nombre_estrategia or "exacta").strip().lower()
    clase_estrategia = ESTRATEGIAS_DISPONIBLES.get(nombre_normalizado)
    if clase_estrategia is None:
        raise ErrorValidacion(
            "Estrategia de cálculo de horas cátedra desconocida.",
            detalles={"estrategias_permitidas": sorted(ESTRATEGIAS_DISPONIBLES)},
        )
    return clase_estrategia()
