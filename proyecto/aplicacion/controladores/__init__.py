"""Blueprints de la API.

Centraliza la lista de controladores que la fábrica de la aplicación registra
bajo el prefijo `/api/v1`.
"""

from .controlador_asistencia_docente import blueprint as blueprint_asistencia_docente
from .controlador_asistencia_estudiantil import (
    blueprint as blueprint_asistencia_estudiantil,
)
from .controlador_autenticacion import blueprint as blueprint_autenticacion
from .controlador_configuracion import blueprint as blueprint_configuracion
from .controlador_estructura_academica import (
    blueprint as blueprint_estructura_academica,
)
from .controlador_reportes import blueprint as blueprint_reportes
from .controlador_salud import blueprint as blueprint_salud
from .controlador_usuarios import blueprint as blueprint_usuarios

LISTA_DE_BLUEPRINTS = [
    blueprint_salud,
    blueprint_autenticacion,
    blueprint_usuarios,
    blueprint_estructura_academica,
    blueprint_asistencia_estudiantil,
    blueprint_asistencia_docente,
    blueprint_reportes,
    blueprint_configuracion,
]

__all__ = ["LISTA_DE_BLUEPRINTS"]
