"""Endpoints de reportes PDF y Excel."""

from io import BytesIO

from flask import Blueprint, request, send_file

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import NombreRol
from ..seguridad import requiere_roles
from ..servicios.servicio_reportes import ServicioReportes
from ..utilidades.validadores import (
    obtener_argumento_cadena,
    obtener_argumento_entero,
)

blueprint = Blueprint("reportes", __name__)

FORMATOS_PERMITIDOS = {"pdf", "xlsx"}


def _validar_formato(formato: str) -> str:
    """Verifica que el formato solicitado sea soportado."""

    formato_normalizado = formato.lower()
    if formato_normalizado not in FORMATOS_PERMITIDOS:
        raise ErrorValidacion(
            "Formato de reporte no soportado.",
            detalles={"formatos_permitidos": sorted(FORMATOS_PERMITIDOS)},
        )
    return formato_normalizado


def _responder_archivo(contenido: bytes, mimetype: str, nombre_archivo: str):
    """Construye la respuesta de descarga del reporte generado.

    `send_file` de Flask envuelve el flujo binario, establece el tipo MIME y
    agrega los encabezados de descarga, incluido el nombre sugerido.
    """

    return send_file(
        BytesIO(contenido),
        mimetype=mimetype,
        as_attachment=True,
        download_name=nombre_archivo,
        max_age=0,
    )


@blueprint.get("/reportes/asistencia-estudiantes.<string:formato>")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR)
def descargar_reporte_asistencia_estudiantes(formato: str):
    """Descarga el reporte de asistencia de un curso en PDF o Excel."""

    formato_validado = _validar_formato(formato)
    curso_id = obtener_argumento_entero(
        request.args, "curso_id", requerido=True, valor_minimo=1
    )
    periodo_id = obtener_argumento_entero(
        request.args, "periodo_id", requerido=True, valor_minimo=1
    )
    estrategia = obtener_argumento_cadena(request.args, "estrategia")

    servicio = ServicioReportes()
    contenido, nombre_archivo, mimetype = (
        servicio.generar_reporte_asistencia_estudiantes(
            curso_id=curso_id,
            periodo_id=periodo_id,
            formato=formato_validado,
            estrategia=estrategia,
        )
    )
    return _responder_archivo(contenido, mimetype, nombre_archivo)


@blueprint.get("/reportes/horas-docentes.<string:formato>")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR)
def descargar_reporte_horas_docentes(formato: str):
    """Descarga el reporte de horas cátedra docentes en PDF o Excel."""

    formato_validado = _validar_formato(formato)
    periodo_id = obtener_argumento_entero(
        request.args, "periodo_id", requerido=True, valor_minimo=1
    )
    estrategia = obtener_argumento_cadena(request.args, "estrategia")

    servicio = ServicioReportes()
    contenido, nombre_archivo, mimetype = servicio.generar_reporte_horas_docentes(
        periodo_id=periodo_id,
        formato=formato_validado,
        estrategia=estrategia,
    )
    return _responder_archivo(contenido, mimetype, nombre_archivo)
