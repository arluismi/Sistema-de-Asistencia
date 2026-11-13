"""Servicio de estructura académica: cursos, materias, períodos, matrículas y grillas."""

from ..errores import ErrorConflicto, ErrorNoEncontrado, ErrorValidacion
from ..modelos import (
    AsignacionDocenteMateria,
    Curso,
    GrillaHorariaInstitucional,
    InscripcionEstudianteCurso,
    Materia,
    PeriodoAcademico,
)
from ..modelos.enumeraciones import EstadoInscripcion
from ..presentadores import (
    presentar_asignacion,
    presentar_curso,
    presentar_grilla_horaria,
    presentar_inscripcion,
    presentar_materia,
    presentar_periodo,
)
from ..repositorios import RepositorioEstructuraAcademica, RepositorioUsuario
from ..utilidades.tiempo import obtener_fecha_servidor
from ..utilidades.validadores import (
    obtener_cadena_opcional,
    obtener_cadena_requerida,
    obtener_entero_requerido,
    obtener_fecha_iso,
    obtener_hora_requerida,
)


class ServicioEstructuraAcademica:
    """Administra la estructura sobre la que se registran asistencias."""

    def __init__(
        self,
        repositorio_estructura: RepositorioEstructuraAcademica | None = None,
        repositorio_usuario: RepositorioUsuario | None = None,
    ):
        self.repositorio_estructura = (
            repositorio_estructura or RepositorioEstructuraAcademica()
        )
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()

    # ------------------------------------------------------------------
    # Cursos
    # ------------------------------------------------------------------
    def crear_curso(self, datos: dict) -> dict:
        """Crea un curso para un año lectivo."""

        nombre = obtener_cadena_requerida(datos, "nombre", longitud_maxima=80)
        division = obtener_cadena_requerida(datos, "division", longitud_maxima=20)
        anio_lectivo = obtener_entero_requerido(
            datos, "anio_lectivo", valor_minimo=2000, valor_maximo=2200
        )
        turno = obtener_cadena_requerida(datos, "turno", longitud_maxima=40)

        existe = any(
            curso.nombre == nombre
            and curso.division == division
            and curso.anio_lectivo == anio_lectivo
            for curso in self.repositorio_estructura.listar_cursos(anio_lectivo)
        )
        if existe:
            raise ErrorConflicto(
                f"El curso '{nombre} {division}' ya existe para el año {anio_lectivo}."
            )

        curso = Curso(
            nombre=nombre,
            division=division,
            anio_lectivo=anio_lectivo,
            turno=turno,
        )
        self.repositorio_estructura.agregar(curso)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_curso(curso)

    def listar_cursos(self, anio_lectivo: int | None = None) -> list[dict]:
        """Lista cursos, opcionalmente filtrados por año lectivo."""

        return [
            presentar_curso(curso)
            for curso in self.repositorio_estructura.listar_cursos(anio_lectivo)
        ]

    # ------------------------------------------------------------------
    # Materias
    # ------------------------------------------------------------------
    def crear_materia(self, datos: dict) -> dict:
        """Crea una materia con nombre y código únicos."""

        nombre = obtener_cadena_requerida(datos, "nombre", longitud_maxima=120)
        codigo = obtener_cadena_requerida(datos, "codigo", longitud_maxima=30)

        materias = self.repositorio_estructura.listar_materias()
        if any(materia.nombre == nombre for materia in materias):
            raise ErrorConflicto(f"Ya existe una materia con el nombre '{nombre}'.")
        if any(materia.codigo == codigo for materia in materias):
            raise ErrorConflicto(f"Ya existe una materia con el código '{codigo}'.")

        materia = Materia(nombre=nombre, codigo=codigo)
        self.repositorio_estructura.agregar(materia)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_materia(materia)

    def listar_materias(self) -> list[dict]:
        """Lista todas las materias."""

        return [
            presentar_materia(materia)
            for materia in self.repositorio_estructura.listar_materias()
        ]

    # ------------------------------------------------------------------
    # Períodos académicos
    # ------------------------------------------------------------------
    def crear_periodo(self, datos: dict) -> dict:
        """Crea un período académico con fechas inclusivas."""

        nombre = obtener_cadena_requerida(datos, "nombre", longitud_maxima=100)
        fecha_inicio = obtener_fecha_iso(datos, "fecha_inicio")
        fecha_fin = obtener_fecha_iso(datos, "fecha_fin")
        anio_lectivo = obtener_entero_requerido(
            datos, "anio_lectivo", valor_minimo=2000, valor_maximo=2200
        )

        if fecha_fin < fecha_inicio:
            raise ErrorValidacion("La fecha final no puede ser anterior a la fecha inicial.")
        if any(
            periodo.nombre == nombre and periodo.anio_lectivo == anio_lectivo
            for periodo in self.repositorio_estructura.listar_periodos(anio_lectivo)
        ):
            raise ErrorConflicto(
                f"El período '{nombre}' ya existe para el año {anio_lectivo}."
            )

        periodo = PeriodoAcademico(
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            anio_lectivo=anio_lectivo,
        )
        self.repositorio_estructura.agregar(periodo)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_periodo(periodo)

    def listar_periodos(self, anio_lectivo: int | None = None) -> list[dict]:
        """Lista períodos académicos."""

        return [
            presentar_periodo(periodo)
            for periodo in self.repositorio_estructura.listar_periodos(anio_lectivo)
        ]

    # ------------------------------------------------------------------
    # Matrículas
    # ------------------------------------------------------------------
    def crear_inscripcion(self, datos: dict) -> dict:
        """Matricula a un estudiante en un curso."""

        estudiante_id = obtener_entero_requerido(datos, "estudiante_id", valor_minimo=1)
        curso_id = obtener_entero_requerido(datos, "curso_id", valor_minimo=1)
        fecha_inscripcion = obtener_fecha_iso(
            datos, "fecha_inscripcion", requerida=False
        ) or obtener_fecha_servidor()
        estado = self._interpretar_estado_inscripcion(datos.get("estado"))

        estudiante = self.repositorio_usuario.obtener_estudiante_por_id(estudiante_id)
        if estudiante is None:
            raise ErrorNoEncontrado("El estudiante indicado no existe.")
        curso = self.repositorio_estructura.obtener_curso(curso_id)
        if curso is None:
            raise ErrorNoEncontrado("El curso indicado no existe.")
        if (
            self.repositorio_estructura.obtener_inscripcion(estudiante_id, curso_id)
            is not None
        ):
            raise ErrorConflicto("El estudiante ya está inscripto en ese curso.")

        inscripcion = InscripcionEstudianteCurso(
            estudiante=estudiante,
            curso=curso,
            fecha_inscripcion=fecha_inscripcion,
            estado=estado,
        )
        self.repositorio_estructura.agregar(inscripcion)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_inscripcion(inscripcion)

    def listar_inscripciones(
        self, curso_id: int | None = None, estudiante_id: int | None = None
    ) -> list[dict]:
        """Lista matrículas con filtros opcionales."""

        return [
            presentar_inscripcion(inscripcion)
            for inscripcion in self.repositorio_estructura.listar_inscripciones(
                curso_id=curso_id, estudiante_id=estudiante_id
            )
        ]

    # ------------------------------------------------------------------
    # Asignaciones docentes
    # ------------------------------------------------------------------
    def crear_asignacion(self, datos: dict) -> dict:
        """Asigna un docente para dictar una materia en un curso."""

        docente_id = obtener_entero_requerido(datos, "docente_id", valor_minimo=1)
        curso_id = obtener_entero_requerido(datos, "curso_id", valor_minimo=1)
        materia_id = obtener_entero_requerido(datos, "materia_id", valor_minimo=1)

        docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
        if docente is None:
            raise ErrorNoEncontrado("El docente indicado no existe.")
        curso = self.repositorio_estructura.obtener_curso(curso_id)
        if curso is None:
            raise ErrorNoEncontrado("El curso indicado no existe.")
        materia = self.repositorio_estructura.obtener_materia(materia_id)
        if materia is None:
            raise ErrorNoEncontrado("La materia indicada no existe.")
        if self.repositorio_estructura.listar_asignaciones(
            docente_id=docente_id, curso_id=curso_id, materia_id=materia_id
        ):
            raise ErrorConflicto("Esa asignación docente ya existe.")

        asignacion = AsignacionDocenteMateria(
            docente=docente,
            curso=curso,
            materia=materia,
        )
        self.repositorio_estructura.agregar(asignacion)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_asignacion(asignacion)

    def listar_asignaciones(
        self,
        docente_id: int | None = None,
        curso_id: int | None = None,
        materia_id: int | None = None,
    ) -> list[dict]:
        """Lista asignaciones docente-materia-curso."""

        return [
            presentar_asignacion(asignacion)
            for asignacion in self.repositorio_estructura.listar_asignaciones(
                docente_id=docente_id, curso_id=curso_id, materia_id=materia_id
            )
        ]

    # ------------------------------------------------------------------
    # Grilla horaria
    # ------------------------------------------------------------------
    def crear_grilla_horaria(self, datos: dict) -> dict:
        """Crea un bloque de la grilla horaria institucional."""

        curso_id = obtener_entero_requerido(datos, "curso_id", valor_minimo=1)
        materia_id = obtener_entero_requerido(datos, "materia_id", valor_minimo=1)
        docente_id = obtener_entero_requerido(datos, "docente_id", valor_minimo=1)
        dia_semana = obtener_entero_requerido(
            datos, "dia_semana", valor_minimo=1, valor_maximo=7
        )
        hora_inicio = obtener_hora_requerida(datos, "hora_inicio")
        hora_fin = obtener_hora_requerida(datos, "hora_fin")
        aula = obtener_cadena_opcional(datos, "aula", longitud_maxima=60)

        if hora_inicio >= hora_fin:
            raise ErrorValidacion("La hora de inicio debe ser anterior a la hora de fin.")

        curso = self.repositorio_estructura.obtener_curso(curso_id)
        if curso is None:
            raise ErrorNoEncontrado("El curso indicado no existe.")
        materia = self.repositorio_estructura.obtener_materia(materia_id)
        if materia is None:
            raise ErrorNoEncontrado("La materia indicada no existe.")
        docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
        if docente is None:
            raise ErrorNoEncontrado("El docente indicado no existe.")
        if not self.repositorio_estructura.existe_asignacion(
            docente_id=docente_id, curso_id=curso_id, materia_id=materia_id
        ):
            raise ErrorValidacion(
                "El docente no tiene una asignación para esa materia y curso. "
                "Cree primero la asignación docente."
            )

        bloques_del_docente = self.repositorio_estructura.listar_grillas(
            docente_id=docente_id, dia_semana=dia_semana
        )
        if any(bloque.hora_inicio == hora_inicio for bloque in bloques_del_docente):
            raise ErrorConflicto("El docente ya tiene un bloque horario a esa hora.")
        bloques_del_curso = self.repositorio_estructura.listar_grillas(
            curso_id=curso_id, dia_semana=dia_semana
        )
        if any(bloque.hora_inicio == hora_inicio for bloque in bloques_del_curso):
            raise ErrorConflicto("El curso ya tiene un bloque horario a esa hora.")

        grilla = GrillaHorariaInstitucional(
            curso=curso,
            materia=materia,
            docente=docente,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            aula=aula,
        )
        self.repositorio_estructura.agregar(grilla)
        self.repositorio_estructura.confirmar_cambios()
        return presentar_grilla_horaria(grilla)

    def listar_grillas_horarias(
        self,
        docente_id: int | None = None,
        curso_id: int | None = None,
        materia_id: int | None = None,
        anio_lectivo: int | None = None,
        dia_semana: int | None = None,
    ) -> list[dict]:
        """Lista bloques horarios con filtros opcionales."""

        return [
            presentar_grilla_horaria(grilla)
            for grilla in self.repositorio_estructura.listar_grillas(
                docente_id=docente_id,
                curso_id=curso_id,
                materia_id=materia_id,
                anio_lectivo=anio_lectivo,
                dia_semana=dia_semana,
            )
        ]

    @staticmethod
    def _interpretar_estado_inscripcion(valor) -> EstadoInscripcion:
        """Convierte el estado recibido en un valor de matrícula admitido."""

        if valor is None:
            return EstadoInscripcion.ACTIVO
        for estado in EstadoInscripcion:
            if estado.value.lower() == str(valor).strip().lower():
                return estado
        raise ErrorValidacion(
            "Estado de inscripción inválido.",
            detalles={
                "estados_permitidos": [estado.value for estado in EstadoInscripcion]
            },
        )
