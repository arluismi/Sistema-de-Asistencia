"""Configuración común de la suite de pruebas."""

import pytest

from aplicacion import crear_aplicacion
from aplicacion.extenciones import base_de_datos
from aplicacion.servicios.inicializacion import inicializar_datos_base
from aplicacion.servicios.servicio_estructura_academica import (
    ServicioEstructuraAcademica,
)
from aplicacion.servicios.servicio_usuarios import ServicioUsuarios
from configuracion import ConfiguracionPruebas


def _sembrar_estructura_minima() -> dict:
    """Crea usuarios y estructura académica deterministas para las pruebas."""

    servicio_usuarios = ServicioUsuarios()
    servicio_estructura = ServicioEstructuraAcademica()

    usuario_admin = servicio_usuarios.crear_usuario(
        {
            "nombre_usuario": "admin.pruebas",
            "correo_electronico": "admin.pruebas@instituto.edu.ar",
            "contrasena": "Admin123!",
            "rol": "Admin/Directivo",
        }
    )
    servicio_usuarios.crear_usuario(
        {
            "nombre_usuario": "preceptor.pruebas",
            "correo_electronico": "preceptor.pruebas@instituto.edu.ar",
            "contrasena": "Preceptor123!",
            "rol": "Preceptor",
        }
    )
    docente = servicio_usuarios.crear_docente(
        {
            "nombre_usuario": "docente.pruebas",
            "correo_electronico": "docente.pruebas@instituto.edu.ar",
            "contrasena": "Docente123!",
            "legajo": "DOC-TEST-001",
            "nombres": "Ana",
            "apellidos": "Suárez",
        }
    )
    alumno_uno = servicio_usuarios.crear_estudiante(
        {
            "nombre_usuario": "alumno.uno",
            "correo_electronico": "alumno.uno@instituto.edu.ar",
            "contrasena": "Alumno123!",
            "legajo": "ALU-TEST-001",
            "nombres": "Juan",
            "apellidos": "Pérez",
        }
    )
    alumno_dos = servicio_usuarios.crear_estudiante(
        {
            "nombre_usuario": "alumno.dos",
            "correo_electronico": "alumno.dos@instituto.edu.ar",
            "contrasena": "Alumno123!",
            "legajo": "ALU-TEST-002",
            "nombres": "Lucía",
            "apellidos": "Gómez",
        }
    )

    curso = servicio_estructura.crear_curso(
        {
            "nombre": "Curso de Prueba",
            "division": "A",
            "anio_lectivo": 2026,
            "turno": "Mañana",
        }
    )
    matematica = servicio_estructura.crear_materia(
        {"nombre": "Matemática de Prueba", "codigo": "MAT-TEST"}
    )
    lengua = servicio_estructura.crear_materia(
        {"nombre": "Lengua de Prueba", "codigo": "LEN-TEST"}
    )
    periodo = servicio_estructura.crear_periodo(
        {
            "nombre": "Período de Prueba",
            "fecha_inicio": "2026-03-02",
            "fecha_fin": "2026-03-31",
            "anio_lectivo": 2026,
        }
    )

    for alumno in (alumno_uno, alumno_dos):
        servicio_estructura.crear_inscripcion(
            {
                "estudiante_id": alumno.id,
                "curso_id": curso["id"],
                "fecha_inscripcion": "2026-03-02",
            }
        )

    for materia in (matematica, lengua):
        servicio_estructura.crear_asignacion(
            {
                "docente_id": docente.id,
                "curso_id": curso["id"],
                "materia_id": materia["id"],
            }
        )

    grilla = servicio_estructura.crear_grilla_horaria(
        {
            "curso_id": curso["id"],
            "materia_id": matematica["id"],
            "docente_id": docente.id,
            "dia_semana": 1,
            "hora_inicio": "08:00",
            "hora_fin": "09:20",
            "aula": "Aula de Prueba",
        }
    )

    return {
        "usuario_admin_id": usuario_admin.id,
        "docente_id": docente.id,
        "estudiantes": [alumno_uno.id, alumno_dos.id],
        "alumno_uno_id": alumno_uno.id,
        "alumno_dos_id": alumno_dos.id,
        "curso_id": curso["id"],
        "matematica_id": matematica["id"],
        "lengua_id": lengua["id"],
        "periodo_id": periodo["id"],
        "grilla_id": grilla["id"],
    }


def _iniciar_sesion(aplicacion, nombre_usuario: str, contrasena: str) -> str:
    """Obtiene un token JWT usando el cliente de pruebas de Flask."""

    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/autenticacion/iniciar-sesion",
        json={"nombre_usuario": nombre_usuario, "contrasena": contrasena},
    )
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()["datos"]["token_acceso"]


@pytest.fixture()
def aplicacion(tmp_path):
    """Crea una aplicación aislada con base SQLite temporal y datos mínimos."""

    ruta_base_de_datos = tmp_path / "institucion_pruebas.db"
    aplicacion_de_prueba = crear_aplicacion(
        ConfiguracionPruebas,
        SQLALCHEMY_DATABASE_URI=(
            "sqlite:///" + ruta_base_de_datos.as_posix()
        ),
    )

    with aplicacion_de_prueba.app_context():
        base_de_datos.create_all()
        inicializar_datos_base()
        aplicacion_de_prueba.config["DATOS_DE_PRUEBA"] = _sembrar_estructura_minima()

    yield aplicacion_de_prueba

    with aplicacion_de_prueba.app_context():
        base_de_datos.session.remove()
        base_de_datos.drop_all()


@pytest.fixture()
def datos(aplicacion):
    """Datos identificadores creados por la fixture de aplicación."""

    return aplicacion.config["DATOS_DE_PRUEBA"]


@pytest.fixture()
def token_admin(aplicacion):
    """Token de un usuario Admin/Directivo."""

    return _iniciar_sesion(aplicacion, "admin.pruebas", "Admin123!")


@pytest.fixture()
def token_preceptor(aplicacion):
    """Token de un usuario Preceptor."""

    return _iniciar_sesion(aplicacion, "preceptor.pruebas", "Preceptor123!")


@pytest.fixture()
def token_docente(aplicacion):
    """Token de un usuario Docente."""

    return _iniciar_sesion(aplicacion, "docente.pruebas", "Docente123!")


@pytest.fixture()
def token_alumno(aplicacion):
    """Token de un usuario Alumno."""

    return _iniciar_sesion(aplicacion, "alumno.uno", "Alumno123!")


def encabezado_autorizacion(token: str) -> dict:
    """Construye el encabezado Bearer usado por los endpoints protegidos."""

    return {"Authorization": f"Bearer {token}"}
