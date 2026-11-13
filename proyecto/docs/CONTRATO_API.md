# Contrato de API — Backend de Asistencia Institucional

> Guía complementaria para el diseño del futuro frontend:
> [`GUIA_INTERFAZ.md`](GUIA_INTERFAZ.md). Este contrato sigue siendo la fuente de verdad.

## 1. Convenciones generales

- **URL base:** `http://localhost:5000/api/v1`
- **Formato:** JSON UTF-8, salvo los reportes binarios PDF/XLSX.
- **Autenticación:** encabezado `Authorization: Bearer <token_acceso>` en todos los endpoints
  protegidos.
- **Fechas:** `AAAA-MM-DD`.
- **Horas:** `HH:MM` en formato de 24 horas.
- **Marcas de tiempo:** `AAAA-MM-DDTHH:MM:SS`, generadas por el servidor en la zona horaria
  institucional.
- **Roles:** `Admin/Directivo`, `Preceptor`, `Docente`, `Alumno`.
- **Objetos anidados:** cuando una respuesta incluye `estudiante`, `docente`, `curso`,
  `materia`, `periodo` o `grilla_horaria`, se devuelve el objeto completo con los campos
  documentados para esa entidad; los ejemplos pueden abreviarlos por claridad.
- **Respuesta de éxito:**

```json
{
  "datos": {},
  "mensaje": "Texto opcional"
}
```

- **Respuesta de error:**

```json
{
  "error": {
    "codigo": "datos_invalidos",
    "mensaje": "Descripción legible",
    "detalles": ["detalle opcional"]
  }
}
```

### Códigos de error

| Código | HTTP | Significado |
|---|---|---|
| `datos_invalidos` | 400 | Campo faltante, formato incorrecto o valor fuera de rango |
| `no_autenticado` | 401 | Token ausente, inválido o expirado |
| `acceso_prohibido` | 403 | El rol o contexto no autoriza la operación |
| `recurso_no_encontrado` | 404 | Entidad o ruta inexistente |
| `conflicto_de_datos` | 409 | Duplicado o violación de integridad |
| `error_interno` | 500 | Falla inesperada del servidor |

### Jerarquía de acceso

| Rol | Capacidades generales |
|---|---|
| Admin/Directivo | Gestión completa, configuración y reportes |
| Preceptor | Asistencias, matrículas, licencias, alertas y reportes |
| Docente | Asistencia de sus materias y datos propios de puntualidad |
| Alumno | Sólo su propia asistencia y regularidad |

---

## 2. Índice de endpoints

| Verbo | Ruta | Roles |
|---|---|---|
| GET | `/salud` | Público |
| POST | `/autenticacion/iniciar-sesion` | Público |
| GET | `/autenticacion/perfil` | Todos los autenticados |
| GET | `/usuarios` | Admin/Directivo |
| POST | `/usuarios` | Admin/Directivo |
| GET | `/usuarios/{usuario_id}` | Admin/Directivo |
| PATCH | `/usuarios/{usuario_id}/estado` | Admin/Directivo |
| GET | `/estudiantes` | Admin/Directivo, Preceptor, Docente |
| POST | `/estudiantes` | Admin/Directivo |
| GET | `/docentes` | Admin/Directivo, Preceptor, Docente |
| POST | `/docentes` | Admin/Directivo |
| GET | `/cursos` | Todos los autenticados |
| POST | `/cursos` | Admin/Directivo |
| GET | `/materias` | Todos los autenticados |
| POST | `/materias` | Admin/Directivo |
| GET | `/periodos-academicos` | Todos los autenticados |
| POST | `/periodos-academicos` | Admin/Directivo |
| GET | `/inscripciones` | Admin/Directivo, Preceptor, Docente |
| POST | `/inscripciones` | Admin/Directivo, Preceptor |
| GET | `/asignaciones-docentes` | Admin/Directivo, Preceptor, Docente |
| POST | `/asignaciones-docentes` | Admin/Directivo |
| GET | `/grillas-horarias` | Todos los autenticados |
| POST | `/grillas-horarias` | Admin/Directivo |
| POST | `/asistencias-estudiantes` | Admin/Directivo, Preceptor, Docente |
| GET | `/asistencias-estudiantes` | Todos (Alumno: sólo lo propio) |
| GET | `/asistencias-estudiantes/resumen` | Todos (Alumno: sólo lo propio) |
| GET | `/alertas` | Admin/Directivo, Preceptor, Docente |
| PATCH | `/alertas/{alerta_id}/marcar-leida` | Admin/Directivo, Preceptor, Docente |
| POST | `/asistencias-docentes/firmas` | Admin/Directivo, Preceptor, Docente |
| GET | `/asistencias-docentes/firmas` | Admin/Directivo, Preceptor, Docente |
| GET | `/asistencias-docentes/incidencias` | Admin/Directivo, Preceptor, Docente |
| POST | `/asistencias-docentes/licencias` | Admin/Directivo, Preceptor |
| GET | `/asistencias-docentes/balance-horas` | Admin/Directivo, Preceptor, Docente |
| GET | `/reportes/asistencia-estudiantes.pdf` | Admin/Directivo, Preceptor |
| GET | `/reportes/asistencia-estudiantes.xlsx` | Admin/Directivo, Preceptor |
| GET | `/reportes/horas-docentes.pdf` | Admin/Directivo, Preceptor |
| GET | `/reportes/horas-docentes.xlsx` | Admin/Directivo, Preceptor |
| GET | `/configuracion` | Admin/Directivo |
| PUT | `/configuracion/{clave}` | Admin/Directivo |

---

## 3. Salud

### GET `/salud`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Público
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": {
    "estado": "operativo",
    "servicio": "API de gestión de asistencia institucional",
    "marca_temporal_servidor": "2026-11-12T20:14:14"
  }
}
```

---

## 4. Autenticación

### POST `/autenticacion/iniciar-sesion`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Público
- **Cuerpo de petición:**

```json
{
  "nombre_usuario": "preceptoria",
  "contrasena": "Preceptor123!"
}
```

- **Respuesta esperada (200):**

```json
{
  "datos": {
    "token_acceso": "eyJhbGciOiJIUzI1NiIs...",
    "tipo_token": "Bearer",
    "expira_en_minutos": 480,
    "usuario": {
      "id": 2,
      "nombre_usuario": "preceptoria",
      "correo_electronico": "preceptoria@instituto.edu.ar",
      "rol": "Preceptor",
      "activo": true,
      "creado_en": "2026-11-12T20:14:13"
    }
  },
  "mensaje": "Sesión iniciada correctamente."
}
```

- **Errores:** `401 no_autenticado` con mensaje genérico si el usuario no existe, la
  contraseña es incorrecta o la cuenta está inactiva.

### GET `/autenticacion/perfil`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos los autenticados
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": {
    "id": 1,
    "nombre_usuario": "direccion",
    "correo_electronico": "direccion@instituto.edu.ar",
    "rol": "Admin/Directivo",
    "activo": true,
    "creado_en": "2026-11-12T20:14:13"
  }
}
```

---

## 5. Usuarios, estudiantes y docentes

### GET `/usuarios`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo
- **Parámetros de consulta:** `rol` (texto), `activo` (`true`/`false`).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de usuarios con la estructura de `/autenticacion/perfil`.

### POST `/usuarios`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "nombre_usuario": "nuevo.usuario",
  "correo_electronico": "nuevo.usuario@instituto.edu.ar",
  "contrasena": "Contrasena123!",
  "rol": "Preceptor"
}
```

- **Campos:** `nombre_usuario` (3–80, letras/números/puntos/guiones), `correo_electronico`,
  `contrasena` (mínimo 8), `rol` (uno de los cuatro roles).
- **Respuesta esperada (201):** `datos` con el usuario creado y `mensaje`.
- **Errores:** `400 datos_invalidos`, `409 conflicto_de_datos` por usuario o correo repetido.

### GET `/usuarios/{usuario_id}`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** `datos` con el usuario solicitado.
- **Errores:** `404 recurso_no_encontrado`.

### PATCH `/usuarios/{usuario_id}/estado`

- **Verbo HTTP:** PATCH
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{ "activo": false }
```

- **Respuesta esperada (200):** usuario actualizado.
- **Errores:** `400`, `403` si intenta desactivar su propia cuenta, `404`.

### GET `/estudiantes`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente
- **Parámetros de consulta:** `curso_id` (opcional).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": [
    {
      "id": 1,
      "legajo": "ALU-2026-001",
      "nombres": "Juan",
      "apellidos": "Pérez",
      "nombre_completo": "Pérez, Juan",
      "fecha_nacimiento": "2010-04-15",
      "usuario": {
        "id": 4,
        "nombre_usuario": "alumno.perez",
        "correo_electronico": "alumno.perez@instituto.edu.ar",
        "rol": "Alumno",
        "activo": true,
        "creado_en": "2026-11-12T20:14:14"
      }
    }
  ]
}
```

### POST `/estudiantes`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "nombre_usuario": "alumno.nuevo",
  "correo_electronico": "alumno.nuevo@instituto.edu.ar",
  "contrasena": "Alumno123!",
  "legajo": "ALU-2026-004",
  "nombres": "Sofía",
  "apellidos": "López",
  "fecha_nacimiento": "2010-06-12"
}
```

- **Campos:** los de cuenta (`nombre_usuario`, `correo_electronico`, `contrasena`) más
  `legajo`, `nombres`, `apellidos` y `fecha_nacimiento` (opcional).
- **Respuesta esperada (201):** estudiante creado con su cuenta.
- **Errores:** `400`, `409` por legajo, usuario o correo repetido.

### GET `/docentes`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de docentes con `id`, `legajo`, `nombres`, `apellidos`,
  `nombre_completo`, `titulo_habilitante` y `usuario`.

### POST `/docentes`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "nombre_usuario": "docente.nuevo",
  "correo_electronico": "docente.nuevo@instituto.edu.ar",
  "contrasena": "Docente123!",
  "legajo": "DOC-2026-002",
  "nombres": "Carlos",
  "apellidos": "Fernández",
  "titulo_habilitante": "Profesor de Historia"
}
```

- **Respuesta esperada (201):** docente creado con su cuenta.
- **Errores:** `400`, `409`.

---

## 6. Estructura académica

### GET `/cursos`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos los autenticados
- **Parámetros de consulta:** `anio_lectivo` (opcional).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": [
    {
      "id": 1,
      "nombre": "1° Año",
      "division": "A",
      "anio_lectivo": 2026,
      "turno": "Mañana",
      "nombre_completo": "1° Año A (2026)"
    }
  ]
}
```

### POST `/cursos`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "nombre": "1° Año",
  "division": "A",
  "anio_lectivo": 2026,
  "turno": "Mañana"
}
```

- **Respuesta esperada (201):** curso creado.
- **Errores:** `400`, `409` por curso duplicado.

### GET `/materias`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos los autenticados
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de `{ id, nombre, codigo }`.

### POST `/materias`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{ "nombre": "Matemática", "codigo": "MAT-01" }
```

- **Respuesta esperada (201):** materia creada.
- **Errores:** `400`, `409` por nombre o código duplicado.

### GET `/periodos-academicos`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos los autenticados
- **Parámetros de consulta:** `anio_lectivo` (opcional).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": [
    {
      "id": 2,
      "nombre": "Segundo Cuatrimestre",
      "fecha_inicio": "2026-08-01",
      "fecha_fin": "2026-11-30",
      "anio_lectivo": 2026
    }
  ]
}
```

### POST `/periodos-academicos`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "nombre": "Segundo Cuatrimestre",
  "fecha_inicio": "2026-08-01",
  "fecha_fin": "2026-11-30",
  "anio_lectivo": 2026
}
```

- **Respuesta esperada (201):** período creado.
- **Errores:** `400` si las fechas son inconsistentes, `409` si se repite nombre y año.

### GET `/inscripciones`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente
- **Parámetros de consulta:** `curso_id`, `estudiante_id` (opcionales).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista con `estudiante`, `curso`, `fecha_inscripcion` y
  `estado`.

### POST `/inscripciones`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo, Preceptor
- **Cuerpo de petición:**

```json
{
  "estudiante_id": 1,
  "curso_id": 1,
  "fecha_inscripcion": "2026-03-02",
  "estado": "Activo"
}
```

- **Campos:** `estudiante_id`, `curso_id` obligatorios; `fecha_inscripcion` y `estado`
  opcionales (`Activo` por defecto).
- **Respuesta esperada (201):** inscripción creada.
- **Errores:** `404` si estudiante o curso no existen, `409` si ya está matriculado.

### GET `/asignaciones-docentes`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente
- **Parámetros de consulta:** `docente_id`, `curso_id`, `materia_id` (opcionales).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista con `docente`, `curso` y `materia`.

### POST `/asignaciones-docentes`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{ "docente_id": 1, "curso_id": 1, "materia_id": 1 }
```

- **Respuesta esperada (201):** asignación creada.
- **Errores:** `404` por referencias inexistentes, `409` por asignación duplicada.

### GET `/grillas-horarias`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos los autenticados
- **Parámetros de consulta:** `docente_id`, `curso_id`, `materia_id`, `anio_lectivo`,
  `dia_semana` (1 = lunes, 7 = domingo).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": [
    {
      "id": 1,
      "curso": { "id": 1, "nombre": "1° Año", "division": "A", "anio_lectivo": 2026, "turno": "Mañana", "nombre_completo": "1° Año A (2026)" },
      "materia": { "id": 1, "nombre": "Matemática", "codigo": "MAT-01" },
      "docente": { "id": 1, "legajo": "DOC-2026-001", "nombre_completo": "Martínez, Laura" },
      "dia_semana": 1,
      "hora_inicio": "08:00",
      "hora_fin": "09:20",
      "aula": "Aula 1"
    }
  ]
}
```

### POST `/grillas-horarias`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{
  "curso_id": 1,
  "materia_id": 1,
  "docente_id": 1,
  "dia_semana": 1,
  "hora_inicio": "08:00",
  "hora_fin": "09:20",
  "aula": "Aula 1"
}
```

- **Respuesta esperada (201):** bloque horario creado.
- **Errores:** `400` por horario inválido, docente sin asignación o día fuera de rango;
  `409` si el docente o el curso ya tienen un bloque a esa hora.

---

## 7. Asistencia estudiantil

### POST `/asistencias-estudiantes`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente (sólo materias asignadas).
- **Cuerpo de petición:**

```json
{
  "curso_id": 1,
  "materia_id": 1,
  "fecha": "2026-11-09",
  "registros": [
    {
      "estudiante_id": 1,
      "estado": "Presente",
      "observacion": null
    },
    {
      "estudiante_id": 2,
      "estado": "Ausente",
      "observacion": "Sin justificación presentada."
    }
  ]
}
```

- **Campos:**
  - `curso_id`: curso de la clase.
  - `materia_id`: materia dictada.
  - `fecha`: fecha de la clase, no futura.
  - `registros`: lista no vacía; cada elemento requiere `estudiante_id` y `estado`
    (`Presente`, `Ausente`, `Justificado`, `Tarde`). `observacion` es opcional.
- **Comportamiento:** si ya existe un registro para la misma fecha, curso, materia y
  estudiante, se actualiza en lugar de duplicarse.
- **Respuesta esperada (201):**

```json
{
  "datos": {
    "creados": 2,
    "actualizados": 0,
    "registros": [
      {
        "id": 1,
        "estudiante": { "id": 1, "legajo": "ALU-2026-001", "nombre_completo": "Pérez, Juan" },
        "curso": { "id": 1, "nombre_completo": "1° Año A (2026)" },
        "materia": { "id": 1, "nombre": "Matemática", "codigo": "MAT-01" },
        "fecha": "2026-11-09",
        "estado": "Presente",
        "observacion": null,
        "registrado_por_usuario_id": 2
      }
    ]
  },
  "mensaje": "Asistencia registrada correctamente."
}
```

- **Errores:** `400` por estado inválido, fecha futura, estudiante no matriculado o repetido;
  `403` si el docente no tiene la asignación; `404` por curso o materia inexistente.
- **Efecto secundario:** publica eventos que pueden generar alertas automáticas.

### GET `/asistencias-estudiantes`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos. El Alumno sólo accede a sus propios registros; el Docente a
  los cursos que dicta.
- **Parámetros de consulta:** `estudiante_id`, `curso_id`, `materia_id`, `fecha`,
  `fecha_desde`, `fecha_hasta` (todos opcionales).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de registros con la estructura mostrada en el POST.
- **Errores:** `403` si el Alumno consulta a otro estudiante.

### GET `/asistencias-estudiantes/resumen`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Todos. El Alumno sólo puede consultar su propio resumen.
- **Parámetros de consulta:**
  - `estudiante_id` o `curso_id`: al menos uno es obligatorio (el Alumno puede omitirlos y
    se fuerza su propio identificador).
  - `materia_id`: opcional.
  - `periodo_id`: opcional; sin período se consideran todos los registros.
  - `estrategia`: opcional (`institucional` o `estricta`); por defecto se usa la configurada.
- **Cuerpo de petición:** No aplica.
- **Respuesta por estudiante (200):**

```json
{
  "datos": {
    "alcance": "estudiante",
    "estudiante": {
      "id": 1,
      "legajo": "ALU-2026-001",
      "nombre_completo": "Pérez, Juan"
    },
    "periodo": {
      "id": 2,
      "nombre": "Segundo Cuatrimestre",
      "fecha_inicio": "2026-08-01",
      "fecha_fin": "2026-11-30",
      "anio_lectivo": 2026
    },
    "estrategia": "institucional",
    "resumen": {
      "total_registros": 9,
      "presentes": 6,
      "ausentes": 2,
      "justificados": 1,
      "tardes": 0,
      "porcentaje_asistencia": 77.78,
      "porcentaje_presentismo_efectivo": 66.67,
      "umbral_regularidad_porcentaje": 75,
      "estado_regularidad": "Regular"
    },
    "detalle_por_materia": [
      {
        "materia": { "id": 1, "nombre": "Matemática", "codigo": "MAT-01" },
        "resumen": {
          "total_registros": 9,
          "presentes": 6,
          "ausentes": 2,
          "justificados": 1,
          "tardes": 0,
          "porcentaje_asistencia": 77.78,
          "porcentaje_presentismo_efectivo": 66.67,
          "umbral_regularidad_porcentaje": 75,
          "estado_regularidad": "Regular"
        }
      }
    ]
  }
}
```

- **Respuesta por curso (200):**

```json
{
  "datos": {
    "alcance": "curso",
    "curso": { "id": 1, "nombre_completo": "1° Año A (2026)" },
    "periodo": { "id": 2, "nombre": "Segundo Cuatrimestre", "fecha_inicio": "2026-08-01", "fecha_fin": "2026-11-30", "anio_lectivo": 2026 },
    "estrategia": "institucional",
    "resumen_general": {
      "total_registros": 9,
      "presentes": 6,
      "ausentes": 2,
      "justificados": 1,
      "tardes": 0,
      "porcentaje_asistencia": 77.78,
      "porcentaje_presentismo_efectivo": 66.67,
      "umbral_regularidad_porcentaje": 75,
      "estado_regularidad": "Regular"
    },
    "estudiantes": [
      {
        "estudiante": { "id": 1, "legajo": "ALU-2026-001", "nombre_completo": "Pérez, Juan" },
        "resumen": { "total_registros": 9, "presentes": 6, "ausentes": 2, "justificados": 1, "tardes": 0, "porcentaje_asistencia": 77.78, "porcentaje_presentismo_efectivo": 66.67, "umbral_regularidad_porcentaje": 75, "estado_regularidad": "Regular" }
      }
    ]
  }
}
```

- **Estados de regularidad:** `Regular` (≥ umbral), `En riesgo` (< umbral) o `Sin datos`.
- **Errores:** `400` si no se indica estudiante ni curso; `403` por acceso ajeno.

---

## 8. Alertas del tablero

### GET `/alertas`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente (sólo estudiantes de sus cursos).
- **Parámetros de consulta:** `estudiante_id`, `activa`, `leida` (opcionales).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": [
    {
      "id": 2,
      "estudiante": { "id": 2, "legajo": "ALU-2026-002", "nombre_completo": "Gómez, Lucía" },
      "tipo": "Inasistencias consecutivas",
      "nivel": "Alta",
      "mensaje": "El estudiante Gómez, Lucía (legajo ALU-2026-002) acumula 3 jornadas consecutivas de inasistencia.",
      "porcentaje_asistencia": null,
      "fecha_generacion": "2026-11-12T20:14:14",
      "activa": true,
      "leida": false
    }
  ]
}
```

### PATCH `/alertas/{alerta_id}/marcar-leida`

- **Verbo HTTP:** PATCH
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente (sólo sus cursos).
- **Cuerpo de petición:** No requiere cuerpo.
- **Respuesta esperada (200):** alerta con `leida: true`.
- **Errores:** `403` si la alerta pertenece a un estudiante fuera de sus cursos, `404`.

---

## 9. Asistencia y puntualidad docente

### POST `/asistencias-docentes/firmas`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente.
- **Cuerpo de petición:**

```json
{
  "tipo_firma": "Ingreso",
  "grilla_horaria_id": 1,
  "docente_id": 1
}
```

- **Campos:**
  - `tipo_firma`: `Ingreso` o `Egreso`.
  - `grilla_horaria_id`: bloque de la grilla que se está firmando.
  - `docente_id`: obligatorio para Admin/Directivo y Preceptor; el Docente no debe enviarlo
    (si lo envía, debe coincidir con su propio identificador).
- **Reglas:**
  - La fecha y hora las genera el servidor; el cliente no puede enviarlas.
  - El bloque debe corresponder al día actual y al docente.
  - No se admite un egreso sin ingreso previo ni firmas duplicadas del mismo tipo.
- **Respuesta esperada (201):**

```json
{
  "datos": {
    "firma": {
      "id": 1,
      "docente": { "id": 1, "legajo": "DOC-2026-001", "nombre_completo": "Martínez, Laura" },
      "grilla_horaria": { "id": 1, "dia_semana": 1, "hora_inicio": "08:00", "hora_fin": "09:20" },
      "tipo_firma": "Ingreso",
      "fecha": "2026-03-09",
      "marca_temporal": "2026-03-09T08:25:00",
      "observacion": null
    },
    "incidencia": {
      "id": 1,
      "docente": { "id": 1, "legajo": "DOC-2026-001", "nombre_completo": "Martínez, Laura" },
      "grilla_horaria_id": 1,
      "firma_asistencia_id": 1,
      "tipo": "Tardanza",
      "fecha": "2026-03-09",
      "minutos_desviacion": 25,
      "descripcion": "Tardanza de 25 minutos en el ingreso correspondiente a Matemática (1° Año A (2026)).",
      "generada_automaticamente": true,
      "registrado_por_usuario_id": 3
    }
  },
  "mensaje": "Firma registrada correctamente."
}
```

- **Errores:** `400` si la grilla no corresponde al día o el tipo es inválido; `403` si el
  docente intenta firmar para otro; `404` si la grilla no existe; `409` por firma duplicada,
  egreso sin ingreso o egreso anterior al ingreso.

### GET `/asistencias-docentes/firmas`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente (sólo las propias).
- **Parámetros de consulta:** `docente_id`, `fecha_desde`, `fecha_hasta` (opcionales).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de firmas con la estructura anterior.

### GET `/asistencias-docentes/incidencias`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor, Docente (sólo las propias).
- **Parámetros de consulta:** `docente_id`, `fecha_desde`, `fecha_hasta`, `tipo`
  (`Tardanza`, `Salida anticipada`, `Ausencia`, `Licencia`).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** lista de incidencias con la estructura mostrada en la firma.

### POST `/asistencias-docentes/licencias`

- **Verbo HTTP:** POST
- **Jerarquía de acceso:** Admin/Directivo, Preceptor.
- **Cuerpo de petición:**

```json
{
  "docente_id": 1,
  "fecha": "2026-03-10",
  "motivo": "Licencia por capacitación docente.",
  "grilla_horaria_id": 1
}
```

- **Campos:** `docente_id`, `fecha` y `motivo` obligatorios; `grilla_horaria_id` opcional.
- **Respuesta esperada (201):** incidencia de tipo `Licencia`.
- **Errores:** `404` por docente o grilla inexistente, `409` por licencia duplicada en la
  misma fecha.

### GET `/asistencias-docentes/balance-horas`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor (cualquier docente); Docente (sólo el
  propio).
- **Parámetros de consulta:** `periodo_id` (opcional; si se omite se usa el período vigente),
  `docente_id` (opcional para Admin/Preceptor; si se omite se calculan todos),
  `estrategia` (`exacta` o `por_bloques`).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": {
    "periodo": {
      "id": 2,
      "nombre": "Segundo Cuatrimestre",
      "fecha_inicio": "2026-08-01",
      "fecha_fin": "2026-11-30",
      "anio_lectivo": 2026
    },
    "balances": [
      {
        "docente": { "id": 1, "legajo": "DOC-2026-001", "nombre_completo": "Martínez, Laura" },
        "balance": {
          "estrategia": "exacta",
          "fecha_inicio": "2026-08-01",
          "fecha_fin": "2026-11-30",
          "minutos_hora_catedra": 40,
          "clases_esperadas": 52,
          "clases_completas": 1,
          "clases_incompletas": 0,
          "clases_sin_firma": 51,
          "minutos_esperados": 4160,
          "minutos_laborados": 35,
          "horas_catedra_esperadas": 104.0,
          "horas_catedra_laboradas": 0.88,
          "saldo_horas_catedra": -103.12,
          "porcentaje_cumplimiento": 0.85,
          "detalle_clases": [
            {
              "grilla_horaria_id": 1,
              "fecha": "2026-08-03",
              "curso": "1° Año A (2026)",
              "materia": "Matemática",
              "hora_inicio": "08:00",
              "hora_fin": "09:20",
              "minutos_esperados": 80,
              "minutos_laborados": 0,
              "estado": "Sin firma"
            }
          ]
        }
      }
    ]
  }
}
```

- **Estados de clase:** `Completa` (ingreso y egreso), `Incompleta` (sólo uno) o
  `Sin firma`.
- **Errores:** `400` sin período vigente ni `periodo_id`; `403` si un Docente consulta a otro.

---

## 10. Reportes

Los reportes se devuelven como archivo adjunto:

- PDF: `application/pdf`.
- Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

### GET `/reportes/asistencia-estudiantes.pdf`

### GET `/reportes/asistencia-estudiantes.xlsx`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor.
- **Parámetros de consulta:** `curso_id` (obligatorio), `periodo_id` (obligatorio),
  `estrategia` (`institucional` o `estricta`, opcional).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** archivo binario con:

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="reporte_asistencia_estudiantes_curso_1_periodo_2.pdf"
```

o su equivalente `.xlsx`. Contiene legajo, estudiante, conteos por estado, porcentajes y
estado de regularidad.

- **Errores:** `400` por formato no soportado; `404` por curso o período inexistente.

### GET `/reportes/horas-docentes.pdf`

### GET `/reportes/horas-docentes.xlsx`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo, Preceptor.
- **Parámetros de consulta:** `periodo_id` (obligatorio), `estrategia` (`exacta` o
  `por_bloques`, opcional).
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):** archivo binario con legajo, docente, clases esperadas y
  completas, horas esperadas y laboradas, saldo y porcentaje de cumplimiento.
- **Errores:** `400` por formato inválido, `404` por período inexistente.

---

## 11. Configuración institucional

### GET `/configuracion`

- **Verbo HTTP:** GET
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:** No aplica.
- **Respuesta esperada (200):**

```json
{
  "datos": {
    "parametros": [
      {
        "clave": "umbral_regularidad_porcentaje",
        "valor": "75",
        "descripcion": "Porcentaje mínimo de asistencia para conservar la regularidad."
      }
    ],
    "valores_aplicados": {
      "umbral_regularidad_porcentaje": 75,
      "limite_inasistencias_consecutivas": 3,
      "minutos_hora_catedra": 40,
      "tolerancia_minutos_firma": 10,
      "estrategia_calculo_asistencia": "institucional",
      "estrategia_calculo_horas": "exacta",
      "zona_horaria_institucional": "America/Argentina/Buenos_Aires"
    }
  }
}
```

### PUT `/configuracion/{clave}`

- **Verbo HTTP:** PUT
- **Jerarquía de acceso:** Admin/Directivo
- **Cuerpo de petición:**

```json
{ "valor": "80" }
```

- **Claves válidas:** `umbral_regularidad_porcentaje`,
  `limite_inasistencias_consecutivas`, `minutos_hora_catedra`, `tolerancia_minutos_firma`,
  `estrategia_calculo_asistencia`, `estrategia_calculo_horas`.
- **Respuesta esperada (200):**

```json
{
  "datos": { "clave": "umbral_regularidad_porcentaje", "valor": "80" },
  "mensaje": "Parámetro actualizado correctamente."
}
```

- **Errores:** `400` por valor no numérico o estrategia inexistente, `404` por clave
  desconocida.
