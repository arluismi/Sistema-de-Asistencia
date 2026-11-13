# Sistema de Gestión de Asistencia Institucional — Backend y frontend

Sistema completo del trabajo práctico final: **backend** en **Python 3.11+** con **Flask** y
**frontend** web estático en HTML, CSS y JavaScript sin dependencias externas. Implementa los
dos módulos exigidos por `liniamientos.md`:

1. Control de asistencia de estudiantes.
2. Asistencia y puntualidad del personal docente.

El contrato de API es la fuente de verdad y está documentado en
[`docs/CONTRATO_API.md`](docs/CONTRATO_API.md). La interfaz sigue
[`docs/GUIA_INTERFAZ.md`](docs/GUIA_INTERFAZ.md) y sólo consume endpoints existentes.

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/CONTRATO_API.md`](docs/CONTRATO_API.md) | Endpoints, roles, cuerpos y respuestas |
| [`docs/GUIA_INTERFAZ.md`](docs/GUIA_INTERFAZ.md) | Pantallas, flujos y criterios de la interfaz |
| [`frontend/README.md`](frontend/README.md) | Ejecución, estructura y alcance del frontend |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Capas, patrones y decisiones de diseño |
| [`docs/MODELO_DE_DATOS.md`](docs/MODELO_DE_DATOS.md) | Esquema normalizado e integridad referencial |
| [`docs/DEPENDENCIAS_EXTERNAS.md`](docs/DEPENDENCIAS_EXTERNAS.md) | Uso documentado de librerías externas |
| [`ia/ORDENES_PERSISTENTES.md`](ia/ORDENES_PERSISTENTES.md) | Registro de órdenes permanentes para la IA |
| [`AGENTS.md`](AGENTS.md) | Guía de trabajo para agentes de IA |

## Requisitos

- Python 3.11 o superior (validado sobre Python 3.14.7).
- `pip` y entorno virtual.
- No requiere servidor de base de datos para desarrollo: usa SQLite con integridad
  referencial activada. La configuración admite PostgreSQL cambiando `URL_BASE_DATOS`.

## Instalación y puesta en marcha

Desde la carpeta `proyecto/`:

```powershell
# 1. Crear el entorno virtual
py -m venv .venv

# 2. Instalar dependencias
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Crear las tablas, roles y parámetros institucionales
.\.venv\Scripts\python.exe run.py inicializar-base-de-datos

# 4. Cargar datos de demostración (opcional)
.\.venv\Scripts\python.exe run.py sembrar-datos-demostracion

# 5. Iniciar el servidor de desarrollo en http://localhost:5000
.\.venv\Scripts\python.exe run.py
```

También se pueden ejecutar los comandos con la CLI de Flask:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py inicializar-base-de-datos
```

## Frontend

La interfaz está en `frontend/` y se sirve como sitio estático. Con el backend en ejecución:

```powershell
# Segunda terminal, desde proyecto/
.\.venv\Scripts\python.exe -m http.server 5173 --directory frontend
```

Abrir <http://localhost:5173> e ingresar con las credenciales de demostración. El frontend
detecta la URL de la API en `http://localhost:5000/api/v1`.

- El token se guarda en `sessionStorage` y se descarta al cerrar sesión o ante cualquier `401`.
- Si se define `CORS_ORIGENES_PERMITIDOS` en `.env`, incluir `http://localhost:5173`.
- No requiere compilación, `npm` ni conexión a internet.
- Las pantallas y la navegación por rol están implementadas según `docs/GUIA_INTERFAZ.md`.

### Variables de entorno

Copiar `.env.example` como `.env` y ajustar los valores. Si no existe `.env`, se usan
valores de desarrollo y una base SQLite en `proyecto/instance/institucion.db`.

| Variable | Descripción |
|---|---|
| `CLAVE_SECRETA` | Clave interna de Flask |
| `CLAVE_TOKEN` | Clave de firma de los JWT (mínimo 32 caracteres) |
| `MINUTOS_VIGENCIA_TOKEN` | Vigencia del token de acceso |
| `URL_BASE_DATOS` | URL SQLAlchemy; vacío usa SQLite local |
| `ZONA_HORARIA_INSTITUCIONAL` | Zona IANA para las marcas de tiempo del servidor |
| `CORS_ORIGENES_PERMITIDOS` | Orígenes del futuro frontend, separados por comas |

## Credenciales de demostración

| Rol | Usuario | Contraseña |
|---|---|---|
| Admin/Directivo | `direccion` | `Admin123!` |
| Preceptor | `preceptoria` | `Preceptor123!` |
| Docente | `docente.martinez` | `Docente123!` |
| Alumno | `alumno.perez` | `Alumno123!` |

> Cambiar estas credenciales en cualquier entorno real. Sólo existen para probar la API.

## Ejemplo rápido de uso

```powershell
# Iniciar sesión
$respuesta = Invoke-RestMethod -Method Post `
  -Uri http://localhost:5000/api/v1/autenticacion/iniciar-sesion `
  -ContentType "application/json" `
  -Body '{"nombre_usuario":"preceptoria","contrasena":"Preceptor123!"}'

$token = $respuesta.datos.token_acceso

# Consultar el resumen de asistencia de un curso
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:5000/api/v1/asistencias-estudiantes/resumen?curso_id=1&periodo_id=2" `
  -Headers @{ Authorization = "Bearer $token" }
```

## Pruebas automatizadas

```powershell
.\.venv\Scripts\python.exe -m pytest
```

La suite cubre autenticación, control de acceso por roles, carga y actualización de
asistencia, estrategias de cálculo, alertas por inasistencias consecutivas, firmas
docentes, incidencias, balance de horas cátedra, reportes PDF/Excel e integridad
referencial de la base de datos.

## Estructura del proyecto

```
proyecto/
├── frontend/             # SPA estática: HTML, CSS y JavaScript sin dependencias
│   ├── index.html
│   └── assets/
│       ├── css/estilos.css
│       └── js/           # Cliente API, componentes, páginas y enrutador
├── aplicacion/
│   ├── controladores/    # Endpoints HTTP y validación de entrada
│   ├── servicios/        # Lógica de negocio y transacciones
│   ├── repositorios/     # Patrón Repository / DAO
│   ├── modelos/          # Entidades SQLAlchemy y enums
│   ├── estrategias/      # Patrón Strategy (asistencia y horas cátedra)
│   ├── observadores/     # Patrón Observer (alertas del tablero)
│   ├── reportes/         # Generadores PDF y Excel
│   ├── seguridad/        # JWT, contraseñas y decoradores de rol
│   ├── presentadores/    # Serialización de entidades
│   ├── utilidades/       # Tiempo, validadores y respuestas
│   ├── errores/          # Excepciones y manejadores globales
│   └── comandos/         # Comandos de inicialización y datos demo
├── docs/                 # Contrato de API, arquitectura y modelo de datos
├── ia/                   # Órdenes persistentes para la IA
├── pruebas/              # Suite pytest
├── configuracion.py
├── run.py
└── requirements.txt
```

## Decisiones destacadas

- **Marcas de tiempo del servidor:** las firmas docentes usan exclusivamente la hora del
  servidor en la zona institucional; el cliente no puede enviar la hora.
- **Asistencia idempotente:** una recarga de la misma fecha, curso y materia actualiza el
  registro existente en lugar de duplicarlo.
- **Alertas automáticas:** el patrón Observer evalúa inasistencias consecutivas y riesgo de
  regularidad al registrar asistencia.
- **Estrategias configurables:** el criterio de asistencia (`institucional` o `estricta`) y
  el cálculo de horas cátedra (`exacta` o `por_bloques`) se seleccionan por configuración
  o por parámetro de consulta.
- **Integridad en la base:** claves foráneas con `ON DELETE` explícito, restricciones
  `UNIQUE`, `CHECK` y `PRAGMA foreign_keys=ON` en SQLite.
