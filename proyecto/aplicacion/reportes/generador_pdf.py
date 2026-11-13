"""Generador de reportes en formato PDF mediante ReportLab."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm as centimetro
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class GeneradorReportePdf:
    """Construye un documento PDF tabular con título, resumen y detalle."""

    def generar(
        self,
        titulo: str,
        subtitulo: str,
        encabezados: list[str],
        filas: list[list],
        resumen: str | None = None,
        orientacion_horizontal: bool = True,
    ) -> bytes:
        """Devuelve el contenido binario del PDF generado."""

        buffer = BytesIO()
        tamano_pagina = landscape(A4) if orientacion_horizontal else A4

        # `SimpleDocTemplate` administra el flujo del documento y los saltos de
        # página. Escribe el resultado en el buffer en memoria al invocar `build`.
        documento = SimpleDocTemplate(
            buffer,
            pagesize=tamano_pagina,
            leftMargin=1.2 * centimetro,
            rightMargin=1.2 * centimetro,
            topMargin=1.5 * centimetro,
            bottomMargin=1.5 * centimetro,
            title=titulo,
        )

        estilos = getSampleStyleSheet()
        elementos = [
            Paragraph(titulo, estilos["Title"]),
            Paragraph(subtitulo, estilos["Normal"]),
            Spacer(1, 0.5 * centimetro),
        ]
        if resumen:
            elementos.append(Paragraph(resumen, estilos["Normal"]))
            elementos.append(Spacer(1, 0.4 * centimetro))

        datos_tabla = [encabezados] + [
            ["" if celda is None else str(celda) for celda in fila] for fila in filas
        ]

        # `Table` distribuye las columnas según el ancho disponible y
        # `repeatRows=1` repite el encabezado en cada página.
        tabla = Table(datos_tabla, repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B0BEC5")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F8")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elementos.append(tabla)

        # `build` procesa los elementos y escribe el PDF completo en el buffer.
        documento.build(elementos)
        return buffer.getvalue()
