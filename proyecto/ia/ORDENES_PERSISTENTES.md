# Registro de Órdenes Persistentes para la IA

Este archivo es el registro oficial y cronológico de las instrucciones permanentes que el
usuario delega a la IA para el desarrollo del proyecto. Toda nueva orden persistente debe
agregarse al final con un identificador incremental, su fecha y su alcance.

## Protocolo de uso

1. Toda instrucción que deba mantenerse vigente entre sesiones se registra aquí, sin
   excepción y sin borrar entradas anteriores.
2. Cada orden recibe un identificador con el formato `OP-NNN` (Orden Persistente).
3. Si una orden nueva contradice a una anterior, se registra la nueva indicando
   explícitamente qué orden reemplaza; la anterior queda marcada como `REEMPLAZADA`.
4. Este registro es de lectura obligatoria al iniciar cualquier sesión de trabajo sobre el
   proyecto.

---

## OP-001 — Registro obligatorio de órdenes persistentes

- **Fecha de alta:** 2026-11-12
- **Estado:** Vigente
- **Origen:** Instrucción directa del usuario.
- **Contenido:** Debe existir, dentro de la carpeta `proyecto/`, un registro permanente de
  las órdenes que el usuario da a la IA. La carpeta elegida es `proyecto/ia/` y el archivo
  oficial es `proyecto/ia/ORDENES_PERSISTENTES.md`. Toda orden persistente futura se anexa
  en este archivo, numerada y fechada. Está prohibido eliminar órdenes anteriores.
- **Motivo:** Conservar el contexto de decisiones a largo plazo entre sesiones y evitar la
  pérdida de instrucciones.

## OP-002 — Stack tecnológico del backend: Python + Flask

- **Fecha de alta:** 2026-11-12
- **Estado:** Vigente
- **Origen:** Instrucción directa del usuario en la sesión de inicio del proyecto.
- **Contenido:** El backend debe desarrollarse en Python y utilizar Flask como framework
  HTTP. Las dependencias, la configuración y los comandos de ejecución deben quedar
  documentados en `proyecto/README.md` y `proyecto/requirements.txt`.
- **Motivo:** Definir una base tecnológica estable para todas las etapas del trabajo.

## OP-003 — Cumplimiento obligatorio de `proyecto/liniamientos.md`

- **Fecha de alta:** 2026-11-12
- **Estado:** Vigente (reemplazada parcialmente por OP-006: se habilita el frontend)
- **Origen:** Instrucción directa del usuario: iniciar el proyecto con los lineamientos
  especificados en `proyecto/liniamientos.md`.
- **Contenido:** Todo desarrollo debe respetar la especificación de arquitectura backend
  vigente: alcance limitado a backend (sin UI), contrato de API documentado por endpoint,
  POO, arquitectura en capas (Modelos, Repositorios/DAO, Servicios, Controladores), roles
  Admin/Directivo, Preceptor, Docente y Alumno, persistencia normalizada con integridad
  referencial, reportabilidad PDF/Excel y los patrones Repository, Strategy y Observer.
- **Motivo:** Es la especificación funcional y arquitectónica base del trabajo práctico.

## OP-004 — Guía de interfaz complementaria al contrato de API

- **Fecha de alta:** 2026-11-12
- **Estado:** Vigente (la restricción de no generar vistas queda reemplazada por OP-006)
- **Origen:** Instrucción directa del usuario: dejar un archivo complementario al contrato
  de API para guiar el diseño de la UI/HTML.
- **Contenido:** Debe existir `proyecto/docs/GUIA_INTERFAZ.md` como especificación de
  pantallas, navegación por rol, componentes, flujos, validaciones de formulario, estados y
  criterios de accesibilidad derivados de `docs/CONTRATO_API.md`. La guía es documental: no
  habilita la generación de vistas, HTML, CSS ni JavaScript de interfaz en esta fase. Toda
  pantalla futura debe trazarse a endpoints documentados; si requiere datos inexistentes, se
  amplía primero el contrato.
- **Motivo:** Preparar la futura incorporación del frontend sin perder la restricción de
  alcance backend y sin que la interfaz invente endpoints, campos o cálculos.

## OP-005 — Un commit de Git por cada edición

- **Fecha de alta:** 2026-11-13
- **Estado:** Vigente
- **Origen:** Instrucción directa del usuario: «nueva regla: commit entre edicion».
- **Contenido:** Toda edición del proyecto (código, pruebas, documentación o
  configuración) debe confirmarse en un commit de Git propio antes de comenzar la
  siguiente edición. Queda prohibido acumular cambios independientes en un mismo commit o
  pasar a otra tarea dejando trabajo sin confirmar. El mensaje del commit debe estar en
  español, describir el cambio con un prefijo de tipo (`feat:`, `fix:`, `docs:`, `test:`,
  `chore:`) y ser autoexplicativo. Antes de confirmar se verifica que el índice no incluya
  secretos, entornos virtuales, cachés ni bases de datos locales.
- **Motivo:** Mantener un historial granular que permita auditar, revisar y revertir cada
  cambio de forma aislada, y evitar la pérdida de trabajo entre sesiones.

## OP-006 — Incorporación del frontend web

- **Fecha de alta:** 2026-11-13
- **Estado:** Vigente. Reemplaza la restricción de alcance exclusivamente backend de OP-003.
- **Origen:** Instrucción directa del usuario: «crea la parte frontend. hazlo rápidamente».
- **Contenido:** Se habilita e incorpora el frontend en `proyecto/frontend/` como aplicación
  web estática (HTML, CSS y JavaScript sin dependencias externas ni paso de compilación) que
  consume la API documentada en `docs/CONTRATO_API.md`. Toda pantalla debe trazarse a
  endpoints existentes y respetar las reglas de `docs/GUIA_INTERFAZ.md` (roles, formato de
  fechas, permisos, accesibilidad y manejo del token). El backend mantiene su arquitectura en
  capas y no se modifican sus endpoints por esta orden. El token se guarda en
  `sessionStorage`; ante `401` se descarta la sesión y se vuelve al inicio de sesión.
- **Motivo:** Permitir el uso real del sistema desde el navegador sin alterar el contrato de
  API ni la arquitectura del backend.

---

## Plantilla para nuevas órdenes

```markdown
## OP-NNN — Título breve

- **Fecha de alta:** AAAA-MM-DD
- **Estado:** Vigente | Reemplazada por OP-NNN
- **Origen:** Instrucción directa del usuario | Derivada de <documento>
- **Contenido:** Descripción precisa e imperativa de la orden.
- **Motivo:** Razón de la orden y su impacto esperado.
```
