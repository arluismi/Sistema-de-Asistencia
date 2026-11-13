"""Datos de demostración para probar la API sin un frontend.

La carga es idempotente: si la cuenta `direccion` ya existe, no se vuelve a
sembrar nada. Las contraseñas son de demostración y deben cambiarse en cualquier
entorno real.
"""

from datetime import date, timedelta

from ..modelos.enumeraciones import NombreRol
from ..repositorios import RepositorioUsuario
from ..utilidades.tiempo import obtener_fecha_servidor
from .inicializacion import inicializar_datos_base
from .servicio_asistencia_estudiantil import ServicioAsistenciaEstudiantil
from .servicio_estructura_academica import ServicioEstructuraAcademica
from .servicio_usuarios import ServicioUsuarios

CREDENCIALES_DEMOSTRACION = {
    "Admin/Directivo": {"nombre_usuario": "direccion", "contrasena": "Admin123!"},
    "Preceptor": {"nombre_usuario": "preceptoria", "contrasena": "Preceptor123!"},
    "Docente": {"nombre_usuario": "docente.martinez", "contrasena": "Docente123!"},
    "Alumno": {"nombre_usuario": "alumno.perez", "contrasena": "Alumno123!"},
}


def sembrar_datos_demostracion() -> dict:
    """Crea usuarios, estructura académica, grilla y asistencias de ejemplo."""

    inicializar_datos_base()

    repositorio_usuario = RepositorioUsuario()
    if repositorio_usuario.obtener_por_nombre_usuario("direccion") is not None:
        return {
            "sembrado": False,
            "mensaje": "Los datos de demostración ya estaban cargados.",
        }

    servicio_usuarios = ServicioUsuarios(repositorio_usuario)
    servicio_estructura = ServicioEstructuraAcademica()
    servicio_asistencia = ServicioAsistenciaEstudiantil()

    usuario_direccion = servicio_usuarios.crear_usuario(
        {
            "nombre_usuario": "direccion",
            "correo_electronico": "direccion@instituto.edu.ar",
            "contrasena": "Admin123!",
            "rol": NombreRol.ADMINISTRATIVO_DIRECTIVO.value,
        }
    )
    servicio_usuarios.crear_usuario(
        {
            "nombre_usuario": "preceptoria",
            "correo_electronico": "preceptoria@instituto.edu.ar",
            "contrasena": "Preceptor123!",
            "rol": NombreRol.PRECEPTOR.value,
        }
    )
    docente_martinez = servicio_usuarios.crear_docente(
        {
            "nombre_usuario": "docente.martinez",
            "correo_electronico": "docente.martinez@instituto.edu.ar",
            "contrasena": "Docente123!",
            "legajo": "DOC-2026-001",
            "nombres": "Laura",
            "apellidos": "Martínez",
            "titulo_habilitante": "Profesora de Matemática",
        }
    )
    alumno_perez = servicio_usuarios.crear_estudiante(
        {
            "nombre_usuario": "alumno.perez",
            "correo_electronico": "alumno.perez@instituto.edu.ar",
            "contrasena": "Alumno123!",
            "legajo": "ALU-2026-001",
            "nombres": "Juan",
            "apellidos": "Pérez",
            "fecha_nacimiento": "2010-04-15",
        }
    )
    alumno_gomez = servicio_usuarios.crear_estudiante(
        {
            "nombre_usuario": "alumno.gomez",
            "correo_electronico": "alumno.gomez@instituto.edu.ar",
            "contrasena": "Alumno123!",
            "legajo": "ALU-2026-002",
            "nombres": "Lucía",
            "apellidos": "Gómez",
            "fecha_nacimiento": "2010-09-02",
        }
    )
    alumno_rodriguez = servicio_usuarios.crear_estudiante(
        {
            "nombre_usuario": "alumno.rodriguez",
            "correo_electronico": "alumno.rodriguez@instituto.edu.ar",
            "contrasena": "Alumno123!",
            "legajo": "ALU-2026-003",
            "nombres": "Mateo",
            "apellidos": "Rodríguez",
            "fecha_nacimiento": "2010-01-20",
        }
    )

    anio_lectivo = obtener_fecha_servidor().year
    curso = servicio_estructura.crear_curso(
        {
            "nombre": "1° Año",
            "division": "A",
            "anio_lectivo": anio_lectivo,
            "turno": "Mañana",
        }
    )
    matematica = servicio_estructura.crear_materia(
        {"nombre": "Matemática", "codigo": "MAT-01"}
    )
    lengua = servicio_estructura.crear_materia(
        {"nombre": "Lengua", "codigo": "LEN-01"}
    )
    historia = servicio_estructura.crear_materia(
        {"nombre": "Historia", "codigo": "HIS-01"}
    )

    servicio_estructura.crear_periodo(
        {
            "nombre": "Primer Cuatrimestre",
            "fecha_inicio": date(anio_lectivo, 3, 1).isoformat(),
            "fecha_fin": date(anio_lectivo, 6, 30).isoformat(),
            "anio_lectivo": anio_lectivo,
        }
    )
    servicio_estructura.crear_periodo(
        {
            "nombre": "Segundo Cuatrimestre",
            "fecha_inicio": date(anio_lectivo, 8, 1).isoformat(),
            "fecha_fin": date(anio_lectivo, 11, 30).isoformat(),
            "anio_lectivo": anio_lectivo,
        }
    )

    for alumno in (alumno_perez, alumno_gomez, alumno_rodriguez):
        servicio_estructura.crear_inscripcion(
            {
                "estudiante_id": alumno.id,
                "curso_id": curso["id"],
                "fecha_inscripcion": date(anio_lectivo, 3, 1).isoformat(),
            }
        )

    for materia in (matematica, lengua, historia):
        servicio_estructura.crear_asignacion(
            {
                "docente_id": docente_martinez.id,
                "curso_id": curso["id"],
                "materia_id": materia["id"],
            }
        )

    servicio_estructura.crear_grilla_horaria(
        {
            "curso_id": curso["id"],
            "materia_id": matematica["id"],
            "docente_id": docente_martinez.id,
            "dia_semana": 1,
            "hora_inicio": "08:00",
            "hora_fin": "09:20",
            "aula": "Aula 1",
        }
    )
    servicio_estructura.crear_grilla_horaria(
        {
            "curso_id": curso["id"],
            "materia_id": lengua["id"],
            "docente_id": docente_martinez.id,
            "dia_semana": 3,
            "hora_inicio": "10:00",
            "hora_fin": "11:20",
            "aula": "Aula 1",
        }
    )
    servicio_estructura.crear_grilla_horaria(
        {
            "curso_id": curso["id"],
            "materia_id": historia["id"],
            "docente_id": docente_martinez.id,
            "dia_semana": 4,
            "hora_inicio": "08:00",
            "hora_fin": "09:20",
            "aula": "Aula 2",
        }
    )

    # Tres jornadas de ejemplo para que el tablero de alertas tenga información.
    fecha_referencia = obtener_fecha_servidor()
    for dias_atras in (3, 2, 1):
        fecha_carga = (fecha_referencia - timedelta(days=dias_atras)).isoformat()
        servicio_asistencia.registrar_carga_diaria(
            {
                "curso_id": curso["id"],
                "materia_id": matematica["id"],
                "fecha": fecha_carga,
                "registros": [
                    {"estudiante_id": alumno_perez.id, "estado": "Presente"},
                    {
                        "estudiante_id": alumno_gomez.id,
                        "estado": "Ausente",
                        "observacion": "Sin justificación presentada.",
                    },
                    {"estudiante_id": alumno_rodriguez.id, "estado": "Tarde"},
                ],
            },
            usuario_direccion,
        )

    return {
        "sembrado": True,
        "credenciales_demostracion": CREDENCIALES_DEMOSTRACION,
        "curso_id": curso["id"],
        "materias": {
            "matematica": matematica["id"],
            "lengua": lengua["id"],
            "historia": historia["id"],
        },
        "estudiantes": [
            alumno_perez.id,
            alumno_gomez.id,
            alumno_rodriguez.id,
        ],
        "docente_id": docente_martinez.id,
    }
