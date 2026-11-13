"""Punto de entrada del backend.

Ejecuta el servidor de desarrollo de Flask o los comandos de administración
registrados en la aplicación (inicialización de base de datos y datos de prueba).
"""

import sys

from aplicacion import crear_aplicacion
from configuracion import ConfiguracionDesarrollo

# La fábrica `crear_aplicacion` devuelve una instancia de Flask completamente
# configurada. Flask la detecta automáticamente para el comando `flask run`.
aplicacion = crear_aplicacion(ConfiguracionDesarrollo)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from aplicacion.comandos import ejecutar_comando_directo

        # Despacha comandos administrativos sin iniciar el servidor HTTP.
        codigo_salida = ejecutar_comando_directo(aplicacion, sys.argv[1:])
        sys.exit(codigo_salida)

    # `aplicacion.run` inicia el servidor HTTP integrado de Flask. No debe
    # usarse en producción, donde se requiere un servidor WSGI dedicado.
    aplicacion.run(
        host="0.0.0.0",
        port=5000,
        debug=aplicacion.config["DEPURACION"],
    )
