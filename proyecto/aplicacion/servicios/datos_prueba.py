"""Generador de datos de prueba con volumen.

Complementa `datos_demostracion`: crea varios cursos, docentes, materias,
matrículas, bloques horarios, asistencias estudiantiles y firmas docentes para
probar listados, tableros, alertas y reportes con una cantidad representativa de
registros.

La generación es determinista (usa una semilla fija) e idempotente: si la cuenta
marcadora `docente.prueba.1` ya existe, no se vuelve a cargar nada. Las
contraseñas son exclusivamente para entornos de prueba.
"""

from datetime import date, datetime, time, timedelta
from random import Random

from ..modelos import FirmaAsistencia, IncidenciaHoraria
from ..modelos.enumeraciones import (
    EstadoAsistencia,
    NombreRol,
    TipoFirma,
    TipoIncidencia,
)
from ..repositorios import RepositorioAsistenciaDocente, RepositorioUsuario
from ..utilidades.tiempo import obtener_fecha_servidor
from .inicializacion import inicializar_datos_base
from .servicio_asistencia_docente import ServicioAsistenciaDocente
from .servicio_asistencia_estudiantil import ServicioAsistenciaEstudiantil
from .servicio_configuracion_institucional import ServicioConfiguracionInstitucional
from .servicio_estructura_academica import ServicioEstructuraAcademica
from .servicio_usuarios import ServicioUsuarios

SEMILLA_ALEATORIA = 2026
CANTIDAD_JORNADAS = 15
CANTIDAD_ESTUDIANTES_POR_CURSO = 8
CONTRASENA_DOCENTE_PRUEBA = "Docente123!"
CONTRASENA_ALUMNO_PRUEBA = "Alumno123!"
NOMBRE_USUARIO_MARCADOR = "docente.prueba.1"

# Cada curso tiene un turno y un horario base distintos para que la grilla no
# repita bloques del mismo curso ni del mismo docente.
CURSOS_PRUEBA = [
    {
        "nombre": "1° Año",
        "division": "B",
        "turno": "Mañana",
        "aula": "Aula 2",
        "hora_inicio": "08:00",
    },
    {
        "nombre": "2° Año",
        "division": "A",
        "turno": "Mañana",
        "aula": "Aula 3",
        "hora_inicio": "09:30",
    },
    {
        "nombre": "3° Año",
        "division": "B",
        "turno": "Tarde",
        "aula": "Aula 4",
        "hora_inicio": "11:00",
    },
    {
        "nombre": "4° Año",
        "division": "A",
        "turno": "Tarde",
        "aula": "Aula 5",
        "hora_inicio": "13:30",
    },
]

MATERIAS_PRUEBA = [
    {"nombre": "Física", "codigo": "PRU-FIS"},
    {"nombre": "Química", "codigo": "PRU-QUI"},
    {"nombre": "Geografía", "codigo": "PRU-GEO"},
    {"nombre": "Educación Física", "codigo": "PRU-EDF"},
    {"nombre": "Informática", "codigo": "PRU-INF"},
]

DOCENTES_PRUEBA = [
    {"nombres": "Lucía", "apellidos": "Fernández", "titulo": "Profesora de Ciencias Naturales"},
    {"nombres": "Martín", "apellidos": "Sosa", "titulo": "Profesor de Ciencias Sociales"},
    {"nombres": "Carla", "apellidos": "Benítez", "titulo": "Profesora de Informática"},
]

NOMBRES_ESTUDIANTES = [
    "Sofía",
    "Tomás",
    "Valentina",
    "Benjamín",
    "Martina",
    "Joaquín",
    "Camila",
    "Thiago",
    "Julieta",
    "Bautista",
    "Emma",
    "Lorenzo",
    "Mía",
    "Santiago",
    "Delfina",
    "Franco",
]

APELLIDOS_ESTUDIANTES = [
    "Acosta",
    "Bravo",
    "Castro",
    "Duarte",
    "Escobar",
    "Ferrari",
    "Gómez",
    "Herrera",
    "Ibarra",
    "Juárez",
    "Ledesma",
    "Molina",
    "Navarro",
    "Ortiz",
    "Paz",
    "Quiroga",
]

DURACION_BLOQUE_MINUTOS = 80


def generar_datos_prueba() -> dict:
    """Crea estructura académica, asistencias y firmas docentes de prueba."""

    inicializar_datos_base()

    repositorio_usuario = RepositorioUsuario()
    if repositorio_usuario.obtener_por_nombre_usuario(NOMBRE_USUARIO_MARCADOR) is not None:
        return {
            "generado": False,
            "mensaje": "Los datos de prueba ya estaban cargados.",
        }

    servicio_usuarios = ServicioUsuarios(repositorio_usuario)
    servicio_estructura = ServicioEstructuraAcademica(
        repositorio_usuario=repositorio_usuario
    )
    servicio_asistencia = ServicioAsistenciaEstudiantil(
        repositorio_usuario=repositorio_usuario
    )
    servicio_asistencia_docente = ServicioAsistenciaDocente(
        repositorio_usuario=repositorio_usuario
    )
    repositorio_asistencia_docente = RepositorioAsistenciaDocente()

    generador = Random(SEMILLA_ALEATORIA)
    fecha_referencia = obtener_fecha_servidor()
    anio_lectivo = fecha_referencia.year

    usuario_actor = _obtener_o_crear_usuario_actor(
        servicio_usuarios, repositorio_usuario
    )
    periodos = _asegurar_periodos(servicio_estructura, anio_lectivo)
    docentes = _crear_docentes(servicio_usuarios)
    materias = _crear_materias(servicio_estructura)
    cursos = _crear_cursos(servicio_estructura, anio_lectivo)
    estudiantes_por_curso = _crear_estudiantes_y_matriculas(
        servicio_usuarios, servicio_estructura, cursos, anio_lectivo
    )
    bloques_por_curso, bloques_por_docente = _crear_asignaciones_y_grillas(
        servicio_estructura, cursos, materias, docentes
    )

    fechas_jornadas = _obtener_ultimas_jornadas(fecha_referencia, CANTIDAD_JORNADAS)
    registros_creados = _registrar_asistencias_estudiantiles(
        servicio_asistencia,
        usuario_actor,
        cursos,
        bloques_por_curso,
        estudiantes_por_curso,
        fechas_jornadas,
        generador,
    )
    firmas, incidencias = _registrar_asistencias_docentes(
        repositorio_asistencia_docente,
        bloques_por_docente,
        fechas_jornadas,
        usuario_actor,
        generador,
    )
    incidencias += _registrar_licencia_de_ejemplo(
        servicio_asistencia_docente, docentes[0], fechas_jornadas[-3], usuario_actor
    )

    return {
        "generado": True,
        "anio_lectivo": anio_lectivo,
        "periodos": len(periodos),
        "cursos": len(cursos),
        "docentes": len(docentes),
        "materias": len(materias),
        "estudiantes": sum(len(alumnos) for alumnos in estudiantes_por_curso.values()),
        "bloques_horarios": len(bloques_por_curso),
        "jornadas_de_asistencia": len(fechas_jornadas),
        "registros_asistencia": registros_creados,
        "firmas_docentes": firmas,
        "incidencias_docentes": incidencias,
        "credenciales": {
            "docente": {
                "nombre_usuario": NOMBRE_USUARIO_MARCADOR,
                "contrasena": CONTRASENA_DOCENTE_PRUEBA,
            },
            "alumno": {
                "nombre_usuario": "alumno.prueba.1",
                "contrasena": CONTRASENA_ALUMNO_PRUEBA,
            },
        },
    }


def _obtener_o_crear_usuario_actor(
    servicio_usuarios: ServicioUsuarios,
    repositorio_usuario: RepositorioUsuario,
):
    """Devuelve una cuenta administrativa existente o crea una de prueba."""

    for nombre_usuario in ("direccion", "preceptoria", "admin.prueba"):
        usuario = repositorio_usuario.obtener_por_nombre_usuario(nombre_usuario)
        if usuario is not None:
            return usuario

    return servicio_usuarios.crear_usuario(
        {
            "nombre_usuario": "admin.prueba",
            "correo_electronico": "admin.prueba@instituto.edu.ar",
            "contrasena": "Admin123!",
            "rol": NombreRol.ADMINISTRATIVO_DIRECTIVO.value,
        }
    )


def _asegurar_periodos(
    servicio_estructura: ServicioEstructuraAcademica, anio_lectivo: int
) -> list[dict]:
    """Crea los cuatrimestres del año si todavía no existen."""

    nombres_existentes = {
        periodo["nombre"]
        for periodo in servicio_estructura.listar_periodos(anio_lectivo)
    }
    definiciones = [
        ("Primer Cuatrimestre", date(anio_lectivo, 3, 1), date(anio_lectivo, 6, 30)),
        ("Segundo Cuatrimestre", date(anio_lectivo, 8, 1), date(anio_lectivo, 11, 30)),
    ]

    periodos = servicio_estructura.listar_periodos(anio_lectivo)
    for nombre, fecha_inicio, fecha_fin in definiciones:
        if nombre in nombres_existentes:
            continue
        periodos.append(
            servicio_estructura.crear_periodo(
                {
                    "nombre": nombre,
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "anio_lectivo": anio_lectivo,
                }
            )
        )
    return periodos


def _crear_docentes(servicio_usuarios: ServicioUsuarios) -> list:
    """Crea los docentes de prueba y devuelve sus entidades."""

    docentes = []
    for indice, definicion in enumerate(DOCENTES_PRUEBA):
        numero = indice + 1
        docentes.append(
            servicio_usuarios.crear_docente(
                {
                    "nombre_usuario": f"docente.prueba.{numero}",
                    "correo_electronico": f"docente.prueba.{numero}@instituto.edu.ar",
                    "contrasena": CONTRASENA_DOCENTE_PRUEBA,
                    "legajo": f"DOC-PRUEBA-{numero:03d}",
                    "nombres": definicion["nombres"],
                    "apellidos": definicion["apellidos"],
                    "titulo_habilitante": definicion["titulo"],
                }
            )
        )
    return docentes


def _crear_materias(servicio_estructura: ServicioEstructuraAcademica) -> list[dict]:
    """Crea las materias de prueba."""

    return [
        servicio_estructura.crear_materia(dict(definicion))
        for definicion in MATERIAS_PRUEBA
    ]


def _crear_cursos(
    servicio_estructura: ServicioEstructuraAcademica, anio_lectivo: int
) -> list[dict]:
    """Crea los cursos de prueba para el año lectivo indicado."""

    cursos = []
    for definicion in CURSOS_PRUEBA:
        cursos.append(
            servicio_estructura.crear_curso(
                {
                    "nombre": definicion["nombre"],
                    "division": definicion["division"],
                    "turno": definicion["turno"],
                    "anio_lectivo": anio_lectivo,
                }
            )
        )
    return cursos


def _crear_estudiantes_y_matriculas(
    servicio_usuarios: ServicioUsuarios,
    servicio_estructura: ServicioEstructuraAcademica,
    cursos: list[dict],
    anio_lectivo: int,
) -> dict[int, list]:
    """Crea estudiantes y los matricula en cada curso de prueba."""

    estudiantes_por_curso: dict[int, list] = {}
    numero_global = 0

    for indice_curso, curso in enumerate(cursos):
        estudiantes = []
        for posicion in range(CANTIDAD_ESTUDIANTES_POR_CURSO):
            numero_global += 1
            estudiantes.append(
                servicio_usuarios.crear_estudiante(
                    {
                        "nombre_usuario": f"alumno.prueba.{numero_global}",
                        "correo_electronico": (
                            f"alumno.prueba.{numero_global}@instituto.edu.ar"
                        ),
                        "contrasena": CONTRASENA_ALUMNO_PRUEBA,
                        "legajo": f"ALU-PRUEBA-{numero_global:03d}",
                        "nombres": NOMBRES_ESTUDIANTES[
                            (indice_curso * CANTIDAD_ESTUDIANTES_POR_CURSO + posicion)
                            % len(NOMBRES_ESTUDIANTES)
                        ],
                        "apellidos": APELLIDOS_ESTUDIANTES[
                            (indice_curso * 3 + posicion) % len(APELLIDOS_ESTUDIANTES)
                        ],
                        "fecha_nacimiento": date(
                            2010 + (indice_curso % 4),
                            (posicion % 12) + 1,
                            (posicion % 27) + 1,
                        ).isoformat(),
                    }
                )
            )

            servicio_estructura.crear_inscripcion(
                {
                    "estudiante_id": estudiantes[-1].id,
                    "curso_id": curso["id"],
                    "fecha_inscripcion": date(anio_lectivo, 3, 1).isoformat(),
                }
            )

        estudiantes_por_curso[curso["id"]] = estudiantes

    return estudiantes_por_curso


def _crear_asignaciones_y_grillas(
    servicio_estructura: ServicioEstructuraAcademica,
    cursos: list[dict],
    materias: list[dict],
    docentes: list,
) -> tuple[dict[tuple[int, int], dict], list[tuple[object, list[dict]]]]:
    """Asigna materias a docentes y arma la grilla semanal de cada curso.

    La materia de índice `s` se dicta el día ISO `s + 1` (lunes a viernes) y el
    horario de inicio depende del curso, de modo que no se repiten bloques del
    mismo curso ni del mismo docente en el mismo día y hora.
    """

    bloques_por_curso: dict[tuple[int, int], dict] = {}
    bloques_por_docente: dict[int, list[dict]] = {}

    for indice_curso, curso in enumerate(cursos):
        hora_inicio = time.fromisoformat(CURSOS_PRUEBA[indice_curso]["hora_inicio"])
        hora_fin = _sumar_minutos(hora_inicio, DURACION_BLOQUE_MINUTOS)

        for indice_materia, materia in enumerate(materias):
            docente = docentes[indice_materia % len(docentes)]
            dia_semana = indice_materia + 1

            servicio_estructura.crear_asignacion(
                {
                    "docente_id": docente.id,
                    "curso_id": curso["id"],
                    "materia_id": materia["id"],
                }
            )
            bloque = servicio_estructura.crear_grilla_horaria(
                {
                    "curso_id": curso["id"],
                    "materia_id": materia["id"],
                    "docente_id": docente.id,
                    "dia_semana": dia_semana,
                    "hora_inicio": hora_inicio.isoformat(timespec="minutes"),
                    "hora_fin": hora_fin.isoformat(timespec="minutes"),
                    "aula": CURSOS_PRUEBA[indice_curso]["aula"],
                }
            )

            bloques_por_curso[(curso["id"], dia_semana)] = bloque
            bloques_por_docente.setdefault(docente.id, []).append(bloque)

    return bloques_por_curso, [
        (docente, bloques_por_docente[docente.id]) for docente in docentes
    ]


def _obtener_ultimas_jornadas(fecha_referencia: date, cantidad: int) -> list[date]:
    """Devuelve las últimas `cantidad` fechas hábiles anteriores a la referencia."""

    fechas: list[date] = []
    cursor = fecha_referencia - timedelta(days=1)
    while len(fechas) < cantidad:
        if cursor.isoweekday() <= 5:
            fechas.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(fechas))


def _registrar_asistencias_estudiantiles(
    servicio_asistencia: ServicioAsistenciaEstudiantil,
    usuario_actor,
    cursos: list[dict],
    bloques_por_curso: dict[tuple[int, int], dict],
    estudiantes_por_curso: dict[int, list],
    fechas_jornadas: list[date],
    generador: Random,
) -> int:
    """Registra la asistencia de cada curso en las jornadas generadas."""

    total_registros = 0
    total_jornadas = len(fechas_jornadas)

    for indice_jornada, fecha in enumerate(fechas_jornadas):
        for curso in cursos:
            bloque = bloques_por_curso.get((curso["id"], fecha.isoweekday()))
            if bloque is None:
                continue

            registros = []
            for posicion, estudiante in enumerate(
                estudiantes_por_curso[curso["id"]]
            ):
                estado, observacion = _estado_de_asistencia(
                    posicion, indice_jornada, total_jornadas, generador
                )
                registros.append(
                    {
                        "estudiante_id": estudiante.id,
                        "estado": estado.value,
                        "observacion": observacion,
                    }
                )

            resultado = servicio_asistencia.registrar_carga_diaria(
                {
                    "curso_id": curso["id"],
                    "materia_id": bloque["materia"]["id"],
                    "fecha": fecha.isoformat(),
                    "registros": registros,
                },
                usuario_actor,
            )
            total_registros += resultado["creados"]

    return total_registros


def _estado_de_asistencia(
    posicion: int, indice_jornada: int, total_jornadas: int, generador: Random
) -> tuple[EstadoAsistencia, str | None]:
    """Define un estado verosímil, con casos que disparan alertas.

    El estudiante en la posición 1 falta una jornada de cada dos (queda por
    debajo del umbral de regularidad) y el de la posición 2 falta las últimas
    cuatro jornadas (supera el límite de inasistencias consecutivas).
    """

    # Las dos primeras jornadas quedan completas para que las alertas de
    # regularidad reflejen porcentajes con varios registros y no 0 %.
    if indice_jornada < 2:
        return EstadoAsistencia.PRESENTE, None

    if posicion == 1 and indice_jornada % 2 == 0:
        return EstadoAsistencia.AUSENTE, "Sin justificación presentada."
    if posicion == 2 and indice_jornada >= total_jornadas - 4:
        return EstadoAsistencia.AUSENTE, "Sin justificación presentada."

    valor = generador.random()
    if valor < 0.06:
        return EstadoAsistencia.AUSENTE, "Sin justificación presentada."
    if valor < 0.12:
        return EstadoAsistencia.TARDE, "Ingresó después del inicio de la clase."
    if valor < 0.17:
        return EstadoAsistencia.JUSTIFICADO, "Certificado médico presentado."
    return EstadoAsistencia.PRESENTE, None


def _registrar_asistencias_docentes(
    repositorio: RepositorioAsistenciaDocente,
    bloques_por_docente: list[tuple[object, list[dict]]],
    fechas_jornadas: list[date],
    usuario_actor,
    generador: Random,
) -> tuple[int, int]:
    """Crea firmas de ingreso y egreso históricas y sus incidencias.

    El servicio de firmas sólo admite el día actual, por eso el histórico se
    construye directamente con los modelos y el repositorio. La desviación se
    compara con la tolerancia institucional para generar tardanzas y salidas
    anticipadas equivalentes a las que produciría el servicio.
    """

    tolerancia = ServicioConfiguracionInstitucional().obtener_entero(
        "tolerancia_minutos_firma"
    )
    firmas_creadas = 0
    incidencias_creadas = 0

    for docente, bloques in bloques_por_docente:
        for bloque in bloques:
            hora_inicio = time.fromisoformat(bloque["hora_inicio"])
            hora_fin = time.fromisoformat(bloque["hora_fin"])
            for fecha in fechas_jornadas:
                if fecha.isoweekday() != bloque["dia_semana"]:
                    continue

                minutos_tardanza = _desviacion(generador, probabilidad=0.2, maximo=40)
                firma_ingreso = FirmaAsistencia(
                    docente_id=docente.id,
                    grilla_horaria_id=bloque["id"],
                    tipo_firma=TipoFirma.INGRESO,
                    fecha=fecha,
                    marca_temporal=(
                        datetime.combine(fecha, hora_inicio)
                        + timedelta(minutes=minutos_tardanza)
                    ),
                    registrado_por_usuario_id=usuario_actor.id,
                )
                repositorio.agregar(firma_ingreso)
                # `flush` asigna el identificador de la firma sin cerrar la
                # transacción, para poder vincular la incidencia.
                repositorio.sesion.flush()
                firmas_creadas += 1

                if minutos_tardanza > tolerancia:
                    repositorio.agregar(
                        _construir_incidencia(
                            docente,
                            bloque,
                            firma_ingreso,
                            TipoIncidencia.TARDANZA,
                            minutos_tardanza,
                            usuario_actor,
                            "Tardanza de {minutos} minutos en el ingreso",
                        )
                    )
                    incidencias_creadas += 1

                minutos_salida = _desviacion(generador, probabilidad=0.15, maximo=35)
                firma_egreso = FirmaAsistencia(
                    docente_id=docente.id,
                    grilla_horaria_id=bloque["id"],
                    tipo_firma=TipoFirma.EGRESO,
                    fecha=fecha,
                    marca_temporal=(
                        datetime.combine(fecha, hora_fin)
                        - timedelta(minutes=minutos_salida)
                    ),
                    registrado_por_usuario_id=usuario_actor.id,
                )
                repositorio.agregar(firma_egreso)
                repositorio.sesion.flush()
                firmas_creadas += 1

                if minutos_salida > tolerancia:
                    repositorio.agregar(
                        _construir_incidencia(
                            docente,
                            bloque,
                            firma_egreso,
                            TipoIncidencia.SALIDA_ANTICIPADA,
                            minutos_salida,
                            usuario_actor,
                            "Salida anticipada de {minutos} minutos",
                        )
                    )
                    incidencias_creadas += 1

        repositorio.confirmar_cambios()

    return firmas_creadas, incidencias_creadas


def _desviacion(generador: Random, probabilidad: float, maximo: int) -> int:
    """Devuelve minutos de desviación: pequeños habitualmente, grandes a veces."""

    if generador.random() < probabilidad:
        return generador.randint(15, maximo)
    return generador.randint(0, 5)


def _construir_incidencia(
    docente,
    bloque: dict,
    firma: FirmaAsistencia,
    tipo: TipoIncidencia,
    minutos: int,
    usuario_actor,
    plantilla: str,
) -> IncidenciaHoraria:
    """Arma una incidencia automática vinculada a una firma docente."""

    detalle = plantilla.format(minutos=minutos)
    return IncidenciaHoraria(
        docente_id=docente.id,
        grilla_horaria_id=bloque["id"],
        firma_asistencia=firma,
        tipo=tipo,
        fecha=firma.fecha,
        minutos_desviacion=minutos,
        descripcion=(
            f"{detalle} correspondiente a {bloque['materia']['nombre']} "
            f"({bloque['curso']['nombre_completo']})."
        ),
        generada_automaticamente=True,
        registrado_por_usuario_id=usuario_actor.id,
    )


def _registrar_licencia_de_ejemplo(
    servicio_asistencia_docente: ServicioAsistenciaDocente,
    docente,
    fecha: date,
    usuario_actor,
) -> int:
    """Registra una licencia mediante el servicio, que valida sus propias reglas."""

    servicio_asistencia_docente.registrar_licencia(
        {
            "docente_id": docente.id,
            "fecha": fecha.isoformat(),
            "motivo": "Capacitación docente fuera del establecimiento.",
        },
        usuario_actor,
    )
    return 1


def _sumar_minutos(hora: time, minutos: int) -> time:
    """Suma minutos a una hora sin superar el final del día."""

    momento = datetime.combine(date(2000, 1, 1), hora) + timedelta(minutes=minutos)
    return momento.time()
