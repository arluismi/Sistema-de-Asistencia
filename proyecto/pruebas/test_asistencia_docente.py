"""Pruebas de firmas, incidencias y balance de horas docentes."""

from datetime import datetime

import pytest

from pruebas.conftest import encabezado_autorizacion


def _fijar_reloj(monkeypatch, momento: datetime) -> None:
    """Reemplaza la hora del servidor para obtener resultados deterministas."""

    monkeypatch.setattr(
        "aplicacion.servicios.servicio_asistencia_docente.obtener_marca_temporal_servidor",
        lambda: momento,
    )


def _registrar_firma(cliente, token, datos, tipo_firma, **extras):
    """Registra una firma docente y devuelve la respuesta HTTP."""

    cuerpo = {
        "tipo_firma": tipo_firma,
        "grilla_horaria_id": datos["grilla_id"],
    }
    cuerpo.update(extras)
    return cliente.post(
        "/api/v1/asistencias-docentes/firmas",
        headers=encabezado_autorizacion(token),
        json=cuerpo,
    )


def test_firma_de_ingreso_tarde_genera_incidencia(
    aplicacion, datos, token_docente, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 8, 25))
    cliente = aplicacion.test_client()

    respuesta = _registrar_firma(cliente, token_docente, datos, "Ingreso")

    assert respuesta.status_code == 201
    resultado = respuesta.get_json()["datos"]
    assert resultado["firma"]["tipo_firma"] == "Ingreso"
    assert resultado["firma"]["fecha"] == "2026-03-09"
    assert resultado["incidencia"]["tipo"] == "Tardanza"
    assert resultado["incidencia"]["minutos_desviacion"] == 25
    assert resultado["incidencia"]["generada_automaticamente"] is True


def test_firma_de_egreso_anticipada_genera_incidencia(
    aplicacion, datos, token_docente, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 8, 5))
    cliente = aplicacion.test_client()
    _registrar_firma(cliente, token_docente, datos, "Ingreso")

    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 9, 0))
    respuesta = _registrar_firma(cliente, token_docente, datos, "Egreso")

    assert respuesta.status_code == 201
    incidencia = respuesta.get_json()["datos"]["incidencia"]
    assert incidencia["tipo"] == "Salida anticipada"
    assert incidencia["minutos_desviacion"] == 20


def test_no_permite_egreso_sin_ingreso(aplicacion, datos, token_docente, monkeypatch):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 16, 9, 10))
    cliente = aplicacion.test_client()

    respuesta = _registrar_firma(cliente, token_docente, datos, "Egreso")

    assert respuesta.status_code == 409
    assert "ingreso" in respuesta.get_json()["error"]["mensaje"].lower()


def test_no_permite_firmar_dos_veces_el_mismo_tipo(
    aplicacion, datos, token_docente, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 7, 55))
    cliente = aplicacion.test_client()
    _registrar_firma(cliente, token_docente, datos, "Ingreso")

    respuesta = _registrar_firma(cliente, token_docente, datos, "Ingreso")

    assert respuesta.status_code == 409


def test_docente_no_puede_firmar_para_otro_docente(
    aplicacion, datos, token_docente, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 7, 55))
    cliente = aplicacion.test_client()

    respuesta = _registrar_firma(
        cliente, token_docente, datos, "Ingreso", docente_id=999
    )

    assert respuesta.status_code == 403


def test_alumno_no_puede_firmar_asistencia_docente(
    aplicacion, datos, token_alumno, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 7, 55))
    cliente = aplicacion.test_client()

    respuesta = _registrar_firma(cliente, token_alumno, datos, "Ingreso")

    assert respuesta.status_code == 403


def test_balance_de_horas_catedra_cruza_grilla_y_firmas(
    aplicacion, datos, token_admin, token_docente, monkeypatch
):
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 8, 25))
    cliente = aplicacion.test_client()
    _registrar_firma(cliente, token_docente, datos, "Ingreso")
    _fijar_reloj(monkeypatch, datetime(2026, 3, 9, 9, 0))
    _registrar_firma(cliente, token_docente, datos, "Egreso")

    respuesta = cliente.get(
        f"/api/v1/asistencias-docentes/balance-horas"
        f"?periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_admin),
    )

    assert respuesta.status_code == 200
    resultado = respuesta.get_json()["datos"]
    assert len(resultado["balances"]) == 1

    balance = resultado["balances"][0]["balance"]
    assert balance["clases_esperadas"] == 5
    assert balance["clases_completas"] == 1
    assert balance["clases_sin_firma"] == 4
    assert balance["minutos_esperados"] == 400
    assert balance["minutos_laborados"] == 35
    assert balance["horas_catedra_esperadas"] == 10.0
    assert balance["horas_catedra_laboradas"] == pytest.approx(0.88)
    assert balance["saldo_horas_catedra"] == pytest.approx(-9.12)

    respuesta_docente = cliente.get(
        f"/api/v1/asistencias-docentes/balance-horas"
        f"?periodo_id={datos['periodo_id']}",
        headers=encabezado_autorizacion(token_docente),
    )
    assert respuesta_docente.status_code == 200
    assert len(respuesta_docente.get_json()["datos"]["balances"]) == 1


def test_registro_de_licencia_y_listado_de_incidencias(
    aplicacion, datos, token_preceptor, token_docente
):
    cliente = aplicacion.test_client()
    respuesta = cliente.post(
        "/api/v1/asistencias-docentes/licencias",
        headers=encabezado_autorizacion(token_preceptor),
        json={
            "docente_id": datos["docente_id"],
            "fecha": "2026-03-10",
            "motivo": "Licencia por capacitación docente.",
        },
    )

    assert respuesta.status_code == 201
    incidencia = respuesta.get_json()["datos"]
    assert incidencia["tipo"] == "Licencia"
    assert incidencia["generada_automaticamente"] is False

    respuesta_duplicada = cliente.post(
        "/api/v1/asistencias-docentes/licencias",
        headers=encabezado_autorizacion(token_preceptor),
        json={
            "docente_id": datos["docente_id"],
            "fecha": "2026-03-10",
            "motivo": "Otra licencia el mismo día.",
        },
    )
    assert respuesta_duplicada.status_code == 409

    respuesta_listado = cliente.get(
        f"/api/v1/asistencias-docentes/incidencias"
        f"?docente_id={datos['docente_id']}&tipo=Licencia",
        headers=encabezado_autorizacion(token_docente),
    )
    assert respuesta_listado.status_code == 200
    assert len(respuesta_listado.get_json()["datos"]) == 1

    respuesta_docente_intenta_licencia = cliente.post(
        "/api/v1/asistencias-docentes/licencias",
        headers=encabezado_autorizacion(token_docente),
        json={
            "docente_id": datos["docente_id"],
            "fecha": "2026-03-11",
            "motivo": "Intento no autorizado.",
        },
    )
    assert respuesta_docente_intenta_licencia.status_code == 403
