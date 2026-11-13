"""Fábrica de la aplicación Flask.

Concentra la inicialización de extensiones, el registro de controladores,
manejadores de error, observadores y comandos de administración.
"""

from flask import Flask
from flask_cors import CORS

from .comandos import registrar_comandos
from .controladores import LISTA_DE_BLUEPRINTS
from .errores import registrar_manejadores_de_errores
from .extenciones import base_de_datos
from .modelos import *  # noqa: F401,F403  (registra todas las tablas en SQLAlchemy)
from .observadores import registrar_observadores


def crear_aplicacion(clase_configuracion=None, **sobrescrituras_de_configuracion) -> Flask:
    """Construye y devuelve una instancia de Flask configurada."""

    if clase_configuracion is None:
        from configuracion import ConfiguracionDesarrollo

        clase_configuracion = ConfiguracionDesarrollo

    # `Flask(__name__)` crea la aplicación y localiza sus recursos relativos al
    # paquete; `instance_relative_config=True` habilita la carpeta `instance/`.
    aplicacion = Flask(__name__, instance_relative_config=True)
    aplicacion.config.from_object(clase_configuracion)
    aplicacion.config.update(sobrescrituras_de_configuracion)

    # El proveedor JSON de Flask permite conservar los acentos sin escapes.
    aplicacion.json.ensure_ascii = False

    # `init_app` vincula SQLAlchemy con esta aplicación y su cadena de conexión.
    base_de_datos.init_app(aplicacion)

    # `CORS` habilita el futuro frontend separado, limitado a las rutas de la API
    # y a los orígenes definidos en la configuración.
    CORS(
        aplicacion,
        resources={
            r"/api/*": {
                "origins": aplicacion.config["CORS_ORIGENES_PERMITIDOS"]
            }
        },
    )

    registrar_manejadores_de_errores(aplicacion)

    # `register_blueprint` monta cada grupo de endpoints bajo el prefijo versión.
    for blueprint in LISTA_DE_BLUEPRINTS:
        aplicacion.register_blueprint(blueprint, url_prefix="/api/v1")

    registrar_observadores()
    registrar_comandos(aplicacion)

    return aplicacion
