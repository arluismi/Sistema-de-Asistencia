"""Excepciones y manejadores de error del backend."""

from .excepciones import (
    ErrorAplicacion,
    ErrorConflicto,
    ErrorNoAutenticado,
    ErrorNoEncontrado,
    ErrorProhibido,
    ErrorValidacion,
)
from .manejadores import registrar_manejadores_de_errores

__all__ = [
    "ErrorAplicacion",
    "ErrorConflicto",
    "ErrorNoAutenticado",
    "ErrorNoEncontrado",
    "ErrorProhibido",
    "ErrorValidacion",
    "registrar_manejadores_de_errores",
]
