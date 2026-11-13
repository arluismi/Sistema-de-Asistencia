"""Modelos de usuarios, estudiantes y docentes."""

from ..extenciones import base_de_datos
from .base import ModeloBase


class Usuario(ModeloBase):
    """Cuenta de acceso al sistema.

    La contraseña nunca se almacena en texto plano: `hash_contrasena` contiene el
    resultado de `werkzeug.security.generate_password_hash`.
    """

    __tablename__ = "usuarios"

    nombre_usuario = base_de_datos.Column(
        base_de_datos.String(80), nullable=False, unique=True, index=True
    )
    correo_electronico = base_de_datos.Column(
        base_de_datos.String(255), nullable=False, unique=True
    )
    hash_contrasena = base_de_datos.Column(base_de_datos.String(255), nullable=False)
    rol_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    activo = base_de_datos.Column(base_de_datos.Boolean, nullable=False, default=True)

    rol = base_de_datos.relationship("Rol", back_populates="usuarios", lazy="joined")
    estudiante = base_de_datos.relationship(
        "Estudiante", back_populates="usuario", uselist=False
    )
    docente = base_de_datos.relationship(
        "Docente", back_populates="usuario", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.nombre_usuario}>"


class Estudiante(ModeloBase):
    """Datos académicos de un estudiante, vinculados a una cuenta de usuario."""

    __tablename__ = "estudiantes"

    usuario_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    legajo = base_de_datos.Column(
        base_de_datos.String(30), nullable=False, unique=True, index=True
    )
    nombres = base_de_datos.Column(base_de_datos.String(120), nullable=False)
    apellidos = base_de_datos.Column(base_de_datos.String(120), nullable=False)
    fecha_nacimiento = base_de_datos.Column(base_de_datos.Date, nullable=True)

    usuario = base_de_datos.relationship("Usuario", back_populates="estudiante", lazy="joined")
    inscripciones = base_de_datos.relationship(
        "InscripcionEstudianteCurso", back_populates="estudiante"
    )
    registros_asistencia = base_de_datos.relationship(
        "RegistroAsistenciaEstudiantil", back_populates="estudiante"
    )
    alertas = base_de_datos.relationship("AlertaAsistencia", back_populates="estudiante")

    @property
    def nombre_completo(self) -> str:
        """Devuelve el nombre y apellido en el orden usado por los reportes."""

        return f"{self.apellidos}, {self.nombres}"

    def __repr__(self) -> str:
        return f"<Estudiante {self.legajo}>"


class Docente(ModeloBase):
    """Datos laborales de un docente, vinculados a una cuenta de usuario."""

    __tablename__ = "docentes"

    usuario_id = base_de_datos.Column(
        base_de_datos.Integer,
        base_de_datos.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    legajo = base_de_datos.Column(
        base_de_datos.String(30), nullable=False, unique=True, index=True
    )
    nombres = base_de_datos.Column(base_de_datos.String(120), nullable=False)
    apellidos = base_de_datos.Column(base_de_datos.String(120), nullable=False)
    titulo_habilitante = base_de_datos.Column(base_de_datos.String(255), nullable=True)

    usuario = base_de_datos.relationship("Usuario", back_populates="docente", lazy="joined")
    asignaciones = base_de_datos.relationship(
        "AsignacionDocenteMateria", back_populates="docente"
    )
    grillas_horarias = base_de_datos.relationship(
        "GrillaHorariaInstitucional", back_populates="docente"
    )
    firmas_asistencia = base_de_datos.relationship(
        "FirmaAsistencia", back_populates="docente"
    )
    incidencias = base_de_datos.relationship(
        "IncidenciaHoraria", back_populates="docente"
    )

    @property
    def nombre_completo(self) -> str:
        """Devuelve el nombre y apellido en el orden usado por los reportes."""

        return f"{self.apellidos}, {self.nombres}"

    def __repr__(self) -> str:
        return f"<Docente {self.legajo}>"
