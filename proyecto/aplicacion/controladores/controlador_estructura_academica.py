"""Endpoints de estructura académica."""

from flask import Blueprint, request

from ..modelos.enumeraciones import NombreRol
from ..seguridad import requiere_autenticacion, requiere_roles
from ..servicios.servicio_estructura_academica import ServicioEstructuraAcademica
from ..utilidades import respuesta_creada, respuesta_exitosa
from ..utilidades.validadores import (
    obtener_argumento_entero,
    obtener_cuerpo_json,
)

blueprint = Blueprint("estructura_academica", __name__)


# ----------------------------------------------------------------------
# Cursos
# ----------------------------------------------------------------------
@blueprint.get("/cursos")
@requiere_autenticacion
def listar_cursos():
    """Lista cursos, opcionalmente filtrados por año lectivo."""

    anio_lectivo = obtener_argumento_entero(
        request.args, "anio_lectivo", valor_minimo=2000
    )
    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(servicio.listar_cursos(anio_lectivo=anio_lectivo))


@blueprint.post("/cursos")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_curso():
    """Crea un curso."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(servicio.crear_curso(datos), "Curso creado correctamente.")


# ----------------------------------------------------------------------
# Materias
# ----------------------------------------------------------------------
@blueprint.get("/materias")
@requiere_autenticacion
def listar_materias():
    """Lista todas las materias."""

    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(servicio.listar_materias())


@blueprint.post("/materias")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_materia():
    """Crea una materia."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(
        servicio.crear_materia(datos), "Materia creada correctamente."
    )


# ----------------------------------------------------------------------
# Períodos académicos
# ----------------------------------------------------------------------
@blueprint.get("/periodos-academicos")
@requiere_autenticacion
def listar_periodos_academicos():
    """Lista períodos académicos."""

    anio_lectivo = obtener_argumento_entero(
        request.args, "anio_lectivo", valor_minimo=2000
    )
    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(servicio.listar_periodos(anio_lectivo=anio_lectivo))


@blueprint.post("/periodos-academicos")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_periodo_academico():
    """Crea un período académico."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(
        servicio.crear_periodo(datos), "Período académico creado correctamente."
    )


# ----------------------------------------------------------------------
# Matrículas
# ----------------------------------------------------------------------
@blueprint.get("/inscripciones")
@requiere_roles(
    NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR, NombreRol.DOCENTE
)
def listar_inscripciones():
    """Lista matrículas con filtros opcionales."""

    curso_id = obtener_argumento_entero(request.args, "curso_id", valor_minimo=1)
    estudiante_id = obtener_argumento_entero(
        request.args, "estudiante_id", valor_minimo=1
    )
    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(
        servicio.listar_inscripciones(
            curso_id=curso_id, estudiante_id=estudiante_id
        )
    )


@blueprint.post("/inscripciones")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR)
def crear_inscripcion():
    """Matricula un estudiante en un curso."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(
        servicio.crear_inscripcion(datos), "Inscripción registrada correctamente."
    )


# ----------------------------------------------------------------------
# Asignaciones docentes
# ----------------------------------------------------------------------
@blueprint.get("/asignaciones-docentes")
@requiere_roles(
    NombreRol.ADMINISTRATIVO_DIRECTIVO, NombreRol.PRECEPTOR, NombreRol.DOCENTE
)
def listar_asignaciones_docentes():
    """Lista asignaciones docente-materia-curso."""

    docente_id = obtener_argumento_entero(request.args, "docente_id", valor_minimo=1)
    curso_id = obtener_argumento_entero(request.args, "curso_id", valor_minimo=1)
    materia_id = obtener_argumento_entero(request.args, "materia_id", valor_minimo=1)

    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(
        servicio.listar_asignaciones(
            docente_id=docente_id, curso_id=curso_id, materia_id=materia_id
        )
    )


@blueprint.post("/asignaciones-docentes")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_asignacion_docente():
    """Asigna un docente a una materia de un curso."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(
        servicio.crear_asignacion(datos),
        "Asignación docente registrada correctamente.",
    )


# ----------------------------------------------------------------------
# Grilla horaria
# ----------------------------------------------------------------------
@blueprint.get("/grillas-horarias")
@requiere_autenticacion
def listar_grillas_horarias():
    """Lista bloques de la grilla horaria institucional."""

    docente_id = obtener_argumento_entero(request.args, "docente_id", valor_minimo=1)
    curso_id = obtener_argumento_entero(request.args, "curso_id", valor_minimo=1)
    materia_id = obtener_argumento_entero(request.args, "materia_id", valor_minimo=1)
    anio_lectivo = obtener_argumento_entero(
        request.args, "anio_lectivo", valor_minimo=2000
    )
    dia_semana = obtener_argumento_entero(
        request.args, "dia_semana", valor_minimo=1
    )

    servicio = ServicioEstructuraAcademica()
    return respuesta_exitosa(
        servicio.listar_grillas_horarias(
            docente_id=docente_id,
            curso_id=curso_id,
            materia_id=materia_id,
            anio_lectivo=anio_lectivo,
            dia_semana=dia_semana,
        )
    )


@blueprint.post("/grillas-horarias")
@requiere_roles(NombreRol.ADMINISTRATIVO_DIRECTIVO)
def crear_grilla_horaria():
    """Crea un bloque de la grilla horaria."""

    datos = obtener_cuerpo_json()
    servicio = ServicioEstructuraAcademica()
    return respuesta_creada(
        servicio.crear_grilla_horaria(datos),
        "Bloque horario creado correctamente.",
    )
