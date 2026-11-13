"""Funciones de validación y normalización de datos de entrada.

Concentran las verificaciones repetitivas para que los controladores sólo se
ocupen de traducir HTTP a llamadas de servicio.
"""

import re
from datetime import date, time
from typing import Any

from flask import request

from ..errores import ErrorValidacion
from ..modelos.enumeraciones import EstadoAsistencia, TipoFirma

PATRON_CORREO_ELECTRONICO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LONGITUD_MINIMA_CONTRASENA = 8


def obtener_cuerpo_json() -> dict:
    """Obtiene el cuerpo JSON de la petición y garantiza que sea un objeto.

    `request.get_json(silent=True)` evita que Flask lance una excepción cuando el
    cuerpo está vacío o mal formado; en ese caso se devuelve `None` y aquí se
    transforma en un error de validación uniforme.
    """

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la petición debe ser un objeto JSON válido.")
    return datos


def obtener_cadena_requerida(
    datos: dict,
    nombre_campo: str,
    longitud_maxima: int = 255,
    longitud_minima: int = 1,
) -> str:
    """Valida que un campo exista, sea texto y respete la longitud permitida."""

    valor = datos.get(nombre_campo)
    if not isinstance(valor, str):
        raise ErrorValidacion(f"El campo '{nombre_campo}' es obligatorio y debe ser texto.")

    valor_limpio = valor.strip()
    if len(valor_limpio) < longitud_minima:
        raise ErrorValidacion(
            f"El campo '{nombre_campo}' debe tener al menos {longitud_minima} caracteres."
        )
    if len(valor_limpio) > longitud_maxima:
        raise ErrorValidacion(
            f"El campo '{nombre_campo}' no puede superar {longitud_maxima} caracteres."
        )
    return valor_limpio


def obtener_cadena_opcional(
    datos: dict,
    nombre_campo: str,
    longitud_maxima: int = 500,
) -> str | None:
    """Valida un campo de texto opcional; devuelve `None` si no fue enviado."""

    if nombre_campo not in datos or datos[nombre_campo] is None:
        return None
    valor_limpio = obtener_cadena_requerida(
        datos,
        nombre_campo,
        longitud_maxima=longitud_maxima,
        longitud_minima=0,
    )
    return valor_limpio or None


def obtener_entero_requerido(
    datos: dict,
    nombre_campo: str,
    valor_minimo: int | None = None,
    valor_maximo: int | None = None,
) -> int:
    """Valida un entero obligatorio, rechazando booleanos y valores fuera de rango."""

    if nombre_campo not in datos:
        raise ErrorValidacion(f"El campo '{nombre_campo}' es obligatorio.")

    valor = datos[nombre_campo]
    if isinstance(valor, bool):
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser un número entero.")

    try:
        valor_entero = int(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser un número entero.")

    if isinstance(valor, float) and not valor.is_integer():
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser un número entero.")
    if valor_minimo is not None and valor_entero < valor_minimo:
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser mayor o igual a {valor_minimo}.")
    if valor_maximo is not None and valor_entero > valor_maximo:
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser menor o igual a {valor_maximo}.")
    return valor_entero


def obtener_entero_opcional(
    datos: dict,
    nombre_campo: str,
    valor_minimo: int | None = None,
    valor_maximo: int | None = None,
) -> int | None:
    """Valida un entero opcional; devuelve `None` si no fue enviado."""

    if nombre_campo not in datos or datos[nombre_campo] is None:
        return None
    return obtener_entero_requerido(datos, nombre_campo, valor_minimo, valor_maximo)


def obtener_fecha_iso(datos: dict, nombre_campo: str, requerida: bool = True) -> date | None:
    """Interpreta una fecha en formato ISO 8601 (`AAAA-MM-DD`)."""

    if nombre_campo not in datos or datos[nombre_campo] is None:
        if requerida:
            raise ErrorValidacion(f"El campo '{nombre_campo}' es obligatorio.")
        return None

    valor = datos[nombre_campo]
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str):
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe usar el formato AAAA-MM-DD.")

    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe usar el formato AAAA-MM-DD.")


def obtener_hora_requerida(datos: dict, nombre_campo: str) -> time:
    """Interpreta una hora en formato de 24 horas (`HH:MM` o `HH:MM:SS`)."""

    valor = datos.get(nombre_campo)
    if not isinstance(valor, str):
        raise ErrorValidacion(f"El campo '{nombre_campo}' es obligatorio y debe ser una hora.")

    try:
        return time.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(
            f"El campo '{nombre_campo}' debe usar el formato de 24 horas HH:MM."
        )


def obtener_booleano_opcional(datos: dict, nombre_campo: str) -> bool | None:
    """Interpreta un booleano opcional enviado como JSON o como texto."""

    if nombre_campo not in datos or datos[nombre_campo] is None:
        return None

    valor = datos[nombre_campo]
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.strip().lower() in {"true", "false"}:
        return valor.strip().lower() == "true"

    raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser verdadero o falso.")


def obtener_lista_requerida(
    datos: dict,
    nombre_campo: str,
    permitir_vacia: bool = False,
) -> list:
    """Valida que un campo sea una lista y, opcionalmente, que no esté vacía."""

    valor = datos.get(nombre_campo)
    if not isinstance(valor, list):
        raise ErrorValidacion(f"El campo '{nombre_campo}' debe ser una lista.")
    if not permitir_vacia and len(valor) == 0:
        raise ErrorValidacion(f"El campo '{nombre_campo}' no puede estar vacío.")
    return valor


def validar_correo_electronico(valor: str) -> str:
    """Comprueba el formato básico de una dirección de correo electrónico."""

    if not PATRON_CORREO_ELECTRONICO.fullmatch(valor):
        raise ErrorValidacion("El correo electrónico no tiene un formato válido.")
    return valor


def validar_contrasena(valor: str) -> str:
    """Exige una longitud mínima para las contraseñas de los usuarios."""

    if len(valor) < LONGITUD_MINIMA_CONTRASENA:
        raise ErrorValidacion(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres."
        )
    return valor


def validar_estado_asistencia(valor: Any) -> EstadoAsistencia:
    """Convierte un texto en un estado de asistencia permitido.

    Acepta diferencias de mayúsculas y minúsculas, pero sólo admite los cuatro
    estados institucionales: Presente, Ausente, Justificado y Tarde.
    """

    estados_permitidos = [estado.value for estado in EstadoAsistencia]
    if isinstance(valor, str):
        for estado in EstadoAsistencia:
            if estado.value.lower() == valor.strip().lower():
                return estado

    raise ErrorValidacion(
        "Estado de asistencia inválido. Valores permitidos: Presente, Ausente, Justificado, Tarde.",
        detalles={"estados_permitidos": estados_permitidos},
    )


def validar_tipo_firma(valor: Any) -> TipoFirma:
    """Convierte un texto en un tipo de firma docente permitido (Ingreso o Egreso)."""

    tipos_permitidos = [tipo.value for tipo in TipoFirma]
    if isinstance(valor, str):
        for tipo in TipoFirma:
            if tipo.value.lower() == valor.strip().lower():
                return tipo

    raise ErrorValidacion(
        "Tipo de firma inválido. Valores permitidos: Ingreso, Egreso.",
        detalles={"tipos_permitidos": tipos_permitidos},
    )


def obtener_argumento_entero(
    argumentos,
    nombre_campo: str,
    requerido: bool = False,
    valor_minimo: int | None = None,
) -> int | None:
    """Lee un entero desde los parámetros de consulta de la URL."""

    valor = argumentos.get(nombre_campo)
    if valor is None or valor == "":
        if requerido:
            raise ErrorValidacion(f"El parámetro '{nombre_campo}' es obligatorio.")
        return None

    try:
        valor_entero = int(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El parámetro '{nombre_campo}' debe ser un número entero.")

    if valor_minimo is not None and valor_entero < valor_minimo:
        raise ErrorValidacion(
            f"El parámetro '{nombre_campo}' debe ser mayor o igual a {valor_minimo}."
        )
    return valor_entero


def obtener_argumento_fecha(
    argumentos,
    nombre_campo: str,
    requerido: bool = False,
) -> date | None:
    """Lee una fecha ISO desde los parámetros de consulta de la URL."""

    valor = argumentos.get(nombre_campo)
    if valor is None or valor == "":
        if requerido:
            raise ErrorValidacion(f"El parámetro '{nombre_campo}' es obligatorio.")
        return None

    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(f"El parámetro '{nombre_campo}' debe usar el formato AAAA-MM-DD.")


def obtener_argumento_cadena(argumentos, nombre_campo: str) -> str | None:
    """Lee un parámetro de consulta textual y descarta espacios sobrantes."""

    valor = argumentos.get(nombre_campo)
    if valor is None:
        return None
    valor_limpio = valor.strip()
    return valor_limpio or None


def obtener_argumento_booleano(argumentos, nombre_campo: str) -> bool | None:
    """Lee un parámetro de consulta booleano (`true`/`false`)."""

    valor = argumentos.get(nombre_campo)
    if valor is None or valor == "":
        return None
    if valor.strip().lower() in {"true", "1", "si", "sí"}:
        return True
    if valor.strip().lower() in {"false", "0", "no"}:
        return False
    raise ErrorValidacion(f"El parámetro '{nombre_campo}' debe ser true o false.")
