"""Suscriptor que genera alertas para el tablero de control.

Cuando el servicio de asistencia publica un evento, este suscriptor evalúa dos
reglas institucionales y persiste las alertas correspondientes:

1. Inasistencias consecutivas iguales o superiores al límite configurado.
2. Porcentaje de asistencia del período por debajo del umbral de regularidad.
"""

from ..errores import ErrorValidacion
from ..estrategias import obtener_estrategia_calculo_asistencia
from ..modelos import AlertaAsistencia
from ..modelos.enumeraciones import EstadoAsistencia, NivelAlerta, TipoAlerta
from ..repositorios import (
    RepositorioAlertas,
    RepositorioAsistenciaEstudiantil,
    RepositorioEstructuraAcademica,
    RepositorioParametrosInstitucionales,
    RepositorioUsuario,
)
from ..utilidades import obtener_marca_temporal_servidor
from .publicador import EventoAsistenciaRegistrada, SuscriptorEventoAsistencia


class SuscriptorAlertasDashboard(SuscriptorEventoAsistencia):
    """Genera alertas de asistencia para el tablero de Preceptoría y Dirección."""

    def actualizar(self, evento: EventoAsistenciaRegistrada) -> None:
        """Evalúa las reglas de alerta para el estudiante involucrado en el evento."""

        # Los repositorios se crean por evento porque la sesión de SQLAlchemy es
        # propia del contexto de la petición que publicó el evento.
        repositorio_alertas = RepositorioAlertas()
        repositorio_asistencia = RepositorioAsistenciaEstudiantil()
        repositorio_estructura = RepositorioEstructuraAcademica()
        repositorio_parametros = RepositorioParametrosInstitucionales()
        repositorio_usuario = RepositorioUsuario()

        estudiante = repositorio_usuario.obtener_estudiante_por_id(evento.estudiante_id)
        if estudiante is None:
            return

        limite_consecutivas = self._obtener_parametro_entero(
            repositorio_parametros, "limite_inasistencias_consecutivas"
        )
        umbral_regularidad = self._obtener_parametro_entero(
            repositorio_parametros, "umbral_regularidad_porcentaje"
        )

        self._evaluar_inasistencias_consecutivas(
            evento,
            estudiante,
            repositorio_alertas,
            repositorio_asistencia,
            limite_consecutivas,
        )
        self._evaluar_regularidad(
            evento,
            estudiante,
            repositorio_alertas,
            repositorio_asistencia,
            repositorio_estructura,
            repositorio_parametros,
            umbral_regularidad,
        )

    @staticmethod
    def _obtener_parametro_entero(repositorio_parametros, clave: str) -> int:
        """Lee un parámetro numérico o falla indicando la clave mal configurada."""

        parametro = repositorio_parametros.obtener_por_clave(clave)
        if parametro is None:
            raise ErrorValidacion(f"Falta el parámetro institucional '{clave}'.")
        try:
            return int(parametro.valor)
        except ValueError:
            raise ErrorValidacion(f"El parámetro institucional '{clave}' debe ser numérico.")

    def _evaluar_inasistencias_consecutivas(
        self,
        evento,
        estudiante,
        repositorio_alertas,
        repositorio_asistencia,
        limite_consecutivas: int,
    ) -> None:
        """Crea una alerta si se alcanzó el límite de faltas consecutivas."""

        registros_recientes = repositorio_asistencia.listar_ultimos_estados(
            evento.estudiante_id, limite=max(60, limite_consecutivas * 10)
        )
        if not registros_recientes:
            return

        fechas_con_estado = {}
        for registro in registros_recientes:
            fechas_con_estado.setdefault(registro.fecha, []).append(registro.estado)

        ausencias_consecutivas = 0
        for fecha in sorted(fechas_con_estado, reverse=True):
            estados_del_dia = fechas_con_estado[fecha]
            if all(estado == EstadoAsistencia.AUSENTE for estado in estados_del_dia):
                ausencias_consecutivas += 1
            else:
                break

        if ausencias_consecutivas < limite_consecutivas:
            return
        if repositorio_alertas.existe_alerta_activa(
            evento.estudiante_id, TipoAlerta.INASISTENCIAS_CONSECUTIVAS
        ):
            return

        alerta = AlertaAsistencia(
            estudiante_id=estudiante.id,
            tipo=TipoAlerta.INASISTENCIAS_CONSECUTIVAS,
            nivel=NivelAlerta.ALTA,
            mensaje=(
                f"El estudiante {estudiante.nombre_completo} (legajo {estudiante.legajo}) "
                f"acumula {ausencias_consecutivas} jornadas consecutivas de inasistencia."
            ),
            fecha_generacion=obtener_marca_temporal_servidor(),
            activa=True,
            leida=False,
        )
        repositorio_alertas.agregar(alerta)

    def _evaluar_regularidad(
        self,
        evento,
        estudiante,
        repositorio_alertas,
        repositorio_asistencia,
        repositorio_estructura,
        repositorio_parametros,
        umbral_regularidad: int,
    ) -> None:
        """Crea una alerta si el porcentaje del período cae bajo el umbral."""

        if repositorio_alertas.existe_alerta_activa(
            evento.estudiante_id, TipoAlerta.REGULARIDAD_EN_RIESGO
        ):
            return

        periodo = repositorio_estructura.obtener_periodo_que_contiene_fecha(evento.fecha)
        registros = repositorio_asistencia.listar_registros(
            estudiante_id=evento.estudiante_id,
            fecha_desde=periodo.fecha_inicio if periodo else None,
            fecha_hasta=periodo.fecha_fin if periodo else None,
        )
        if not registros:
            return

        parametro_estrategia = repositorio_parametros.obtener_por_clave(
            "estrategia_calculo_asistencia"
        )
        estrategia = obtener_estrategia_calculo_asistencia(
            parametro_estrategia.valor if parametro_estrategia else None
        )
        resumen = estrategia.calcular(registros)

        if resumen.porcentaje_asistencia >= umbral_regularidad:
            return

        alerta = AlertaAsistencia(
            estudiante_id=estudiante.id,
            tipo=TipoAlerta.REGULARIDAD_EN_RIESGO,
            nivel=NivelAlerta.MEDIA,
            mensaje=(
                f"El estudiante {estudiante.nombre_completo} (legajo {estudiante.legajo}) "
                f"registra {resumen.porcentaje_asistencia}% de asistencia, por debajo del "
                f"umbral institucional de {umbral_regularidad}%."
            ),
            porcentaje_asistencia=resumen.porcentaje_asistencia,
            fecha_generacion=obtener_marca_temporal_servidor(),
            activa=True,
            leida=False,
        )
        repositorio_alertas.agregar(alerta)
