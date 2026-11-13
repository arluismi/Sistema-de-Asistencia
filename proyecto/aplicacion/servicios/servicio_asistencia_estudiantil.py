"""Servicio de asistencia estudiantil.

Implementa la carga diaria, el cálculo de porcentajes por estudiante y curso, y
la publicación de eventos para el sistema de alertas (patrón Observer).
"""

from ..errores import (
    ErrorConflicto,
    ErrorNoEncontrado,
    ErrorProhibido,
    ErrorValidacion,
)
from ..estrategias import obtener_estrategia_calculo_asistencia
from ..modelos import RegistroAsistenciaEstudiantil
from ..modelos.enumeraciones import EstadoInscripcion, NombreRol
from ..observadores import EventoAsistenciaRegistrada, publicador_eventos
from ..presentadores import (
    presentar_curso,
    presentar_estudiante,
    presentar_materia,
    presentar_periodo,
    presentar_registro_asistencia,
)
from ..repositorios import (
    RepositorioAsistenciaEstudiantil,
    RepositorioEstructuraAcademica,
    RepositorioParametrosInstitucionales,
    RepositorioUsuario,
)
from ..utilidades.tiempo import obtener_fecha_servidor
from ..utilidades.validadores import (
    obtener_cadena_opcional,
    obtener_entero_requerido,
    obtener_fecha_iso,
    obtener_lista_requerida,
    validar_estado_asistencia,
)


class ServicioAsistenciaEstudiantil:
    """Registra asistencia y calcula la situación de regularidad de los estudiantes."""

    def __init__(
        self,
        repositorio_asistencia: RepositorioAsistenciaEstudiantil | None = None,
        repositorio_estructura: RepositorioEstructuraAcademica | None = None,
        repositorio_usuario: RepositorioUsuario | None = None,
        repositorio_parametros: RepositorioParametrosInstitucionales | None = None,
        publicador=None,
    ):
        self.repositorio_asistencia = (
            repositorio_asistencia or RepositorioAsistenciaEstudiantil()
        )
        self.repositorio_estructura = (
            repositorio_estructura or RepositorioEstructuraAcademica()
        )
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()
        self.repositorio_parametros = (
            repositorio_parametros or RepositorioParametrosInstitucionales()
        )
        self.publicador = publicador or publicador_eventos

    # ------------------------------------------------------------------
    # Carga diaria
    # ------------------------------------------------------------------
    def registrar_carga_diaria(self, datos: dict, usuario_actual) -> dict:
        """Registra o actualiza la asistencia de varios estudiantes en una clase."""

        curso_id = obtener_entero_requerido(datos, "curso_id", valor_minimo=1)
        materia_id = obtener_entero_requerido(datos, "materia_id", valor_minimo=1)
        fecha = obtener_fecha_iso(datos, "fecha")
        registros_recibidos = obtener_lista_requerida(datos, "registros")

        curso = self.repositorio_estructura.obtener_curso(curso_id)
        if curso is None:
            raise ErrorNoEncontrado("El curso indicado no existe.")
        materia = self.repositorio_estructura.obtener_materia(materia_id)
        if materia is None:
            raise ErrorNoEncontrado("La materia indicada no existe.")
        if fecha > obtener_fecha_servidor():
            raise ErrorValidacion(
                "No se puede registrar asistencia de una fecha futura."
            )

        docente = self._obtener_docente_si_corresponde(usuario_actual)
        if docente is not None and not self.repositorio_estructura.existe_asignacion(
            docente.id, curso_id, materia_id
        ):
            raise ErrorProhibido(
                "No tiene asignada esa materia en el curso indicado para registrar asistencia."
            )

        registros_afectados = []
        estudiantes_procesados = set()
        creados = 0
        actualizados = 0

        for indice, elemento in enumerate(registros_recibidos):
            if not isinstance(elemento, dict):
                raise ErrorValidacion(
                    f"El registro en la posición {indice} debe ser un objeto JSON."
                )

            estudiante_id = obtener_entero_requerido(
                elemento, "estudiante_id", valor_minimo=1
            )
            if estudiante_id in estudiantes_procesados:
                raise ErrorValidacion(
                    f"El estudiante con id {estudiante_id} está repetido en la carga."
                )
            estudiantes_procesados.add(estudiante_id)

            estado = validar_estado_asistencia(elemento.get("estado"))
            observacion = obtener_cadena_opcional(
                elemento, "observacion", longitud_maxima=500
            )

            inscripcion = self.repositorio_estructura.obtener_inscripcion(
                estudiante_id, curso_id
            )
            if inscripcion is None or inscripcion.estado != EstadoInscripcion.ACTIVO:
                raise ErrorValidacion(
                    f"El estudiante con id {estudiante_id} no está matriculado "
                    f"activamente en el curso '{curso.nombre_completo}'."
                )

            registro = self.repositorio_asistencia.obtener_registro(
                estudiante_id, curso_id, materia_id, fecha
            )
            if registro is not None:
                registro.estado = estado
                registro.observacion = observacion
                registro.registrado_por_usuario_id = usuario_actual.id
                actualizados += 1
            else:
                registro = RegistroAsistenciaEstudiantil(
                    estudiante_id=estudiante_id,
                    curso_id=curso_id,
                    materia_id=materia_id,
                    fecha=fecha,
                    estado=estado,
                    observacion=observacion,
                    registrado_por_usuario_id=usuario_actual.id,
                )
                self.repositorio_asistencia.agregar(registro)
                creados += 1

            registros_afectados.append(registro)

        # `Session.flush` envía los cambios a la base sin cerrar la transacción,
        # de modo que los suscriptores del evento pueden consultar los registros.
        self.repositorio_asistencia.sesion.flush()

        for registro in registros_afectados:
            self.publicador.publicar(
                EventoAsistenciaRegistrada(
                    estudiante_id=registro.estudiante_id,
                    curso_id=registro.curso_id,
                    materia_id=registro.materia_id,
                    fecha=registro.fecha,
                    estado=registro.estado,
                )
            )

        self.repositorio_asistencia.confirmar_cambios()

        return {
            "creados": creados,
            "actualizados": actualizados,
            "registros": [
                presentar_registro_asistencia(registro)
                for registro in registros_afectados
            ],
        }

    # ------------------------------------------------------------------
    # Cálculos de asistencia
    # ------------------------------------------------------------------
    def calcular_resumen_estudiante(
        self,
        estudiante_id: int,
        curso_id: int | None = None,
        materia_id: int | None = None,
        periodo_id: int | None = None,
        estrategia: str | None = None,
    ) -> dict:
        """Calcula el resumen de asistencia de un estudiante."""

        estudiante = self.repositorio_usuario.obtener_estudiante_por_id(estudiante_id)
        if estudiante is None:
            raise ErrorNoEncontrado("El estudiante indicado no existe.")
        periodo = self._obtener_periodo_opcional(periodo_id)
        estrategia_calculo = self._resolver_estrategia(estrategia)

        registros = self.repositorio_asistencia.listar_registros(
            estudiante_id=estudiante_id,
            curso_id=curso_id,
            materia_id=materia_id,
            fecha_desde=periodo.fecha_inicio if periodo else None,
            fecha_hasta=periodo.fecha_fin if periodo else None,
        )

        umbral = self._obtener_umbral_regularidad()
        resumen = self._resumen_con_regularidad(
            estrategia_calculo.calcular(registros), umbral
        )

        registros_por_materia = {}
        for registro in registros:
            registros_por_materia.setdefault(registro.materia_id, []).append(registro)

        detalle_por_materia = []
        for materia_id_registro, registros_de_materia in sorted(
            registros_por_materia.items(),
            key=lambda elemento: elemento[1][0].materia.nombre,
        ):
            materia = self.repositorio_estructura.obtener_materia(materia_id_registro)
            detalle_por_materia.append(
                {
                    "materia": presentar_materia(materia) if materia else None,
                    "resumen": self._resumen_con_regularidad(
                        estrategia_calculo.calcular(registros_de_materia), umbral
                    ),
                }
            )

        return {
            "alcance": "estudiante",
            "estudiante": presentar_estudiante(estudiante),
            "periodo": presentar_periodo(periodo),
            "estrategia": estrategia_calculo.nombre,
            "resumen": resumen,
            "detalle_por_materia": detalle_por_materia,
        }

    def calcular_resumen_curso(
        self,
        curso_id: int,
        materia_id: int | None = None,
        periodo_id: int | None = None,
        estrategia: str | None = None,
    ) -> dict:
        """Calcula el resumen de asistencia de todos los estudiantes de un curso."""

        curso = self.repositorio_estructura.obtener_curso(curso_id)
        if curso is None:
            raise ErrorNoEncontrado("El curso indicado no existe.")
        periodo = self._obtener_periodo_opcional(periodo_id)
        estrategia_calculo = self._resolver_estrategia(estrategia)

        registros_del_curso = self.repositorio_asistencia.listar_registros(
            curso_id=curso_id,
            materia_id=materia_id,
            fecha_desde=periodo.fecha_inicio if periodo else None,
            fecha_hasta=periodo.fecha_fin if periodo else None,
        )

        registros_por_estudiante = {}
        for registro in registros_del_curso:
            registros_por_estudiante.setdefault(registro.estudiante_id, []).append(
                registro
            )

        umbral = self._obtener_umbral_regularidad()
        estudiantes = self.repositorio_estructura.listar_estudiantes_de_curso(curso_id)
        filas_estudiantes = []
        for estudiante in estudiantes:
            registros = registros_por_estudiante.get(estudiante.id, [])
            filas_estudiantes.append(
                {
                    "estudiante": presentar_estudiante(estudiante),
                    "resumen": self._resumen_con_regularidad(
                        estrategia_calculo.calcular(registros), umbral
                    ),
                }
            )

        return {
            "alcance": "curso",
            "curso": presentar_curso(curso),
            "periodo": presentar_periodo(periodo),
            "estrategia": estrategia_calculo.nombre,
            "resumen_general": self._resumen_con_regularidad(
                estrategia_calculo.calcular(registros_del_curso), umbral
            ),
            "estudiantes": filas_estudiantes,
        }

    def generar_resumen(self, filtros: dict, usuario_actual) -> dict:
        """Valida permisos y genera el resumen solicitado por el usuario."""

        estudiante_id = filtros.get("estudiante_id")
        curso_id = filtros.get("curso_id")
        materia_id = filtros.get("materia_id")
        periodo_id = filtros.get("periodo_id")
        estrategia = filtros.get("estrategia")

        rol_usuario = usuario_actual.rol.nombre
        if rol_usuario == NombreRol.ALUMNO:
            estudiante_propio = self._obtener_estudiante_de_usuario(usuario_actual)
            if estudiante_id is not None and estudiante_id != estudiante_propio.id:
                raise ErrorProhibido("Un alumno sólo puede consultar su propia asistencia.")
            if (
                curso_id is not None
                and self.repositorio_estructura.obtener_inscripcion(
                    estudiante_propio.id, curso_id
                )
                is None
            ):
                raise ErrorProhibido("No está matriculado en el curso consultado.")
            estudiante_id = estudiante_propio.id

        elif rol_usuario == NombreRol.DOCENTE:
            docente = self._obtener_docente_de_usuario(usuario_actual)
            if curso_id is not None:
                self._validar_asignacion_docente(docente, curso_id, materia_id)
            elif estudiante_id is not None:
                self._validar_docente_puede_ver_estudiante(docente, estudiante_id)

        if estudiante_id is None and curso_id is None:
            raise ErrorValidacion(
                "Debe indicar 'estudiante_id' o 'curso_id' para calcular el resumen."
            )

        if estudiante_id is not None:
            return self.calcular_resumen_estudiante(
                estudiante_id=estudiante_id,
                curso_id=curso_id,
                materia_id=materia_id,
                periodo_id=periodo_id,
                estrategia=estrategia,
            )

        return self.calcular_resumen_curso(
            curso_id=curso_id,
            materia_id=materia_id,
            periodo_id=periodo_id,
            estrategia=estrategia,
        )

    # ------------------------------------------------------------------
    # Consultas de registros
    # ------------------------------------------------------------------
    def listar_registros(self, filtros: dict, usuario_actual) -> list[dict]:
        """Lista registros de asistencia aplicando las restricciones por rol."""

        estudiante_id = filtros.get("estudiante_id")
        curso_id = filtros.get("curso_id")
        materia_id = filtros.get("materia_id")
        fecha = filtros.get("fecha")
        fecha_desde = filtros.get("fecha_desde")
        fecha_hasta = filtros.get("fecha_hasta")
        curso_ids = None

        rol_usuario = usuario_actual.rol.nombre
        if rol_usuario == NombreRol.ALUMNO:
            estudiante_propio = self._obtener_estudiante_de_usuario(usuario_actual)
            if estudiante_id is not None and estudiante_id != estudiante_propio.id:
                raise ErrorProhibido("Un alumno sólo puede consultar su propia asistencia.")
            estudiante_id = estudiante_propio.id

        elif rol_usuario == NombreRol.DOCENTE:
            docente = self._obtener_docente_de_usuario(usuario_actual)
            if curso_id is not None:
                self._validar_asignacion_docente(docente, curso_id, materia_id)
            else:
                curso_ids = [
                    asignacion.curso_id
                    for asignacion in self.repositorio_estructura.listar_asignaciones(
                        docente_id=docente.id
                    )
                ]
                if not curso_ids:
                    return []

        registros = self.repositorio_asistencia.listar_registros(
            estudiante_id=estudiante_id,
            curso_id=curso_id,
            materia_id=materia_id,
            fecha=fecha,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            curso_ids=curso_ids,
        )
        return [presentar_registro_asistencia(registro) for registro in registros]

    # ------------------------------------------------------------------
    # Ayudantes internos
    # ------------------------------------------------------------------
    def _obtener_docente_si_corresponde(self, usuario_actual):
        """Devuelve el perfil docente si el usuario tiene ese rol; si no, `None`."""

        if usuario_actual.rol.nombre != NombreRol.DOCENTE:
            return None
        return self._obtener_docente_de_usuario(usuario_actual)

    def _obtener_docente_de_usuario(self, usuario_actual):
        """Obtiene el perfil docente asociado a la cuenta autenticada."""

        docente = self.repositorio_usuario.obtener_docente_por_usuario_id(
            usuario_actual.id
        )
        if docente is None:
            raise ErrorProhibido("La cuenta docente no tiene un perfil asociado.")
        return docente

    def _obtener_estudiante_de_usuario(self, usuario_actual):
        """Obtiene el perfil de estudiante asociado a la cuenta autenticada."""

        estudiante = self.repositorio_usuario.obtener_estudiante_por_usuario_id(
            usuario_actual.id
        )
        if estudiante is None:
            raise ErrorProhibido("La cuenta de alumno no tiene un perfil asociado.")
        return estudiante

    def _validar_asignacion_docente(
        self, docente, curso_id: int, materia_id: int | None = None
    ) -> None:
        """Verifica que el docente dicte clase en el curso y materia consultados."""

        if not self.repositorio_estructura.existe_asignacion(
            docente.id, curso_id, materia_id
        ):
            raise ErrorProhibido(
                "No tiene asignada la materia o el curso consultado."
            )

    def _validar_docente_puede_ver_estudiante(self, docente, estudiante_id: int) -> None:
        """Verifica que el estudiante pertenezca a algún curso del docente."""

        cursos_asignados = {
            asignacion.curso_id
            for asignacion in self.repositorio_estructura.listar_asignaciones(
                docente_id=docente.id
            )
        }
        inscripciones = self.repositorio_estructura.listar_inscripciones(
            estudiante_id=estudiante_id
        )
        if not any(
            inscripcion.curso_id in cursos_asignados for inscripcion in inscripciones
        ):
            raise ErrorProhibido(
                "El estudiante no pertenece a ninguno de los cursos que usted dicta."
            )

    def _obtener_periodo_opcional(self, periodo_id: int | None):
        """Busca un período académico si se recibió su identificador."""

        if periodo_id is None:
            return None
        periodo = self.repositorio_estructura.obtener_periodo(periodo_id)
        if periodo is None:
            raise ErrorNoEncontrado("El período académico indicado no existe.")
        return periodo

    def _resolver_estrategia(self, nombre_estrategia: str | None):
        """Selecciona la estrategia explícita o la configurada institucionalmente."""

        parametro = self.repositorio_parametros.obtener_por_clave(
            "estrategia_calculo_asistencia"
        )
        nombre = nombre_estrategia or (parametro.valor if parametro else None)
        return obtener_estrategia_calculo_asistencia(nombre)

    def _obtener_umbral_regularidad(self) -> int:
        """Lee el umbral de regularidad desde los parámetros institucionales."""

        parametro = self.repositorio_parametros.obtener_por_clave(
            "umbral_regularidad_porcentaje"
        )
        if parametro is None:
            raise ErrorConflicto(
                "Falta inicializar el parámetro 'umbral_regularidad_porcentaje'."
            )
        return int(parametro.valor)

    @staticmethod
    def _resumen_con_regularidad(resumen, umbral: int) -> dict:
        """Agrega al resumen el estado de regularidad según el umbral institucional."""

        datos = resumen.como_diccionario()
        if datos["total_registros"] == 0:
            estado = "Sin datos"
        elif datos["porcentaje_asistencia"] >= umbral:
            estado = "Regular"
        else:
            estado = "En riesgo"

        datos["umbral_regularidad_porcentaje"] = umbral
        datos["estado_regularidad"] = estado
        return datos
