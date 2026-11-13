"""Modelos de datos del backend.

La importación centralizada permite que `base_de_datos.create_all()` detecte
todas las tablas al inicializar el esquema y resuelve las referencias entre
modelos declaradas como cadenas.
"""

from .alerta import AlertaAsistencia
from .asistencia_docente import FirmaAsistencia, GrillaHorariaInstitucional, IncidenciaHoraria
from .asistencia_estudiantil import RegistroAsistenciaEstudiantil
from .enumeraciones import (
    EstadoAsistencia,
    EstadoInscripcion,
    NivelAlerta,
    NombreRol,
    TipoAlerta,
    TipoFirma,
    TipoIncidencia,
)
from .estructura_academica import (
    AsignacionDocenteMateria,
    Curso,
    InscripcionEstudianteCurso,
    Materia,
    PeriodoAcademico,
)
from .parametro_institucional import ParametroInstitucional
from .rol import Rol
from .usuario import Docente, Estudiante, Usuario

__all__ = [
    "AlertaAsistencia",
    "AsignacionDocenteMateria",
    "Curso",
    "Docente",
    "EstadoAsistencia",
    "EstadoInscripcion",
    "Estudiante",
    "FirmaAsistencia",
    "GrillaHorariaInstitucional",
    "IncidenciaHoraria",
    "InscripcionEstudianteCurso",
    "Materia",
    "NivelAlerta",
    "NombreRol",
    "ParametroInstitucional",
    "PeriodoAcademico",
    "RegistroAsistenciaEstudiantil",
    "Rol",
    "TipoAlerta",
    "TipoFirma",
    "TipoIncidencia",
    "Usuario",
]
