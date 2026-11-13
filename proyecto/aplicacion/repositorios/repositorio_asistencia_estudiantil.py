"""Consultas de registros de asistencia estudiantil."""

from datetime import date

from sqlalchemy import select

from ..modelos import RegistroAsistenciaEstudiantil
from .repositorio_base import RepositorioBase


class RepositorioAsistenciaEstudiantil(RepositorioBase):
    """Acceso a los registros diarios de asistencia de estudiantes."""

    modelo = RegistroAsistenciaEstudiantil

    def obtener_registro(
        self,
        estudiante_id: int,
        curso_id: int,
        materia_id: int,
        fecha: date,
    ) -> RegistroAsistenciaEstudiantil | None:
        """Busca el registro único de un estudiante para una clase y fecha."""

        return self.sesion.execute(
            select(RegistroAsistenciaEstudiantil).where(
                RegistroAsistenciaEstudiantil.estudiante_id == estudiante_id,
                RegistroAsistenciaEstudiantil.curso_id == curso_id,
                RegistroAsistenciaEstudiantil.materia_id == materia_id,
                RegistroAsistenciaEstudiantil.fecha == fecha,
            )
        ).scalar_one_or_none()

    def listar_registros(
        self,
        estudiante_id: int | None = None,
        curso_id: int | None = None,
        materia_id: int | None = None,
        fecha: date | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        curso_ids: list[int] | None = None,
    ):
        """Lista registros de asistencia con filtros opcionales y orden cronológico."""

        consulta = select(RegistroAsistenciaEstudiantil).order_by(
            RegistroAsistenciaEstudiantil.fecha,
            RegistroAsistenciaEstudiantil.estudiante_id,
        )
        if estudiante_id is not None:
            consulta = consulta.where(
                RegistroAsistenciaEstudiantil.estudiante_id == estudiante_id
            )
        if curso_id is not None:
            consulta = consulta.where(RegistroAsistenciaEstudiantil.curso_id == curso_id)
        if materia_id is not None:
            consulta = consulta.where(
                RegistroAsistenciaEstudiantil.materia_id == materia_id
            )
        if fecha is not None:
            consulta = consulta.where(RegistroAsistenciaEstudiantil.fecha == fecha)
        if fecha_desde is not None:
            consulta = consulta.where(
                RegistroAsistenciaEstudiantil.fecha >= fecha_desde
            )
        if fecha_hasta is not None:
            consulta = consulta.where(
                RegistroAsistenciaEstudiantil.fecha <= fecha_hasta
            )
        if curso_ids is not None:
            consulta = consulta.where(
                RegistroAsistenciaEstudiantil.curso_id.in_(curso_ids)
            )
        return self.sesion.execute(consulta).scalars().all()

    def listar_ultimos_estados(
        self,
        estudiante_id: int,
        limite: int = 30,
    ):
        """Devuelve los registros más recientes de un estudiante, del más nuevo al más viejo."""

        return self.sesion.execute(
            select(RegistroAsistenciaEstudiantil)
            .where(RegistroAsistenciaEstudiantil.estudiante_id == estudiante_id)
            .order_by(
                RegistroAsistenciaEstudiantil.fecha.desc(),
                RegistroAsistenciaEstudiantil.id.desc(),
            )
            .limit(limite)
        ).scalars().all()
