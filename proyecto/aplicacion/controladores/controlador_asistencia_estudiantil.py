"""Endpoints de asistencia estudiantil y alertas del tablero."""

from flask import Blueprint, request

from ..modelos.enumeraciones import NombreRol
from ..seguridad import obtener_usuario_autenticado, requiere_roles
from ..servicios.servicio_alertas import ServicioAlertas
from ..servicios.servicio_asistencia_estudiantil import ServicioAsistenciaEstudiantil
from ..utilidades import respuesta_creada, respuesta_exitosa
from ..utilidades.validadores import (
    obtener_argumento_booleano,
    obtener_argumento_cadena,
    obtener_argumento_entero,
    obtener_argumento_fecha,
    obtener_cuerpo_json,
)

blueprint = Blueprint("asistencia_estudiantil", __name__)

ROLES_ASISTENCIA = (
    NombreRol.ADMINISTRATIVO_DIRECTIVO,
    NombreRol.PRECEPTOR,
    NombreRol.DOCENTE,
)
ROLES_TODOS = ROLES_ASISTENCIA + (NombreRol.ALUMNO,)


def _obtener_filtros_de_registros() -> dict:
    """Interpreta los parámetros de consulta comunes a los listados."""

    return {
        "estudiante_id": obtener_argumento_entero(
            request.args, "estudiante_id", valor_minimo=1
        ),
        "curso_id": obtener_argumento_entero(
            request.args, "curso_id", valor_minimo=1
        ),
        "materia_id": obtener_argumento_entero(
            request.args, "materia_id", valor_minimo=1
        ),
        "fecha": obtener_argumento_fecha(request.args, "fecha"),
        "fecha_desde": obtener_argumento_fecha(request.args, "fecha_desde"),
        "fecha_hasta": obtener_argumento_fecha(request.args, "fecha_hasta"),
    }


@blueprint.post("/asistencias-estudiantes")
@requiere_roles(*ROLES_ASISTENCIA)
def registrar_carga_diaria():
    """Registra o actualiza la asistencia diaria de un curso y materia."""

    datos = obtener_cuerpo_json()
    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaEstudiantil()
    resultado = servicio.registrar_carga_diaria(datos, usuario_actual)
    return respuesta_creada(resultado, "Asistencia registrada correctamente.")


@blueprint.get("/asistencias-estudiantes")
@requiere_roles(*ROLES_TODOS)
def listar_registros_asistencia():
    """Lista registros de asistencia según los filtros y el rol del usuario."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaEstudiantil()
    registros = servicio.listar_registros(
        _obtener_filtros_de_registros(), usuario_actual
    )
    return respuesta_exitosa(registros)


@blueprint.get("/asistencias-estudiantes/resumen")
@requiere_roles(*ROLES_TODOS)
def obtener_resumen_asistencia():
    """Calcula porcentajes de asistencia por estudiante o por curso."""

    filtros = {
        "estudiante_id": obtener_argumento_entero(
            request.args, "estudiante_id", valor_minimo=1
        ),
        "curso_id": obtener_argumento_entero(
            request.args, "curso_id", valor_minimo=1
        ),
        "materia_id": obtener_argumento_entero(
            request.args, "materia_id", valor_minimo=1
        ),
        "periodo_id": obtener_argumento_entero(
            request.args, "periodo_id", valor_minimo=1
        ),
        "estrategia": obtener_argumento_cadena(request.args, "estrategia"),
    }

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaEstudiantil()
    return respuesta_exitosa(servicio.generar_resumen(filtros, usuario_actual))


@blueprint.get("/alertas")
@requiere_roles(*ROLES_ASISTENCIA)
def listar_alertas():
    """Lista las alertas generadas para el tablero de control."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAlertas()
    return respuesta_exitosa(
        servicio.listar_alertas(
            usuario_actual=usuario_actual,
            estudiante_id=obtener_argumento_entero(
                request.args, "estudiante_id", valor_minimo=1
            ),
            activa=obtener_argumento_booleano(request.args, "activa"),
            leida=obtener_argumento_booleano(request.args, "leida"),
        )
    )


@blueprint.patch("/alertas/<int:alerta_id>/marcar-leida")
@requiere_roles(*ROLES_ASISTENCIA)
def marcar_alerta_leida(alerta_id: int):
    """Marca una alerta como leída."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAlertas()
    return respuesta_exitosa(
        servicio.marcar_alerta_leida(alerta_id, usuario_actual),
        "Alerta marcada como leída.",
    )
