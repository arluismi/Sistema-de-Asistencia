"""Autenticación por token Bearer y control de acceso por roles."""

from functools import wraps

from flask import g, request

from ..errores import ErrorNoAutenticado, ErrorProhibido
from ..repositorios import RepositorioUsuario
from .tokens import decodificar_token_acceso

PREFIJO_AUTORIZACION = "Bearer "


def obtener_usuario_autenticado():
    """Recupera el usuario de la petición actual a partir del token JWT.

    El resultado se guarda en `flask.g`, almacenamiento con alcance de una
    petición, para resolver la autenticación una sola vez por solicitud.
    """

    usuario_en_contexto = g.get("usuario_actual")
    if usuario_en_contexto is not None:
        return usuario_en_contexto

    encabezado_autorizacion = request.headers.get("Authorization", "")
    if not encabezado_autorizacion.startswith(PREFIJO_AUTORIZACION):
        raise ErrorNoAutenticado(
            "Debe enviar el encabezado Authorization con el formato 'Bearer <token>'."
        )

    token = encabezado_autorizacion[len(PREFIJO_AUTORIZACION) :].strip()
    contenido_token = decodificar_token_acceso(token)

    try:
        usuario_id = int(contenido_token.get("sub"))
    except (TypeError, ValueError):
        raise ErrorNoAutenticado("El token de acceso no contiene un usuario válido.")

    usuario = RepositorioUsuario().obtener_por_id(usuario_id)
    if usuario is None:
        raise ErrorNoAutenticado("La cuenta asociada al token no existe.")
    if not usuario.activo:
        raise ErrorNoAutenticado("La cuenta asociada al token está inactiva.")

    g.usuario_actual = usuario
    return usuario


def requiere_autenticacion(funcion_controladora):
    """Exige un token válido antes de ejecutar la función controladora."""

    @wraps(funcion_controladora)
    def envoltura(*argumentos, **argumentos_nombrados):
        obtener_usuario_autenticado()
        return funcion_controladora(*argumentos, **argumentos_nombrados)

    return envoltura


def requiere_roles(*roles_permitidos):
    """Restringe la ejecución a los roles indicados y exige autenticación previa."""

    def decorador(funcion_controladora):
        @wraps(funcion_controladora)
        def envoltura(*argumentos, **argumentos_nombrados):
            usuario = obtener_usuario_autenticado()
            if usuario.rol.nombre not in roles_permitidos:
                raise ErrorProhibido(
                    "Su rol no tiene autorización para acceder a este recurso. "
                    f"Roles permitidos: {', '.join(rol.value for rol in roles_permitidos)}."
                )
            return funcion_controladora(*argumentos, **argumentos_nombrados)

        return envoltura

    return decorador
