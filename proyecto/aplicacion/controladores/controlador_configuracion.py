"""Endpoints de configuración institucional."""

from flask import Blueprint

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import NombreRol
from ..seguridad import requiere_roles
from ..servicios.servicio_configuracion_institucional import (
    ServicioConfiguracionInstitucional,
)
from ..utilidades import respuesta_exitosa
from ..utilidades.validadores import obtener_cuerpo_json

blueprint = Blueprint("configuracion", __name__)


@blueprint.get("/configuracion")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def obtener_configuracion():
    """Devuelve los parámetros institucionales vigentes."""

    servicio = ServicioConfiguracionInstitucional()
    return respuesta_exitosa(
        {
            "parametros": [
                {
                    "clave": parametro.clave,
                    "valor": parametro.valor,
                    "descripcion": parametro.descripcion,
                }
                for parametro in servicio.listar_parametros()
            ],
            "valores_aplicados": servicio.configuracion_publica(),
        }
    )


@blueprint.put("/configuracion/<string:clave>")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def actualizar_configuracion(clave: str):
    """Actualiza el valor de un parámetro institucional conocido."""

    datos = obtener_cuerpo_json()
    if "valor" not in datos:
        raise ErrorValidacion("El campo 'valor' es obligatorio.")

    servicio = ServicioConfiguracionInstitucional()
    servicio.actualizar_parametro(clave, datos["valor"])
    return respuesta_exitosa(
        {"clave": clave, "valor": servicio.obtener_valor(clave)},
        "Parámetro actualizado correctamente.",
    )
