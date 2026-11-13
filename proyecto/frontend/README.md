# Frontend — Sistema de Asistencia Institucional

Aplicación web estática que consume la API del backend. No requiere compilación ni
dependencias externas: son HTML, CSS y JavaScript clásicos.

## Ejecución

Con el backend en `http://localhost:5000` (ver `../README.md`):

```powershell
# Desde proyecto/
.\.venv\Scripts\python.exe -m http.server 5173 --directory frontend
```

Abrir <http://localhost:5173>. El cliente apunta a `http://localhost:5000/api/v1`; si la
aplicación se sirve desde el puerto 5000, usa una ruta relativa.

Si existe un archivo `.env` con `CORS_ORIGENES_PERMITIDOS`, debe incluir
`http://localhost:5173`. Sin `.env`, el backend permite cualquier origen en desarrollo.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `index.html` | Punto de entrada y carga de scripts |
| `assets/css/estilos.css` | Diseño responsive, accesible e imprimible |
| `assets/js/api.js` | Cliente HTTP, manejo de errores y sesión |
| `assets/js/componentes.js` | Formato de datos, tablas, formularios, avisos y diálogos |
| `assets/js/paginas.js` | Utilidades compartidas, panel, perfil y horario personal |
| `assets/js/paginas_academicas.js` | Usuarios, estudiantes, docentes y estructura académica |
| `assets/js/paginas_operacion.js` | Asistencia, resumen, alertas, reportes y configuración |
| `assets/js/paginas_docentes.js` | Firmas, incidencias, licencias y balance de horas |
| `assets/js/app.js` | Inicio de sesión, shell, menú por rol y enrutador por hash |

Las rutas usan hash, por ejemplo `#/panel`, `#/cursos` o `#/cargar-asistencia`.

## Sesión y seguridad

- La autenticación es por `Authorization: Bearer <token>`; no se usan cookies.
- El token se guarda en `sessionStorage`, por lo que se pierde al cerrar la pestaña. Se
  descarta ante cualquier `401`, que redirige al inicio de sesión.
- No hay endpoints de cierre de sesión ni renovación: el cierre es local.
- Todo dato del servidor se escapa antes de insertarse en el DOM. Aun así, `sessionStorage`
  es accesible desde JavaScript: una vulnerabilidad XSS podría leer el token, por lo que el
  backend debe mantener la validación de permisos como autoridad final.

## Reglas respetadas

- Roles: Admin/Directivo, Preceptor, Docente y Alumno; el menú oculta módulos sin acceso y
  el enrutador muestra "Sin acceso" ante una URL directa no permitida.
- Fechas `AAAA-MM-DD` y marcas de tiempo se muestran por componentes, sin conversión de zona
  horaria del navegador; se usa la hora del servidor para "hoy".
- Porcentajes en escala 0–100, sin multiplicar ni recalcular.
- No se inventan endpoints, campos ni operaciones de edición/eliminación.
- Las descargas de reportes se hacen con `fetch` y el encabezado de autorización.
- La carga de asistencia advierte que la operación es idempotente y que puede generar alertas.
