"""Consultas de alertas del tablero de control."""

from sqlalchemy import select

from ..modelos import AlertaAsistencia
from .repositorio_base import RepositorioBase


class RepositorioAlertas(RepositorioBase):
    """Acceso a las alertas de asistencia estudiantil."""

    modelo = AlertaAsistencia

    def listar_alertas(
        self,
        estudiante_id: int | None = None,
        activa: bool | None = None,
        leida: bool | None = None,
    ):
        """Lista alertas con filtros opcionales, de la más reciente a la más antigua."""

        consulta = select(AlertaAsistencia).order_by(
            AlertaAsistencia.fecha_generacion.desc(), AlertaAsistencia.id.desc()
        )
        if estudiante_id is not None:
            consulta = consulta.where(AlertaAsistencia.estudiante_id == estudiante_id)
        if activa is not None:
            consulta = consulta.where(AlertaAsistencia.activa.is_(activa))
        if leida is not None:
            consulta = consulta.where(AlertaAsistencia.leida.is_(leida))
        return self.sesion.execute(consulta).scalars().all()

    def existe_alerta_activa(self, estudiante_id: int, tipo) -> bool:
        """Indica si el estudiante ya tiene una alerta activa del mismo tipo."""

        return (
            self.sesion.execute(
                select(AlertaAsistencia.id)
                .where(
                    AlertaAsistencia.estudiante_id == estudiante_id,
                    AlertaAsistencia.tipo == tipo,
                    AlertaAsistencia.activa.is_(True),
                )
                .limit(1)
            ).first()
            is not None
        )
