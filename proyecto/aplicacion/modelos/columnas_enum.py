"""Fábrica de columnas para enums almacenados como texto.

`native_enum=False` obliga a SQLAlchemy a usar `VARCHAR` con una restricción
`CHECK`, lo que mantiene el esquema portable entre SQLite y PostgreSQL.
"""

from ..extenciones import base_de_datos


def columna_enum(clase_enum, nombre_tipo: str):
    """Construye una columna de tipo enum basada en los valores del enum recibido.

    `values_callable` indica a SQLAlchemy que persista `elemento.value` (por
    ejemplo `"Presente"`) en lugar del nombre interno del miembro.
    """

    return base_de_datos.Enum(
        clase_enum,
        values_callable=lambda clase: [elemento.value for elemento in clase],
        native_enum=False,
        validate_strings=True,
        name=nombre_tipo,
    )
