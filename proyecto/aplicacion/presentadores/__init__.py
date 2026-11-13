"""Funciones de serialización de entidades para las respuestas HTTP.

Mantener la serialización fuera de los modelos evita mezclar la representación
de la API con el esquema de persistencia.
"""

from datetime import date, datetime, time


def _fecha_a_texto(valor: date | None) -> str | None:
    """Convierte una fecha a formato ISO 8601."""

    return valor.isoformat() if valor is not None else None


def _fecha_hora_a_texto(valor: datetime | None) -> str | None:
    """Convierte una fecha y hora a formato ISO 8601 sin microsegundos."""

    return valor.isoformat(timespec="seconds") if valor is not None else None


def _hora_a_texto(valor: time | None) -> str | None:
    """Convierte una hora a formato HH:MM para las respuestas y grillas."""

    return valor.strftime("%H:%M") if valor is not None else None


def _valor_enum(valor):
    """Extrae el texto de un enum o devuelve el valor original."""

    return valor.value if hasattr(valor, "value") else valor


def presentar_rol(rol) -> dict:
    """Serializa un rol institucional."""

    return {
        "id": rol.id,
        "nombre": _valor_enum(rol.nombre),
        "descripcion": rol.descripcion,
        "nivel_jerarquico": rol.nivel_jerarquico,
    }


def presentar_usuario(usuario) -> dict:
    """Serializa una cuenta de usuario sin exponer su hash de contraseña."""

    return {
        "id": usuario.id,
        "nombre_usuario": usuario.nombre_usuario,
        "correo_electronico": usuario.correo_electronico,
        "rol": _valor_enum(usuario.rol.nombre) if usuario.rol is not None else None,
        "activo": usuario.activo,
        "creado_en": _fecha_hora_a_texto(usuario.creado_en),
    }


def presentar_estudiante(estudiante) -> dict:
    """Serializa un estudiante y los datos mínimos de su cuenta."""

    return {
        "id": estudiante.id,
        "legajo": estudiante.legajo,
        "nombres": estudiante.nombres,
        "apellidos": estudiante.apellidos,
        "nombre_completo": estudiante.nombre_completo,
        "fecha_nacimiento": _fecha_a_texto(estudiante.fecha_nacimiento),
        "usuario": presentar_usuario(estudiante.usuario) if estudiante.usuario else None,
    }


def presentar_docente(docente) -> dict:
    """Serializa un docente y los datos mínimos de su cuenta."""

    return {
        "id": docente.id,
        "legajo": docente.legajo,
        "nombres": docente.nombres,
        "apellidos": docente.apellidos,
        "nombre_completo": docente.nombre_completo,
        "titulo_habilitante": docente.titulo_habilitante,
        "usuario": presentar_usuario(docente.usuario) if docente.usuario else None,
    }


def presentar_curso(curso) -> dict:
    """Serializa un curso."""

    return {
        "id": curso.id,
        "nombre": curso.nombre,
        "division": curso.division,
        "anio_lectivo": curso.anio_lectivo,
        "turno": curso.turno,
        "nombre_completo": curso.nombre_completo,
    }


def presentar_materia(materia) -> dict:
    """Serializa una materia."""

    return {
        "id": materia.id,
        "nombre": materia.nombre,
        "codigo": materia.codigo,
    }


def presentar_periodo(periodo) -> dict | None:
    """Serializa un período académico; acepta `None`."""

    if periodo is None:
        return None
    return {
        "id": periodo.id,
        "nombre": periodo.nombre,
        "fecha_inicio": _fecha_a_texto(periodo.fecha_inicio),
        "fecha_fin": _fecha_a_texto(periodo.fecha_fin),
        "anio_lectivo": periodo.anio_lectivo,
    }


def presentar_inscripcion(inscripcion) -> dict:
    """Serializa una matrícula de estudiante en curso."""

    return {
        "id": inscripcion.id,
        "estudiante": presentar_estudiante(inscripcion.estudiante)
        if inscripcion.estudiante
        else None,
        "curso": presentar_curso(inscripcion.curso) if inscripcion.curso else None,
        "fecha_inscripcion": _fecha_a_texto(inscripcion.fecha_inscripcion),
        "estado": _valor_enum(inscripcion.estado),
    }


def presentar_asignacion(asignacion) -> dict:
    """Serializa una asignación docente-materia-curso."""

    return {
        "id": asignacion.id,
        "docente": presentar_docente(asignacion.docente)
        if asignacion.docente
        else None,
        "curso": presentar_curso(asignacion.curso) if asignacion.curso else None,
        "materia": presentar_materia(asignacion.materia)
        if asignacion.materia
        else None,
    }


def presentar_grilla_horaria(grilla) -> dict:
    """Serializa un bloque de la grilla horaria institucional."""

    return {
        "id": grilla.id,
        "curso": presentar_curso(grilla.curso) if grilla.curso else None,
        "materia": presentar_materia(grilla.materia) if grilla.materia else None,
        "docente": presentar_docente(grilla.docente) if grilla.docente else None,
        "dia_semana": grilla.dia_semana,
        "hora_inicio": _hora_a_texto(grilla.hora_inicio),
        "hora_fin": _hora_a_texto(grilla.hora_fin),
        "aula": grilla.aula,
    }


def presentar_registro_asistencia(registro) -> dict:
    """Serializa un registro de asistencia estudiantil."""

    return {
        "id": registro.id,
        "estudiante": {
            "id": registro.estudiante_id,
            "legajo": registro.estudiante.legajo if registro.estudiante else None,
            "nombre_completo": registro.estudiante.nombre_completo
            if registro.estudiante
            else None,
        },
        "curso": presentar_curso(registro.curso) if registro.curso else None,
        "materia": presentar_materia(registro.materia) if registro.materia else None,
        "fecha": _fecha_a_texto(registro.fecha),
        "estado": _valor_enum(registro.estado),
        "observacion": registro.observacion,
        "registrado_por_usuario_id": registro.registrado_por_usuario_id,
    }


def presentar_firma_asistencia(firma) -> dict:
    """Serializa una firma de ingreso o egreso docente."""

    return {
        "id": firma.id,
        "docente": presentar_docente(firma.docente) if firma.docente else None,
        "grilla_horaria": presentar_grilla_horaria(firma.grilla_horaria)
        if firma.grilla_horaria
        else None,
        "tipo_firma": _valor_enum(firma.tipo_firma),
        "fecha": _fecha_a_texto(firma.fecha),
        "marca_temporal": _fecha_hora_a_texto(firma.marca_temporal),
        "observacion": firma.observacion,
    }


def presentar_incidencia(incidencia) -> dict:
    """Serializa una incidencia horaria docente."""

    return {
        "id": incidencia.id,
        "docente": presentar_docente(incidencia.docente)
        if incidencia.docente
        else None,
        "grilla_horaria_id": incidencia.grilla_horaria_id,
        "firma_asistencia_id": incidencia.firma_asistencia_id,
        "tipo": _valor_enum(incidencia.tipo),
        "fecha": _fecha_a_texto(incidencia.fecha),
        "minutos_desviacion": incidencia.minutos_desviacion,
        "descripcion": incidencia.descripcion,
        "generada_automaticamente": incidencia.generada_automaticamente,
        "registrado_por_usuario_id": incidencia.registrado_por_usuario_id,
    }


def presentar_alerta(alerta) -> dict:
    """Serializa una alerta del tablero de control."""

    return {
        "id": alerta.id,
        "estudiante": presentar_estudiante(alerta.estudiante)
        if alerta.estudiante
        else None,
        "tipo": _valor_enum(alerta.tipo),
        "nivel": _valor_enum(alerta.nivel),
        "mensaje": alerta.mensaje,
        "porcentaje_asistencia": float(alerta.porcentaje_asistencia)
        if alerta.porcentaje_asistencia is not None
        else None,
        "fecha_generacion": _fecha_hora_a_texto(alerta.fecha_generacion),
        "activa": alerta.activa,
        "leida": alerta.leida,
    }


def presentar_parametro(parametro) -> dict:
    """Serializa un parámetro institucional."""

    return {
        "clave": parametro.clave,
        "valor": parametro.valor,
        "descripcion": parametro.descripcion,
    }
