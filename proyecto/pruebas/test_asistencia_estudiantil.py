"""Pruebas de asistencia estudiantil, resúmenes y alertas."""

from pruebas.conftest import encabezado_autorizacion


def _registrar_asistencia(cliente, token, datos, fecha, estados_por_estudiante):
    """Envía una carga diaria de asistencia y devuelve la respuesta HTTP."""

    return cliente.post(
        "/api/v1/asistencias-estudiantes",
        headers=encabezado_autorizacion(token),
        json={
            "curso_id": datos["curso_id"],
            "materia_id": datos["matematica_id"],
            "fecha": fecha,
            "registros": [
                {"estudiante_id": estudiante_id, "estado": estado}
                for estudiante_id, estado in estados_por_estudiante.items()
            ],
        },
    )


def test_registra_y_actualiza_asistencia_diaria(aplicacion, datos, token_preceptor):
    cliente = aplicacion.test_client()

    respuesta = _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Presente",
            datos["alumno_dos_id"]: "Ausente",
        },
    )

    assert respuesta.status_code == 201
    resultado = respuesta.get_json()["datos"]
    assert resultado["creados"] == 2
    assert resultado["actualizados"] == 0

    respuesta_actualizacion = _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Tarde",
            datos["alumno_dos_id"]: "Justificado",
        },
    )

    assert respuesta_actualizacion.status_code == 201
    resultado_actualizacion = respuesta_actualizacion.get_json()["datos"]
    assert resultado_actualizacion["creados"] == 0
    assert resultado_actualizacion["actualizados"] == 2


def test_resumen_por_curso_calcula_porcentajes(
    aplicacion, datos, token_preceptor
):
    cliente = aplicacion.test_client()
    _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Presente",
            datos["alumno_dos_id"]: "Ausente",
        },
    )
    _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-03",
        {
            datos["alumno_uno_id"]: "Tarde",
            datos["alumno_dos_id"]: "Presente",
        },
    )

    respuesta = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen?curso_id={datos['curso_id']}"
        f"&periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_preceptor),
    )

    assert respuesta.status_code == 200
    resumen = respuesta.get_json()["datos"]
    assert resumen["alcance"] == "curso"
    assert resumen["resumen_general"]["total_registros"] == 4
    assert resumen["resumen_general"]["presentes"] == 2
    assert resumen["resumen_general"]["ausentes"] == 1
    assert resumen["resumen_general"]["tardes"] == 1

    filas_por_estudiante = {
        fila["estudiante"]["id"]: fila["resumen"]
        for fila in resumen["estudiantes"]
    }
    assert filas_por_estudiante[datos["alumno_uno_id"]]["porcentaje_asistencia"] == 100.0
    assert filas_por_estudiante[datos["alumno_dos_id"]]["porcentaje_asistencia"] == 50.0
    assert (
        filas_por_estudiante[datos["alumno_dos_id"]]["estado_regularidad"]
        == "En riesgo"
    )


def test_resumen_por_estudiante_incluye_detalle_por_materia(
    aplicacion, datos, token_preceptor
):
    cliente = aplicacion.test_client()
    _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Presente",
            datos["alumno_dos_id"]: "Presente",
        },
    )

    respuesta = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen"
        f"?estudiante_id={datos['alumno_uno_id']}"
        f"&periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_preceptor),
    )

    assert respuesta.status_code == 200
    resumen = respuesta.get_json()["datos"]
    assert resumen["alcance"] == "estudiante"
    assert resumen["resumen"]["porcentaje_asistencia"] == 100.0
    assert len(resumen["detalle_por_materia"]) == 1
    assert (
        resumen["detalle_por_materia"][0]["materia"]["id"]
        == datos["matematica_id"]
    )


def test_estrategia_estricta_no_computa_justificados(
    aplicacion, datos, token_preceptor
):
    cliente = aplicacion.test_client()
    _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Justificado",
            datos["alumno_dos_id"]: "Presente",
        },
    )

    respuesta_institucional = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen"
        f"?estudiante_id={datos['alumno_uno_id']}&estrategia=institucional",
        headers=encabezado_autorizacion(token_preceptor),
    )
    respuesta_estricta = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen"
        f"?estudiante_id={datos['alumno_uno_id']}&estrategia=estricta",
        headers=encabezado_autorizacion(token_preceptor),
    )

    assert respuesta_institucional.status_code == 200
    assert respuesta_estricta.status_code == 200
    assert (
        respuesta_institucional.get_json()["datos"]["resumen"][
            "porcentaje_asistencia"
        ]
        == 100.0
    )
    assert (
        respuesta_estricta.get_json()["datos"]["resumen"]["porcentaje_asistencia"]
        == 0.0
    )


def test_genera_alertas_por_inasistencias_consecutivas(
    aplicacion, datos, token_preceptor
):
    cliente = aplicacion.test_client()
    for fecha in ("2026-03-02", "2026-03-03", "2026-03-04"):
        _registrar_asistencia(
            cliente,
            token_preceptor,
            datos,
            fecha,
            {
                datos["alumno_uno_id"]: "Presente",
                datos["alumno_dos_id"]: "Ausente",
            },
        )

    respuesta = cliente.get(
        "/api/v1/alertas",
        headers=encabezado_autorizacion(token_preceptor),
    )

    assert respuesta.status_code == 200
    alertas = respuesta.get_json()["datos"]
    tipos = [alerta["tipo"] for alerta in alertas]
    assert "Inasistencias consecutivas" in tipos
    assert "Regularidad en riesgo" in tipos
    assert tipos.count("Regularidad en riesgo") == 1
    assert tipos.count("Inasistencias consecutivas") == 1

    alerta = next(
        alerta
        for alerta in alertas
        if alerta["tipo"] == "Inasistencias consecutivas"
    )
    assert alerta["estudiante"]["id"] == datos["alumno_dos_id"]
    assert alerta["activa"] is True
    assert alerta["leida"] is False

    respuesta_lectura = cliente.patch(
        f"/api/v1/alertas/{alerta['id']}/marcar-leida",
        headers=encabezado_autorizacion(token_preceptor),
    )
    assert respuesta_lectura.status_code == 200
    assert respuesta_lectura.get_json()["datos"]["leida"] is True


def test_rechaza_estado_de_asistencia_invalido(aplicacion, datos, token_preceptor):
    cliente = aplicacion.test_client()
    respuesta = _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {datos["alumno_uno_id"]: "Desaprobado"},
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]["codigo"] == "datos_invalidos"


def test_rechaza_estudiante_no_matriculado(aplicacion, datos, token_preceptor):
    cliente = aplicacion.test_client()
    respuesta = _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {999999: "Presente"},
    )

    assert respuesta.status_code == 400
    assert "no está matriculado" in respuesta.get_json()["error"]["mensaje"]


def test_alumno_solo_puede_consultar_su_asistencia(
    aplicacion, datos, token_preceptor, token_alumno
):
    cliente = aplicacion.test_client()
    _registrar_asistencia(
        cliente,
        token_preceptor,
        datos,
        "2026-03-02",
        {
            datos["alumno_uno_id"]: "Presente",
            datos["alumno_dos_id"]: "Presente",
        },
    )

    respuesta_propia = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen"
        f"?estudiante_id={datos['alumno_uno_id']}",
        headers=encabezado_autorizacion(token_alumno),
    )
    respuesta_ajena = cliente.get(
        f"/api/v1/asistencias-estudiantes/resumen"
        f"?estudiante_id={datos['alumno_dos_id']}",
        headers=encabezado_autorizacion(token_alumno),
    )
    respuesta_carga = _registrar_asistencia(
        cliente,
        token_alumno,
        datos,
        "2026-03-03",
        {datos["alumno_uno_id"]: "Presente"},
    )
    respuesta_listado = cliente.get(
        "/api/v1/asistencias-estudiantes",
        headers=encabezado_autorizacion(token_alumno),
    )

    assert respuesta_propia.status_code == 200
    assert respuesta_ajena.status_code == 403
    assert respuesta_carga.status_code == 403
    assert respuesta_listado.status_code == 200
    estudiantes_listados = {
        registro["estudiante"]["id"]
        for registro in respuesta_listado.get_json()["datos"]
    }
    assert estudiantes_listados == {datos["alumno_uno_id"]}
