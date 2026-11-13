"""Modelo base con identificador y marcas de auditoría."""

from datetime import datetime

from ..extenciones import base_de_datos


class ModeloBase(base_de_datos.Model):
    """Columnas comunes a todas las entidades persistidas.

    `__abstract__` evita que SQLAlchemy cree una tabla para esta clase; sólo se
    heredan sus columnas.
    """

    __abstract__ = True

    id = base_de_datos.Column(base_de_datos.Integer, primary_key=True)

    creado_en = base_de_datos.Column(
        base_de_datos.DateTime,
        nullable=False,
        default=datetime.now,
    )

    actualizado_en = base_de_datos.Column(
        base_de_datos.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
