"""Modelos de grilla horaria, firmas e incidencias del personal docente."""

from ..extenciones import base_de_datos
from .base import ModeloBase
from .columnas_enum import columna_enum
from .enumeraciones import TipoFirma, TipoIncidencia


class GrillaHorariaInstitucional(ModeloBase):
    """Bloque horario asignado a un docente para una materia y curso.

    `dia_semana` usa la numeración ISO: 1 = lunes, 7 = domingo.
    """

    __tablename__ = "grillas_horarias_institucionales"
    __table_args__ = (
        base_de_datos.CheckConstraint(
            "dia_semana >= 1 AND dia_semana <= 7", name="ck_grilla_dia_semana"
        ),
        base_de_datos.CheckConstraint(
            "hora_inicio < hora_fin", name="ck_grilla_horario_ordenado"
        ),
        base_de_datos.UniqueConstraint(
            "docente_id",
            "dia_semana",
            "hora_inicio",
            name="uq_grilla_docente_horario",
        ),
        base_de_datos.UniqueConstraint(
            "curso_id",
            "dia_semana",
            "hora_inicio",
            name="uq_grilla_curso_horario",
        ),
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
    docente_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("docentes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dia_semana = base_de_datos.Column(base_de_datos.Integer, nullable=False)
    hora_inicio = base_de_datos.Column(base_de_datos.Time, nullable=False)
    hora_fin = base_de_datos.Column(base_de_datos.Time, nullable=False)
    aula = base_de_datos.Column(base_de_datos.String(60), nullable=True)

    curso = base_de_datos.relationship("Curso", back_populates="grillas_horarias")
    materia = base_de_datos.relationship("Materia", back_populates="grillas_horarias")
    docente = base_de_datos.relationship("Docente", back_populates="grillas_horarias")
    firmas_asistencia = base_de_datos.relationship(
        "FirmaAsistencia", back_populates="grilla_horaria"
    )
    incidencias = base_de_datos.relationship(
        "IncidenciaHoraria", back_populates="grilla_horaria"
    )

    def __repr__(self) -> str:
        return (
            f"<GrillaHoraria docente={self.docente_id} dia={self.dia_semana} "
            f"{self.hora_inicio}-{self.hora_fin}>"
        )


class FirmaAsistencia(ModeloBase):
    """Marca de ingreso o egreso de un docente, generada por el servidor.

    El campo `marca_temporal` nunca se recibe desde el cliente: lo completa el
    servicio con el reloj institucional del servidor.
    """

    __tablename__ = "firmas_asistencia_docente"
    __table_args__ = (
        base_de_datos.UniqueConstraint(
            "docente_id",
            "grilla_horaria_id",
            "fecha",
            "tipo_firma",
            name="uq_firma_docente_grilla_fecha_tipo",
        ),
    )

    docente_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("docentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grilla_horaria_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("grillas_horarias_institucionales.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo_firma = base_de_datos.Column(
        columna_enum(TipoFirma, "tipo_firma_docente"), nullable=False
    )
    fecha = base_de_datos.Column(base_de_datos.Date, nullable=False, index=True)
    marca_temporal = base_de_datos.Column(base_de_datos.DateTime, nullable=False)
    observacion = base_de_datos.Column(base_de_datos.String(500), nullable=True)
    registrado_por_usuario_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    docente = base_de_datos.relationship("Docente", back_populates="firmas_asistencia")
    grilla_horaria = base_de_datos.relationship(
        "GrillaHorariaInstitucional", back_populates="firmas_asistencia"
    )
    registrado_por = base_de_datos.relationship("Usuario")
    incidencia = base_de_datos.relationship(
        "IncidenciaHoraria", back_populates="firma_asistencia", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<FirmaAsistencia docente={self.docente_id} fecha={self.fecha} "
            f"tipo={self.tipo_firma.value}>"
        )


class IncidenciaHoraria(ModeloBase):
    """Discrepancia horaria detectada o licencia registrada para un docente."""

    __tablename__ = "incidencias_horarias"

    docente_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("docentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grilla_horaria_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("grillas_horarias_institucionales.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    firma_asistencia_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("firmas_asistencia_docente.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )
    tipo = base_de_datos.Column(
        columna_enum(TipoIncidencia, "tipo_incidencia_docente"), nullable=False
    )
    fecha = base_de_datos.Column(base_de_datos.Date, nullable=False, index=True)
    minutos_desviacion = base_de_datos.Column(
        base_de_datos.Integer, nullable=False, default=0
    )
    descripcion = base_de_datos.Column(base_de_datos.String(500), nullable=False)
    generada_automaticamente = base_de_datos.Column(
        base_de_datos.Boolean, nullable=False, default=True
    )
    registrado_por_usuario_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
    )

    docente = base_de_datos.relationship("Docente", back_populates="incidencias")
    grilla_horaria = base_de_datos.relationship(
        "GrillaHorariaInstitucional", back_populates="incidencias"
    )
    firma_asistencia = base_de_datos.relationship(
        "FirmaAsistencia", back_populates="incidencia"
    )
    registrado_por = base_de_datos.relationship("Usuario")

    def __repr__(self) -> str:
        return f"<IncidenciaHoraria docente={self.docente_id} tipo={self.tipo.value}>"
