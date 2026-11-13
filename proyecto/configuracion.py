"""Configuración central del backend.

La configuración se obtiene de variables de entorno para evitar credenciales
incrustadas en el código. El archivo `.env` es opcional y se carga mediante
`python-dotenv`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
DIRECTORIO_INSTANCIA = DIRECTORIO_PROYECTO / "instance"
DIRECTORIO_INSTANCIA.mkdir(parents=True, exist_ok=True)

# `load_dotenv` (librería python-dotenv) lee el archivo indicado y expone cada
# variable como variable de entorno, sin sobreescribir las ya definidas.
load_dotenv(DIRECTORIO_PROYECTO / ".env")

RUTA_BASE_DATOS_PREDETERMINADA = DIRECTORIO_INSTANCIA / "institucion.db"


def _obtener_origenes_cors() -> list[str]:
    """Convierte la lista de orígenes separada por comas en una lista de Python."""
    valor_configurado = os.getenv("CORS_ORIGENES_PERMITIDOS", "*")
    return [origen.strip() for origen in valor_configurado.split(",") if origen.strip()]


class ConfiguracionBase:
    """Valores comunes a todos los entornos de ejecución."""

    CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", "clave-secreta-solo-para-desarrollo")
    CLAVE_TOKEN = os.getenv("CLAVE_TOKEN", "clave-token-solo-para-desarrollo")
    ALGORITMO_TOKEN = "HS256"
    MINUTOS_VIGENCIA_TOKEN = int(os.getenv("MINUTOS_VIGENCIA_TOKEN", "480"))

    ZONA_HORARIA_INSTITUCIONAL = os.getenv(
        "ZONA_HORARIA_INSTITUCIONAL", "America/Argentina/Buenos_Aires"
    )

    URL_BASE_DATOS = os.getenv("URL_BASE_DATOS") or (
        "sqlite:///" + RUTA_BASE_DATOS_PREDETERMINADA.as_posix()
    )

    # Nombre exigido por Flask-SQLAlchemy para localizar el motor de persistencia.
    SQLALCHEMY_DATABASE_URI = URL_BASE_DATOS

    # Evita que Flask-SQLAlchemy registre cada cambio de objeto en memoria.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # `JSON_AS_ASCII` mantiene los acentos legibles en las respuestas JSON.
    JSON_AS_ASCII = False

    CORS_ORIGENES_PERMITIDOS = _obtener_origenes_cors()


class ConfiguracionDesarrollo(ConfiguracionBase):
    """Configuración usada por el servidor de desarrollo local."""

    DEPURACION = True


class ConfiguracionPruebas(ConfiguracionBase):
    """Configuración usada por la suite automatizada de pruebas."""

    DEPURACION = False
    TESTING = True
    CLAVE_SECRETA = "clave-secreta-de-pruebas-con-longitud-suficiente"
    CLAVE_TOKEN = "clave-token-de-pruebas-con-longitud-suficiente"
    ZONA_HORARIA_INSTITUCIONAL = "America/Argentina/Buenos_Aires"


class ConfiguracionProduccion(ConfiguracionBase):
    """Configuración sugerida para despliegue; las claves deben venir del entorno."""

    DEPURACION = False
