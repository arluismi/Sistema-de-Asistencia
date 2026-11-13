"""Servicio de reportabilidad transversal en PDF y Excel."""

from ..errores import ErrorValidacion
from ..reportes import GeneradorReporteExcel, GeneradorReportePdf
from .servicio_asistencia_docente import ServicioAsistenciaDocente
from .servicio_asistencia_estudiantil import ServicioAsistenciaEstudiantil

MIMETIPO_PDF = "application/pdf"
MIMETIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ServicioReportes:
    """Genera reportes institucionales de asistencia y horas cátedra."""

    def __init__(
        self,
        servicio_asistencia_estudiantil: ServicioAsistenciaEstudiantil | None = None,
        servicio_asistencia_docente: ServicioAsistenciaDocente | None = None,
        generador_pdf: GeneradorReportePdf | None = None,
        generador_excel: GeneradorReporteExcel | None = None,
    ):
        self.servicio_asistencia_estudiantil = (
            servicio_asistencia_estudiantil or ServicioAsistenciaEstudiantil()
        )
        self.servicio_asistencia_docente = (
            servicio_asistencia_docente or ServicioAsistenciaDocente()
        )
        self.generador_pdf = generador_pdf or GeneradorReportePdf()
        self.generador_excel = generador_excel or GeneradorReporteExcel()

    def generar_reporte_asistencia_estudiantes(
        self,
        curso_id: int,
        periodo_id: int,
        formato: str,
        estrategia: str | None = None,
    ) -> tuple[bytes, str, str]:
        """Genera el reporte de asistencia de un curso para un período."""

        resumen_curso = self.servicio_asistencia_estudiantil.calcular_resumen_curso(
            curso_id=curso_id,
            periodo_id=periodo_id,
            estrategia=estrategia,
        )

        encabezados = [
            "Legajo",
            "Estudiante",
            "Presentes",
            "Ausentes",
            "Justificados",
            "Tardes",
            "Registros",
            "% Asistencia",
            "% Presentismo",
            "Regularidad",
        ]

        filas = []
        for fila in resumen_curso["estudiantes"]:
            estudiante = fila["estudiante"]
            resumen = fila["resumen"]
            filas.append(
                [
                    estudiante["legajo"],
                    estudiante["nombre_completo"],
                    resumen["presentes"],
                    resumen["ausentes"],
                    resumen["justificados"],
                    resumen["tardes"],
                    resumen["total_registros"],
                    resumen["porcentaje_asistencia"],
                    resumen["porcentaje_presentismo_efectivo"],
                    resumen["estado_regularidad"],
                ]
            )

        resumen_general = resumen_curso["resumen_general"]
        texto_resumen = (
            f"Registros totales: {resumen_general['total_registros']} | "
            f"Asistencia general: {resumen_general['porcentaje_asistencia']}% | "
            f"Presentismo efectivo: "
            f"{resumen_general['porcentaje_presentismo_efectivo']}% | "
            f"Estado: {resumen_general['estado_regularidad']} | "
            f"Estrategia: {resumen_curso['estrategia']}"
        )

        curso = resumen_curso["curso"]
        periodo = resumen_curso["periodo"]
        subtitulo = (
            f"Curso: {curso['nombre_completo']} | "
            f"Período: {periodo['nombre']} "
            f"({periodo['fecha_inicio']} a {periodo['fecha_fin']}) | "
            f"Umbral de regularidad: "
            f"{resumen_general['umbral_regularidad_porcentaje']}%"
        )

        contenido, mimetype = self._generar_documento(
            formato=formato,
            nombre_hoja="Asistencia estudiantes",
            titulo="Reporte de asistencia estudiantil",
            subtitulo=subtitulo,
            encabezados=encabezados,
            filas=filas,
            resumen=texto_resumen,
            orientacion_horizontal=True,
        )
        nombre_archivo = (
            f"reporte_asistencia_estudiantes_curso_{curso_id}"
            f"_periodo_{periodo_id}.{formato}"
        )
        return contenido, nombre_archivo, mimetype

    def generar_reporte_horas_docentes(
        self,
        periodo_id: int,
        formato: str,
        estrategia: str | None = None,
    ) -> tuple[bytes, str, str]:
        """Genera el reporte de horas cátedra laboradas por todos los docentes."""

        resultado = self.servicio_asistencia_docente.calcular_balances(
            periodo_id=periodo_id,
            estrategia=estrategia,
        )
        periodo = resultado["periodo"]
        balances = resultado["balances"]

        encabezados = [
            "Legajo",
            "Docente",
            "Clases esperadas",
            "Completas",
            "Incompletas",
            "Sin firma",
            "Horas esperadas",
            "Horas laboradas",
            "Saldo",
            "% Cumplimiento",
        ]

        filas = []
        horas_esperadas_totales = 0.0
        horas_laboradas_totales = 0.0
        for elemento in balances:
            docente = elemento["docente"]
            balance = elemento["balance"]
            horas_esperadas_totales += balance["horas_catedra_esperadas"]
            horas_laboradas_totales += balance["horas_catedra_laboradas"]
            filas.append(
                [
                    docente["legajo"],
                    docente["nombre_completo"],
                    balance["clases_esperadas"],
                    balance["clases_completas"],
                    balance["clases_incompletas"],
                    balance["clases_sin_firma"],
                    balance["horas_catedra_esperadas"],
                    balance["horas_catedra_laboradas"],
                    balance["saldo_horas_catedra"],
                    balance["porcentaje_cumplimiento"],
                ]
            )

        saldo_total = round(horas_laboradas_totales - horas_esperadas_totales, 2)
        texto_resumen = (
            f"Docentes evaluados: {len(balances)} | "
            f"Horas cátedra esperadas: {round(horas_esperadas_totales, 2)} | "
            f"Horas cátedra laboradas: {round(horas_laboradas_totales, 2)} | "
            f"Saldo total: {saldo_total}"
        )
        subtitulo = (
            f"Período: {periodo['nombre']} "
            f"({periodo['fecha_inicio']} a {periodo['fecha_fin']}) | "
            f"Estrategia: {balances[0]['balance']['estrategia'] if balances else 'sin datos'}"
        )

        contenido, mimetype = self._generar_documento(
            formato=formato,
            nombre_hoja="Horas docentes",
            titulo="Reporte de horas cátedra docentes",
            subtitulo=subtitulo,
            encabezados=encabezados,
            filas=filas,
            resumen=texto_resumen,
            orientacion_horizontal=True,
        )
        nombre_archivo = f"reporte_horas_docentes_periodo_{periodo_id}.{formato}"
        return contenido, nombre_archivo, mimetype

    def _generar_documento(
        self,
        formato: str,
        nombre_hoja: str,
        titulo: str,
        subtitulo: str,
        encabezados: list[str],
        filas: list[list],
        resumen: str,
        orientacion_horizontal: bool,
    ) -> tuple[bytes, str]:
        """Selecciona el generador adecuado y devuelve contenido y MIME type."""

        if formato == "pdf":
            contenido = self.generador_pdf.generar(
                titulo=titulo,
                subtitulo=subtitulo,
                encabezados=encabezados,
                filas=filas,
                resumen=resumen,
                orientacion_horizontal=orientacion_horizontal,
            )
            return contenido, MIMETIPO_PDF

        if formato == "xlsx":
            contenido = self.generador_excel.generar(
                nombre_hoja=nombre_hoja,
                titulo=titulo,
                subtitulo=subtitulo,
                encabezados=encabezados,
                filas=filas,
                resumen=resumen,
            )
            return contenido, MIMETIPO_EXCEL

        # La validación del formato se realiza también en el controlador; esta
        # comprobación protege al servicio ante llamadas internas incorrectas.
        raise ErrorValidacion(
            "Formato de reporte no admitido.",
            detalles={"formatos_permitidos": ["pdf", "xlsx"]},
        )
