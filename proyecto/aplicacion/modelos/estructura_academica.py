"""Modelos de la estructura académica institucional."""

from datetime import date

from ..extenciones import base_de_datos
from .base import ModeloBase
from .columnas_enum import columna_enum
from .enumeraciones import EstadoInscripcion


class Curso(ModeloBase):
    """Curso o división de la institución para un año lectivo determinado."""

    __tablename__ = "cursos"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "nombre", "division", "anio_lectivo", name="uq_curso_por_anio"
        ),
        base_de_datos.CheckConstraint(
            "anio_lectivo >= 2000 AND anio_lectivo <= 2200",
            name="ck_curso_anio_lectivo",
        ),
    )

    nombre = base_de_datos.Column(base_de_datos.String(80), nullable=False)
    division = base_de_datos.Column(base_de_datos.String(20), nullable=False)
    anio_lectivo = base_de_datos.Column(base_de_datos.Integer, nullable=False, index=True)
    turno = base_de_datos.Column(base_de_datos.String(40), nullable=False)

    inscripciones = base_de_datos.relationship(
        "InscripcionEstudianteCurso", back_populates="curso"
    )
    asignaciones_docentes = base_de_datos.relationship(
        "AsignacionDocenteMateria", back_populates="curso"
    )
    grillas_horarias = base_de_datos.relationship(
        "GrillaHorariaInstitucional", back_populates="curso"
    )
    registros_asistencia = base_de_datos.relationship(
        "RegistroAsistenciaEstudiantil", back_populates="curso"
    )

    @property
    def nombre_completo(self) -> str:
        """Identificación legible del curso usada en respuestas y reportes."""

        return f"{self.nombre} {self.division} ({self.anio_lectivo})"

    def __repr__(self) -> str:
        return f"<Curso {self.nombre_completo}>"


class Materia(ModeloBase):
    """Espacio curricular dictado en uno o más cursos."""

    __tablename__ = "materias"

    nombre = base_de_datos.Column(base_de_datos.String(120), nullable=False, unique=True)
    codigo = base_de_datos.Column(base_de_datos.String(30), nullable=False, unique=True)

    asignaciones_docentes = base_de_datos.relationship(
        "AsignacionDocenteMateria", back_populates="materia"
    )
    grillas_horarias = base_de_datos.relationship(
        "GrillaHorariaInstitucional", back_populates="materia"
    )
    registros_asistencia = base_de_datos.relationship(
        "RegistroAsistenciaEstudiantil", back_populates="materia"
    )

    def __repr__(self) -> str:
        return f"<Materia {self.nombre}>"


class PeriodoAcademico(ModeloBase):
    """Período lectivo usado para agrupar cálculos de asistencia y reportes."""

    __tablename__ = "periodos_academicos"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "nombre", "anio_lectivo", name="uq_periodo_por_anio"
        ),
        base_de_datos.CheckConstraint(
            "fecha_inicio <= fecha_fin", name="ck_periodo_fechas_ordenadas"
        ),
    )

    nombre = base_de_datos.Column(base_de_datos.String(100), nullable=False)
    fecha_inicio = base_de_datos.Column(base_de_datos.Date, nullable=False)
    fecha_fin = base_de_datos.Column(base_de_datos.Date, nullable=False)
    anio_lectivo = base_de_datos.Column(base_de_datos.Integer, nullable=False, index=True)

    def contiene_fecha(self, fecha_consultada: date) -> bool:
        """Indica si una fecha pertenece al rango inclusivo del período."""

        return self.fecha_inicio <= fecha_consultada <= self.fecha_fin

    def __repr__(self) -> str:
        return f"<PeriodoAcademico {self.nombre} {self.anio_lectivo}>"


class InscripcionEstudianteCurso(ModeloBase):
    """Matrícula de un estudiante en un curso."""

    __tablename__ = "inscripciones_estudiantes_cursos"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "estudiante_id", "curso_id", name="uq_inscripcion_estudiante_curso"
        ),
    )

    estudiante_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("estudiantes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curso_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("cursos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_inscripcion = base_de_datos.Column(
        base_de_datos.Date, nullable=False, default=date.today
    )
    estado = base_de_datos.Column(
        columna_enum(EstadoInscripcion, "estado_inscripcion"),
        nullable=False,
        default=EstadoInscripcion.ACTIVO,
    )

    estudiante = base_de_datos.relationship("Estudiante", back_populates="inscripciones")
    curso = base_de_datos.relationship("Curso", back_populates="inscripciones")

    def __repr__(self) -> str:
        return f"<Inscripcion estudiante={self.estudiante_id} curso={self.curso_id}>"


class AsignacionDocenteMateria(ModeloBase):
    """Asignación de un docente para dictar una materia en un curso."""

    __tablename__ = "asignaciones_docentes_materias"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "docente_id",
            "curso_id",
            "materia_id",
            name="uq_asignacion_docente_curso_materia",
        ),
    )

    docente_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("docentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curso_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("cursos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    materia_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    docente = base_de_datos.relationship("Docente", back_populates="asignaciones")
    curso = base_de_datos.relationship("Curso", back_populates="asignaciones_docentes")
    materia = base_de_datos.relationship("Materia", back_populates="asignaciones_docentes")

    def __repr__(self) -> str:
        return (
            f"<Asignacion docente={self.docente_id} curso={self.curso_id} "
            f"materia={self.materia_id}>"
        )
