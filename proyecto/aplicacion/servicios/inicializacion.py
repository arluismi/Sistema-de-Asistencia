"""Inicialización de datos maestros indispensables del sistema."""

from ..extenciones import base_de_datos
from ..modelos import ParametroInstitucional, Rol
from ..modelos.enumeraciones import NombreRol
from ..repositorios import (
    RepositorioParametrosInstitucionales,
    RepositorioUsuario,
)
from .servicio_configuracion_institucional import PARAMETROS_PREDETERMINADOS

CATALOGO_ROLES = [
    (
        NombreRol.ADMINISTRATIVO_DIRECTIVO,
        "Dirección institucional con acceso total al sistema.",
        1,
    ),
    (
        NombreRol.PRECEPTOR,
        "Gestión de asistencia, alertas y reportes institucionales.",
        2,
    ),
    (
        NombreRol.DOCENTE,
        "Registro de asistencia de sus materias y firma horaria personal.",
        3,
    ),
    (
        NombreRol.ALUMNO,
        "Consulta de su propia asistencia y situación de regularidad.",
        4,
    ),
]


def inicializar_datos_base() -> None:
    """Crea roles y parámetros faltantes sin duplicar los existentes.

    Es idempotente: puede ejecutarse en cada despliegue o antes de las pruebas.
    """

    repositorio_usuario = RepositorioUsuario()
    repositorio_parametros = RepositorioParametrosInstitucionales()

    for nombre_rol, descripcion, nivel_jerarquico in CATALOGO_ROLES:
        rol_existente = repositorio_usuario.obtener_rol_por_nombre(nombre_rol)
        if rol_existente is None:
            base_de_datos.session.add(
                Rol(
                    nombre=nombre_rol,
                    descripcion=descripcion,
                    nivel_jerarquico=nivel_jerarquico,
                )
            )

    for definicion in PARAMETROS_PREDETERMINADOS:
        parametro_existente = repositorio_parametros.obtener_por_clave(
            definicion["clave"]
        )
        if parametro_existente is None:
            base_de_datos.session.add(
                ParametroInstitucional(
                    clave=definicion["clave"],
                    valor=definicion["valor"],
                    descripcion=definicion["descripcion"],
                )
            )

    # `Session.commit` confirma en una única transacción todos los datos maestros.
    base_de_datos.session.commit()
