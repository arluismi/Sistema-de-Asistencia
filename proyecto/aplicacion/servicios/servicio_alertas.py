"""Servicio de consulta y gestión de alertas del tablero de control."""

from ..errores import ErrorNoEncontrado, ErrorProhibido
from ..modelos.enumeraciones import NombreRol
from ..presentadores import presentar_alerta
from ..repositorios import (
    RepositorioAlertas,
    RepositorioEstructuraAcademica,
    RepositorioUsuario,
)


class ServicioAlertas:
    """Consulta alertas y administra su estado de lectura."""

    def __init__(
        self,
        repositorio_alertas: RepositorioAlertas | None = None,
        repositorio_usuario: RepositorioUsuario | None = None,
        repositorio_estructura: RepositorioEstructuraAcademica | None = None,
    ):
        self.repositorio_alertas = repositorio_alertas or RepositorioAlertas()
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()
        self.repositorio_estructura = repositorio_estructura or RepositorioEstructuraAcademica()

    def listar_alertas(
        self,
        usuario_actual,
        estudiante_id: int | None = None,
        activa: bool | None = None,
        leida: bool | None = None,
    ) -> list[dict]:
        """Lista alertas aplicando las restricciones del rol docente."""

        estudiantes_permitidos = self._obtener_estudiantes_permitidos(usuario_actual)
        if (
            estudiante_id is not None
            and estudiantes_permitidos is not None
            and estudiante_id not in estudiantes_permitidos
        ):
            raise ErrorProhibido(
                "El estudiante consultado no pertenece a sus cursos asignados."
            )

        alertas = self.repositorio_alertas.listar_alertas(
            estudiante_id=estudiante_id, activa=activa, leida=leida
        )
        if estudiantes_permitidos is not None:
            alertas = [
                alerta
                for alerta in alertas
                if alerta.estudiante_id in estudiantes_permitidos
            ]
        return [presentar_alerta(alerta) for alerta in alertas]

    def marcar_alerta_leida(self, alerta_id: int, usuario_actual) -> dict:
        """Marca una alerta como leída tras verificar el acceso del usuario."""

        alerta = self.repositorio_alertas.obtener_por_id(alerta_id)
        if alerta is None:
            raise ErrorNoEncontrado("La alerta indicada no existe.")

        estudiantes_permitidos = self._obtener_estudiantes_permitidos(usuario_actual)
        if (
            estudiantes_permitidos is not None
            and alerta.estudiante_id not in estudiantes_permitidos
        ):
            raise ErrorProhibido(
                "La alerta pertenece a un estudiante fuera de sus cursos asignados."
            )

        alerta.leida = True
        self.repositorio_alertas.confirmar_cambios()
        return presentar_alerta(alerta)

    def _obtener_estudiantes_permitidos(self, usuario_actual) -> set[int] | None:
        """Devuelve los estudiantes visibles para un docente; `None` si ve todos."""

        if usuario_actual.rol.nombre != NombreRol.DOCENTE:
            return None

        docente = self.repositorio_usuario.obtener_docente_por_usuario_id(
            usuario_actual.id
        )
        if docente is None:
            raise ErrorProhibido("La cuenta docente no tiene un perfil asociado.")

        cursos_asignados = {
            asignacion.curso_id
            for asignacion in self.repositorio_estructura.listar_asignaciones(
                docente_id=docente.id
            )
        }
        estudiantes_permitidos = set()
        for curso_id in cursos_asignados:
            estudiantes_permitidos.update(
                estudiante.id
                for estudiante in self.repositorio_estructura.listar_estudiantes_de_curso(
                    curso_id
                )
            )
        return estudiantes_permitidos
