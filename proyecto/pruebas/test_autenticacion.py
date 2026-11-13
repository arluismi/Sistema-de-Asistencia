"""Pruebas de autenticación, salud y control de acceso."""

from pruebas.conftest import encabezado_autorizacion


def test_salud_responde_operativo(aplicacion):
    cliente = aplicacion.test_client()
    respuesta = cliente.get("/api/v1/salud")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["estado"] == "operativo"


def test_inicio_de_sesion_exitoso(aplicacion):
    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/autenticacion/iniciar-sesion",
        json={"nombre_usuario": "admin.pruebas", "contrasena": "Admin123!"},
    )

    assert respuesta.status_code == 200
    datos = respuesta.get_json()["datos"]
    assert datos["tipo_token"] == "Bearer"
    assert datos["usuario"]["rol"] == "Admin/Directivo"
    assert datos["token_acceso"]


def test_inicio_de_sesion_con_contrasena_incorrecta(aplicacion):
    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/autenticacion/iniciar-sesion",
        json={"nombre_usuario": "admin.pruebas", "contrasena": "incorrecta"},
    )

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "no_autenticado"


def test_perfil_requiere_token(aplicacion):
    cliente = aplicacion.test_client()

    respuesta = cliente.get("/api/v1/autenticacion/perfil")

    assert respuesta.status_code == 401


def test_perfil_devuelve_usuario_autenticado(aplicacion, token_admin):
    cliente = aplicacion.test_client()
    respuesta = cliente.get(
        "/api/v1/autenticacion/perfil",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["nombre_usuario"] == "admin.pruebas"


def test_alumno_no_puede_listar_usuarios(aplicacion, token_alumno):
    cliente = aplicacion.test_client()
    respuesta = cliente.get(
        "/api/v1/usuarios", headers=encabezado_autorizacion(token_alumno)
    )

    assert respuesta.status_code == 403
    assert respuesta.get_json()["error"]["codigo"] == "acceso_prohibido"


def test_solo_direccion_puede_crear_cursos(aplicacion, token_preceptor):
    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/cursos",
        headers=encabezado_autorizacion(token_preceptor),
        json={
            "nombre": "Curso no autorizado",
            "division": "B",
            "anio_lectivo": 2026,
            "turno": "Tarde",
        },
    )

    assert respuesta.status_code == 403
