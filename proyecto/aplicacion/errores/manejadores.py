"""Manejadores globales de errores de la API.

Todas las respuestas de error respetan la misma estructura:

```json
{
  "error": {
    "codigo": "datos_invalidos",
    "mensaje": "Descripción legible",
    "detalles": ["detalle opcional"]
  }
}
```
"""

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from ..extenciones import base_de_datos
from .excepciones import ErrorAplicacion


def registrar_manejadores_de_errores(aplicacion: Flask) -> None:
    """Registra en la aplicación Flask los manejadores de excepciones."""

    @aplicacion.errorhandler(ErrorAplicacion)
    def manejar_error_aplicacion(error: ErrorAplicacion):
        """Convierte un error de negocio en una respuesta JSON con su código HTTP."""

        _revertir_transaccion_pendiente()
        cuerpo_error = {
            "codigo": error.codigo_error,
            "mensaje": error.mensaje,
        }
        if error.detalles is not None:
            cuerpo_error["detalles"] = error.detalles
        return jsonify({"error": cuerpo_error}), error.codigo_http

    @aplicacion.errorhandler(IntegrityError)
    def manejar_error_integridad(error: IntegrityError):
        """Traduce una violación de restricción de base de datos en HTTP 409."""

        _revertir_transaccion_pendiente()
        # `aplicacion.logger` es el registrador estándar de Flask; se usa para
        # conservar la causa técnica sin exponerla al cliente.
        aplicacion.logger.warning("Violación de integridad de datos: %s", error)
        return (
            jsonify(
                {
                    "error": {
                        "codigo": "conflicto_de_datos",
                        "mensaje": (
                            "La operación viola una restricción de integridad. "
                            "Verifique datos duplicados o referencias inexistentes."
                        ),
                    }
                }
            ),
            409,
        )

    @aplicacion.errorhandler(HTTPException)
    def manejar_error_http(error: HTTPException):
        """Normaliza los errores propios de Flask (ruta inexistente, método no permitido)."""

        return (
            jsonify(
                {
                    "error": {
                        "codigo": error.name.lower().replace(" ", "_"),
                        "mensaje": error.description,
                    }
                }
            ),
            error.code or 500,
        )

    @aplicacion.errorhandler(Exception)
    def manejar_error_no_controlado(error: Exception):
        """Captura cualquier falla inesperada y evita filtrar trazas al cliente."""

        _revertir_transaccion_pendiente()
        # `logger.exception` incluye la traza completa en los registros del servidor.
        aplicacion.logger.exception("Error no controlado en la API: %s", error)
        return (
            jsonify(
                {
                    "error": {
                        "codigo": "error_interno",
                        "mensaje": "Ocurrió un error interno. Consulte los registros del servidor.",
                    }
                }
            ),
            500,
        )


def _revertir_transaccion_pendiente() -> None:
    """Descarta cambios incompletos para dejar la sesión de SQLAlchemy utilizable."""

    # `session.rollback` revierte la transacción activa de SQLAlchemy. Se invoca
    # sólo si hay una sesión asociada al contexto actual (por ejemplo, dentro de
    # una petición HTTP o de un comando CLI).
    try:
        base_de_datos.session.rollback()
    except RuntimeError:
        # Ocurre cuando no existe un contexto de aplicación activo.
        pass
