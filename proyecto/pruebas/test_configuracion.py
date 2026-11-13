"""Pruebas de configuración institucional."""

from pruebas.conftest import encabezado_autorizacion


def test_admin_consulta_y_actualiza_parametros(aplicacion, token_admin, token_preceptor):
    cliente = aplicacion.test_client()

    respuesta_inicial = cliente.get(
        "/api/v1/configuracion",
        headers=encabezado_autorizacion(token_admin),
    )
    assert respuesta_inicial.status_code == 200
    assert (
        respuesta_inicial.get_json()["datos"]["valores_aplicados"][
            "umbral_regularidad_porcentaje"
        ]
        == 75
    )

    respuesta_actualizacion = cliente.put(
        "/api/v1/configuracion/umbral_regularidad_porcentaje",
        headers=encabezado_autorizacion(token_admin),
        json={"valor": "80"},
    )
    assert respuesta_actualizacion.status_code == 200
    assert respuesta_actualizacion.get_json()["datos"]["valor"] == "80"

    respuesta_final = cliente.get(
        "/api/v1/configuracion",
        headers=encabezado_autorizacion(token_admin),
    )
    assert (
        respuesta_final.get_json()["datos"]["valores_aplicados"][
            "umbral_regularidad_porcentaje"
        ]
        == 80
    )

    respuesta_preceptor = cliente.put(
        "/api/v1/configuracion/umbral_regularidad_porcentaje",
        headers=encabezado_autorizacion(token_preceptor),
        json={"valor": "70"},
    )
    assert respuesta_preceptor.status_code == 403


def test_rechaza_estrategia_de_horas_inexistente(aplicacion, token_admin):
    cliente = aplicacion.test_client()

    respuesta = cliente.put(
        "/api/v1/configuracion/estrategia_calculo_horas",
        headers=encabezado_autorizacion(token_admin),
        json={"valor": "estrategia_inexistente"},
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]["codigo"] == "datos_invalidos"
