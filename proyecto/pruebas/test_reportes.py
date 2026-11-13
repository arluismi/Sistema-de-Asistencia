"""Pruebas de generación de reportes PDF y Excel."""

from pruebas.conftest import encabezado_autorizacion


def _preparar_asistencia(aplicacion, datos, token_preceptor):
    """Registra una jornada de asistencia para alimentar los reportes."""

    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/asistencias-estudiantes",
        headers=encabezado_autorizacion(token_preceptor),
        json={
            "curso_id": datos["curso_id"],
            "materia_id": datos["matematica_id"],
            "fecha": "2026-03-02",
            "registros": [
                {"estudiante_id": datos["alumno_uno_id"], "estado": "Presente"},
                {"estudiante_id": datos["alumno_dos_id"], "estado": "Ausente"},
            ],
        },
    )
    assert respuesta.status_code == 201


def test_reporte_de_asistencia_en_pdf(
    aplicacion, datos, token_preceptor, token_admin
):
    _preparar_asistencia(aplicacion, datos, token_preceptor)
    cliente = aplicacion.test_client()

    respuesta = cliente.get(
        f"/api/v1/reportes/asistencia-estudiantes.pdf"
        f"?curso_id={datos['curso_id']}&periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 200
    assert respuesta.content_type.startswith("application/pdf")
    assert respuesta.data.startswith(b"%PDF")
    assert "attachment" in respuesta.headers["Content-Disposition"]


def test_reporte_de_asistencia_en_excel(
    aplicacion, datos, token_preceptor, token_admin
):
    _preparar_asistencia(aplicacion, datos, token_preceptor)
    cliente = aplicacion.test_client()

    respuesta = cliente.get(
        f"/api/v1/reportes/asistencia-estudiantes.xlsx"
        f"?curso_id={datos['curso_id']}&periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 200
    assert "spreadsheetml" in respuesta.content_type
    assert respuesta.data.startswith(b"PK")


def test_reporte_de_horas_docentes_en_pdf(
    aplicacion, datos, token_admin
):
    cliente = aplicacion.test_client()

    respuesta = cliente.get(
        f"/api/v1/reportes/horas-docentes.pdf"
        f"?periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 200
    assert respuesta.data.startswith(b"%PDF")


def test_alumno_y_docente_no_pueden_descargar_reportes_institucionales(
    aplicacion, datos, token_alumno, token_docente
):
    cliente = aplicacion.test_client()
    ruta = (
        f"/api/v1/reportes/asistencia-estudiantes.pdf"
        f"?curso_id={datos['curso_id']}&periodo_id={datos['periodo_id']}"
    )

    for token in (token_alumno, token_docente):
        respuesta = cliente.get(ruta, headers=encabezado_autorizacion(token))
        assert respuesta.status_code == 403


def test_rechaza_formato_de_reporte_no_soportado(
    aplicacion, datos, token_admin
):
    cliente = aplicacion.test_client()

    respuesta = cliente.get(
        f"/api/v1/reportes/asistencia-estudiantes.docx"
        f"?curso_id={datos['curso_id']}&periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]["codigo"] == "datos_invalidos"
