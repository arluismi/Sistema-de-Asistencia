"""Endpoints de usuarios, estudiantes y docentes."""

from flask import Blueprint, request

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import NombreRol
from ..presentadores import (
    presentar_docente,
    presentar_estudiante,
    presentar_usuario,
)
from ..seguridad import obtener_usuario_autenticado, requiere_roles
from ..servicios.servicio_usuarios import ServicioUsuarios, resolver_nombre_rol
from ..utilidades import respuesta_creada, respuesta_exitosa
from ..utilidades.validadores import (
    obtener_argumento_booleano,
    obtener_argumento_entero,
    obtener_booleano_opcional,
    obtener_cuerpo_json,
)

blueprint = Blueprint("usuarios", __name__)

ROLES_CONSULTA_ACADEMICA = (
    NombreRol.ADMINISTRATIVO_DIRECTIVO,
    NombreRol.PRECEPTOR,
    NombreRol.DOCENTE,
)


@blueprint.get("/usuarios")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def listar_usuarios():
    """Lista cuentas con filtros opcionales de rol y estado."""

    rol_solicitado = request.args.get("rol")
    nombre_rol = resolver_nombre_rol(rol_solicitado) if rol_solicitado else None
    activo = obtener_argumento_booleano(request.args, "activo")

    servicio = ServicioUsuarios()
    return respuesta_exitosa(servicio.listar_usuarios(rol=nombre_rol, activo=activo))


@blueprint.post("/usuarios")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_usuario():
    """Crea una cuenta con rol explícito."""

    datos = obtener_cuerpo_json()
    servicio = ServicioUsuarios()
    usuario = servicio.crear_usuario(datos)
    return respuesta_creada(
        presentar_usuario(usuario), "Usuario creado correctamente."
    )


@blueprint.get("/usuarios/<int:usuario_id>")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def obtener_usuario(usuario_id: int):
    """Obtiene una cuenta por identificador."""

    servicio = ServicioUsuarios()
    return respuesta_exitosa(servicio.obtener_usuario(usuario_id))


@blueprint.patch("/usuarios/<int:usuario_id>/estado")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def cambiar_estado_usuario(usuario_id: int):
    """Activa o desactiva una cuenta."""

    datos = obtener_cuerpo_json()
    activo = obtener_booleano_opcional(datos, "activo")
    if activo is None:
        raise ErrorValidacion("El campo 'activo' es obligatorio y debe ser booleano.")

    servicio = ServicioUsuarios()
    usuario_actual = obtener_usuario_autenticado()
    return respuesta_exitosa(
        servicio.cambiar_estado_usuario(usuario_id, activo, usuario_actual),
        "Estado de la cuenta actualizado.",
    )


@blueprint.get("/estudiantes")
@requiere_roles(*ROLES_CONSULTA_ACADEMICA)
def listar_estudiantes():
    """Lista estudiantes, opcionalmente filtrados por curso."""

    curso_id = obtener_argumento_entero(request.args, "curso_id", valor_minimo=1)
    servicio = ServicioUsuarios()
    return respuesta_exitosa(servicio.listar_estudiantes(curso_id=curso_id))


@blueprint.post("/estudiantes")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_estudiante():
    """Crea la cuenta y el perfil de un estudiante."""

    datos = obtener_cuerpo_json()
    servicio = ServicioUsuarios()
    estudiante = servicio.crear_estudiante(datos)
    return respuesta_creada(
        presentar_estudiante(estudiante), "Estudiante creado correctamente."
    )


@blueprint.get("/docentes")
@requiere_roles(*ROLES_CONSULTA_ACADEMICA)
def listar_docentes():
    """Lista todos los docentes."""

    servicio = ServicioUsuarios()
    return respuesta_exitosa(servicio.listar_docentes())


@blueprint.post("/docentes")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_docente():
    """Crea la cuenta y el perfil de un docente."""

    datos = obtener_cuerpo_json()
    servicio = ServicioUsuarios()
    docente = servicio.crear_docente(datos)
    return respuesta_creada(
        presentar_docente(docente), "Docente creado correctamente."
    )
