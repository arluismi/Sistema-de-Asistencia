"""Servicio de parámetros institucionales configurables."""

from flask import current_app

from ..errores import ErrorNoEncontrado, ErrorValidacion
from ..estrategias.calculo_asistencia import (
    ESTRATEGIAS_DISPONIBLES as ESTRATEGIAS_ASISTENCIA,
)
from ..estrategias.calculo_horas_docentes import (
    ESTRATEGIAS_DISPONIBLES as ESTRATEGIAS_HORAS_CATEDRA,
)
from ..repositorios import RepositorioParametrosInstitucionales

PARAMETROS_PREDETERMINADOS = [
    {
        "clave": "umbral_regularidad_porcentaje",
        "valor": "75",
        "descripcion": "Porcentaje mínimo de asistencia para conservar la regularidad.",
    },
    {
        "clave": "limite_inasistencias_consecutivas",
        "valor": "3",
        "descripcion": "Cantidad de jornadas consecutivas ausentes que dispara una alerta.",
    },
    {
        "clave": "minutos_hora_catedra",
        "valor": "40",
        "descripcion": "Duración en minutos de una hora cátedra institucional.",
    },
    {
        "clave": "tolerancia_minutos_firma",
        "valor": "10",
        "descripcion": "Tolerancia en minutos antes de registrar tardanza o salida anticipada.",
    },
    {
        "clave": "estrategia_calculo_asistencia",
        "valor": "institucional",
        "descripcion": "Estrategia aplicada por defecto al calcular porcentajes de asistencia.",
    },
    {
        "clave": "estrategia_calculo_horas",
        "valor": "exacta",
        "descripcion": "Estrategia aplicada por defecto al calcular horas cátedra docentes.",
    },
]

CLAVES_NUMERICAS = {
    "umbral_regularidad_porcentaje",
    "limite_inasistencias_consecutivas",
    "minutos_hora_catedra",
    "tolerancia_minutos_firma",
}


class ServicioConfiguracionInstitucional:
    """Lectura y actualización de las reglas configurables del instituto."""

    def __init__(self, repositorio_parametros: RepositorioParametrosInstitucionales | None = None):
        self.repositorio_parametros = (
            repositorio_parametros or RepositorioParametrosInstitucionales()
        )

    def obtener_valor(self, clave: str) -> str:
        """Devuelve el valor vigente de un parámetro o su valor predeterminado."""

        parametro = self.repositorio_parametros.obtener_por_clave(clave)
        if parametro is not None:
            return parametro.valor

        predeterminado = next(
            (item for item in PARAMETROS_PREDETERMINADOS if item["clave"] == clave),
            None,
        )
        if predeterminado is not None:
            return predeterminado["valor"]

        raise ErrorNoEncontrado(f"No existe el parámetro institucional '{clave}'.")

    def obtener_entero(self, clave: str) -> int:
        """Devuelve un parámetro numérico y falla si su valor no es un entero."""

        valor = self.obtener_valor(clave)
        try:
            return int(valor)
        except (TypeError, ValueError):
            raise ErrorValidacion(
                f"El parámetro institucional '{clave}' debe contener un número entero."
            )

    def listar_parametros(self):
        """Lista todos los parámetros persistidos."""

        return self.repositorio_parametros.listar_todos()

    def actualizar_parametro(self, clave: str, valor) -> None:
        """Actualiza un parámetro existente validando que la clave sea conocida."""

        parametro = self.repositorio_parametros.obtener_por_clave(clave)
        if parametro is None:
            raise ErrorNoEncontrado(f"No existe el parámetro institucional '{clave}'.")

        valor_texto = str(valor).strip() if valor is not None else ""
        if not valor_texto:
            raise ErrorValidacion("El valor del parámetro no puede estar vacío.")

        if clave in CLAVES_NUMERICAS:
            try:
                numero = int(valor_texto)
            except ValueError:
                raise ErrorValidacion(f"El parámetro '{clave}' debe ser numérico.")
            if numero < 0:
                raise ErrorValidacion(f"El parámetro '{clave}' no puede ser negativo.")
            if clave == "umbral_regularidad_porcentaje" and numero > 100:
                raise ErrorValidacion("El umbral de regularidad debe estar entre 0 y 100.")
            if clave in {"minutos_hora_catedra", "limite_inasistencias_consecutivas"} and numero == 0:
                raise ErrorValidacion(f"El parámetro '{clave}' debe ser mayor que cero.")

        if clave == "estrategia_calculo_asistencia" and valor_texto not in ESTRATEGIAS_ASISTENCIA:
            raise ErrorValidacion(
                "La estrategia de asistencia no es válida.",
                detalles={"estrategias_permitidas": sorted(ESTRATEGIAS_ASISTENCIA)},
            )

        if clave == "estrategia_calculo_horas" and valor_texto not in ESTRATEGIAS_HORAS_CATEDRA:
            raise ErrorValidacion(
                "La estrategia de horas cátedra no es válida.",
                detalles={
                    "estrategias_permitidas": sorted(ESTRATEGIAS_HORAS_CATEDRA)
                },
            )

        parametro.valor = valor_texto
        self.repositorio_parametros.confirmar_cambios()

    def configuracion_publica(self) -> dict:
        """Expone la configuración aplicable al cálculo sin datos sensibles."""

        return {
            "umbral_regularidad_porcentaje": self.obtener_entero(
                "umbral_regularidad_porcentaje"
            ),
            "limite_inasistencias_consecutivas": self.obtener_entero(
                "limite_inasistencias_consecutivas"
            ),
            "minutos_hora_catedra": self.obtener_entero("minutos_hora_catedra"),
            "tolerancia_minutos_firma": self.obtener_entero(
                "tolerancia_minutos_firma"
            ),
            "estrategia_calculo_asistencia": self.obtener_valor(
                "estrategia_calculo_asistencia"
            ),
            "estrategia_calculo_horas": self.obtener_valor(
                "estrategia_calculo_horas"
            ),
            "zona_horaria_institucional": current_app.config[
                "ZONA_HORARIA_INSTITUCIONAL"
            ],
        }
