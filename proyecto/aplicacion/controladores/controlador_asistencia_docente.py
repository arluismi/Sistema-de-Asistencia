"""Endpoints de asistencia y puntualidad docente."""

from flask import Blueprint, request

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import NombreRol, TipoIncidencia
from ..seguridad import obtener_usuario_autenticado, requiere_roles
from ..servicios.servicio_asistencia_docente import ServicioAsistenciaDocente
from ..utilidades import respuesta_creada, respuesta_exitosa
from ..utilidades.validadores import (
    obtener_argumento_cadena,
    obtener_argumento_entero,
    obtener_argumento_fecha,
    obtener_cuerpo_json,
)

blueprint = Blueprint("asistencia_docente", __name__)

ROLES_ASISTENCIA_DOCENTE = (
    NombreRol.ADMINISTRATIVO_DIRECTIVO,
    NombreRol.PRECEPTOR,
    NombreRol.DOCENTE,
)


def _interpretar_tipo_incidencia(valor: str | None):
    """Convierte el parámetro de tipo de incidencia en el enum correspondiente."""

    if valor is None:
        return None
    for tipo in TipoIncidencia:
        if tipo.value.lower() == valor.strip().lower():
            return tipo
    raise ErrorValidacion(
        "Tipo de incidencia inválido.",
        detalles={"tipos_permitidos": [tipo.value for tipo in TipoIncidencia]},
    )


@blueprint.post("/asistencias-docentes/firmas")
@requiere_roles(*ROLES_ASISTENCIA_DOCENTE)
def registrar_firma_asistencia():
    """Registra el ingreso o egreso de un docente con hora del servidor."""

    datos = obtener_cuerpo_json()
    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaDocente()
    resultado = servicio.registrar_firma(datos, usuario_actual)
    return respuesta_creada(resultado, "Firma registrada correctamente.")


@blueprint.get("/asistencias-docentes/firmas")
@requiere_roles(*ROLES_ASISTENCIA_DOCENTE)
def listar_firmas_asistencia():
    """Lista firmas de ingreso y egreso docentes."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaDocente()
    return respuesta_exitosa(
        servicio.listar_firmas(
            usuario_actual=usuario_actual,
            docente_id=obtener_argumento_entero(
                request.args, "docente_id", valor_minimo=1
            ),
            fecha_desde=obtener_argumento_fecha(request.args, "fecha_desde"),
            fecha_hasta=obtener_argumento_fecha(request.args, "fecha_hasta"),
        )
    )


@blueprint.get("/asistencias-docentes/incidencias")
@requiere_roles(*ROLES_ASISTENCIA_DOCENTE)
def listar_incidencias_horarias():
    """Lista tardanzas, salidas anticipadas y licencias docentes."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaDocente()
    return respuesta_exitosa(
        servicio.listar_incidencias(
            usuario_actual=usuario_actual,
            docente_id=obtener_argumento_entero(
                request.args, "docente_id", valor_minimo=1
            ),
            fecha_desde=obtener_argumento_fecha(request.args, "fecha_desde"),
            fecha_hasta=obtener_argumento_fecha(request.args, "fecha_hasta"),
            tipo=_interpretar_tipo_incidencia(
                obtener_argumento_cadena(request.args, "tipo")
            ),
        )
    )


@blueprint.post("/asistencias-docentes/licencias")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR)
def registrar_licencia_docente():
    """Registra una licencia docente."""

    datos = obtener_cuerpo_json()
    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaDocente()
    return respuesta_creada(
        servicio.registrar_licencia(datos, usuario_actual),
        "Licencia registrada correctamente.",
    )


@blueprint.get("/asistencias-docentes/balance-horas")
@requiere_roles(*ROLES_ASISTENCIA_DOCENTE)
def obtener_balance_horas_catedra():
    """Calcula el balance de horas cátedra laboradas en un período."""

    usuario_actual = obtener_usuario_autenticado()
    servicio = ServicioAsistenciaDocente()
    return respuesta_exitosa(
        servicio.obtener_balance(
            usuario_actual=usuario_actual,
            docente_id=obtener_argumento_entero(
                request.args, "docente_id", valor_minimo=1
            ),
            periodo_id=obtener_argumento_entero(
                request.args, "periodo_id", valor_minimo=1
            ),
            estrategia=obtener_argumento_cadena(request.args, "estrategia"),
        )
    )
