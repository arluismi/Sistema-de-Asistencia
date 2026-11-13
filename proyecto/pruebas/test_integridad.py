"""Pruebas de integridad referencial a nivel de base de datos."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from aplicacion.extenciones import base_de_datos
from aplicacion.modelos import RegistroAsistenciaEstudiantil
from aplicacion.modelos.enumeraciones import EstadoAsistencia


def test_sqlite_rechaza_referencias_inexistentes(aplicacion, datos):
    """La clave foránea debe fallar aun si se omite la validación de servicios."""

    with aplicacion.app_context():
        registro_invalido = RegistroAsistenciaEstudiantil(
            estudiante_id=999999,
            curso_id=datos["curso_id"],
            materia_id=datos["matematica_id"],
            fecha=date(2026, 3, 2),
            estado=EstadoAsistencia.PRESENTE,
            registrado_por_usuario_id=datos["usuario_admin_id"],
        )
        base_de_datos.session.add(registro_invalido)

        with pytest.raises(IntegrityError):
            base_de_datos.session.commit()

        base_de_datos.session.rollback()
