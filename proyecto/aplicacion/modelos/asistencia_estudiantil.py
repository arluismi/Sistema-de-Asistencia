"""Modelo del registro de asistencia estudiantil."""

from ..extenciones import base_de_datos
from .base import ModeloBase
from .columnas_enum import columna_enum
from .enumeraciones import EstadoAsistencia


class RegistroAsistenciaEstudiantil(ModeloBase):
    """Estado de asistencia de un estudiante para una materia, curso y fecha.

    La combinación `(estudiante, curso, materia, fecha)` es única: una recarga
    diaria actualiza el registro existente en lugar de duplicarlo.
    """

    __tablename__ = "registros_asistencia_estudiantil"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "estudiante_id",
            "curso_id",
            "materia_id",
            "fecha",
            name="uq_asistencia_estudiante_curso_materia_fecha",
        ),
        base_de_datos.Index(
            "ix_asistencia_curso_fecha", "curso_id", "fecha"
        ),
    )

    estudiante_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("estudiantes.id", ondelete="RESTRICT"),
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
    fecha = base_de_datos.Column(base_de_datos.Date, nullable=False, index=True)
    estado = base_de_datos.Column(
        columna_enum(EstadoAsistencia, "estado_asistencia_estudiantil"),
        nullable=False,
    )
    observacion = base_de_datos.Column(base_de_datos.String(500), nullable=True)
    registrado_por_usuario_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    estudiante = base_de_datos.relationship(
        "Estudiante", back_populates="registros_asistencia"
    )
    curso = base_de_datos.relationship("Curso", back_populates="registros_asistencia")
    materia = base_de_datos.relationship("Materia", back_populates="registros_asistencia")
    registrado_por = base_de_datos.relationship("Usuario")

    def __repr__(self) -> str:
        return (
            f"<RegistroAsistencia estudiante={self.estudiante_id} "
            f"fecha={self.fecha} estado={self.estado.value}>"
        )
