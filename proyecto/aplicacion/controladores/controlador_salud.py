"""Endpoints de verificación de disponibilidad del servicio."""

from flask import Blueprint

from ..utilidades import obtener_marca_temporal_servidor, respuesta_exitosa

blueprint = Blueprint("salud", __name__)


@blueprint.get("/salud")
def verificar_salud():
    """Informa que la API está operativa y la hora institucional del servidor."""

    return respuesta_exitosa(
        {
            "estado": "operativo",
            "servicio": "API de gestión de asistencia institucional",
            "marca_temporal_servidor": obtener_marca_temporal_servidor().isoformat(
                timespec="seconds"
            ),
        }
    )
