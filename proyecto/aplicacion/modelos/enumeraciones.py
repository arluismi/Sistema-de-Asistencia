"""Enumeraciones compartidas por modelos, servicios y validadores.

Se utilizan enums de texto (`str, Enum`) para que la base de datos almacene
valores legibles y estables, y para que la API exponga exactamente los mismos
textos que valida el dominio.
"""

from enum import Enum


class NombreRol(str, Enum):
    """Roles institucionales admitidos, ordenados de mayor a menor jerarquía."""

    ADMINISTRATIVO_DIRECTIVO = "Admin/Directivo"
    PRECEPTOR = "Preceptor"
    DOCENTE = "Docente"
    ALUMNO = "Alumno"


class EstadoAsistencia(str, Enum):
    """Estados permitidos para el registro de asistencia estudiantil."""

    PRESENTE = "Presente"
    AUSENTE = "Ausente"
    JUSTIFICADO = "Justificado"
    TARDE = "Tarde"


class EstadoInscripcion(str, Enum):
    """Situación de la matrícula de un estudiante en un curso."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class TipoFirma(str, Enum):
    """Tipos de marca de asistencia del personal docente."""

    INGRESO = "Ingreso"
    EGRESO = "Egreso"


class TipoIncidencia(str, Enum):
    """Clasificación de las incidencias horarias docentes."""

    TARDANZA = "Tardanza"
    SALIDA_ANTICIPADA = "Salida anticipada"
    AUSENCIA = "Ausencia"
    LICENCIA = "Licencia"


class TipoAlerta(str, Enum):
    """Motivos de alerta generados por el observador de asistencia."""

    INASISTENCIAS_CONSECUTIVAS = "Inasistencias consecutivas"
    REGULARIDAD_EN_RIESGO = "Regularidad en riesgo"


class NivelAlerta(str, Enum):
    """Severidad de una alerta del tablero de control."""

    ALTA = "Alta"
    MEDIA = "Media"
