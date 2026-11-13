"""Extensiones compartidas por la aplicación.

Se declaran instancias únicas que luego se inicializan en la fábrica de la
aplicación (`aplicacion.__init__.crear_aplicacion`).
"""

import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

# `SQLAlchemy` es la extensión de Flask que administra el motor, las sesiones y
# los modelos. Se crea sin aplicación para permitir el patrón de fábrica.
base_de_datos = SQLAlchemy()


@event.listens_for(Engine, "connect")
def habilitar_claves_foraneas_en_sqlite(conexion_dbapi, _registro_conexion):
    """Activa la verificación de integridad referencial en cada conexión SQLite.

    SQLite no aplica las claves foráneas por defecto. El evento `connect` de
    SQLAlchemy se ejecuta cada vez que se abre una conexión, por lo que se emite
    `PRAGMA foreign_keys=ON` antes de cualquier consulta.

    En motores como PostgreSQL este bloque no interviene y las restricciones se
    aplican de forma nativa.
    """

    if isinstance(conexion_dbapi, sqlite3.Connection):
        cursor = conexion_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
