"""Repositorios de acceso a datos (patrón Repository / DAO)."""

from .repositorio_alertas import RepositorioAlertas
from .repositorio_asistencia_docente import RepositorioAsistenciaDocente
from .repositorio_asistencia_estudiantil import RepositorioAsistenciaEstudiantil
from .repositorio_base import RepositorioBase
from .repositorio_estructura_academica import RepositorioEstructuraAcademica
from .repositorio_parametros import RepositorioParametrosInstitucionales
from .repositorio_usuario import RepositorioUsuario

__all__ = [
    "RepositorioAlertas",
    "RepositorioAsistenciaDocente",
    "RepositorioAsistenciaEstudiantil",
    "RepositorioBase",
    "RepositorioEstructuraAcademica",
    "RepositorioParametrosInstitucionales",
    "RepositorioUsuario",
]
