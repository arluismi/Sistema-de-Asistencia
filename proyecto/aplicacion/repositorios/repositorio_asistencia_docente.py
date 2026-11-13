"""Consultas de firmas, incidencias y grillas horarias docentes."""

from datetime import date

from sqlalchemy import select

from ..modelos import Curso, FirmaAsistencia, GrillaHorariaInstitucional, IncidenciaHoraria
from .repositorio_base import RepositorioBase


class RepositorioAsistenciaDocente(RepositorioBase):
    """Acceso a las marcas de asistencia e incidencias del personal docente."""

    def obtener_firma(
        self,
        docente_id: int,
        grilla_horaria_id: int,
        fecha: date,
        tipo_firma,
    ) -> FirmaAsistencia | None:
        """Busca una firma por docente, bloque horario, fecha y tipo."""

        return self.sesion.execute(
            select(FirmaAsistencia).where(
                FirmaAsistencia.docente_id == docente_id,
                FirmaAsistencia.grilla_horaria_id == grilla_horaria_id,
                FirmaAsistencia.fecha == fecha,
                FirmaAsistencia.tipo_firma == tipo_firma,
            )
        ).scalar_one_or_none()

    def listar_firmas(
        self,
        docente_id: int | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        grilla_horaria_id: int | None = None,
    ):
        """Lista firmas con filtros opcionales y orden cronológico."""

        consulta = select(FirmaAsistencia).order_by(
            FirmaAsistencia.fecha, FirmaAsistencia.marca_temporal
        )
        if docente_id is not None:
            consulta = consulta.where(FirmaAsistencia.docente_id == docente_id)
        if fecha_desde is not None:
            consulta = consulta.where(FirmaAsistencia.fecha >= fecha_desde)
        if fecha_hasta is not None:
            consulta = consulta.where(FirmaAsistencia.fecha <= fecha_hasta)
        if grilla_horaria_id is not None:
            consulta = consulta.where(
                FirmaAsistencia.grilla_horaria_id == grilla_horaria_id
            )
        return self.sesion.execute(consulta).scalars().all()

    def listar_incidencias(
        self,
        docente_id: int | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        tipo=None,
    ):
        """Lista incidencias horarias con filtros opcionales."""

        consulta = select(IncidenciaHoraria).order_by(
            IncidenciaHoraria.fecha.desc(), IncidenciaHoraria.id.desc()
        )
        if docente_id is not None:
            consulta = consulta.where(IncidenciaHoraria.docente_id == docente_id)
        if fecha_desde is not None:
            consulta = consulta.where(IncidenciaHoraria.fecha >= fecha_desde)
        if fecha_hasta is not None:
            consulta = consulta.where(IncidenciaHoraria.fecha <= fecha_hasta)
        if tipo is not None:
            consulta = consulta.where(IncidenciaHoraria.tipo == tipo)
        return self.sesion.execute(consulta).scalars().all()

    def listar_grillas(
        self,
        docente_id: int | None = None,
        anio_lectivo: int | None = None,
    ):
        """Lista bloques de grilla con filtros de docente y año lectivo."""

        consulta = select(GrillaHorariaInstitucional).order_by(
            GrillaHorariaInstitucional.dia_semana,
            GrillaHorariaInstitucional.hora_inicio,
        )
        if anio_lectivo is not None:
            consulta = consulta.join(
                Curso, GrillaHorariaInstitucional.curso_id == Curso.id
            ).where(Curso.anio_lectivo == anio_lectivo)
        if docente_id is not None:
            consulta = consulta.where(
                GrillaHorariaInstitucional.docente_id == docente_id
            )
        return self.sesion.execute(consulta).scalars().all()
