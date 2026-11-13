"""Servicio de gestión de usuarios, estudiantes y docentes."""

import re

from ..errores import ErrorConflicto, ErrorNoEncontrado, ErrorProhibido, ErrorValidacion
from ..modelos import Docente, Estudiante, Usuario
from ..modelos.enumeraciones import NombreRol
from ..presentadores import presentar_docente, presentar_estudiante, presentar_usuario
from ..repositorios import RepositorioUsuario
from ..seguridad import generar_hash_contrasena
from ..utilidades.validadores import (
    obtener_cadena_opcional,
    obtener_cadena_requerida,
    obtener_fecha_iso,
    validar_contrasena,
    validar_correo_electronico,
)

PATRON_NOMBRE_USUARIO = re.compile(r"^[a-zA-Z0-9._-]+$")


def resolver_nombre_rol(valor_rol: str) -> NombreRol:
    """Convierte el texto recibido en un rol institucional válido."""

    for nombre_rol in NombreRol:
        if nombre_rol.value.lower() == str(valor_rol).strip().lower():
            return nombre_rol

    raise ErrorValidacion(
        "Rol inválido.",
        detalles={"roles_permitidos": [rol.value for rol in NombreRol]},
    )


class ServicioUsuarios:
    """Creación, consulta y administración de cuentas institucionales."""

    def __init__(self, repositorio_usuario: RepositorioUsuario | None = None):
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()

    def crear_usuario(self, datos: dict) -> Usuario:
        """Crea una cuenta genérica con el rol indicado en la petición."""

        datos_usuario = self._validar_datos_de_cuenta(datos)
        nombre_rol = resolver_nombre_rol(
            obtener_cadena_requerida(datos, "rol", longitud_maxima=40)
        )

        self._verificar_disponibilidad(datos_usuario)

        usuario = self._construir_usuario(datos_usuario, nombre_rol)
        self.repositorio_usuario.agregar(usuario)
        self.repositorio_usuario.confirmar_cambios()
        return usuario

    def crear_estudiante(self, datos: dict) -> Estudiante:
        """Crea la cuenta y el perfil académico de un estudiante."""

        datos_usuario = self._validar_datos_de_cuenta(datos)
        legajo = obtener_cadena_requerida(datos, "legajo", longitud_maxima=30)
        nombres = obtener_cadena_requerida(datos, "nombres", longitud_maxima=120)
        apellidos = obtener_cadena_requerida(datos, "apellidos", longitud_maxima=120)
        fecha_nacimiento = obtener_fecha_iso(datos, "fecha_nacimiento", requerida=False)

        self._verificar_disponibilidad(datos_usuario)
        if self.repositorio_usuario.obtener_estudiante_por_legajo(legajo) is not None:
            raise ErrorConflicto(f"Ya existe un estudiante con el legajo '{legajo}'.")

        usuario = self._construir_usuario(datos_usuario, NombreRol.ALUMNO)
        estudiante = Estudiante(
            usuario=usuario,
            legajo=legajo,
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
        )

        self.repositorio_usuario.agregar(usuario)
        self.repositorio_usuario.agregar(estudiante)
        self.repositorio_usuario.confirmar_cambios()
        return estudiante

    def crear_docente(self, datos: dict) -> Docente:
        """Crea la cuenta y el perfil laboral de un docente."""

        datos_usuario = self._validar_datos_de_cuenta(datos)
        legajo = obtener_cadena_requerida(datos, "legajo", longitud_maxima=30)
        nombres = obtener_cadena_requerida(datos, "nombres", longitud_maxima=120)
        apellidos = obtener_cadena_requerida(datos, "apellidos", longitud_maxima=120)
        titulo_habilitante = obtener_cadena_opcional(
            datos, "titulo_habilitante", longitud_maxima=255
        )

        self._verificar_disponibilidad(datos_usuario)
        if self.repositorio_usuario.obtener_docente_por_legajo(legajo) is not None:
            raise ErrorConflicto(f"Ya existe un docente con el legajo '{legajo}'.")

        usuario = self._construir_usuario(datos_usuario, NombreRol.DOCENTE)
        docente = Docente(
            usuario=usuario,
            legajo=legajo,
            nombres=nombres,
            apellidos=apellidos,
            titulo_habilitante=titulo_habilitante,
        )

        self.repositorio_usuario.agregar(usuario)
        self.repositorio_usuario.agregar(docente)
        self.repositorio_usuario.confirmar_cambios()
        return docente

    def listar_usuarios(self, rol=None, activo: bool | None = None) -> list[dict]:
        """Lista cuentas serializadas, con filtros opcionales."""

        usuarios = self.repositorio_usuario.listar_usuarios(rol=rol, activo=activo)
        return [presentar_usuario(usuario) for usuario in usuarios]

    def obtener_usuario(self, usuario_id: int) -> dict:
        """Obtiene una cuenta por identificador o falla con HTTP 404."""

        usuario = self.repositorio_usuario.obtener_por_id(usuario_id)
        if usuario is None:
            raise ErrorNoEncontrado("El usuario solicitado no existe.")
        return presentar_usuario(usuario)

    def cambiar_estado_usuario(
        self, usuario_id: int, activo: bool, usuario_actual
    ) -> dict:
        """Activa o desactiva una cuenta, impidiendo la autodesactivación."""

        usuario = self.repositorio_usuario.obtener_por_id(usuario_id)
        if usuario is None:
            raise ErrorNoEncontrado("El usuario solicitado no existe.")
        if usuario.id == usuario_actual.id and not activo:
            raise ErrorProhibido("No puede desactivar su propia cuenta.")

        usuario.activo = activo
        self.repositorio_usuario.confirmar_cambios()
        return presentar_usuario(usuario)

    def listar_estudiantes(self, curso_id: int | None = None) -> list[dict]:
        """Lista estudiantes, opcionalmente filtrados por curso."""

        estudiantes = self.repositorio_usuario.listar_estudiantes(curso_id=curso_id)
        return [presentar_estudiante(estudiante) for estudiante in estudiantes]

    def listar_docentes(self) -> list[dict]:
        """Lista todos los docentes."""

        docentes = self.repositorio_usuario.listar_docentes()
        return [presentar_docente(docente) for docente in docentes]

    def _validar_datos_de_cuenta(self, datos: dict) -> dict:
        """Valida los campos comunes de una cuenta y normaliza el correo."""

        nombre_usuario = obtener_cadena_requerida(
            datos, "nombre_usuario", longitud_maxima=80, longitud_minima=3
        )
        if not PATRON_NOMBRE_USUARIO.fullmatch(nombre_usuario):
            raise ErrorValidacion(
                "El nombre de usuario sólo admite letras, números, puntos, guiones y guiones bajos."
            )

        correo_electronico = validar_correo_electronico(
            obtener_cadena_requerida(datos, "correo_electronico", longitud_maxima=255)
        ).lower()
        contrasena = validar_contrasena(
            obtener_cadena_requerida(datos, "contrasena", longitud_maxima=128)
        )

        return {
            "nombre_usuario": nombre_usuario,
            "correo_electronico": correo_electronico,
            "contrasena": contrasena,
        }

    def _verificar_disponibilidad(self, datos_usuario: dict) -> None:
        """Verifica que nombre de usuario y correo no estén registrados."""

        if (
            self.repositorio_usuario.obtener_por_nombre_usuario(
                datos_usuario["nombre_usuario"]
            )
            is not None
        ):
            raise ErrorConflicto(
                f"El nombre de usuario '{datos_usuario['nombre_usuario']}' ya está en uso."
            )
        if (
            self.repositorio_usuario.obtener_por_correo_electronico(
                datos_usuario["correo_electronico"]
            )
            is not None
        ):
            raise ErrorConflicto(
                f"El correo electrónico '{datos_usuario['correo_electronico']}' ya está registrado."
            )

    def _construir_usuario(self, datos_usuario: dict, nombre_rol: NombreRol) -> Usuario:
        """Construye una entidad `Usuario` con la contraseña ya cifrada."""

        rol = self.repositorio_usuario.obtener_rol_por_nombre(nombre_rol)
        if rol is None:
            raise ErrorNoEncontrado(
                f"El rol '{nombre_rol.value}' no está inicializado en la base de datos."
            )

        return Usuario(
            nombre_usuario=datos_usuario["nombre_usuario"],
            correo_electronico=datos_usuario["correo_electronico"],
            hash_contrasena=generar_hash_contrasena(datos_usuario["contrasena"]),
            rol=rol,
            activo=True,
        )
