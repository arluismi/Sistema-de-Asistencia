# Arquitectura del Backend

## 1. Alcance

El desarrollo se limita a la capa backend: lógica de negocio, controladores, persistencia,
seguridad y reportabilidad. No existen vistas HTML, hojas de estilo, scripts de interfaz ni
componentes gráficos. El frontend futuro deberá consumir exclusivamente el contrato descrito
en [`CONTRATO_API.md`](CONTRATO_API.md).

## 2. Stack técnico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ |
| Framework HTTP | Flask 3.1 |
| Persistencia | SQLAlchemy 2.x + Flask-SQLAlchemy |
| Base de datos | SQLite en desarrollo (portable a PostgreSQL) |
| Autenticación | JWT firmados con PyJWT |
| Contraseñas | Hash con `werkzeug.security` |
| Reportes | ReportLab (PDF) y openpyxl (Excel) |
| Pruebas | pytest |

## 3. Arquitectura en capas

```
Petición HTTP
    │
    ▼
controladores/        Traduce HTTP ↔ servicios. Valida formato de entrada.
    │                 No ejecuta consultas ni conoce SQLAlchemy.
    ▼
servicios/            Reglas de negocio, transacciones, permisos finos,
    │                 orquestación de estrategias y observadores.
    ▼
repositorios/         Patrón Repository / DAO. Única capa que consulta
    │                 la base de datos mediante SQLAlchemy.
    ▼
modelos/              Entidades, relaciones y restricciones del esquema.
```

Dependencias auxiliares:

| Paquete | Responsabilidad |
|---|---|
| `seguridad/` | JWT, hash de contraseñas y decoradores de autenticación/roles |
| `estrategias/` | Implementaciones intercambiables de cálculo (Strategy) |
| `observadores/` | Publicador y suscriptores de eventos (Observer) |
| `reportes/` | Generadores de documentos PDF y Excel |
| `presentadores/` | Serialización de entidades hacia JSON |
| `utilidades/` | Reloj institucional, validadores y respuestas uniformes |
| `errores/` | Excepciones de dominio y manejadores globales |
| `comandos/` | Inicialización de esquema y datos de demostración |

Regla de dependencia: las capas superiores conocen a las inferiores, nunca al revés. Ni los
modelos ni los repositorios importan controladores.

## 4. Patrones de diseño aplicados

### 4.1 Repository / DAO

Cada agregado tiene un repositorio especializado:

| Repositorio | Responsabilidad |
|---|---|
| `RepositorioUsuario` | Cuentas, estudiantes y docentes |
| `RepositorioEstructuraAcademica` | Cursos, materias, períodos, matrículas, asignaciones y grillas |
| `RepositorioAsistenciaEstudiantil` | Registros de asistencia de estudiantes |
| `RepositorioAsistenciaDocente` | Firmas, incidencias y grillas |
| `RepositorioAlertas` | Alertas del tablero |
| `RepositorioParametrosInstitucionales` | Parámetros configurables |

`RepositorioBase` centraliza `add`, `commit`, `get`, `delete` y listados. Los servicios nunca
construyen consultas SQL directamente.

### 4.2 Strategy

Interfaz `EstrategiaCalculoAsistencia` con implementaciones:

- `EstrategiaCalculoAsistenciaInstitucional`: Presente + Tarde + Justificado computan como
  asistencia; el presentismo efectivo excluye justificados.
- `EstrategiaCalculoAsistenciaEstricta`: sólo Presente + Tarde computan; los justificados no
  elevan el porcentaje.

Interfaz `EstrategiaBalanceHorasCatedra` con implementaciones:

- `EstrategiaBalanceHorasCatedraExacta`: minutos laborados / minutos por hora cátedra.
- `EstrategiaBalanceHorasCatedraPorBloques`: bloques completos de hora cátedra.

La estrategia se selecciona por parámetro `estrategia` o por el parámetro institucional
`estrategia_calculo_asistencia` / `estrategia_calculo_horas`.

### 4.3 Observer

- `PublicadorEventosAsistencia` mantiene la lista de suscriptores.
- El evento `EventoAsistenciaRegistrada` se publica después de cada carga diaria.
- `SuscriptorAlertasDashboard` evalúa dos reglas y crea alertas:
  1. Inasistencias consecutivas ≥ `limite_inasistencias_consecutivas`.
  2. Porcentaje del período < `umbral_regularidad_porcentaje`.
- Las alertas activas del mismo tipo se deduplican antes de crear una nueva.

El servicio de asistencia no conoce las reglas de alerta: sólo publica el evento.

## 5. Control de acceso por roles

| Rol | Alcance principal |
|---|---|
| Admin/Directivo | Gestión completa de usuarios, estructura, configuración y reportes |
| Preceptor | Carga de asistencia, matrículas, licencias, alertas y reportes |
| Docente | Asistencia de sus materias, firmas propias, sus incidencias y balance |
| Alumno | Consulta exclusiva de su propia asistencia y regularidad |

La autenticación se resuelve en `seguridad/autenticacion.py`:

1. Se exige `Authorization: Bearer <token>`.
2. Se valida firma y expiración del JWT.
3. Se carga el usuario activo y se guarda en `flask.g` para toda la petición.
4. `@requiere_autenticacion` y `@requiere_roles(...)` protegen los controladores.

Los servicios vuelven a verificar permisos contextuales: un docente sólo puede registrar
asistencia de materias asignadas, firmar su propia grilla y consultar sus propios datos.

## 6. Flujo de una carga diaria de asistencia

1. El controlador valida el JSON y delega en `ServicioAsistenciaEstudiantil`.
2. El servicio verifica curso, materia, fecha no futura, matrícula activa del estudiante y
   asignación docente cuando corresponde.
3. Por cada estudiante se crea o actualiza el registro único
   `(estudiante, curso, materia, fecha)`.
4. Se hace `flush` para que los cambios sean visibles dentro de la transacción.
5. Se publica un evento por estudiante.
6. El suscriptor de alertas consulta la base, evalúa las reglas y agrega alertas si
   corresponden.
7. Se confirma una única transacción.

## 7. Decisiones de persistencia

- Esquema normalizado en tercera forma normal: no se almacenan totales, porcentajes ni
  campos derivados; se calculan en tiempo real.
- Tablas puente para matrículas y asignaciones docente-materia-curso.
- Restricciones `UNIQUE` para evitar duplicados funcionales (asistencia diaria, firma por
  tipo, matrícula, asignación).
- Restricciones `CHECK` para estados, días de la semana, horarios ordenados y años lectivos.
- Claves foráneas con `ON DELETE RESTRICT` o `CASCADE` según la relación.
- En SQLite se ejecuta `PRAGMA foreign_keys=ON` en cada conexión mediante un listener de
  SQLAlchemy.

Detalle completo en [`MODELO_DE_DATOS.md`](MODELO_DE_DATOS.md).

## 8. Tiempo y puntualidad

- `utilidades/tiempo.py` obtiene la hora del servidor en la zona institucional configurada.
- La firma docente no acepta fecha ni hora del cliente: ambas se derivan de
  `obtener_marca_temporal_servidor()`.
- La tolerancia (`tolerancia_minutos_firma`, por defecto 10) decide si una desviación genera
  incidencia.
- El balance cruza cada bloque de la grilla con las firmas de ingreso/egreso de cada fecha
  del período y calcula minutos esperados, laborados, horas cátedra y saldo.

## 9. Reportabilidad

`ServicioReportes` reutiliza los cálculos de negocio y delega la presentación en:

- `GeneradorReportePdf` (ReportLab): tabla con encabezado repetido y resumen.
- `GeneradorReporteExcel` (openpyxl): encabezados estilizados, anchos automáticos y panel
  congelado.

Los endpoints devuelven el archivo como descarga con nombre y MIME type correctos.

## 10. Manejo de errores

Todas las respuestas de error comparten la estructura:

```json
{
  "error": {
    "codigo": "datos_invalidos",
    "mensaje": "Descripción",
    "detalles": ["opcional"]
  }
}
```

`ErrorValidacion` (400), `ErrorNoAutenticado` (401), `ErrorProhibido` (403),
`ErrorNoEncontrado` (404) y `ErrorConflicto` (409) son manejadas globalmente. Las
violaciones de integridad de SQLAlchemy se traducen a 409 y las fallas inesperadas a 500 sin
exponer trazas al cliente.

## 11. Pruebas

`pruebas/` contiene pruebas de integración con una base SQLite temporal aislada por prueba:

- Autenticación, perfil y restricciones por rol.
- Carga y actualización idempotente de asistencia.
- Resúmenes por estudiante, curso y período.
- Estrategias institucional y estricta.
- Alertas por inasistencias consecutivas y deduplicación.
- Firmas, tardanzas, salidas anticipadas, licencias y balance de horas.
- Reportes PDF/Excel y formatos inválidos.
- Integridad referencial a nivel de base de datos.

Comando: `python -m pytest`.

## 12. Trazabilidad con `liniamientos.md`

| Exigencia | Implementación |
|---|---|
| Sólo backend, sin UI | No hay plantillas ni archivos de interfaz |
| Contrato de API obligatorio | `docs/CONTRATO_API.md` |
| Nombres descriptivos | Clases, métodos y variables en español sin abreviaturas ambiguas |
| Comentarios de librerías externas | Comentarios inline y `docs/DEPENDENCIAS_EXTERNAS.md` |
| POO | Modelos, repositorios, servicios, estrategias y observadores son clases |
| Arquitectura multitier | `modelos` → `repositorios` → `servicios` → `controladores` |
| Roles jerárquicos | Admin/Directivo, Preceptor, Docente y Alumno |
| Persistencia normalizada | Modelo relacional en 3FN documentado |
| Integridad referencial | FK, UNIQUE, CHECK y `PRAGMA foreign_keys=ON` |
| Reportes PDF/Excel | Módulo `reportes/` y endpoints dedicados |
| Repository / DAO | Paquete `repositorios/` |
| Strategy | `estrategias/calculo_asistencia.py` y `calculo_horas_docentes.py` |
| Observer | `observadores/` y alertas del tablero |
