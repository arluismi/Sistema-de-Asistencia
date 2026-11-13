"""Pruebas del generador de datos de prueba con volumen."""

from aplicacion.modelos import AlertaAsistencia, Estudiante
from aplicacion.servicios.datos_prueba import (
    CANTIDAD_ESTUDIANTES_POR_CURSO,
    CURSOS_PRUEBA,
    generar_datos_prueba,
)


def test_generar_datos_prueba_carga_volumen(aplicacion):
    """El generador crea estructura, asistencias y firmas docentes."""

    with aplicacion.app_context():
        resultado = generar_datos_prueba()

    assert resultado["generado"] is True
    assert resultado["cursos"] == len(CURSOS_PRUEBA)
    assert (
        resultado["estudiantes"]
        == len(CURSOS_PRUEBA) * CANTIDAD_ESTUDIANTES_POR_CURSO
    )
    assert resultado["registros_asistencia"] > 100
    assert resultado["firmas_docentes"] > 0
    assert resultado["incidencias_docentes"] > 0


def test_generar_datos_prueba_produce_alertas(aplicacion):
    """Los estados de asistencia elegidos disparan alertas del tablero."""

    with aplicacion.app_context():
        generar_datos_prueba()
        cantidad_alertas = AlertaAsistencia.query.count()

    assert cantidad_alertas > 0


def test_generar_datos_prueba_es_idempotente(aplicacion):
    """Una segunda ejecución no duplica los datos ya generados."""

    with aplicacion.app_context():
        primera = generar_datos_prueba()
        segunda = generar_datos_prueba()
        estudiantes_generados = Estudiante.query.filter(
            Estudiante.legajo.like("ALU-PRUEBA-%")
        ).count()

    assert primera["generado"] is True
    assert segunda["generado"] is False
    assert segunda["mensaje"] == "Los datos de prueba ya estaban cargados."
    assert (
        estudiantes_generados
        == len(CURSOS_PRUEBA) * CANTIDAD_ESTUDIANTES_POR_CURSO
    )
