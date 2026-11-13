"""Constructores de respuestas HTTP uniformes."""

from typing import Any

from flask import jsonify


def respuesta_exitosa(
    datos: Any = None,
    mensaje: str | None = None,
    codigo_http: int = 200,
):
    """Construye una respuesta JSON de éxito con la estructura acordada.

    `jsonify` serializa el diccionario a JSON, escapa correctamente los textos y
    establece el encabezado `Content-Type: application/json`.
    """

    cuerpo = {"datos": datos}
    if mensaje is not None:
        cuerpo["mensaje"] = mensaje
    return jsonify(cuerpo), codigo_http


def respuesta_creada(datos: Any = None, mensaje: str | None = None):
    """Atajo para respuestas de creación con código HTTP 201."""

    return respuesta_exitosa(datos=datos, mensaje=mensaje, codigo_http=201)
