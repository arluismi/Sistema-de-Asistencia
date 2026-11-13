"""Comandos de administración disponibles desde la CLI.

Se exponen por dos vías:
- `flask --app run.py <comando>` (CLI de Flask).
- `python run.py <comando>` (ejecución directa, útil en Windows).
"""

import json

from flask import Flask

from ..extenciones import base_de_datos
from ..servicios.datos_demostracion import sembrar_datos_demostracion
from ..servicios.datos_prueba import generar_datos_prueba
from ..servicios.inicializacion import inicializar_datos_base


def comando_inicializar_base_de_datos() -> None:
    """Crea las tablas y carga roles y parámetros predeterminados."""

    # `create_all` de SQLAlchemy crea únicamente las tablas que aún no existen.
    base_de_datos.create_all()
    inicializar_datos_base()
    print("Base de datos inicializada con roles y parámetros institucionales.")


def comando_sembrar_datos_demostracion() -> None:
    """Carga usuarios, estructura académica y asistencias de demostración."""

    base_de_datos.create_all()
    resultado = sembrar_datos_demostracion()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


def comando_generar_datos_prueba() -> None:
    """Carga varios cursos, asistencias y firmas para probar con volumen."""

    base_de_datos.create_all()
    resultado = generar_datos_prueba()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


COMANDOS_DISPONIBLES = {
    "inicializar-base-de-datos": comando_inicializar_base_de_datos,
    "sembrar-datos-demostracion": comando_sembrar_datos_demostracion,
    "generar-datos-prueba": comando_generar_datos_prueba,
}


def registrar_comandos(aplicacion: Flask) -> None:
    """Registra los comandos propios del proyecto en la CLI de Flask.

    `aplicacion.cli.command` es el decorador de Flask que expone una función
    como comando de terminal; Flask le inyecta el contexto de aplicación.
    """

    aplicacion.cli.command("inicializar-base-de-datos")(
        comando_inicializar_base_de_datos
    )
    aplicacion.cli.command("sembrar-datos-demostracion")(
        comando_sembrar_datos_demostracion
    )
    aplicacion.cli.command("generar-datos-prueba")(comando_generar_datos_prueba)


def ejecutar_comando_directo(aplicacion: Flask, argumentos: list[str]) -> int:
    """Ejecuta un comando administrativo desde `python run.py <comando>`."""

    if not argumentos:
        print("Comandos disponibles:")
        for nombre in COMANDOS_DISPONIBLES:
            print(f"  - {nombre}")
        return 1

    nombre_comando = argumentos[0]
    comando = COMANDOS_DISPONIBLES.get(nombre_comando)
    if comando is None:
        print(f"Comando desconocido: '{nombre_comando}'.")
        print("Comandos disponibles:")
        for nombre in COMANDOS_DISPONIBLES:
            print(f"  - {nombre}")
        return 1

    # `app_context` crea el contexto necesario para que SQLAlchemy resuelva la
    # sesión y la configuración de la aplicación fuera de una petición HTTP.
    with aplicacion.app_context():
        comando()
    return 0
