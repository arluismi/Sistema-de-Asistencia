"""Servicio de autenticación de usuarios."""

from flask import current_app

from ..errores import ErrorNoAutenticado
from ..presentadores import presentar_usuario
from ..repositorios import RepositorioUsuario
from ..seguridad import generar_token_acceso, verificar_contrasena


class ServicioAutenticacion:
    """Valida credenciales y emite tokens de acceso."""

    def __init__(self, repositorio_usuario: RepositorioUsuario | None = None):
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()

    def iniciar_sesion(self, nombre_usuario: str, contrasena: str) -> dict:
        """Verifica las credenciales y devuelve un token JWT con los datos del usuario."""

        usuario = self.repositorio_usuario.obtener_por_nombre_usuario(nombre_usuario)

        # Se usa el mismo mensaje para usuario inexistente, contraseña incorrecta o
        # cuenta inactiva para no revelar qué dato falló.
        if (
            usuario is None
            or not usuario.activo
            or not verificar_contrasena(contrasena, usuario.hash_contrasena)
        ):
            raise ErrorNoAutenticado("Nombre de usuario o contraseña incorrectos.")

        token_acceso = generar_token_acceso(usuario)
        return {
            "token_acceso": token_acceso,
            "tipo_token": "Bearer",
            "expira_en_minutos": current_app.config["MINUTOS_VIGENCIA_TOKEN"],
            "usuario": presentar_usuario(usuario),
        }

    def obtener_perfil(self, usuario) -> dict:
        """Devuelve los datos públicos del usuario autenticado."""

        return presentar_usuario(usuario)
