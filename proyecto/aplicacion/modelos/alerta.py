"""Modelo de alertas para el tablero de control."""

from datetime import datetime

from ..extenciones import base_de_datos
from .base import ModeloBase
from .columnas_enum import columna_enum
from .enumeraciones import NivelAlerta, TipoAlerta


class AlertaAsistencia(ModeloBase):
    """Alerta generada cuando la asistencia de un estudiante requiere atención.

    Las alertas son producidas por los suscriptores del patrón Observer y
    consultadas por el tablero de control de Preceptoría y Dirección.
    """

    __tablename__ = "alertas_asistencia"
    __table_args__ = (
        base_de_datos.Index(
            "ix_alerta_estudiante_activa", "estudiante_id", "activa"
        ),
    )

    estudiante_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("estudiantes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo = base_de_datos.Column(
        columna_enum(TipoAlerta, "tipo_alerta_asistencia"), nullable=False
    )
    nivel = base_de_datos.Column(
        columna_enum(NivelAlerta, "nivel_alerta_asistencia"), nullable=False
    )
    mensaje = base_de_datos.Column(base_de_datos.String(500), nullable=False)
    porcentaje_asistencia = base_de_datos.Column(
        base_de_datos.Numeric(5, 2), nullable=True
    )
    fecha_generacion = base_de_datos.Column(
        base_de_datos.DateTime, nullable=False, default=datetime.now
    )
    activa = base_de_datos.Column(base_de_datos.Boolean, nullable=False, default=True)
    leida = base_de_datos.Column(base_de_datos.Boolean, nullable=False, default=False)

    estudiante = base_de_datos.relationship("Estudiante", back_populates="alertas")

    def __repr__(self) -> str:
        return f"<AlertaAsistencia estudiante={self.estudiante_id} tipo={self.tipo.value}>"
