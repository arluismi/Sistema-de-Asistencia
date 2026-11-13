"""Endpoints de autenticación."""

from flask import Blueprint

from ..seguridad import obtener_usuario_autenticado, requiere_autenticacion
from ..servicios.servicio_autenticacion import ServicioAutenticacion
from ..utilidades import respuesta_exitosa
from ..utilidades.validadores import obtener_cadena_requerida, obtener_cuerpo_json

blueprint = Blueprint("autenticacion", __name__)


@blueprint.post("/autenticacion/iniciar-sesion")
def iniciar_sesion():
    """Valida credenciales y devuelve un token de acceso JWT."""

    datos = obtener_cuerpo_json()
    nombre_usuario = obtener_cadena_requerida(
        datos, "nombre_usuario", longitud_maxima=80
    )
    contrasena = obtener_cadena_requerida(datos, "contrasena", longitud_maxima=128)

    servicio = ServicioAutenticacion()
    resultado = servicio.iniciar_sesion(nombre_usuario, contrasena)
    return respuesta_exitosa(resultado, "Sesión iniciada correctamente.")


@blueprint.get("/autenticacion/perfil")
@requiere_autenticacion
def obtener_perfil():
    """Devuelve los datos del usuario autenticado."""

    usuario = obtener_usuario_autenticado()
    servicio = ServicioAutenticacion()
    return respuesta_exitosa(servicio.obtener_perfil(usuario))
