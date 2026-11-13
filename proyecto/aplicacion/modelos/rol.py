"""Modelo de roles institucionales."""

from ..extenciones import base_de_datos
from .base import ModeloBase
from .columnas_enum import columna_enum
from .enumeraciones import NombreRol


class Rol(ModeloBase):
    """Rol asignable a un usuario del sistema.

    La jerarquía se expone como texto en `descripcion` y el orden numérico en
    `nivel_jerarquico` (1 es el máximo nivel). El control de acceso efectivo se
    realiza por nombre de rol en la capa de seguridad.
    """

    __tablename__ = "roles"

    nombre = base_de_datos.Column(
        columna_enum(NombreRol, "nombre_rol"),
        nullable=False,
        unique=True,
    )
    descripcion = base_de_datos.Column(base_de_datos.String(255), nullable=False)
    nivel_jerarquico = base_de_datos.Column(base_de_datos.Integer, nullable=False)

    usuarios = base_de_datos.relationship("Usuario", back_populates="rol")

    def __repr__(self) -> str:
        return f"<Rol {self.nombre.value}>"
