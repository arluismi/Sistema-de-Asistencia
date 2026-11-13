"""Excepciones de negocio utilizadas por todas las capas.

Permiten que los servicios informen errores con un código HTTP y un código
interno estable, sin depender de Flask. Los manejadores globales convierten
estas excepciones en respuestas JSON uniformes.
"""

from typing import Any


class ErrorAplicacion(Exception):
    """Error controlado del dominio de la aplicación."""

    def __init__(
        self,
        mensaje: str,
        codigo_http: int = 400,
        codigo_error: str = "solicitud_invalida",
        detalles: Any | None = None,
    ):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_http = codigo_http
        self.codigo_error = codigo_error
        self.detalles = detalles


class ErrorValidacion(ErrorAplicacion):
    """Datos de entrada ausentes, con formato incorrecto o fuera de rango."""

    def __init__(self, mensaje: str, detalles: Any | None = None):
        super().__init__(
            mensaje=mensaje,
            codigo_http=400,
            codigo_error="datos_invalidos",
            detalles=detalles,
        )


class ErrorNoAutenticado(ErrorAplicacion):
    """Falta el token, es inválido o expiró."""

    def __init__(self, mensaje: str = "Se requiere autenticación."):
        super().__init__(
            mensaje=mensaje,
            codigo_http=401,
            codigo_error="no_autenticado",
        )


class ErrorProhibido(ErrorAplicacion):
    """El usuario está autenticado pero su rol no autoriza la operación."""

    def __init__(self, mensaje: str = "No tiene permisos para realizar esta operación."):
        super().__init__(
            mensaje=mensaje,
            codigo_http=403,
            codigo_error="acceso_prohibido",
        )


class ErrorNoEncontrado(ErrorAplicacion):
    """El recurso solicitado no existe."""

    def __init__(self, mensaje: str = "El recurso solicitado no existe."):
        super().__init__(
            mensaje=mensaje,
            codigo_http=404,
            codigo_error="recurso_no_encontrado",
        )


class ErrorConflicto(ErrorAplicacion):
    """La operación contradice el estado actual de los datos."""

    def __init__(self, mensaje: str, detalles: Any | None = None):
        super().__init__(
            mensaje=mensaje,
            codigo_http=409,
            codigo_error="conflicto_de_datos",
            detalles=detalles,
        )
