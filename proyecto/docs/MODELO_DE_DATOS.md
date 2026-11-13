# Modelo de Datos

## 1. Principios

- Motor relacional (SQLite en desarrollo, PostgreSQL posible en producción).
- Esquema normalizado en **tercera forma normal (3FN)**: sin grupos repetidos, sin
  dependencias parciales y sin campos derivados.
- Integridad referencial declarada en la base, no sólo en la aplicación.
- Nombres de tablas y columnas descriptivos, en español.
- Fechas y horas institucionales almacenadas como `DATE`/`TIME`; marcas de tiempo de
  auditoría como `DATETIME`.

## 2. Diagrama lógico

```
roles 1 ─── N usuarios
usuarios 1 ─── 0..1 estudiantes
usuarios 1 ─── 0..1 docentes

estudiantes N ─── N cursos          (inscripciones_estudiantes_cursos)
docentes    N ─── N cursos/materias (asignaciones_docentes_materias)
cursos      N ─── N materias        (a través de asignaciones y grillas)

cursos 1 ─── N grillas_horarias_institucionales
materias 1 ─── N grillas_horarias_institucionales
docentes 1 ─── N grillas_horarias_institucionales

estudiantes 1 ─── N registros_asistencia_estudiantil
cursos      1 ─── N registros_asistencia_estudiantil
materias    1 ─── N registros_asistencia_estudiantil
usuarios    1 ─── N registros_asistencia_estudiantil (registrado_por)

docentes 1 ─── N firmas_asistencia_docente
grillas  1 ─── N firmas_asistencia_docente
firmas   1 ─── 0..1 incidencias_horarias
docentes 1 ─── N incidencias_horarias

estudiantes 1 ─── N alertas_asistencia
periodos_academicos se relaciona por rango de fechas con registros y firmas
```

## 3. Tablas

### 3.1 `roles`

Catálogo de roles institucionales.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `nombre` | VARCHAR | NOT NULL, UNIQUE, CHECK contra `Admin/Directivo`, `Preceptor`, `Docente`, `Alumno` |
| `descripcion` | VARCHAR(255) | NOT NULL |
| `nivel_jerarquico` | INTEGER | NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

### 3.2 `usuarios`

Cuenta de acceso. La contraseña se guarda como hash con sal.

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `nombre_usuario` | VARCHAR(80) | NOT NULL, UNIQUE, índice |
| `correo_electronico` | VARCHAR(255) | NOT NULL, UNIQUE |
| `hash_contrasena` | VARCHAR(255) | NOT NULL |
| `rol_id` | INTEGER | FK → `roles.id` ON DELETE RESTRICT, NOT NULL |
| `activo` | BOOLEAN | NOT NULL, default `true` |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

### 3.3 `estudiantes`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `usuario_id` | INTEGER | FK → `usuarios.id` ON DELETE CASCADE, UNIQUE, NOT NULL |
| `legajo` | VARCHAR(30) | NOT NULL, UNIQUE, índice |
| `nombres`, `apellidos` | VARCHAR(120) | NOT NULL |
| `fecha_nacimiento` | DATE | NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

### 3.4 `docentes`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `usuario_id` | INTEGER | FK → `usuarios.id` ON DELETE CASCADE, UNIQUE, NOT NULL |
| `legajo` | VARCHAR(30) | NOT NULL, UNIQUE, índice |
| `nombres`, `apellidos` | VARCHAR(120) | NOT NULL |
| `titulo_habilitante` | VARCHAR(255) | NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

### 3.5 `cursos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `nombre` | VARCHAR(80) | NOT NULL |
| `division` | VARCHAR(20) | NOT NULL |
| `anio_lectivo` | INTEGER | NOT NULL, índice, CHECK 2000–2200 |
| `turno` | VARCHAR(40) | NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(nombre, division, anio_lectivo)`.

### 3.6 `materias`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `nombre` | VARCHAR(120) | NOT NULL, UNIQUE |
| `codigo` | VARCHAR(30) | NOT NULL, UNIQUE |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

### 3.7 `periodos_academicos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `nombre` | VARCHAR(100) | NOT NULL |
| `fecha_inicio` | DATE | NOT NULL |
| `fecha_fin` | DATE | NOT NULL |
| `anio_lectivo` | INTEGER | NOT NULL, índice |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(nombre, anio_lectivo)`. **CHECK** `fecha_inicio <= fecha_fin`.

### 3.8 `inscripciones_estudiantes_cursos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `estudiante_id` | INTEGER | FK → `estudiantes.id` ON DELETE CASCADE, NOT NULL |
| `curso_id` | INTEGER | FK → `cursos.id` ON DELETE RESTRICT, NOT NULL |
| `fecha_inscripcion` | DATE | NOT NULL |
| `estado` | VARCHAR | NOT NULL, CHECK `Activo`/`Inactivo` |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(estudiante_id, curso_id)`. Índices por `estudiante_id` y `curso_id`.

### 3.9 `asignaciones_docentes_materias`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `docente_id` | INTEGER | FK → `docentes.id` ON DELETE CASCADE, NOT NULL |
| `curso_id` | INTEGER | FK → `cursos.id` ON DELETE RESTRICT, NOT NULL |
| `materia_id` | INTEGER | FK → `materias.id` ON DELETE RESTRICT, NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(docente_id, curso_id, materia_id)`.

El año lectivo no se duplica: se obtiene desde `cursos.anio_lectivo`.

### 3.10 `grillas_horarias_institucionales`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `curso_id` | INTEGER | FK → `cursos.id` ON DELETE RESTRICT, NOT NULL |
| `materia_id` | INTEGER | FK → `materias.id` ON DELETE RESTRICT, NOT NULL |
| `docente_id` | INTEGER | FK → `docentes.id` ON DELETE RESTRICT, NOT NULL |
| `dia_semana` | INTEGER | NOT NULL, CHECK 1–7 (ISO: 1 = lunes) |
| `hora_inicio` | TIME | NOT NULL |
| `hora_fin` | TIME | NOT NULL |
| `aula` | VARCHAR(60) | NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**CHECK** `hora_inicio < hora_fin`.
**UNIQUE** `(docente_id, dia_semana, hora_inicio)` para evitar superposición del docente.
**UNIQUE** `(curso_id, dia_semana, hora_inicio)` para evitar superposición del curso.

### 3.11 `registros_asistencia_estudiantil`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `estudiante_id` | INTEGER | FK → `estudiantes.id` ON DELETE RESTRICT, NOT NULL |
| `curso_id` | INTEGER | FK → `cursos.id` ON DELETE RESTRICT, NOT NULL |
| `materia_id` | INTEGER | FK → `materias.id` ON DELETE RESTRICT, NOT NULL |
| `fecha` | DATE | NOT NULL, índice |
| `estado` | VARCHAR | NOT NULL, CHECK `Presente`/`Ausente`/`Justificado`/`Tarde` |
| `observacion` | VARCHAR(500) | NULL |
| `registrado_por_usuario_id` | INTEGER | FK → `usuarios.id` ON DELETE RESTRICT, NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(estudiante_id, curso_id, materia_id, fecha)`: una única asistencia por alumno,
materia y día. La recarga actualiza el registro existente.

Índice compuesto `(curso_id, fecha)` para resúmenes y reportes.

### 3.12 `firmas_asistencia_docente`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `docente_id` | INTEGER | FK → `docentes.id` ON DELETE CASCADE, NOT NULL |
| `grilla_horaria_id` | INTEGER | FK → `grillas_horarias_institucionales.id` ON DELETE RESTRICT, NOT NULL |
| `tipo_firma` | VARCHAR | NOT NULL, CHECK `Ingreso`/`Egreso` |
| `fecha` | DATE | NOT NULL, índice |
| `marca_temporal` | DATETIME | NOT NULL, generada por el servidor |
| `observacion` | VARCHAR(500) | NULL |
| `registrado_por_usuario_id` | INTEGER | FK → `usuarios.id` ON DELETE RESTRICT, NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

**UNIQUE** `(docente_id, grilla_horaria_id, fecha, tipo_firma)`. Impide dos ingresos o dos
egresos para el mismo bloque y día.

### 3.13 `incidencias_horarias`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `docente_id` | INTEGER | FK → `docentes.id` ON DELETE CASCADE, NOT NULL |
| `grilla_horaria_id` | INTEGER | FK → grillas, ON DELETE RESTRICT, NULL |
| `firma_asistencia_id` | INTEGER | FK → firmas, ON DELETE CASCADE, NULL, UNIQUE |
| `tipo` | VARCHAR | NOT NULL, CHECK `Tardanza`/`Salida anticipada`/`Ausencia`/`Licencia` |
| `fecha` | DATE | NOT NULL, índice |
| `minutos_desviacion` | INTEGER | NOT NULL, default 0 |
| `descripcion` | VARCHAR(500) | NOT NULL |
| `generada_automaticamente` | BOOLEAN | NOT NULL |
| `registrado_por_usuario_id` | INTEGER | FK → `usuarios.id` ON DELETE RESTRICT, NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

`firma_asistencia_id` es único para asegurar como máximo una incidencia automática por firma.
Las licencias no dependen de una firma.

### 3.14 `alertas_asistencia`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `estudiante_id` | INTEGER | FK → `estudiantes.id` ON DELETE CASCADE, NOT NULL |
| `tipo` | VARCHAR | NOT NULL, CHECK `Inasistencias consecutivas`/`Regularidad en riesgo` |
| `nivel` | VARCHAR | NOT NULL, CHECK `Alta`/`Media` |
| `mensaje` | VARCHAR(500) | NOT NULL |
| `porcentaje_asistencia` | NUMERIC(5,2) | NULL |
| `fecha_generacion` | DATETIME | NOT NULL |
| `activa` | BOOLEAN | NOT NULL, default `true` |
| `leida` | BOOLEAN | NOT NULL, default `false` |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

Índice `(estudiante_id, activa)`. La deduplicación de alertas activas por tipo se realiza en
el repositorio y en el suscriptor.

### 3.15 `parametros_institucionales`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | INTEGER | PK |
| `clave` | VARCHAR(100) | NOT NULL, UNIQUE, índice |
| `valor` | VARCHAR(255) | NOT NULL |
| `descripcion` | VARCHAR(500) | NOT NULL |
| `creado_en`, `actualizado_en` | DATETIME | NOT NULL |

Parámetros iniciales: `umbral_regularidad_porcentaje`, `limite_inasistencias_consecutivas`,
`minutos_hora_catedra`, `tolerancia_minutos_firma`, `estrategia_calculo_asistencia` y
`estrategia_calculo_horas`.

## 4. Justificación de la normalización

- **1FN:** todos los atributos son atómicos; no hay listas ni grupos repetidos. La relación
  docente-materia-curso se resuelve con la tabla puente `asignaciones_docentes_materias`.
- **2FN:** todas las tablas usan clave primaria simple `id`; no existen dependencias
  parciales de una clave compuesta.
- **3FN:** no hay dependencias transitivas. Ejemplos:
  - La grilla no repite el año lectivo: se obtiene desde `cursos.anio_lectivo`.
  - La asignación docente no repite el año lectivo por la misma razón.
  - Los porcentajes, totales de horas y saldos no se almacenan: se calculan con las
    estrategias a partir de registros y firmas.
- Los estados y tipos se restringen con `CHECK` a valores estables del dominio.

## 5. Integridad referencial

- Todas las relaciones tienen clave foránea declarada con `ON DELETE` explícito.
- `RESTRICT` protege datos maestros con historial (cursos, materias, usuarios, grillas).
- `CASCADE` se aplica a datos dependientes del perfil (inscripciones, firmas, incidencias,
  alertas).
- En SQLite, `PRAGMA foreign_keys=ON` se ejecuta en cada conexión desde
  `aplicacion/extenciones.py`; de lo contrario SQLite no aplicaría las claves foráneas.
- La restricción se verifica en pruebas insertando una referencia inexistente y esperando
  `IntegrityError`.
