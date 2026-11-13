"""Consultas de usuarios, estudiantes y docentes."""

from sqlalchemy import select

from ..modelos import Docente, Estudiante, InscripcionEstudianteCurso, Rol, Usuario
from .repositorio_base import RepositorioBase


class RepositorioUsuario(RepositorioBase):
    """Acceso a datos de cuentas, estudiantes y docentes."""

    modelo = Usuario

    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        """Busca una cuenta por su nombre de usuario único."""

        return self.sesion.execute(
            select(Usuario).where(Usuario.nombre_usuario == nombre_usuario)
        ).scalar_one_or_none()

    def obtener_por_correo_electronico(self, correo_electronico: str) -> Usuario | None:
        """Busca una cuenta por su correo electrónico único."""

        return self.sesion.execute(
            select(Usuario).where(Usuario.correo_electronico == correo_electronico)
        ).scalar_one_or_none()

    def obtener_rol_por_nombre(self, nombre_rol) -> Rol | None:
        """Obtiene el rol institucional por su nombre enumerado."""

        return self.sesion.execute(
            select(Rol).where(Rol.nombre == nombre_rol)
        ).scalar_one_or_none()

    def listar_usuarios(self, rol=None, activo: bool | None = None):
        """Lista cuentas con filtros opcionales de rol y estado."""

        consulta = select(Usuario).order_by(Usuario.id)
        if rol is not None:
            consulta = consulta.join(Usuario.rol).where(Rol.nombre == rol)
        if activo is not None:
            consulta = consulta.where(Usuario.activo.is_(activo))
        return self.sesion.execute(consulta).scalars().all()

    def obtener_estudiante_por_id(self, estudiante_id: int) -> Estudiante | None:
        """Busca un estudiante por su identificador."""

        return self.sesion.get(Estudiante, estudiante_id)

    def obtener_estudiante_por_usuario_id(self, usuario_id: int) -> Estudiante | None:
        """Obtiene el perfil de estudiante asociado a una cuenta."""

        return self.sesion.execute(
            select(Estudiante).where(Estudiante.usuario_id == usuario_id)
        ).scalar_one_or_none()

    def obtener_estudiante_por_legajo(self, legajo: str) -> Estudiante | None:
        """Busca un estudiante por su legajo institucional."""

        return self.sesion.execute(
            select(Estudiante).where(Estudiante.legajo == legajo)
        ).scalar_one_or_none()

    def listar_estudiantes(self, curso_id: int | None = None):
        """Lista estudiantes, opcionalmente restringidos a un curso."""

        consulta = select(Estudiante).order_by(Estudiante.apellidos, Estudiante.nombres)
        if curso_id is not None:
            consulta = consulta.join(
                InscripcionEstudianteCurso,
                InscripcionEstudianteCurso.estudiante_id == Estudiante.id,
            ).where(InscripcionEstudianteCurso.curso_id == curso_id)
        return self.sesion.execute(consulta).scalars().unique().all()

    def obtener_docente_por_id(self, docente_id: int) -> Docente | None:
        """Busca un docente por su identificador."""

        return self.sesion.get(Docente, docente_id)

    def obtener_docente_por_usuario_id(self, usuario_id: int) -> Docente | None:
        """Obtiene el perfil docente asociado a una cuenta."""

        return self.sesion.execute(
            select(Docente).where(Docente.usuario_id == usuario_id)
        ).scalar_one_or_none()

    def obtener_docente_por_legajo(self, legajo: str) -> Docente | None:
        """Busca un docente por su legajo institucional."""

        return self.sesion.execute(
            select(Docente).where(Docente.legajo == legajo)
        ).scalar_one_or_none()

    def listar_docentes(self):
        """Lista todos los docentes ordenados por apellido y nombre."""

        return self.sesion.execute(
            select(Docente).order_by(Docente.apellidos, Docente.nombres)
        ).scalars().all()
