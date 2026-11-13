"""Consultas de parámetros institucionales."""

from sqlalchemy import select

from ..modelos import ParametroInstitucional
from .repositorio_base import RepositorioBase


class RepositorioParametrosInstitucionales(RepositorioBase):
    """Acceso al par clave-valor de configuración institucional."""

    modelo = ParametroInstitucional

    def obtener_por_clave(self, clave: str) -> ParametroInstitucional | None:
        """Busca un parámetro por su clave única."""

        return self.sesion.execute(
            select(ParametroInstitucional).where(
                ParametroInstitucional.clave == clave
            )
        ).scalar_one_or_none()

    def listar_todos(self):
        """Lista todos los parámetros ordenados por clave."""

        return self.sesion.execute(
            select(ParametroInstitucional).order_by(ParametroInstitucional.clave)
        ).scalars().all()
