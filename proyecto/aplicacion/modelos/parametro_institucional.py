"""Modelo de parámetros institucionales configurables."""

from ..extenciones import base_de_datos
from .base import ModeloBase


class ParametroInstitucional(ModeloBase):
    """Par clave-valor con las reglas configurables del instituto.

    Se utiliza para evitar valores mágicos en el código: umbral de regularidad,
    límite de inasistencias consecutivas, tolerancia de firmas y estrategias de
    cálculo seleccionadas.
    """

    __tablename__ = "parametros_institucionales"

    clave = base_de_datos.Column(
        base_de_datos.String(100), nullable=False, unique=True, index=True
    )
    valor = base_de_datos.Column(base_de_datos.String(255), nullable=False)
    descripcion = base_de_datos.Column(base_de_datos.String(500), nullable=False)

    def __repr__(self) -> str:
        return f"<ParametroInstitucional {self.clave}={self.valor}>"
