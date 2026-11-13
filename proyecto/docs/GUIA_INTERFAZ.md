# Guía de diseño de interfaz (HTML) — Complemento del Contrato de API

> Este documento es una especificación para el futuro frontend. **No contiene código de
> interfaz**: no hay HTML, CSS ni JavaScript ejecutable. Su función es traducir
> [`CONTRATO_API.md`](CONTRATO_API.md) a pantallas, componentes, flujos y criterios de
> usabilidad verificables.

## 1. Propósito y alcance

### 1.1 Para qué sirve

- Servir de puente entre el contrato de API y el diseño/implementación del frontend.
- Evitar que la interfaz invente campos, parámetros o endpoints que el backend no expone.
- Definir la estructura de navegación, las pantallas mínimas, los estados de cada pantalla y
  las reglas de presentación de los datos.
- Dar a QA una lista de comportamientos observables para validar la interfaz.

### 1.2 Jerarquía documental

| Documento | Autoridad |
|---|---|
| [`CONTRATO_API.md`](CONTRATO_API.md) | **Fuente de verdad** de rutas, roles, cuerpos y respuestas |
| `GUIA_INTERFAZ.md` (este documento) | Deriva el diseño de pantallas del contrato |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Explica las capas y patrones del backend |
| [`MODELO_DE_DATOS.md`](MODELO_DE_DATOS.md) | Explica la persistencia |

Si este documento y el contrato difieren, **prevalece el contrato**. Cualquier pantalla que
necesite un dato inexistente debe resolverse primero ampliando el contrato, no simulando el
dato en el cliente.

### 1.3 Relación con el alcance del trabajo práctico

`liniamientos.md` restringe esta fase al backend. Esta guía **no habilita** la generación de
vistas, hojas de estilo, scripts de interfaz ni componentes gráficos dentro del repositorio.
Su existencia es documental: prepara la futura incorporación del frontend sin alterar el
alcance actual.

### 1.4 Convenciones de esta guía

- **Pantalla:** unidad navegable con una URL propia.
- **Bloque:** sección interna de una pantalla (filtros, tabla, formulario, tarjetas).
- **P1–P5:** patrones reutilizables descritos en la sección 6.
- **Rol:** uno de `Admin/Directivo`, `Preceptor`, `Docente` o `Alumno`.
- Los textos entre comillas son copy sugerido, no obligatorio.
- Los wireframes son esquemas ASCII; no representan HTML real.

---

## 2. Principios rectores

1. **Fidelidad al contrato.** Cada dato mostrado, enviado o filtrado debe existir en el
   contrato. No se agregan campos calculados en el cliente si el backend ya los devuelve.
2. **El servidor manda.** Fechas, horas, marcas de tiempo, porcentajes, estados de
   regularidad, alertas e incidencias se muestran tal como llegan. El cliente no recalcula ni
   corrige esos valores.
3. **Permisos visibles, permisos validados.** La navegación oculta lo que el rol no puede
   usar, pero toda acción se valida igualmente contra `401`, `403` y `404`.
4. **Idempotencia explícita.** La carga de asistencia actualiza registros existentes; la
   interfaz debe avisarlo antes y después de guardar.
5. **Sin acciones fantasma.** No se muestran botones de editar o eliminar si el contrato no
   ofrece `PUT`, `PATCH` o `DELETE` para ese recurso.
6. **Prevención antes que corrección.** La validación local refleja las reglas del backend
   para evitar viajes innecesarios, pero el backend sigue siendo la autoridad final.
7. **Mensajes del backend primero.** Cuando la respuesta incluye `mensaje`, se usa como
   confirmación. Cuando incluye `error.mensaje`, se usa como explicación.
8. **Accesibilidad por defecto.** Formularios etiquetados, tablas con encabezados, foco
   gestionado, contraste suficiente y operación completa por teclado.
9. **Consistencia.** Un mismo tipo de dato se presenta igual en todas las pantallas (badges,
   fechas, porcentajes, nombres).
10. **Diseño responsive.** La carga de asistencia debe ser cómoda en tableta y teléfono, no
    sólo en escritorio.

---

## 3. Integración con la API

### 3.1 Entorno y CORS

- **URL base:** `http://localhost:5000/api/v1` en desarrollo.
- El frontend se sirve desde un origen distinto; debe estar incluido en
  `CORS_ORIGENES_PERMITIDOS` (variable de entorno del backend).
- La autenticación es por encabezado `Authorization`, no por cookie. Por lo tanto, las
  peticiones no requieren `credentials: "include"`.
- Los cuerpos se envían como `Content-Type: application/json`.
- Las descargas de reportes también requieren el encabezado `Authorization`.

### 3.2 Sesión y token

Flujo recomendado:

1. `POST /autenticacion/iniciar-sesion` con `nombre_usuario` y `contrasena`.
2. Guardar `token_acceso`, `usuario` y `expira_en_minutos`.
3. En cada petición protegida enviar `Authorization: Bearer <token_acceso>`.
4. Al iniciar la aplicación con un token guardado, validar la sesión con
   `GET /autenticacion/perfil`.
5. Ante cualquier `401`, descartar el token y volver al inicio de sesión con un aviso.

Reglas:

- No existe endpoint de cierre de sesión: el cierre es local (descartar el token).
- No existe endpoint de renovación: al expirar, se vuelve a iniciar sesión.
- No colocar el token en la URL, en el HTML ni en registros de consola.
- Preferir `sessionStorage` o memoria sobre `localStorage`; si se usa `localStorage`,
  documentar el riesgo de XSS. Nunca usar cookies para este esquema.
- La vigencia la informa el backend (`expira_en_minutos`); no se inventa un temporizador
  propio. El manejo de `401` es la red de seguridad.
- Si una operación falla con `401`, conservar los datos del formulario en memoria para
  evitar pérdida y ofrecer reingreso.

### 3.3 Estructura de respuestas

Éxito:

```json
{
  "datos": {},
  "mensaje": "Texto opcional"
}
```

Error:

```json
{
  "error": {
    "codigo": "datos_invalidos",
    "mensaje": "Descripción legible",
    "detalles": ["detalle opcional"]
  }
}
```

Consideraciones de interfaz:

- `datos` puede ser objeto o lista; la pantalla debe saber qué espera cada endpoint.
- `mensaje` es opcional: no diseñar una confirmación que dependa de su existencia.
- `detalles` es opcional y **no tiene forma fija**: puede ser una lista, un objeto o un
  texto. La interfaz debe mostrarlo de forma genérica si no reconoce su estructura.
- `error.codigo` es estable y sirve para decidir el tratamiento; `error.mensaje` es el texto
  para el usuario.

### 3.4 Fechas, horas y números

| Dato | Formato en la API | Presentación sugerida |
|---|---|---|
| Fecha | `AAAA-MM-DD` | `DD/MM/AAAA` |
| Hora | `HH:MM` (24 h) | `HH:MM` |
| Marca de tiempo | `AAAA-MM-DDTHH:MM:SS` | `DD/MM/AAAA HH:MM` |
| Porcentaje | Número de 0 a 100 (`77.78`) | `77,78 %` |
| Horas cátedra | Decimal (`0.88`) | `0,88 h` |
| Booleano | `true` / `false` | Etiqueta textual, no sólo color |
| Nulo | `null` | `—` o "Sin datos", según contexto |

Reglas críticas:

- Las marcas de tiempo **no incluyen offset horario**, pero están expresadas en la zona
  institucional (`America/Argentina/Buenos_Aires` por defecto). No convertirlas con la zona
  del navegador. Formatear por componentes o con una librería configurada explícitamente en
  esa zona.
- Las fechas `AAAA-MM-DD` deben tratarse como fecha civil, no como instante UTC. Evitar
  `new Date("2026-11-09")` seguido de `toLocaleDateString()`, porque puede mostrar el día
  anterior en husos negativos.
- Los porcentajes llegan en escala 0–100; **no multiplicar por 100**. `porcentaje_cumplimiento`
  del balance también usa esa escala (por eso un valor `0.85` significa `0,85 %`).
- No sumar ni promediar porcentajes en el cliente; usar los totales de la API.

### 3.5 Descargas de reportes

Los endpoints de reportes devuelven un archivo binario, no JSON:

1. Hacer la petición con `fetch` y el encabezado `Authorization`.
2. Si el `Content-Type` es JSON, tratarlo como error y mostrar `error.mensaje`.
3. Si es binario, obtener un `Blob` y descargarlo con un enlace temporal.
4. Usar el nombre de archivo de `Content-Disposition`; si no está disponible, sugerir el
   nombre documentado (`reporte_asistencia_estudiantes_curso_<id>_periodo_<id>.<ext>` o
   `reporte_horas_docentes_periodo_<id>.<ext>`).
5. Mostrar estado de descarga por botón y evitar dobles clics.

No usar un enlace directo `<a href="...">` para estos endpoints, porque no puede adjuntar el
encabezado `Authorization` y fallaría con `401`.

### 3.6 Listados, filtros y paginación

- El contrato **no define paginación ni búsqueda global**. No enviar parámetros `page`,
  `limit`, `q` o `sort` que el backend ignora.
- Usar únicamente los parámetros documentados por endpoint.
- Si el volumen crece, paginar y ordenar en el cliente es aceptable como primera etapa. Cuando
  deje de serlo, proponer al backend los parámetros correspondientes y actualizar el contrato.
- Mantener los filtros en la URL (por ejemplo, `?curso_id=1&periodo_id=2`) permite compartir
  y recargar la vista sin perder el contexto.
- Al cambiar un filtro, reiniciar la selección dependiente (por ejemplo, al cambiar de curso,
  volver a cargar materias y estudiantes).

### 3.7 Operaciones no disponibles

El contrato sólo expone creación y consulta para la mayoría de las entidades académicas. No
diseñar pantallas de edición o baja de usuarios, estudiantes, docentes, cursos, materias,
períodos, inscripciones, asignaciones, grillas, asistencias ni alertas. Las únicas
actualizaciones previstas son:

- `PATCH /usuarios/{id}/estado` (activar/desactivar cuenta).
- `PATCH /alertas/{id}/marcar-leida` (marcar alerta).
- `PUT /configuracion/{clave}` (parámetro institucional).

---

## 4. Roles, navegación y permisos

### 4.1 Matriz de capacidades

`C` = crear, `R` = consultar. No hay edición ni baja salvo las excepciones indicadas.

| Módulo | Admin/Directivo | Preceptor | Docente | Alumno |
|---|---|---|---|---|
| Usuarios | C R | — | — | — |
| Estudiantes | C R | R | R | — |
| Docentes | C R | R | R | — |
| Cursos | C R | R | R | R |
| Materias | C R | R | R | R |
| Períodos académicos | C R | R | R | R |
| Inscripciones | C R | C R | R | — |
| Asignaciones docentes | C R | R | R | — |
| Grilla horaria | C R | R | R (propia) | R (de su curso) |
| Carga de asistencia estudiantil | C | C | C (materias asignadas) | — |
| Consulta de asistencias | R | R | R (sus cursos) | R (propias) |
| Resumen y regularidad | R | R | R | R (propio) |
| Alertas | R | R | R (sus cursos) | — |
| Firmas docentes | C R | C R | C (propias) | — |
| Incidencias docentes | R | R | R (propias) | — |
| Licencias docentes | C | C | — | — |
| Balance de horas | R | R | R (propio) | — |
| Reportes | R | R | — | — |
| Configuración | C R | — | — | — |

### 4.2 Navegación por rol

**Admin/Directivo**

- Panel
- Operación diaria: Carga de asistencia, Consulta de asistencias, Resumen, Alertas
- Asistencia docente: Firmas, Incidencias, Licencias, Balance de horas
- Gestión académica: Estudiantes, Docentes, Cursos, Materias, Períodos, Inscripciones,
  Asignaciones, Grilla horaria
- Administración: Usuarios, Configuración, Reportes
- Mi perfil

**Preceptor**

- Panel
- Operación diaria: Carga de asistencia, Consulta de asistencias, Resumen, Alertas
- Asistencia docente: Firmas, Incidencias, Licencias, Balance de horas
- Gestión académica: Estudiantes, Docentes, Cursos, Materias, Períodos, Inscripciones,
  Asignaciones, Grilla horaria (grilla sólo consulta)
- Reportes
- Mi perfil

**Docente**

- Panel
- Carga de asistencia (sólo materias asignadas)
- Consulta de asistencias
- Resumen y regularidad
- Alertas
- Mis firmas (ingreso/egreso)
- Mis incidencias
- Mi balance de horas
- Mi horario
- Estudiantes (consulta)
- Mi perfil

**Alumno**

- Panel
- Mi asistencia
- Mi regularidad
- Mi horario
- Mi perfil

### 4.3 Presentación de permisos

- Ocultar del menú los módulos sin acceso. No mostrarlos deshabilitados de forma permanente.
- En pantallas compartidas (por ejemplo, Cursos), ocultar el botón "Nuevo" a quien no puede
  crear.
- Si el usuario llega por URL directa a una pantalla sin permiso, mostrar un estado
  "No tenés acceso a esta sección" con enlace al panel. No redirigir silenciosamente.
- Un `403` durante una acción contextual (por ejemplo, un docente sin asignación) se muestra
  como aviso dentro de la pantalla, no como cierre de sesión.
- El ocultamiento de acciones es usabilidad; la seguridad real está en el backend.

### 4.4 Resolución del contexto propio

El perfil (`GET /autenticacion/perfil`) devuelve la cuenta, pero **no** el `estudiante_id` ni
el `docente_id`. Mientras el contrato no los incluya:

- **Alumno:** omitir `estudiante_id` en `GET /asistencias-estudiantes` y
  `GET /asistencias-estudiantes/resumen`; el backend fuerza su propio identificador. No
  intentar adivinar identificadores ajenos.
- **Docente:** en firmas, incidencias y balance puede omitir `docente_id`; el backend fuerza
  su propio identificador. En `GET /grillas-horarias` no existe esa imposición, por lo que
  "Mi horario" debe filtrar explícitamente por su `docente_id`. Para obtenerlo, consultar
  `GET /docentes` y localizar el registro cuyo `usuario.id` coincida con el `id` del perfil.
  Guardar esa correspondencia en la sesión de la aplicación.
- **Alumno y su curso:** no existe un endpoint directo que devuelva su matrícula. Se puede
  inferir el curso desde sus propios registros de asistencia, que incluyen el objeto `curso`.
  Si no hay registros, mostrar un estado informativo y no inventar el curso.
- Estas soluciones son adaptaciones de interfaz, no reglas de negocio. Se listan como deuda
  de contrato en la sección 15.

---

## 5. Arquitectura de información

### 5.1 Inventario de pantallas

| ID | Pantalla | Rol principal | Endpoints |
|---|---|---|---|
| UI-01 | Inicio de sesión | Público | `GET /salud`, `POST /autenticacion/iniciar-sesion` |
| UI-02 | Panel de inicio | Todos | `GET /alertas`, `GET /asistencias-estudiantes/resumen`, `GET /grillas-horarias`, `GET /asistencias-docentes/firmas` |
| UI-03 | Mi perfil | Todos | `GET /autenticacion/perfil` |
| UI-04 | Usuarios | Admin | `GET/POST /usuarios`, `GET /usuarios/{id}`, `PATCH /usuarios/{id}/estado` |
| UI-05 | Estudiantes | Admin, Preceptor, Docente | `GET/POST /estudiantes` |
| UI-06 | Docentes | Admin, Preceptor, Docente | `GET/POST /docentes` |
| UI-07 | Cursos | Todos (alta: Admin) | `GET/POST /cursos` |
| UI-08 | Materias | Todos (alta: Admin) | `GET/POST /materias` |
| UI-09 | Períodos académicos | Todos (alta: Admin) | `GET/POST /periodos-academicos` |
| UI-10 | Inscripciones | Admin, Preceptor, Docente | `GET/POST /inscripciones` |
| UI-11 | Asignaciones docentes | Admin, Preceptor, Docente | `GET/POST /asignaciones-docentes` |
| UI-12 | Grilla horaria | Todos (alta: Admin) | `GET/POST /grillas-horarias` |
| UI-13 | Carga de asistencia estudiantil | Admin, Preceptor, Docente | `POST /asistencias-estudiantes`, `GET /asistencias-estudiantes` |
| UI-14 | Consulta de asistencias | Todos | `GET /asistencias-estudiantes` |
| UI-15 | Resumen y regularidad | Todos | `GET /asistencias-estudiantes/resumen` |
| UI-16 | Alertas | Admin, Preceptor, Docente | `GET /alertas`, `PATCH /alertas/{id}/marcar-leida` |
| UI-17 | Firmas docentes | Admin, Preceptor, Docente | `POST/GET /asistencias-docentes/firmas` |
| UI-18 | Incidencias docentes | Admin, Preceptor, Docente | `GET /asistencias-docentes/incidencias` |
| UI-19 | Licencias docentes | Admin, Preceptor | `POST /asistencias-docentes/licencias`, `GET /asistencias-docentes/incidencias` |
| UI-20 | Balance de horas cátedra | Admin, Preceptor, Docente | `GET /asistencias-docentes/balance-horas` |
| UI-21 | Reportes | Admin, Preceptor | `GET /reportes/asistencia-estudiantes.{pdf,xlsx}`, `GET /reportes/horas-docentes.{pdf,xlsx}` |
| UI-22 | Configuración institucional | Admin | `GET /configuracion`, `PUT /configuracion/{clave}` |

### 5.2 Estructura global de la aplicación (shell)

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ [Marca] Sistema de Asistencia      [Rol] [Nombre de usuario] [Salir]    │
├───────────────────┬─────────────────────────────────────────────────────┤
│ Navegación        │  Título de la pantalla            [Acción primaria] │
│                   │  Descripción breve (opcional)                       │
│ ▸ Operación diaria│  ─────────────────────────────────────────────────  │
│ ▸ Asistencia doc. │  [Filtros]                                          │
│ ▸ Gestión académ. │  ┌─────────────────────────────────────────────────┐ │
│ ▸ Administración  │  │ Contenido: tabla / tarjetas / formulario        │ │
│                   │  └─────────────────────────────────────────────────┘ │
│                   │  [Mensajes de éxito, error o advertencia]           │
└───────────────────┴─────────────────────────────────────────────────────┘
```

Elementos obligatorios del shell:

- Enlace "Saltar al contenido".
- Encabezado con nombre del sistema, rol, nombre de usuario y cierre de sesión.
- Navegación principal con `aria-current="page"` en la sección activa.
- Región de avisos (`aria-live`) fuera del contenido, para no perder foco.
- Contenido principal con un único `h1` por pantalla.
- Idioma declarado como `es-AR`.

### 5.3 Mapa de navegación

- **Operación diaria** agrupa lo que se usa a diario: cargar asistencia, consultarla, ver el
  resumen y atender alertas.
- **Asistencia docente** agrupa firmas, incidencias, licencias y balance.
- **Gestión académica** agrupa entidades de estructura. Es el grupo con más pantallas de
  consulta y alta.
- **Administración** contiene usuarios, configuración y reportes.
- **Mi espacio** (Docente/Alumno) contiene las vistas personales.

No anidar más de dos niveles. Los filtros no son pantallas: viven dentro de cada listado.

---

## 6. Patrones de pantalla reutilizables

### 6.1 P1 — Listado con filtros y alta

Usado por: UI-04 a UI-12, UI-14, UI-16, UI-18, UI-19.

```text
┌ Título ─────────────────────────────────────────────── [Nuevo …] ┐
│ [Filtro A] [Filtro B] [Filtro C]                    [Limpiar]    │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Columna 1 │ Columna 2 │ … │ Estado │ Acciones                │ │
│ │ …         │ …         │ … │ …      │ [Ver] [Acción]          │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ Mostrando N resultados                          [Actualizar]     │
└──────────────────────────────────────────────────────────────────┘
```

Reglas:

- La acción primaria ("Nuevo …") sólo aparece si el rol puede crear.
- Los filtros se aplican con un botón "Filtrar" o al cambiar el valor; definir una sola
  convención y respetarla en todas las pantallas.
- "Limpiar" restablece todos los filtros.
- La tabla tiene un encabezado comprensible y una fila por entidad.
- Las acciones por fila son enlaces o botones con nombre accesible; no sólo íconos.
- El estado vacío explica por qué no hay filas y qué hacer a continuación.
- El listado no se recarga solo. Ofrecer "Actualizar" y, si se desea, refresco periódico
  opcional y visible.

### 6.2 P2 — Detalle

Para entidades con endpoint de detalle (`/usuarios/{id}`) o cuando la fila ya trae todos los
datos:

- Encabezado con nombre principal y estado.
- Lista de definición (término/valor) para los campos.
- Acciones permitidas en la parte superior.
- Enlace "Volver al listado" que conserva los filtros previos.

### 6.3 P3 — Carga masiva

Usado por UI-13.

- Cabecera con contexto: curso, materia, fecha.
- Tabla o lista de estudiantes con un control de estado por fila.
- Acciones globales: "Marcar todos presentes", "Limpiar marcas".
- Resumen en vivo: cantidad de presentes, ausentes, justificados y tardes.
- Botón de guardado fijo y visible; deshabilitado mientras se envía.
- Resultado posterior con `creados` y `actualizados`.

### 6.4 P4 — Panel de indicadores y tarjetas

Usado por UI-02, UI-15, UI-20.

- Tarjetas con un solo número principal y una etiqueta clara.
- El porcentaje se acompaña de su umbral cuando corresponde.
- No usar gráficos si el contrato no entrega series temporales. Un gráfico de evolución
  requeriría datos que la API no expone.
- Las tarjetas no reemplazan a la tabla de detalle: la complementan.

### 6.5 P5 — Descarga de archivo

Usado por UI-21.

- Un botón por formato (PDF, XLSX), con el formato visible en el texto.
- Estado "Generando…" con el botón deshabilitado.
- Error en línea si falla la generación.
- Confirmación de descarga sin prometer que el archivo se abrió.

### 6.6 Formularios: reglas comunes

- Cada campo tiene `<label>` asociado; los obligatorios se marcan con texto, no sólo asterisco.
- Mostrar ayuda breve cuando el formato no es evidente (por ejemplo, legajo, día de la semana).
- Validar al salir del campo y al enviar; no mostrar errores mientras el usuario todavía escribe
  el primer carácter.
- Errores junto al campo y resumen de errores al inicio del formulario cuando haya varios.
- El botón de envío se deshabilita mientras la petición está en curso.
- No borrar el formulario si el servidor responde con error.
- Si el backend devuelve `409`, explicar el conflicto y ofrecer corregir; no reintentar solo.
- Si el formulario es largo (estudiante, docente), usar página completa; si es corto
  (materia, curso, período, asignación), modal o panel lateral.

### 6.7 Tablas: reglas comunes

- `<caption>` visible o sólo para lectores de pantalla.
- Encabezados con `scope="col"`.
- Ordenamiento por columna sólo si se implementa en el cliente y se anuncia con `aria-sort`.
- Números alineados a la derecha; texto a la izquierda; fechas y estados centrados o
  consistentes.
- En pantallas pequeñas, permitir desplazamiento horizontal o convertir cada fila en tarjeta.
- No truncar nombres o legajos sin ofrecer el valor completo (título o detalle).
- Mostrar `—` para nulos; no dejar celdas vacías.

### 6.8 Retroalimentación

- **Carga inicial:** esqueleto o indicador con `aria-busy="true"`.
- **Guardado exitoso:** aviso no bloqueante con `mensaje` del backend.
- **Error de validación:** resumen + errores por campo.
- **Error de permisos:** bloque informativo, sin botón de reintento.
- **Error de red:** aviso con opción "Reintentar".
- **Confirmaciones:** sólo para acciones destructivas o irreversibles (desactivar cuenta). Las
  operaciones de sólo lectura no requieren confirmación.

### 6.9 Estados vacíos

Cada listado define su texto:

| Pantalla | Estado vacío sugerido |
|---|---|
| Usuarios | "No hay usuarios que coincidan con los filtros." |
| Estudiantes | "No hay estudiantes para el curso seleccionado." |
| Docentes | "Todavía no hay docentes registrados." |
| Cursos | "No hay cursos para el año lectivo seleccionado." |
| Materias | "Todavía no hay materias registradas." |
| Períodos | "No hay períodos para el año lectivo seleccionado." |
| Inscripciones | "No hay matrículas que coincidan con los filtros." |
| Asignaciones | "No hay asignaciones docente-materia-curso." |
| Grilla | "No hay bloques horarios para los filtros seleccionados." |
| Asistencias | "No hay registros de asistencia para los filtros seleccionados." |
| Alertas | "No hay alertas para los filtros seleccionados." |
| Incidencias | "No hay incidencias para los filtros seleccionados." |
| Balance | "No hay clases en el período seleccionado." |
| Reportes | "Seleccione curso y período para generar el reporte." |

---

## 7. Catálogo de pantallas

### UI-01 · Inicio de sesión

- **Ruta sugerida:** `/ingresar`
- **Roles:** público.
- **Endpoints:** `POST /autenticacion/iniciar-sesion`; opcional `GET /salud`.
- **Objetivo:** obtener el token y entrar al sistema.

**Estructura**

```text
┌──────────────────────────────────────────────┐
│              [Marca institucional]           │
│  Iniciar sesión                              │
│  Usuario        [__________________________] │
│  Contraseña     [__________________] [Ver]   │
│  [ Ingresar ]                                │
│  (aviso de error)                            │
│  (estado del servicio, opcional)             │
└──────────────────────────────────────────────┘
```

**Reglas**

- Campos: `nombre_usuario` y `contrasena`, ambos obligatorios.
- Permitir mostrar/ocultar la contraseña; no copiar ni registrar su valor.
- El error `401` se muestra genérico: "Usuario o contraseña incorrectos." No revelar si la
  cuenta existe o está inactiva.
- Deshabilitar "Ingresar" mientras se envía.
- Al éxito, guardar token y usuario; redirigir según rol:
  - Admin/Directivo y Preceptor → Panel.
  - Docente → Panel.
  - Alumno → Mi asistencia.
- Si ya hay un token válido, ir directamente al destino del rol.
- No mostrar "Crear cuenta" ni "Olvidé mi contraseña": no existen endpoints para eso.
- En desarrollo se pueden mostrar las credenciales de demostración en un bloque aparte,
  nunca en producción.
- `GET /salud` puede alimentar un indicador discreto de disponibilidad; no bloquear el login
  si falla.

### UI-02 · Panel de inicio

- **Ruta sugerida:** `/panel`
- **Roles:** todos, con contenido distinto.
- **Endpoints:** `GET /alertas`, `GET /asistencias-estudiantes/resumen`,
  `GET /grillas-horarias`, `GET /asistencias-docentes/firmas`,
  `GET /asistencias-docentes/balance-horas`.
- **Objetivo:** ofrecer un punto de partida con lo urgente y los accesos frecuentes.

**Contenido por rol**

- **Admin/Directivo y Preceptor**
  - Tarjeta "Alertas sin leer" (conteo calculado a partir de
    `GET /alertas?activa=true&leida=false`).
  - Accesos directos: Cargar asistencia, Resumen, Reportes.
  - Aviso si no hay período vigente al intentar un balance.
- **Docente**
  - "Mis clases de hoy" a partir de su grilla y del día actual.
  - "Firmas pendientes" del día: bloques sin ingreso o sin egreso.
  - Alertas de sus cursos.
  - Enlace a "Mi balance".
- **Alumno**
  - Tarjeta de regularidad con `GET /asistencias-estudiantes/resumen` sin parámetros.
  - Últimos registros propios.
  - Próximas clases de su horario, si logra resolver su curso (ver 4.4).

**Reglas**

- No existe un endpoint de agregación para el panel. Los valores que se muestran deben salir
  de endpoints documentados; no inventar un "resumen global" que el backend no calcula.
- Si se desea un indicador que requiera agregación del servidor, proponerlo como extensión
  del contrato antes de diseñarlo.
- No bloquear el panel completo si falla una tarjeta: mostrar el error sólo en esa tarjeta.
- Fecha y día actuales: obtenerlos de `GET /salud` (`marca_temporal_servidor`) si la
  exactitud del día es crítica; el reloj del cliente puede estar desfasado.

### UI-03 · Mi perfil

- **Ruta sugerida:** `/perfil`
- **Roles:** todos.
- **Endpoints:** `GET /autenticacion/perfil`.
- **Objetivo:** mostrar la identidad y el rol con los que opera la sesión.

**Contenido**

- Nombre de usuario, correo electrónico, rol, estado de la cuenta y fecha de creación.
- Botón "Cerrar sesión" (descarta el token localmente).
- Enlace a la pantalla principal del rol.

**Reglas**

- Vista de sólo lectura: no existe endpoint para editar datos personales ni contraseña.
- Si el perfil responde `401`, cerrar la sesión y volver al login.
- No mostrar identificadores internos salvo que aporten (por ejemplo, en una sección
  "Detalles técnicos" plegable).

### UI-04 · Usuarios

- **Ruta sugerida:** `/usuarios`
- **Roles:** Admin/Directivo.
- **Endpoints:** `GET /usuarios`, `POST /usuarios`, `GET /usuarios/{usuario_id}`,
  `PATCH /usuarios/{usuario_id}/estado`.
- **Objetivo:** administrar cuentas y su estado.

**Listado (P1)**

- Columnas: nombre de usuario, correo electrónico, rol, estado (Activa/Inactiva), creado en,
  acciones.
- Filtros: `rol` (los cuatro roles) y `activo` (Todos/Activas/Inactivas).
- Acciones por fila: "Ver detalle" y "Activar"/"Desactivar".
- Mostrar la cantidad de resultados devueltos por la consulta.

**Alta**

- Campos: `nombre_usuario`, `correo_electronico`, `contrasena`, `rol`.
- El rol es un select con los cuatro valores exactos del contrato.
- Tras crear, cerrar el formulario y refrescar el listado; mostrar el `mensaje`.

**Desactivar / activar**

- Pedir confirmación con el nombre de usuario.
- Si el backend responde `403` porque se intenta desactivar la propia cuenta, mostrar el
  mensaje del backend.
- No ofrecer eliminar ni restablecer contraseña.

**Estados**

- Sin resultados, error de carga, error de permisos y error de red con reintento.

### UI-05 · Estudiantes

- **Ruta sugerida:** `/estudiantes`
- **Roles:** consulta Admin/Directivo, Preceptor y Docente; alta sólo Admin/Directivo.
- **Endpoints:** `GET /estudiantes`, `POST /estudiantes`.
- **Objetivo:** consultar el padrón y dar de alta estudiantes con su cuenta.

**Listado (P1)**

- Filtro: `curso_id` (opcional).
- Columnas: legajo, nombre completo, fecha de nacimiento, usuario, correo, estado de cuenta.
- Acciones: "Ver detalle" si se implementa con los datos de la fila; no hay endpoint de
  detalle específico, por lo que se usa el objeto de la lista.
- Aclarar que el filtro por curso incluye estudiantes con matrícula en ese curso, incluso si
  la matrícula no está activa. Para el padrón de asistencia usar UI-10 y filtrar
  `estado === "Activo"`.

**Alta**

- Página completa con dos bloques: "Cuenta" y "Datos del estudiante".
- Campos de cuenta: `nombre_usuario`, `correo_electronico`, `contrasena`.
- Campos de estudiante: `legajo`, `nombres`, `apellidos`, `fecha_nacimiento` (opcional).
- Al crear, mostrar el estudiante y su cuenta; volver al listado.
- No ofrecer edición ni baja.

### UI-06 · Docentes

- **Ruta sugerida:** `/docentes`
- **Roles:** consulta Admin/Directivo, Preceptor y Docente; alta sólo Admin/Directivo.
- **Endpoints:** `GET /docentes`, `POST /docentes`.
- **Objetivo:** consultar el plantel docente y dar de alta docentes con su cuenta.

**Listado (P1)**

- Columnas: legajo, nombre completo, título habilitante, usuario, correo, estado de cuenta.
- Sin filtros documentados: si se agrega búsqueda, debe ser local y explícita.
- Acción "Ver detalle" con los datos de la fila.

**Alta**

- Bloques "Cuenta" y "Datos del docente".
- Campos: `nombre_usuario`, `correo_electronico`, `contrasena`, `legajo`, `nombres`,
  `apellidos`, `titulo_habilitante` (opcional).
- No ofrecer edición ni baja.

### UI-07 · Cursos

- **Ruta sugerida:** `/cursos`
- **Roles:** consulta todos; alta sólo Admin/Directivo.
- **Endpoints:** `GET /cursos`, `POST /cursos`.
- **Objetivo:** mantener el catálogo de cursos por año lectivo.

**Listado (P1)**

- Filtro: `anio_lectivo`.
- Columnas: nombre completo (`nombre_completo`), nombre, división, turno, año lectivo.
- Orden sugerido: año descendente, luego nombre y división.
- Sin acciones de edición.

**Alta**

- Campos: `nombre`, `division`, `anio_lectivo`, `turno`.
- Validar año lectivo numérico de cuatro dígitos; el backend acepta 2000–2200.
- `409` si el curso ya existe para el año.

**Uso como catálogo**

- Este listado alimenta los selectores de inscripciones, asignaciones, grilla, asistencia,
  resumen y reportes.

### UI-08 · Materias

- **Ruta sugerida:** `/materias`
- **Roles:** consulta todos; alta sólo Admin/Directivo.
- **Endpoints:** `GET /materias`, `POST /materias`.
- **Objetivo:** mantener el catálogo de materias.

**Listado (P1)**

- Columnas: código, nombre.
- Búsqueda local por nombre o código si el volumen lo justifica.
- Sin edición ni baja.

**Alta**

- Campos: `nombre`, `codigo`.
- `409` por nombre o código duplicado.
- El código se muestra en mayúsculas según el dato recibido; no transformarlo sin necesidad.

### UI-09 · Períodos académicos

- **Ruta sugerida:** `/periodos`
- **Roles:** consulta todos; alta sólo Admin/Directivo.
- **Endpoints:** `GET /periodos-academicos`, `POST /periodos-academicos`.
- **Objetivo:** definir los períodos usados en resúmenes, balances y reportes.

**Listado (P1)**

- Filtro: `anio_lectivo`.
- Columnas: nombre, fecha de inicio, fecha de fin, año lectivo.
- Indicar visualmente el período vigente si la fecha actual está entre inicio y fin (cálculo
  de presentación permitido, no de negocio).

**Alta**

- Campos: `nombre`, `fecha_inicio`, `fecha_fin`, `anio_lectivo`.
- Validar que la fecha final no sea anterior a la inicial antes de enviar.
- `409` si se repite nombre y año.

### UI-10 · Inscripciones

- **Ruta sugerida:** `/inscripciones`
- **Roles:** consulta Admin/Directivo, Preceptor y Docente; alta Admin/Directivo y Preceptor.
- **Endpoints:** `GET /inscripciones`, `POST /inscripciones`.
- **Objetivo:** matricular estudiantes en cursos y consultar el padrón.

**Listado (P1)**

- Filtros: `curso_id`, `estudiante_id`.
- Columnas: estudiante (`legajo`, `nombre_completo`), curso (`nombre_completo`), fecha de
  inscripción, estado (Activo/Inactivo).
- No existe endpoint para cambiar el estado de una inscripción: no mostrar esa acción.
- Para la carga de asistencia, usar este listado y conservar sólo `estado === "Activo"`.

**Alta**

- Campos: `estudiante_id`, `curso_id`, `fecha_inscripcion` (por defecto hoy),
  `estado` (por defecto Activo).
- Selectores de estudiante y curso desde sus catálogos.
- `404` si alguna referencia no existe; `409` si el estudiante ya está matriculado en el curso.
- Tras crear, refrescar el listado y el padrón de asistencia si está abierto.

### UI-11 · Asignaciones docentes

- **Ruta sugerida:** `/asignaciones`
- **Roles:** consulta Admin/Directivo, Preceptor y Docente; alta sólo Admin/Directivo.
- **Endpoints:** `GET /asignaciones-docentes`, `POST /asignaciones-docentes`.
- **Objetivo:** vincular docente, curso y materia antes de armar la grilla.

**Listado (P1)**

- Filtros: `docente_id`, `curso_id`, `materia_id`.
- Columnas: docente (legajo, nombre completo), curso (nombre completo), materia (código,
  nombre).
- Sin edición ni baja.

**Alta**

- Campos: `docente_id`, `curso_id`, `materia_id`.
- `404` por referencias inexistentes; `409` por asignación duplicada.
- La asignación debe existir antes de crear un bloque de grilla para ese docente, curso y
  materia.

### UI-12 · Grilla horaria

- **Ruta sugerida:** `/grilla`
- **Roles:** consulta todos; alta sólo Admin/Directivo.
- **Endpoints:** `GET /grillas-horarias`, `POST /grillas-horarias`.
- **Objetivo:** consultar y construir el horario institucional.

**Vistas**

1. **Listado (P1):** filtros `docente_id`, `curso_id`, `materia_id`, `anio_lectivo`,
   `dia_semana`. Columnas: día, hora inicio, hora fin, curso, materia, docente, aula.
2. **Semana:** grilla de lunes a domingo con bloques. No existe un endpoint de "campanas" o
   franjas fijas; construir las filas de horario a partir de las horas inicio/fin presentes
   en los datos. Si hay muchas franjas distintas, agrupar por intervalos de 30 o 60 minutos
   como decisión de presentación.

**Alta**

- Campos: `curso_id`, `materia_id`, `docente_id`, `dia_semana` (1–7), `hora_inicio`,
  `hora_fin`, `aula` (opcional).
- Mostrar los días con nombre, no con número.
- Validar `hora_inicio < hora_fin`.
- `400` si el docente no tiene asignación para ese curso y materia; `409` si el docente o el
  curso ya tienen un bloque a esa hora.
- Tras crear, refrescar la vista semanal.

**Vistas personales**

- Docente: "Mi horario" filtrando por su `docente_id` (ver 4.4).
- Alumno: "Mi horario" filtrando por su curso. Si no puede resolverlo, ofrecer una vista
  informativa y no mostrar horarios de otros cursos.

**Reglas**

- No ofrecer edición ni eliminación de bloques.
- No permitir crear un bloque sin asignación docente previa; enlazar a UI-11 si falta.

### UI-13 · Carga de asistencia estudiantil

- **Ruta sugerida:** `/asistencias/cargar`
- **Roles:** Admin/Directivo, Preceptor y Docente (sólo materias asignadas).
- **Endpoints:** `GET /cursos`, `GET /materias`, `GET /inscripciones`,
  `GET /estudiantes`, `GET /asistencias-estudiantes`, `POST /asistencias-estudiantes`.
- **Objetivo:** registrar o actualizar la asistencia de una clase completa.

**Estructura (P3)**

```text
┌ Cargar asistencia ────────────────────────────────────────────────┐
│ Curso [1° Año A (2026) ▾]  Materia [Matemática ▾]  Fecha [hoy]    │
│ ─────────────────────────────────────────────────────────────────  │
│ [Marcar todos presentes]  [Limpiar marcas]     12 estudiantes      │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Estudiante            │ Presente │ Ausente │ Justif. │ Tarde   │  │
│ │ Pérez, Juan           │   (•)    │   ( )   │   ( )   │  ( )    │  │
│ │ Gómez, Lucía          │   (•)    │   ( )   │   ( )   │  ( )    │  │
│ │ …                     │          │         │         │         │  │
│ └───────────────────────────────────────────────────────────────┘  │
│ Observación general / por estudiante (opcional)                    │
│ [Guardar asistencia]                                               │
└────────────────────────────────────────────────────────────────────┘
```

**Flujo**

1. Cargar cursos y materias.
2. Si el usuario es Docente, limitar las combinaciones a las asignaciones que puede consultar
   (`GET /asignaciones-docentes?docente_id=<propio>`). No mostrar materias no asignadas.
3. Elegir curso, materia y fecha. La fecha por defecto es hoy y no puede ser futura; usar la
   fecha del servidor (`GET /salud`) como referencia si el reloj del cliente no es confiable.
4. Obtener el padrón con `GET /inscripciones?curso_id=<id>` y conservar sólo las matrículas
   activas. Alternativamente `GET /estudiantes?curso_id=<id>`, sabiendo que no distingue
   matrículas inactivas.
5. Consultar registros existentes con
   `GET /asistencias-estudiantes?curso_id=<id>&materia_id=<id>&fecha=<AAAA-MM-DD>`.
6. Precargar el estado y la observación de cada estudiante que ya tenga registro.
7. Para los estudiantes sin registro, proponer "Presente" como valor inicial y permitir
   cambiarlo. La acción "Marcar todos presentes" debe ser explícita y reversible.
8. Enviar un único `POST /asistencias-estudiantes` con `curso_id`, `materia_id`, `fecha` y
   `registros` (lista no vacía, sin estudiantes repetidos).
9. Mostrar el resultado: `creados`, `actualizados` y los registros devueltos.
10. Avisar que la operación puede generar alertas automáticas.

**Campos por registro**

- `estudiante_id`: obligatorio, entero.
- `estado`: obligatorio, uno de `Presente`, `Ausente`, `Justificado`, `Tarde`.
- `observacion`: opcional, texto de hasta 500 caracteres.

**Reglas y errores**

- `400` por fecha futura, estado inválido, estudiante no matriculado activamente o repetido.
- `403` si el Docente no tiene asignada esa materia en el curso.
- `404` si el curso o la materia no existen.
- La operación es idempotente: si ya existe registro para esa fecha, curso, materia y
  estudiante, se actualiza. Informarlo antes de guardar cuando se detecten registros previos.
- No permitir guardar con la lista vacía.
- No enviar `estado` en mayúsculas ni variantes; usar los valores exactos.
- Si el backend devuelve un error de validación con `detalles`, mostrarlo sin asumir formato.

**Accesibilidad**

- Cada estudiante debe tener un grupo de opciones con nombre accesible que incluya su nombre.
- La tabla debe poder recorrerse con teclado sin perder la fila.
- No usar sólo color para indicar el estado seleccionado.
- Anunciar el resultado del guardado en una región `aria-live`.

### UI-14 · Consulta de asistencias

- **Ruta sugerida:** `/asistencias`
- **Roles:** todos. Alumno sólo sus propios registros; Docente los de sus cursos.
- **Endpoints:** `GET /asistencias-estudiantes`.
- **Objetivo:** consultar registros históricos de asistencia.

**Filtros (P1)**

- `estudiante_id`, `curso_id`, `materia_id`, `fecha`, `fecha_desde`, `fecha_hasta`.
- Para Alumno: no mostrar el filtro de estudiante; el backend fuerza su identidad.
- Para Docente: no ofrecer estudiantes o cursos fuera de su alcance; el backend responde
  `403` si se intenta.

**Columnas**

- Fecha, estudiante (legajo, nombre completo), curso (nombre completo), materia (código,
  nombre), estado, observación, registrado por (id).
- Los objetos anidados llegan completos; mostrar los campos relevantes, no el JSON crudo.

**Reglas**

- El rango de fechas debe ser coherente (`fecha_desde <= fecha_hasta`).
- No ofrecer exportación desde esta pantalla: los reportes formales son UI-21.
- No ofrecer edición ni eliminación. Para corregir, volver a UI-13 (actualiza el registro).
- Estado vacío específico y enlace a "Cargar asistencia" si el rol puede hacerlo.

### UI-15 · Resumen y regularidad

- **Ruta sugerida:** `/resumen`
- **Roles:** todos. Alumno sólo el propio.
- **Endpoints:** `GET /asistencias-estudiantes/resumen`.
- **Objetivo:** mostrar porcentajes, umbral y estado de regularidad por estudiante o por curso.

**Modos**

1. **Por estudiante**
   - Filtros: `estudiante_id` (Admin/Preceptor/Docente), `periodo_id`, `materia_id`,
     `estrategia`.
   - Para Alumno: no mostrar selector de estudiante; el backend usa su identidad.
   - La respuesta tiene `alcance: "estudiante"`.
   - Mostrar tarjetas: total de registros, presentes, ausentes, justificados, tardes,
     porcentaje de asistencia, presentismo efectivo, umbral y estado.
   - Tabla `detalle_por_materia` con el mismo resumen por materia.

2. **Por curso**
   - Filtros: `curso_id`, `periodo_id`, `materia_id`, `estrategia`.
   - La respuesta tiene `alcance: "curso"`.
   - Mostrar `resumen_general` y una tabla de estudiantes con su resumen.
   - Ordenar por estado (En riesgo primero) y luego por nombre.

**Reglas**

- El umbral **se toma de `umbral_regularidad_porcentaje`**; no hardcodear 75.
- Los estados posibles son `Regular`, `En riesgo` y `Sin datos`.
- `Sin datos` no equivale a `En riesgo`; usar un tratamiento visual neutro.
- Mostrar la estrategia aplicada (`institucional` o `estricta`) y permitir cambiarla sólo a
  Admin/Directivo y Preceptor. Para Docente y Alumno, mostrar la estrategia vigente sin
  selector si se decide simplificar la vista.
- Explicar la diferencia entre "asistencia" y "presentismo efectivo" con una ayuda breve:
  el presentismo efectivo excluye los justificados en la estrategia institucional.
- Si `periodo` es `null`, indicar "Todos los registros" y no inventar un período.
- `400` si no se indica estudiante ni curso (excepto Alumno); `403` por consulta ajena.
- No calcular porcentajes localmente ni sumar filas para reemplazar el resumen general.

### UI-16 · Alertas

- **Ruta sugerida:** `/alertas`
- **Roles:** Admin/Directivo, Preceptor y Docente (sólo estudiantes de sus cursos).
- **Endpoints:** `GET /alertas`, `PATCH /alertas/{alerta_id}/marcar-leida`.
- **Objetivo:** revisar y dar por leídas las alertas generadas automáticamente.

**Listado**

- Filtros: `estudiante_id`, `activa` (Todas/Activas/Inactivas), `leida`
  (Todas/Leídas/No leídas).
- Presentación recomendada: tarjetas o tabla con columnas fecha de generación, estudiante,
  tipo, nivel, mensaje, estado (Activa/Inactiva, Leída/No leída).
- `nivel`: `Alta` o `Media`.
- `tipo`: `Inasistencias consecutivas` o `Regularidad en riesgo`.
- `porcentaje_asistencia` puede ser `null`; mostrar `—` cuando no aplique.
- Indicar visualmente las no leídas, pero también con texto o ícono accesible.

**Acciones**

- "Marcar como leída" por alerta; no requiere cuerpo.
- Actualizar la fila con `leida: true` usando la respuesta.
- No ofrecer crear, editar, desactivar ni eliminar alertas: las genera el backend.
- No exigir confirmación para marcar como leída.

**Reglas**

- Ordenar por fecha de generación descendente y luego por nivel.
- Si el Docente intenta marcar una alerta fuera de sus cursos, el backend responde `403`;
  mostrar el mensaje.
- El refresco automático es opcional y debe ser visible y pausable; no interrumpir la lectura.

### UI-17 · Firmas docentes

- **Ruta sugerida:** `/asistencias-docentes/firmas`
- **Roles:** Admin/Directivo, Preceptor y Docente (sólo sus propias firmas).
- **Endpoints:** `GET /grillas-horarias`, `GET /asistencias-docentes/firmas`,
  `POST /asistencias-docentes/firmas`.
- **Objetivo:** registrar ingreso y egreso docente y consultar el historial.

**Bloque "Firmar hoy"**

- Para Docente: mostrar únicamente sus bloques del día actual, sin selector de docente.
- Para Admin/Preceptor: seleccionar docente y luego sus bloques del día.
- Un bloque sólo es firmable si `dia_semana` coincide con el día actual. El backend valida
  esta regla; la interfaz debe evitar ofrecer bloques de otros días.
- Mostrar por bloque: curso, materia, hora inicio, hora fin, aula y estado de firmas del día.
- Estado derivado de las firmas consultadas:
  - Sin ingreso: mostrar "Firmar ingreso".
  - Con ingreso y sin egreso: mostrar "Firmar egreso" y la hora de ingreso.
  - Con ingreso y egreso: "Completo", sin acciones.
- No mostrar un campo de hora editable: la marca de tiempo la genera el servidor.
- Pedir confirmación breve con el bloque y el tipo de firma antes de enviar, para evitar
  errores por clic accidental.
- Deshabilitar el botón mientras se envía; no permitir doble envío.

**Cuerpo**

- `tipo_firma`: `Ingreso` o `Egreso`.
- `grilla_horaria_id`: bloque seleccionado.
- `docente_id`: obligatorio para Admin/Preceptor; el Docente no debe enviarlo.

**Resultado**

- Mostrar la firma registrada con `marca_temporal` del servidor.
- Si la respuesta trae `incidencia`, mostrarla como aviso: tipo, minutos de desviación y
  descripción. No ocultarla ni reinterpretarla.
- `409`: firma duplicada, egreso sin ingreso previo o egreso anterior al ingreso. Explicar el
  caso y refrescar el estado del bloque.
- `400`: bloque que no corresponde al día o tipo inválido.
- `403`: intento de firmar para otro docente o bloque ajeno.
- `404`: bloque inexistente.

**Historial**

- Tabla con filtros `docente_id` (sólo Admin/Preceptor), `fecha_desde`, `fecha_hasta`.
- Columnas: fecha, docente, bloque (día, hora inicio, hora fin), tipo de firma, marca de
  tiempo, observación.
- Para Docente, no mostrar el filtro de docente y no listar firmas ajenas.
- No ofrecer edición ni eliminación.

**Referencia temporal**

- Para determinar "hoy" y el día de la semana, usar la marca de tiempo del servidor
  (`GET /salud`) si el reloj del cliente puede estar desfasado. La habilitación de botones es
  una ayuda visual; la regla definitiva la aplica el backend.

### UI-18 · Incidencias docentes

- **Ruta sugerida:** `/asistencias-docentes/incidencias`
- **Roles:** Admin/Directivo, Preceptor y Docente (sólo las propias).
- **Endpoints:** `GET /asistencias-docentes/incidencias`.
- **Objetivo:** consultar tardanzas, salidas anticipadas, ausencias y licencias.

**Listado (P1)**

- Filtros: `docente_id` (sólo Admin/Preceptor), `fecha_desde`, `fecha_hasta`, `tipo`.
- `tipo`: `Tardanza`, `Salida anticipada`, `Ausencia`, `Licencia`.
- Columnas: fecha, docente, tipo, minutos de desviación, descripción, generada
  automáticamente, registrada por (id), bloque asociado (`grilla_horaria_id`).
- Distinguir visualmente las generadas automáticamente de las manuales (licencias).
- Vista de sólo lectura: no hay endpoint para editar ni eliminar incidencias.
- Para Docente, ocultar el filtro de docente y no mostrar datos ajenos.

### UI-19 · Licencias docentes

- **Ruta sugerida:** `/asistencias-docentes/licencias`
- **Roles:** Admin/Directivo y Preceptor.
- **Endpoints:** `POST /asistencias-docentes/licencias`,
  `GET /asistencias-docentes/incidencias?tipo=Licencia`.
- **Objetivo:** registrar licencias y consultar las existentes.

**Formulario**

- Campos: `docente_id`, `fecha`, `motivo`, `grilla_horaria_id` (opcional).
- El motivo es obligatorio, hasta 500 caracteres. Usar un área de texto con contador.
- El bloque horario es opcional; si se elige, limitarlo a bloques del docente.
- `404` si el docente o la grilla no existen; `409` si ya hay una licencia para ese docente en
  la misma fecha.
- Tras crear, limpiar el formulario y refrescar el listado de licencias.

**Listado**

- Reutilizar la tabla de UI-18 con `tipo=Licencia` fijo y filtros de fechas/docente.
- No existe un `GET /licencias` dedicado; no inventarlo.

### UI-20 · Balance de horas cátedra

- **Ruta sugerida:** `/asistencias-docentes/balance`
- **Roles:** Admin/Directivo y Preceptor (cualquier docente); Docente (sólo el propio).
- **Endpoints:** `GET /asistencias-docentes/balance-horas`.
- **Objetivo:** mostrar horas esperadas, laboradas, saldo y cumplimiento por período.

**Filtros**

- `periodo_id`: opcional. Si se omite, el backend usa el período vigente; si no hay período
  vigente, responde `400`. En ese caso, pedir al usuario que seleccione un período.
- `docente_id`: opcional para Admin/Preceptor; oculto para Docente.
- `estrategia`: `exacta` o `por_bloques`, opcional.

**Contenido (P4)**

- Encabezado con el período aplicado (nombre y fechas).
- Por cada docente:
  - Tarjetas: clases esperadas, completas, incompletas, sin firma, horas esperadas, horas
    laboradas, saldo de horas cátedra y porcentaje de cumplimiento.
  - Tabla `detalle_clases`: fecha, curso, materia, hora inicio, hora fin, minutos esperados,
    minutos laborados, estado (`Completa`, `Incompleta`, `Sin firma`).
- `saldo_horas_catedra` negativo se destaca como déficit; positivo como excedente. No usar
  sólo color.
- `porcentaje_cumplimiento` en escala 0–100; mostrar con dos decimales y `%`.
- `minutos_hora_catedra` explica la conversión; mostrarlo en la ayuda o en el encabezado.
- Docente: la respuesta contiene sólo su balance; no mostrar selector de docente.
- `403` si un Docente consulta a otro.
- Estado vacío: "No hay clases en el período seleccionado."

### UI-21 · Reportes

- **Ruta sugerida:** `/reportes`
- **Roles:** Admin/Directivo y Preceptor.
- **Endpoints:** `GET /reportes/asistencia-estudiantes.pdf`,
  `GET /reportes/asistencia-estudiantes.xlsx`, `GET /reportes/horas-docentes.pdf`,
  `GET /reportes/horas-docentes.xlsx`.
- **Objetivo:** descargar los reportes formales.

**Contenido (P5)**

1. **Asistencia de estudiantes**
   - Campos obligatorios: `curso_id`, `periodo_id`.
   - Campo opcional: `estrategia` (`institucional` o `estricta`).
   - Botones: "Descargar PDF" y "Descargar Excel".
2. **Horas docentes**
   - Campo obligatorio: `periodo_id`.
   - Campo opcional: `estrategia` (`exacta` o `por_bloques`).
   - Botones: "Descargar PDF" y "Descargar Excel".

**Reglas**

- No mostrar vista previa: el backend no la ofrece.
- Validar los campos obligatorios antes de habilitar las descargas.
- `400` por formato no soportado (ruta inválida) o estrategia inválida; `404` por curso o
  período inexistente.
- Manejar la descarga como binario con `Authorization` (ver 3.5).
- Nombre de archivo esperado:
  `reporte_asistencia_estudiantes_curso_<curso>_periodo_<periodo>.<ext>` o
  `reporte_horas_docentes_periodo_<periodo>.<ext>`.
- No ofrecer programación, envío por correo ni historial de reportes: no existen endpoints.

### UI-22 · Configuración institucional

- **Ruta sugerida:** `/configuracion`
- **Roles:** Admin/Directivo.
- **Endpoints:** `GET /configuracion`, `PUT /configuracion/{clave}`.
- **Objetivo:** consultar y actualizar los parámetros que afectan cálculos y alertas.

**Listado**

- Mostrar `parametros` con clave, valor, descripción.
- Mostrar también `valores_aplicados`, que incluye la zona horaria institucional y los
  valores tipados vigentes.
- Agrupar visualmente:
  - Reglas de asistencia: `umbral_regularidad_porcentaje`,
    `estrategia_calculo_asistencia`.
  - Reglas de alertas: `limite_inasistencias_consecutivas`.
  - Reglas de horas docentes: `minutos_hora_catedra`, `estrategia_calculo_horas`,
    `tolerancia_minutos_firma`.
- La zona horaria se muestra como sólo lectura: no figura entre las claves actualizables.

**Edición**

- Un formulario por clave o edición en línea con "Guardar".
- Enviar `PUT /configuracion/{clave}` con `{ "valor": "<texto>" }`.
- Controles según la clave:
  - Porcentaje: número entero de 0 a 100.
  - Límite de inasistencias: entero mayor que cero.
  - Minutos de hora cátedra: entero mayor que cero.
  - Tolerancia de firma: entero mayor o igual a cero.
  - Estrategia de asistencia: select `institucional` / `estricta`.
  - Estrategia de horas: select `exacta` / `por_bloques`.
- Advertir que los cambios afectan cálculos futuros y pueden alterar la interpretación de
  datos existentes; los totales no están almacenados.
- `400` por valor no numérico, fuera de rango o estrategia inexistente; `404` por clave
  desconocida.
- Mostrar el valor devuelto y refrescar `valores_aplicados`.
- No ofrecer crear ni eliminar parámetros.

---

## 8. Diccionario de campos y validaciones

Los máximos indicados provienen de la validación vigente del backend. Cuando el contrato no
fija un máximo, la interfaz debe guiar pero no bloquear de forma más estricta que el servidor.

### 8.1 Cuenta de usuario

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre_usuario` | texto | Sí | 3–80; letras, números, puntos, guiones y guiones bajos |
| `correo_electronico` | email | Sí | Formato de correo; máximo 255 |
| `contrasena` | password | Sí | Mínimo 8; máximo 128 |
| `rol` | select | Sí | `Admin/Directivo`, `Preceptor`, `Docente`, `Alumno` |

### 8.2 Estudiante

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre_usuario` | texto | Sí | Igual que cuenta |
| `correo_electronico` | email | Sí | Igual que cuenta |
| `contrasena` | password | Sí | Igual que cuenta |
| `legajo` | texto | Sí | Máximo 30; único |
| `nombres` | texto | Sí | Máximo 120 |
| `apellidos` | texto | Sí | Máximo 120 |
| `fecha_nacimiento` | date | No | `AAAA-MM-DD`; no futura (validación de interfaz) |

### 8.3 Docente

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre_usuario` | texto | Sí | Igual que cuenta |
| `correo_electronico` | email | Sí | Igual que cuenta |
| `contrasena` | password | Sí | Igual que cuenta |
| `legajo` | texto | Sí | Máximo 30; único |
| `nombres` | texto | Sí | Máximo 120 |
| `apellidos` | texto | Sí | Máximo 120 |
| `titulo_habilitante` | texto | No | Máximo 255 |

### 8.4 Curso

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre` | texto | Sí | Máximo 80 |
| `division` | texto | Sí | Máximo 20 |
| `anio_lectivo` | number | Sí | Entero 2000–2200 |
| `turno` | texto | Sí | Máximo 40 |

### 8.5 Materia

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre` | texto | Sí | Máximo 120; único |
| `codigo` | texto | Sí | Máximo 30; único |

### 8.6 Período académico

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `nombre` | texto | Sí | Máximo 100 |
| `fecha_inicio` | date | Sí | `AAAA-MM-DD` |
| `fecha_fin` | date | Sí | `AAAA-MM-DD`; no anterior a inicio |
| `anio_lectivo` | number | Sí | Entero 2000–2200 |

### 8.7 Inscripción

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `estudiante_id` | select | Sí | Estudiante existente |
| `curso_id` | select | Sí | Curso existente |
| `fecha_inscripcion` | date | No | Por defecto, fecha del servidor |
| `estado` | select | No | `Activo` (por defecto) o `Inactivo` |

### 8.8 Asignación docente

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `docente_id` | select | Sí | Docente existente |
| `curso_id` | select | Sí | Curso existente |
| `materia_id` | select | Sí | Materia existente |

### 8.9 Grilla horaria

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `curso_id` | select | Sí | Curso existente |
| `materia_id` | select | Sí | Materia existente |
| `docente_id` | select | Sí | Docente con asignación para curso y materia |
| `dia_semana` | select | Sí | 1 = lunes … 7 = domingo |
| `hora_inicio` | time | Sí | `HH:MM` |
| `hora_fin` | time | Sí | `HH:MM`; posterior a inicio |
| `aula` | texto | No | Máximo 60 |

### 8.10 Carga de asistencia

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `curso_id` | select | Sí | Curso existente |
| `materia_id` | select | Sí | Materia existente |
| `fecha` | date | Sí | No futura |
| `registros` | lista | Sí | No vacía; un elemento por estudiante |
| `registros[].estudiante_id` | oculto | Sí | Matriculado activamente en el curso |
| `registros[].estado` | radio/select | Sí | `Presente`, `Ausente`, `Justificado`, `Tarde` |
| `registros[].observacion` | textarea | No | Máximo 500 |

### 8.11 Firma docente

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `tipo_firma` | select | Sí | `Ingreso` o `Egreso` |
| `grilla_horaria_id` | oculto/select | Sí | Bloque del docente para el día actual |
| `docente_id` | select | Condicional | Obligatorio para Admin/Preceptor; omitido por Docente |

### 8.12 Licencia docente

| Campo | Control | Obligatorio | Regla |
|---|---|---|---|
| `docente_id` | select | Sí | Docente existente |
| `fecha` | date | Sí | `AAAA-MM-DD` |
| `motivo` | textarea | Sí | Máximo 500 |
| `grilla_horaria_id` | select | No | Bloque del docente |

### 8.13 Filtros de consulta

| Endpoint | Parámetros |
|---|---|
| `GET /usuarios` | `rol`, `activo` |
| `GET /estudiantes` | `curso_id` |
| `GET /cursos` | `anio_lectivo` |
| `GET /periodos-academicos` | `anio_lectivo` |
| `GET /inscripciones` | `curso_id`, `estudiante_id` |
| `GET /asignaciones-docentes` | `docente_id`, `curso_id`, `materia_id` |
| `GET /grillas-horarias` | `docente_id`, `curso_id`, `materia_id`, `anio_lectivo`, `dia_semana` |
| `GET /asistencias-estudiantes` | `estudiante_id`, `curso_id`, `materia_id`, `fecha`, `fecha_desde`, `fecha_hasta` |
| `GET /asistencias-estudiantes/resumen` | `estudiante_id`, `curso_id`, `materia_id`, `periodo_id`, `estrategia` |
| `GET /alertas` | `estudiante_id`, `activa`, `leida` |
| `GET /asistencias-docentes/firmas` | `docente_id`, `fecha_desde`, `fecha_hasta` |
| `GET /asistencias-docentes/incidencias` | `docente_id`, `fecha_desde`, `fecha_hasta`, `tipo` |
| `GET /asistencias-docentes/balance-horas` | `periodo_id`, `docente_id`, `estrategia` |

---

## 9. Flujos críticos

### 9.1 Ingreso y sesión

1. Mostrar UI-01.
2. Enviar credenciales.
3. Si `401`, mostrar mensaje genérico y permitir reintentar.
4. Si `200`, guardar `token_acceso`, `usuario` y `expira_en_minutos`.
5. Redirigir según rol.
6. En cada arranque posterior, validar con `GET /autenticacion/perfil`.
7. Ante `401` en cualquier petición, limpiar la sesión y volver a UI-01 con aviso.

### 9.2 Carga diaria de asistencia

1. El usuario elige curso, materia y fecha (UI-13).
2. La interfaz valida que la fecha no sea futura.
3. Carga el padrón activo y los registros existentes.
4. Precarga estados y observaciones.
5. El usuario ajusta estados.
6. Se envía una sola petición con todos los registros.
7. Se informa `creados` y `actualizados`.
8. Se advierte que pueden haberse generado alertas.
9. Si se recarga la misma clase, los datos vuelven a precargarse y el guardado actualiza.

### 9.3 Consulta de regularidad

1. El usuario elige modo (estudiante o curso), período y materia opcional (UI-15).
2. Para Alumno, no se envía `estudiante_id`.
3. La interfaz lee `alcance` y renderiza la variante correspondiente.
4. Muestra porcentajes, umbral y estado.
5. Si el estado es `En riesgo`, ofrece enlace a Alertas (si el rol puede verlas) y a la
   consulta de asistencias para revisar el detalle.
6. No recalcula ni redondea los valores del backend.

### 9.4 Firma docente

1. Determinar la fecha y el día actuales con la marca del servidor.
2. Listar los bloques del docente para hoy.
3. Consultar las firmas del día y derivar el estado de cada bloque.
4. El usuario elige "Firmar ingreso" o "Firmar egreso".
5. Confirmar el bloque y el tipo.
6. Enviar sin fecha ni hora.
7. Mostrar la marca de tiempo del servidor.
8. Si hay incidencia, mostrarla.
9. Si hay `409`, refrescar el estado y explicar el motivo.

### 9.5 Descarga de reporte

1. El usuario completa curso y período (o sólo período).
2. Elige PDF o XLSX.
3. Se valida localmente lo obligatorio.
4. Se solicita el archivo con `Authorization`.
5. Si la respuesta es JSON, se muestra el error.
6. Si es binaria, se descarga con el nombre indicado.
7. Se restablece el botón y se confirma la descarga.

### 9.6 Actualización de configuración

1. Cargar parámetros y valores aplicados.
2. El usuario edita un valor.
3. Validar según la clave.
4. Enviar `PUT` con `valor` como texto.
5. Mostrar confirmación.
6. Refrescar la lista y los valores aplicados.
7. Advertir el impacto en cálculos y alertas.

---

## 10. Convenciones de presentación

### 10.1 Nombres y entidades

- Usar `nombre_completo` para mostrar personas (`Pérez, Juan`).
- Usar `nombre_completo` de curso (`1° Año A (2026)`) cuando exista; evita ambigüedades.
- Para materias, mostrar `código — nombre` en selects y `nombre` en columnas si el código ya
  está en otra columna.
- Mostrar legajos tal como llegan (`ALU-2026-001`), sin truncar.
- No cambiar mayúsculas, acentos ni signos de los valores de enumeración.

### 10.2 Badges y estados

| Dominio | Valor | Tratamiento sugerido |
|---|---|---|
| Asistencia | `Presente` | verde |
| Asistencia | `Ausente` | rojo |
| Asistencia | `Justificado` | azul o gris |
| Asistencia | `Tarde` | ámbar |
| Regularidad | `Regular` | verde |
| Regularidad | `En riesgo` | rojo o ámbar |
| Regularidad | `Sin datos` | gris |
| Nivel de alerta | `Alta` | rojo |
| Nivel de alerta | `Media` | ámbar |
| Incidencia | `Tardanza` | ámbar |
| Incidencia | `Salida anticipada` | ámbar |
| Incidencia | `Ausencia` | rojo |
| Incidencia | `Licencia` | azul |
| Clase | `Completa` | verde |
| Clase | `Incompleta` | ámbar |
| Clase | `Sin firma` | gris |
| Cuenta | Activa / Inactiva | verde / gris |
| Inscripción | Activo / Inactivo | verde / gris |
| Firma | `Ingreso` / `Egreso` | azul / violeta |

Reglas:

- Todo badge lleva texto; el color es un refuerzo, nunca el único portador del significado.
- Verificar contraste AA en texto y fondo.
- No usar rojo para "Sin datos": no es un error.
- El estado de regularidad se toma de `estado_regularidad`, no se deriva del porcentaje en el
  cliente (el backend aplica la estrategia).

### 10.3 Copy

- Español institucional, frases cortas, sin abreviaturas ambiguas.
- Verbos en infinitivo para acciones ("Guardar", "Descargar", "Marcar como leída").
- Evitar "OK" y "Aceptar" genéricos; usar el verbo de la acción.
- Los mensajes de error del backend se muestran completos; no reemplazarlos por "Error".
- Para confirmaciones, nombrar el objeto: "¿Desactivar la cuenta `preceptoria`?".
- Fechas y horas con el formato de la sección 3.4.

---

## 11. Errores, carga y estados

### 11.1 Tratamiento por código

| Código HTTP | Código de error | Tratamiento de interfaz |
|---|---|---|
| 400 | `datos_invalidos` | Mostrar `mensaje`; resaltar campos si se pueden identificar; conservar datos |
| 401 | `no_autenticado` | Limpiar sesión; volver al login con aviso; conservar formulario si es posible |
| 403 | `acceso_prohibido` | Bloque informativo dentro de la pantalla; no ofrecer reintento |
| 404 | `recurso_no_encontrado` | "El recurso ya no existe"; ofrecer volver al listado |
| 409 | `conflicto_de_datos` | Explicar duplicado o conflicto; permitir corregir; no reintentar solo |
| 500 | `error_interno` | Aviso genérico con opción de reintentar; no mostrar detalles técnicos |

### 11.2 Estados de pantalla

Toda pantalla que consulta datos debe definir:

1. **Inicial:** sin datos todavía, con filtros por defecto.
2. **Cargando:** indicador o esqueleto; `aria-busy`.
3. **Con datos:** contenido normal.
4. **Vacío:** consulta exitosa sin resultados.
5. **Error de validación:** filtros inválidos.
6. **Error de permisos:** `403`.
7. **Error de recurso:** `404`.
8. **Error de red/servidor:** mensaje y reintento.

### 11.3 Mensajes sugeridos

- Login fallido: "Usuario o contraseña incorrectos."
- Sesión expirada: "Tu sesión expiró. Volvé a ingresar."
- Sin permisos: "No tenés permisos para realizar esta acción."
- Recurso inexistente: "El recurso solicitado ya no existe."
- Conflicto de matrícula: mostrar el `mensaje` del backend.
- Fecha futura: "No se puede registrar asistencia de una fecha futura."
- Firma duplicada: mostrar el `mensaje` del backend.
- Descarga fallida: "No se pudo generar el reporte. Intentá nuevamente."

---

## 12. Accesibilidad, semántica HTML y responsive

### 12.1 Estructura semántica

- `header` para el encabezado, `nav` para la navegación principal, `main` para el contenido y
  `footer` si se agrega información institucional.
- Un `h1` por pantalla; jerarquía de encabezados sin saltos.
- `section` con `aria-labelledby` para los bloques principales.
- `table` con `caption` y `th scope`; no usar tablas para maquetar.
- `form` con `fieldset` y `legend` cuando haya grupos de campos relacionados (por ejemplo,
  datos de cuenta y datos del estudiante, o el estado de cada alumno).
- `button` para acciones y `a` para navegación; no usar `div` clicables.
- `time datetime="AAAA-MM-DD"` para fechas cuando se muestre la versión localizada.
- `dialog` nativo o modal con foco atrapado, cierre con `Esc` y retorno de foco al disparador.

### 12.2 Formularios accesibles

- `label for` en todos los campos; placeholder no reemplaza la etiqueta.
- `aria-describedby` para ayudas y errores.
- `aria-invalid="true"` en campos con error.
- Resumen de errores al inicio, con enlaces a cada campo.
- No deshabilitar el envío por errores que el usuario todavía no puede ver sin explicar por qué.
- Mantener el foco en el primer campo con error tras un envío fallido.
- No usar el color como único indicador de error.

### 12.3 Tablas accesibles

- Encabezados claros y repetidos en cada tabla.
- `aria-sort` sólo si hay ordenamiento real.
- Si una fila se puede abrir, incluir un enlace o botón con nombre accesible.
- En móvil, permitir desplazamiento horizontal con indicador visual o transformar la fila en
  una tarjeta con etiquetas.
- Evitar tablas de más de 7 columnas en móvil sin una vista alternativa.

### 12.4 Carga de asistencia accesible

- Cada alumno es un grupo de opciones con su nombre en el `legend`.
- Los atajos de teclado no deben provocar cambios accidentales.
- "Marcar todos presentes" debe anunciar cuántos registros cambió.
- El resultado del guardado se anuncia en una región `aria-live="polite"`.
- En móvil, mostrar una tarjeta por alumno con botones de estado grandes.

### 12.5 Responsive

- Priorizar escritorio para gestión académica y reportes.
- Priorizar tableta/teléfono para carga de asistencia y firmas.
- Evitar menús que oculten la acción principal en pantallas chicas.
- No usar hover como única forma de revelar acciones.
- Mantener el botón de guardar accesible sin desplazamiento excesivo cuando sea posible.

### 12.6 Movimiento y tiempo

- Respetar `prefers-reduced-motion`.
- No usar animaciones para indicar estados críticos.
- No cerrar sesión automáticamente sin aviso mientras hay un formulario con datos.
- No recargar listados mientras el usuario está leyendo, salvo que el refresco sea visible y
  pausable.

---

## 13. Seguridad de la interfaz

- El token nunca se muestra en pantalla ni se registra en consola.
- No construir URLs con el token.
- No confiar en el ocultamiento de botones como control de seguridad.
- Validar en el cliente sólo para mejorar la experiencia; el backend valida de nuevo.
- Escapar todo texto proveniente de la API antes de insertarlo en el DOM. Los mensajes de
  alerta incluyen nombres y legajos.
- No interpretar HTML dentro de `mensaje`, `descripcion` u `observacion`.
- Descargar archivos sólo desde los endpoints documentados.
- Al cerrar sesión, limpiar token, usuario y cualquier caché de datos personales.
- Evitar guardar datos de estudiantes en almacenamiento persistente del navegador; mantenerlos
  en memoria o en caché de sesión.
- No incluir datos personales en la URL más allá de identificadores necesarios para filtros.

---

## 14. Trazabilidad endpoint → pantalla

| Endpoint | Pantallas |
|---|---|
| `GET /salud` | UI-01, UI-02, UI-13, UI-17 |
| `POST /autenticacion/iniciar-sesion` | UI-01 |
| `GET /autenticacion/perfil` | UI-02, UI-03 |
| `GET /usuarios` | UI-04 |
| `POST /usuarios` | UI-04 |
| `GET /usuarios/{usuario_id}` | UI-04 |
| `PATCH /usuarios/{usuario_id}/estado` | UI-04 |
| `GET /estudiantes` | UI-05, UI-13, UI-14 |
| `POST /estudiantes` | UI-05 |
| `GET /docentes` | UI-06, UI-11, UI-17, UI-19, UI-20 |
| `POST /docentes` | UI-06 |
| `GET /cursos` | UI-07, UI-10, UI-11, UI-12, UI-13, UI-15, UI-21 |
| `POST /cursos` | UI-07 |
| `GET /materias` | UI-08, UI-11, UI-12, UI-13, UI-15, UI-21 |
| `POST /materias` | UI-08 |
| `GET /periodos-academicos` | UI-09, UI-15, UI-20, UI-21 |
| `POST /periodos-academicos` | UI-09 |
| `GET /inscripciones` | UI-10, UI-13 |
| `POST /inscripciones` | UI-10 |
| `GET /asignaciones-docentes` | UI-11, UI-13, UI-17 |
| `POST /asignaciones-docentes` | UI-11 |
| `GET /grillas-horarias` | UI-02, UI-12, UI-17, UI-19 |
| `POST /grillas-horarias` | UI-12 |
| `POST /asistencias-estudiantes` | UI-13 |
| `GET /asistencias-estudiantes` | UI-02, UI-13, UI-14 |
| `GET /asistencias-estudiantes/resumen` | UI-02, UI-15 |
| `GET /alertas` | UI-02, UI-16 |
| `PATCH /alertas/{alerta_id}/marcar-leida` | UI-16 |
| `POST /asistencias-docentes/firmas` | UI-17 |
| `GET /asistencias-docentes/firmas` | UI-02, UI-17 |
| `GET /asistencias-docentes/incidencias` | UI-18, UI-19 |
| `POST /asistencias-docentes/licencias` | UI-19 |
| `GET /asistencias-docentes/balance-horas` | UI-02, UI-20 |
| `GET /reportes/asistencia-estudiantes.{pdf,xlsx}` | UI-21 |
| `GET /reportes/horas-docentes.{pdf,xlsx}` | UI-21 |
| `GET /configuracion` | UI-22 |
| `PUT /configuracion/{clave}` | UI-22 |

---

## 15. Limitaciones del contrato y propuestas

Estas limitaciones no bloquean el diseño, pero deben conocerse para no inventar soluciones en
el cliente. Cualquier ampliación debe documentarse primero en `CONTRATO_API.md`.

| Limitación | Impacto en la interfaz | Propuesta |
|---|---|---|
| El perfil no incluye `estudiante_id` ni `docente_id` | Dificulta las vistas personales del Docente y del Alumno | Agregar identificadores académicos a `GET /autenticacion/perfil` |
| No hay endpoint de matrícula propia | El Alumno no puede resolver su curso de forma directa | Agregar "mis cursos" o incluir el curso en el perfil |
| `GET /estudiantes?curso_id` no filtra por estado de matrícula | El padrón puede incluir estudiantes con matrícula inactiva | Usar `/inscripciones` y filtrar `Activo`; a futuro agregar `estado` |
| No hay paginación, búsqueda ni ordenamiento en listados | Tablas grandes poco eficientes | Paginar/ordenar en cliente al inicio; luego ampliar el contrato |
| No hay `GET /licencias` | Se depende de `/incidencias?tipo=Licencia` | Agregar endpoint dedicado si crece el volumen |
| No hay edición ni baja de entidades académicas | No se pueden corregir datos desde la interfaz | Definir endpoints `PATCH`/`DELETE` si el alcance lo requiere |
| No hay endpoint de panel agregado | El panel se compone de varias llamadas | Agregar un resumen de panel si se necesita una sola carga |
| No hay cierre de sesión ni refresco de token | La sesión sólo termina por expiración o descarte local | Mantener el manejo global de `401`; evaluar refresh token |
| Las alertas no se pueden crear ni eliminar | La interfaz es de triage, no de gestión | Correcto según el alcance; documentarlo |
| El reporte no tiene vista previa | El usuario descarga a ciegas | Mantener filtros claros y resumen en pantalla antes de descargar |
| `GET /docentes` no acepta filtros | Búsqueda local obligatoria | Agregar `q` o filtros si el plantel crece |
| No hay endpoint de "campañas" horarias | La vista semanal debe construir franjas con los datos | Usar las horas presentes; acordar franjas con el instituto |

---

## 16. Checklist de aceptación

### 16.1 Checklist transversal

- [ ] La pantalla sólo consume endpoints documentados.
- [ ] La navegación y las acciones respetan el rol.
- [ ] Toda petición protegida envía `Authorization: Bearer`.
- [ ] `401`, `403`, `404`, `409` y `500` tienen tratamiento visible y diferenciado.
- [ ] Los mensajes de éxito usan `mensaje` cuando existe.
- [ ] Los errores muestran `error.mensaje` y no exponen detalles técnicos.
- [ ] Existen estados de carga, vacío y error.
- [ ] Fechas, horas y marcas de tiempo se muestran sin corrimiento de zona.
- [ ] Los porcentajes se muestran en escala 0–100 y con `%`.
- [ ] Los formularios validan lo mismo que el backend y conservan datos ante error.
- [ ] No hay botones de editar/eliminar sin endpoint.
- [ ] La pantalla se opera por teclado y con lector de pantalla.
- [ ] El diseño es usable en escritorio y en tableta/teléfono.
- [ ] No se guardan datos personales en almacenamiento persistente innecesario.

### 16.2 Checklist por flujo

- [ ] Login: error genérico, redirección por rol, validación de token al arrancar.
- [ ] Asistencia: padrón activo, precarga, no fechas futuras, resumen de creados/actualizados.
- [ ] Resumen: variante según `alcance`, umbral desde la respuesta, estado `Sin datos` neutro.
- [ ] Alertas: marcar leída actualiza la fila, no hay acciones inexistentes.
- [ ] Firmas: sólo bloques de hoy, sin hora editable, manejo de `409` e incidencia.
- [ ] Balance: período vigente o selección, saldo y cumplimiento sin recálculo.
- [ ] Reportes: descarga autenticada, errores JSON, nombre de archivo.
- [ ] Configuración: controles por clave, valores como texto, impacto advertido.

---

## 17. Anexo: enumeraciones y valores exactos

Usar estos textos tal cual; no traducirlos ni cambiarlos por variantes.

### 17.1 Roles

- `Admin/Directivo`
- `Preceptor`
- `Docente`
- `Alumno`

### 17.2 Estados de asistencia

- `Presente`
- `Ausente`
- `Justificado`
- `Tarde`

### 17.3 Estados de inscripción

- `Activo`
- `Inactivo`

El contrato ejemplifica `Activo` como valor por defecto; `Inactivo` también es admitido por
el backend.

### 17.4 Tipos de firma

- `Ingreso`
- `Egreso`

### 17.5 Tipos de incidencia

- `Tardanza`
- `Salida anticipada`
- `Ausencia`
- `Licencia`

### 17.6 Tipos de alerta

- `Inasistencias consecutivas`
- `Regularidad en riesgo`

### 17.7 Niveles de alerta

- `Alta`
- `Media`

El contrato ejemplifica `Alta`; `Media` también es admitido por el backend.

### 17.8 Estados de regularidad

- `Regular`
- `En riesgo`
- `Sin datos`

### 17.9 Estados de clase en el balance

- `Completa`
- `Incompleta`
- `Sin firma`

### 17.10 Estrategias

- Asistencia: `institucional`, `estricta`
- Horas cátedra: `exacta`, `por_bloques`

### 17.11 Días de la semana

| Valor | Día |
|---|---|
| 1 | Lunes |
| 2 | Martes |
| 3 | Miércoles |
| 4 | Jueves |
| 5 | Viernes |
| 6 | Sábado |
| 7 | Domingo |

### 17.12 Claves de configuración

- `umbral_regularidad_porcentaje`
- `limite_inasistencias_consecutivas`
- `minutos_hora_catedra`
- `tolerancia_minutos_firma`
- `estrategia_calculo_asistencia`
- `estrategia_calculo_horas`

La zona horaria (`zona_horaria_institucional`) se muestra en `valores_aplicados` pero no se
actualiza desde este endpoint.
