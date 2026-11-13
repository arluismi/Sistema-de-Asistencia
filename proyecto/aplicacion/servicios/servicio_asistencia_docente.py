"""Servicio de asistencia y puntualidad del personal docente."""

from datetime import datetime

from ..errores import (
    ErrorConflicto,
    ErrorNoEncontrado,
    ErrorProhibido,
    ErrorValidacion,
)
from ..estrategias import obtener_estrategia_balance_horas
from ..modelos import FirmaAsistencia, IncidenciaHoraria
from ..modelos.enumeraciones import NombreRol, TipoFirma, TipoIncidencia
from ..presentadores import (
    presentar_docente,
    presentar_firma_asistencia,
    presentar_incidencia,
    presentar_periodo,
)
from ..repositorios import (
    RepositorioAsistenciaDocente,
    RepositorioEstructuraAcademica,
    RepositorioParametrosInstitucionales,
    RepositorioUsuario,
)
from ..utilidades.tiempo import (
    calcular_minutos_entre,
    obtener_fecha_servidor,
    obtener_marca_temporal_servidor,
)
from ..utilidades.validadores import (
    obtener_cadena_requerida,
    obtener_entero_requerido,
    obtener_entero_opcional,
    obtener_fecha_iso,
    validar_tipo_firma,
)


class ServicioAsistenciaDocente:
    """Gestiona firmas, incidencias y balance de horas cátedra docentes."""

    def __init__(
        self,
        repositorio_asistencia_docente: RepositorioAsistenciaDocente | None = None,
        repositorio_estructura: RepositorioEstructuraAcademica | None = None,
        repositorio_usuario: RepositorioUsuario | None = None,
        repositorio_parametros: RepositorioParametrosInstitucionales | None = None,
    ):
        self.repositorio_asistencia_docente = (
            repositorio_asistencia_docente or RepositorioAsistenciaDocente()
        )
        self.repositorio_estructura = (
            repositorio_estructura or RepositorioEstructuraAcademica()
        )
        self.repositorio_usuario = repositorio_usuario or RepositorioUsuario()
        self.repositorio_parametros = (
            repositorio_parametros or RepositorioParametrosInstitucionales()
        )

    # ------------------------------------------------------------------
    # Firmas de ingreso y egreso
    # ------------------------------------------------------------------
    def registrar_firma(self, datos: dict, usuario_actual) -> dict:
        """Registra una firma docente con la marca de tiempo del servidor."""

        tipo_firma = validar_tipo_firma(datos.get("tipo_firma"))
        grilla_horaria_id = obtener_entero_requerido(
            datos, "grilla_horaria_id", valor_minimo=1
        )
        grilla_horaria = self.repositorio_estructura.obtener_grilla(
            grilla_horaria_id
        )
        if grilla_horaria is None:
            raise ErrorNoEncontrado("El bloque de grilla horaria indicado no existe.")

        docente = self._resolver_docente_para_firma(datos, usuario_actual)
        if grilla_horaria.docente_id != docente.id:
            raise ErrorProhibido("El bloque horario no pertenece al docente indicado.")

        # La marca de tiempo se obtiene exclusivamente del reloj del servidor.
        marca_temporal = obtener_marca_temporal_servidor()
        fecha = marca_temporal.date()

        if fecha.isoweekday() != grilla_horaria.dia_semana:
            raise ErrorValidacion(
                "El bloque de grilla seleccionado no corresponde al día actual."
            )

        firma_existente = self.repositorio_asistencia_docente.obtener_firma(
            docente_id=docente.id,
            grilla_horaria_id=grilla_horaria.id,
            fecha=fecha,
            tipo_firma=tipo_firma,
        )
        if firma_existente is not None:
            raise ErrorConflicto(
                f"Ya existe una firma de {tipo_firma.value.lower()} para este bloque hoy."
            )

        firma_ingreso = self.repositorio_asistencia_docente.obtener_firma(
            docente_id=docente.id,
            grilla_horaria_id=grilla_horaria.id,
            fecha=fecha,
            tipo_firma=TipoFirma.INGRESO,
        )
        if tipo_firma == TipoFirma.EGRESO:
            if firma_ingreso is None:
                raise ErrorConflicto(
                    "Debe registrar la firma de ingreso antes de la firma de egreso."
                )
            if marca_temporal < firma_ingreso.marca_temporal:
                raise ErrorConflicto(
                    "La marca de egreso no puede ser anterior a la marca de ingreso."
                )

        firma = FirmaAsistencia(
            docente_id=docente.id,
            grilla_horaria_id=grilla_horaria.id,
            tipo_firma=tipo_firma,
            fecha=fecha,
            marca_temporal=marca_temporal,
            registrado_por_usuario_id=usuario_actual.id,
        )
        self.repositorio_asistencia_docente.agregar(firma)
        self.repositorio_asistencia_docente.sesion.flush()

        incidencia = self._evaluar_desviacion_horaria(
            firma=firma,
            grilla_horaria=grilla_horaria,
            marca_temporal=marca_temporal,
            usuario_actual=usuario_actual,
        )
        if incidencia is not None:
            self.repositorio_asistencia_docente.agregar(incidencia)

        self.repositorio_asistencia_docente.confirmar_cambios()

        return {
            "firma": presentar_firma_asistencia(firma),
            "incidencia": presentar_incidencia(incidencia)
            if incidencia is not None
            else None,
        }

    def listar_firmas(
        self,
        usuario_actual,
        docente_id: int | None = None,
        fecha_desde=None,
        fecha_hasta=None,
    ) -> list[dict]:
        """Lista firmas respetando que un docente sólo vea las propias."""

        docente_id = self._resolver_filtro_docente(usuario_actual, docente_id)
        firmas = self.repositorio_asistencia_docente.listar_firmas(
            docente_id=docente_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return [presentar_firma_asistencia(firma) for firma in firmas]

    def listar_incidencias(
        self,
        usuario_actual,
        docente_id: int | None = None,
        fecha_desde=None,
        fecha_hasta=None,
        tipo=None,
    ) -> list[dict]:
        """Lista incidencias horarias con las restricciones del rol docente."""

        docente_id = self._resolver_filtro_docente(usuario_actual, docente_id)
        incidencias = self.repositorio_asistencia_docente.listar_incidencias(
            docente_id=docente_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo=tipo,
        )
        return [presentar_incidencia(incidencia) for incidencia in incidencias]

    def registrar_licencia(self, datos: dict, usuario_actual) -> dict:
        """Registra una licencia docente como incidencia no automática."""

        docente_id = obtener_entero_requerido(datos, "docente_id", valor_minimo=1)
        fecha = obtener_fecha_iso(datos, "fecha")
        motivo = obtener_cadena_requerida(datos, "motivo", longitud_maxima=500)
        grilla_horaria_id = obtener_entero_opcional(
            datos, "grilla_horaria_id", valor_minimo=1
        )

        docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
        if docente is None:
            raise ErrorNoEncontrado("El docente indicado no existe.")

        if grilla_horaria_id is not None:
            grilla_horaria = self.repositorio_estructura.obtener_grilla(
                grilla_horaria_id
            )
            if grilla_horaria is None:
                raise ErrorNoEncontrado("El bloque de grilla horaria indicado no existe.")
            if grilla_horaria.docente_id != docente.id:
                raise ErrorValidacion(
                    "El bloque horario indicado no pertenece al docente."
                )

        licencias_existentes = self.repositorio_asistencia_docente.listar_incidencias(
            docente_id=docente_id,
            fecha_desde=fecha,
            fecha_hasta=fecha,
            tipo=TipoIncidencia.LICENCIA,
        )
        if licencias_existentes:
            raise ErrorConflicto("Ya existe una licencia registrada para esa fecha.")

        incidencia = IncidenciaHoraria(
            docente_id=docente_id,
            grilla_horaria_id=grilla_horaria_id,
            tipo=TipoIncidencia.LICENCIA,
            fecha=fecha,
            minutos_desviacion=0,
            descripcion=motivo,
            generada_automaticamente=False,
            registrado_por_usuario_id=usuario_actual.id,
        )
        self.repositorio_asistencia_docente.agregar(incidencia)
        self.repositorio_asistencia_docente.confirmar_cambios()
        return presentar_incidencia(incidencia)

    # ------------------------------------------------------------------
    # Balance de horas cátedra
    # ------------------------------------------------------------------
    def calcular_balances(
        self,
        periodo_id: int | None = None,
        docente_id: int | None = None,
        estrategia: str | None = None,
    ) -> dict:
        """Calcula el balance de horas cátedra para un docente o para todos."""

        periodo = self._resolver_periodo(periodo_id)
        minutos_hora_catedra = self._obtener_minutos_hora_catedra()
        estrategia_calculo = self._resolver_estrategia_horas(estrategia)

        if docente_id is not None:
            docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
            if docente is None:
                raise ErrorNoEncontrado("El docente indicado no existe.")
            docentes = [docente]
        else:
            docentes = self.repositorio_usuario.listar_docentes()

        balances = []
        for docente in docentes:
            grillas_horarias = self.repositorio_asistencia_docente.listar_grillas(
                docente_id=docente.id, anio_lectivo=periodo.anio_lectivo
            )
            firmas_asistencia = self.repositorio_asistencia_docente.listar_firmas(
                docente_id=docente.id,
                fecha_desde=periodo.fecha_inicio,
                fecha_hasta=periodo.fecha_fin,
            )
            balance = estrategia_calculo.calcular(
                grillas_horarias=grillas_horarias,
                firmas_asistencia=firmas_asistencia,
                fecha_inicio=periodo.fecha_inicio,
                fecha_fin=periodo.fecha_fin,
                minutos_hora_catedra=minutos_hora_catedra,
            )
            balances.append(
                {
                    "docente": presentar_docente(docente),
                    "balance": balance,
                }
            )

        return {
            "periodo": presentar_periodo(periodo),
            "balances": balances,
        }

    def obtener_balance(
        self,
        usuario_actual,
        docente_id: int | None = None,
        periodo_id: int | None = None,
        estrategia: str | None = None,
    ) -> dict:
        """Devuelve el balance aplicando las restricciones del rol autenticado."""

        if usuario_actual.rol.nombre == NombreRol.DOCENTE:
            docente = self._obtener_docente_de_usuario(usuario_actual)
            if docente_id is not None and docente_id != docente.id:
                raise ErrorProhibido(
                    "Un docente sólo puede consultar su propio balance de horas."
                )
            docente_id = docente.id
        elif docente_id is not None:
            docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
            if docente is None:
                raise ErrorNoEncontrado("El docente indicado no existe.")

        return self.calcular_balances(
            periodo_id=periodo_id,
            docente_id=docente_id,
            estrategia=estrategia,
        )

    # ------------------------------------------------------------------
    # Ayudantes internos
    # ------------------------------------------------------------------
    def _resolver_docente_para_firma(self, datos: dict, usuario_actual):
        """Determina sobre qué docente se registra la firma."""

        if usuario_actual.rol.nombre == NombreRol.DOCENTE:
            docente = self._obtener_docente_de_usuario(usuario_actual)
            if datos.get("docente_id") is not None:
                docente_id_solicitado = obtener_entero_requerido(
                    datos, "docente_id", valor_minimo=1
                )
                if docente_id_solicitado != docente.id:
                    raise ErrorProhibido(
                        "Un docente sólo puede firmar su propia asistencia."
                    )
            return docente

        docente_id = obtener_entero_requerido(datos, "docente_id", valor_minimo=1)
        docente = self.repositorio_usuario.obtener_docente_por_id(docente_id)
        if docente is None:
            raise ErrorNoEncontrado("El docente indicado no existe.")
        return docente

    def _resolver_filtro_docente(self, usuario_actual, docente_id: int | None):
        """Fuerza el identificador propio cuando el usuario es docente."""

        if usuario_actual.rol.nombre == NombreRol.DOCENTE:
            docente = self._obtener_docente_de_usuario(usuario_actual)
            if docente_id is not None and docente_id != docente.id:
                raise ErrorProhibido(
                    "Un docente sólo puede consultar su propia asistencia."
                )
            return docente.id

        if docente_id is not None:
            if self.repositorio_usuario.obtener_docente_por_id(docente_id) is None:
                raise ErrorNoEncontrado("El docente indicado no existe.")
        return docente_id

    def _obtener_docente_de_usuario(self, usuario_actual):
        """Obtiene el perfil docente de la cuenta autenticada."""

        docente = self.repositorio_usuario.obtener_docente_por_usuario_id(
            usuario_actual.id
        )
        if docente is None:
            raise ErrorProhibido("La cuenta docente no tiene un perfil asociado.")
        return docente

    def _evaluar_desviacion_horaria(
        self,
        firma: FirmaAsistencia,
        grilla_horaria,
        marca_temporal: datetime,
        usuario_actual,
    ):
        """Detecta tardanzas o salidas anticipadas y construye la incidencia."""

        tolerancia_minutos = self._obtener_tolerancia_minutos_firma()
        fecha = firma.fecha

        if firma.tipo_firma == TipoFirma.INGRESO:
            inicio_programado = datetime.combine(fecha, grilla_horaria.hora_inicio)
            minutos_de_tardanza = calcular_minutos_entre(
                inicio_programado, marca_temporal
            )
            if minutos_de_tardanza <= tolerancia_minutos:
                return None

            return IncidenciaHoraria(
                docente_id=firma.docente_id,
                grilla_horaria_id=grilla_horaria.id,
                firma_asistencia=firma,
                tipo=TipoIncidencia.TARDANZA,
                fecha=fecha,
                minutos_desviacion=minutos_de_tardanza,
                descripcion=(
                    f"Tardanza de {minutos_de_tardanza} minutos en el ingreso "
                    f"correspondiente a {grilla_horaria.materia.nombre} "
                    f"({grilla_horaria.curso.nombre_completo})."
                ),
                generada_automaticamente=True,
                registrado_por_usuario_id=usuario_actual.id,
            )

        fin_programado = datetime.combine(fecha, grilla_horaria.hora_fin)
        minutos_de_salida_anticipada = calcular_minutos_entre(
            marca_temporal, fin_programado
        )
        if minutos_de_salida_anticipada <= tolerancia_minutos:
            return None

        return IncidenciaHoraria(
            docente_id=firma.docente_id,
            grilla_horaria_id=grilla_horaria.id,
            firma_asistencia=firma,
            tipo=TipoIncidencia.SALIDA_ANTICIPADA,
            fecha=fecha,
            minutos_desviacion=minutos_de_salida_anticipada,
            descripcion=(
                f"Salida anticipada de {minutos_de_salida_anticipada} minutos "
                f"correspondiente a {grilla_horaria.materia.nombre} "
                f"({grilla_horaria.curso.nombre_completo})."
            ),
            generada_automaticamente=True,
            registrado_por_usuario_id=usuario_actual.id,
        )

    def _resolver_periodo(self, periodo_id: int | None):
        """Obtiene el período indicado o el que contiene la fecha actual."""

        if periodo_id is not None:
            periodo = self.repositorio_estructura.obtener_periodo(periodo_id)
            if periodo is None:
                raise ErrorNoEncontrado("El período académico indicado no existe.")
            return periodo

        periodo_actual = self.repositorio_estructura.obtener_periodo_que_contiene_fecha(
            obtener_fecha_servidor()
        )
        if periodo_actual is None:
            raise ErrorValidacion(
                "No hay un período académico vigente. Indique 'periodo_id'."
            )
        return periodo_actual

    def _obtener_minutos_hora_catedra(self) -> int:
        """Lee la duración configurada de la hora cátedra."""

        parametro = self.repositorio_parametros.obtener_por_clave(
            "minutos_hora_catedra"
        )
        if parametro is None:
            raise ErrorConflicto(
                "Falta inicializar el parámetro 'minutos_hora_catedra'."
            )
        return int(parametro.valor)

    def _obtener_tolerancia_minutos_firma(self) -> int:
        """Lee la tolerancia configurada para las firmas docentes."""

        parametro = self.repositorio_parametros.obtener_por_clave(
            "tolerancia_minutos_firma"
        )
        if parametro is None:
            raise ErrorConflicto(
                "Falta inicializar el parámetro 'tolerancia_minutos_firma'."
            )
        return int(parametro.valor)

    def _resolver_estrategia_horas(self, nombre_estrategia: str | None):
        """Selecciona la estrategia explícita o la configurada institucionalmente."""

        parametro = self.repositorio_parametros.obtener_por_clave(
            "estrategia_calculo_horas"
        )
        nombre = nombre_estrategia or (parametro.valor if parametro else None)
        return obtener_estrategia_balance_horas(nombre)
