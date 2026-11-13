"""Generación y validación de tokens JWT."""

from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from ..errores import ErrorNoAutenticado


def generar_token_acceso(usuario) -> str:
    """Genera un token JWT firmado con los datos de identidad del usuario.

    El token incluye `sub` (identificador), rol, nombre de usuario, momento de
    emisión (`iat`) y expiración (`exp`). `jwt.encode` firma el contenido con la
    clave configurada y el algoritmo HS256.
    """

    momento_actual = datetime.now(timezone.utc)
    momento_expiracion = momento_actual + timedelta(
        minutes=current_app.config["MINUTOS_VIGENCIA_TOKEN"]
    )
    contenido_token = {
        "sub": str(usuario.id),
        "rol": usuario.rol.nombre.value,
        "nombre_usuario": usuario.nombre_usuario,
        "iat": momento_actual,
        "exp": momento_expiracion,
    }
    return jwt.encode(
        contenido_token,
        current_app.config["CLAVE_TOKEN"],
        algorithm=current_app.config["ALGORITMO_TOKEN"],
    )


def decodificar_token_acceso(token: str) -> dict:
    """Valida la firma y la expiración de un token y devuelve su contenido.

    `jwt.decode` verifica automáticamente la firma y el campo `exp`; cualquier
    fallo se traduce en un error de autenticación uniforme para el cliente.
    """

    try:
        return jwt.decode(
            token,
            current_app.config["CLAVE_TOKEN"],
            algorithms=[current_app.config["ALGORITMO_TOKEN"]],
        )
    except jwt.ExpiredSignatureError:
        raise ErrorNoAutenticado("El token de acceso expiró. Inicie sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise ErrorNoAutenticado("El token de acceso es inválido.")
