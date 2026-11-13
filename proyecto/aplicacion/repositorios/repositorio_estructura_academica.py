"""Consultas de la estructura académica."""

from datetime import date

from sqlalchemy import select

from ..modelos import (
    AsignacionDocenteMateria,
    Curso,
    Estudiante,
    GrillaHorariaInstitucional,
    InscripcionEstudianteCurso,
    Materia,
    PeriodoAcademico,
)
from ..modelos.enumeraciones import EstadoInscripcion
from .repositorio_base import RepositorioBase


class RepositorioEstructuraAcademica(RepositorioBase):
    """Acceso a cursos, materias, períodos, matrículas, asignaciones y grillas."""

    def obtener_curso(self, curso_id: int) -> Curso | None:
        """Busca un curso por su identificador."""

        return self.sesion.get(Curso, curso_id)

    def listar_cursos(self, anio_lectivo: int | None = None):
        """Lista cursos ordenados por año y nombre, con filtro opcional de año."""

        consulta = select(Curso).order_by(
            Curso.anio_lectivo.desc(), Curso.nombre, Curso.division
        )
        if anio_lectivo is not None:
            consulta = consulta.where(Curso.anio_lectivo == anio_lectivo)
        return self.sesion.execute(consulta).scalars().all()

    def obtener_materia(self, materia_id: int) -> Materia | None:
        """Busca una materia por su identificador."""

        return self.sesion.get(Materia, materia_id)

    def listar_materias(self):
        """Lista todas las materias por nombre."""

        return self.sesion.execute(select(Materia).order_by(Materia.nombre)).scalars().all()

    def obtener_periodo(self, periodo_id: int) -> PeriodoAcademico | None:
        """Busca un período académico por su identificador."""

        return self.sesion.get(PeriodoAcademico, periodo_id)

    def listar_periodos(self, anio_lectivo: int | None = None):
        """Lista períodos académicos, opcionalmente filtrados por año lectivo."""

        consulta = select(PeriodoAcademico).order_by(
            PeriodoAcademico.anio_lectivo.desc(), PeriodoAcademico.fecha_inicio
        )
        if anio_lectivo is not None:
            consulta = consulta.where(PeriodoAcademico.anio_lectivo == anio_lectivo)
        return self.sesion.execute(consulta).scalars().all()

    def obtener_periodo_que_contiene_fecha(self, fecha: date) -> PeriodoAcademico | None:
        """Devuelve el período más reciente que incluye la fecha indicada."""

        return self.sesion.execute(
            select(PeriodoAcademico)
            .where(
                PeriodoAcademico.fecha_inicio <= fecha,
                PeriodoAcademico.fecha_fin >= fecha,
            )
            .order_by(PeriodoAcademico.fecha_inicio.desc())
        ).scalars().first()

    def obtener_inscripcion(
        self, estudiante_id: int, curso_id: int
    ) -> InscripcionEstudianteCurso | None:
        """Busca la matrícula de un estudiante en un curso."""

        return self.sesion.execute(
            select(InscripcionEstudianteCurso).where(
                InscripcionEstudianteCurso.estudiante_id == estudiante_id,
                InscripcionEstudianteCurso.curso_id == curso_id,
            )
        ).scalar_one_or_none()

    def listar_inscripciones(
        self,
        curso_id: int | None = None,
        estudiante_id: int | None = None,
    ):
        """Lista matrículas con filtros opcionales de curso o estudiante."""

        consulta = select(InscripcionEstudianteCurso).order_by(
            InscripcionEstudianteCurso.id
        )
        if curso_id is not None:
            consulta = consulta.where(InscripcionEstudianteCurso.curso_id == curso_id)
        if estudiante_id is not None:
            consulta = consulta.where(
                InscripcionEstudianteCurso.estudiante_id == estudiante_id
            )
        return self.sesion.execute(consulta).scalars().all()

    def listar_estudiantes_de_curso(self, curso_id: int):
        """Lista estudiantes activos matriculados en un curso."""

        return self.sesion.execute(
            select(Estudiante)
            .join(
                InscripcionEstudianteCurso,
                InscripcionEstudianteCurso.estudiante_id == Estudiante.id,
            )
            .where(
                InscripcionEstudianteCurso.curso_id == curso_id,
                InscripcionEstudianteCurso.estado == EstadoInscripcion.ACTIVO,
            )
            .order_by(Estudiante.apellidos, Estudiante.nombres)
        ).scalars().all()

    def obtener_asignacion(self, asignacion_id: int) -> AsignacionDocenteMateria | None:
        """Busca una asignación docente por su identificador."""

        return self.sesion.get(AsignacionDocenteMateria, asignacion_id)

    def listar_asignaciones(
        self,
        docente_id: int | None = None,
        curso_id: int | None = None,
        materia_id: int | None = None,
    ):
        """Lista asignaciones docente-materia-curso con filtros opcionales."""

        consulta = select(AsignacionDocenteMateria).order_by(
            AsignacionDocenteMateria.id
        )
        if docente_id is not None:
            consulta = consulta.where(AsignacionDocenteMateria.docente_id == docente_id)
        if curso_id is not None:
            consulta = consulta.where(AsignacionDocenteMateria.curso_id == curso_id)
        if materia_id is not None:
            consulta = consulta.where(AsignacionDocenteMateria.materia_id == materia_id)
        return self.sesion.execute(consulta).scalars().all()

    def existe_asignacion(
        self,
        docente_id: int,
        curso_id: int | None = None,
        materia_id: int | None = None,
    ) -> bool:
        """Verifica si un docente tiene asignada una combinación curso-materia."""

        consulta = select(AsignacionDocenteMateria.id).where(
            AsignacionDocenteMateria.docente_id == docente_id
        )
        if curso_id is not None:
            consulta = consulta.where(AsignacionDocenteMateria.curso_id == curso_id)
        if materia_id is not None:
            consulta = consulta.where(AsignacionDocenteMateria.materia_id == materia_id)
        return self.sesion.execute(consulta.limit(1)).first() is not None

    def obtener_grilla(self, grilla_horaria_id: int) -> GrillaHorariaInstitucional | None:
        """Busca un bloque de grilla horaria por su identificador."""

        return self.sesion.get(GrillaHorariaInstitucional, grilla_horaria_id)

    def listar_grillas(
        self,
        docente_id: int | None = None,
        curso_id: int | None = None,
        materia_id: int | None = None,
        anio_lectivo: int | None = None,
        dia_semana: int | None = None,
    ):
        """Lista bloques horarios con filtros opcionales y orden cronológico."""

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
        if curso_id is not None:
            consulta = consulta.where(GrillaHorariaInstitucional.curso_id == curso_id)
        if materia_id is not None:
            consulta = consulta.where(GrillaHorariaInstitucional.materia_id == materia_id)
        if dia_semana is not None:
            consulta = consulta.where(
                GrillaHorariaInstitucional.dia_semana == dia_semana
            )
        return self.sesion.execute(consulta).scalars().all()
