"""Generador de reportes en formato Excel mediante openpyxl."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


class GeneradorReporteExcel:
    """Construye un libro de Excel con encabezados y datos tabulares."""

    def generar(
        self,
        nombre_hoja: str,
        titulo: str,
        subtitulo: str,
        encabezados: list[str],
        filas: list[list],
        resumen: str | None = None,
    ) -> bytes:
        """Devuelve el contenido binario del archivo `.xlsx` generado."""

        # `Workbook` crea un libro nuevo; `active` devuelve la hoja inicial.
        libro = Workbook()
        hoja = libro.active
        hoja.title = nombre_hoja[:31]

        hoja["A1"] = titulo
        hoja["A1"].font = Font(bold=True, size=14, color="1F3A5F")
        hoja["A2"] = subtitulo
        hoja["A2"].font = Font(size=10, color="455A64")

        fila_encabezados = 4
        if resumen:
            hoja["A3"] = resumen
            hoja["A3"].font = Font(size=9, italic=True, color="555555")
            fila_encabezados = 5

        relleno_encabezado = PatternFill(
            fill_type="solid", start_color="1F3A5F", end_color="1F3A5F"
        )
        borde_fino = Border(
            left=Side(style="thin", color="B0BEC5"),
            right=Side(style="thin", color="B0BEC5"),
            top=Side(style="thin", color="B0BEC5"),
            bottom=Side(style="thin", color="B0BEC5"),
        )

        for numero_columna, encabezado in enumerate(encabezados, start=1):
            celda = hoja.cell(
                row=fila_encabezados, column=numero_columna, value=encabezado
            )
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = relleno_encabezado
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.border = borde_fino

        for numero_fila, fila in enumerate(filas, start=fila_encabezados + 1):
            for numero_columna, valor in enumerate(fila, start=1):
                celda = hoja.cell(row=numero_fila, column=numero_columna, value=valor)
                celda.border = borde_fino
                celda.alignment = Alignment(
                    horizontal="center" if numero_columna != 2 else "left",
                    vertical="center",
                )

        for numero_columna, encabezado in enumerate(encabezados, start=1):
            longitud_maxima = max(
                [len(str(encabezado))]
                + [
                    len(str(fila[numero_columna - 1]))
                    for fila in filas
                    if len(fila) >= numero_columna
                ]
            )
            hoja.column_dimensions[get_column_letter(numero_columna)].width = min(
                max(12, longitud_maxima + 2), 45
            )

        # `freeze_panes` fija las filas superiores al desplazarse por la hoja.
        hoja.freeze_panes = hoja.cell(row=fila_encabezados + 1, column=1)

        buffer = BytesIO()
        # `save` serializa el libro completo en el archivo o buffer indicado.
        libro.save(buffer)
        return buffer.getvalue()
