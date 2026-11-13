# ESPECIFICACIÓN DE ARQUITECTURA BACKEND (IA-READABLE) - ACTUALIZACIÓN DE ALCANCE

## 1. EXIGENCIA DE ALCANCE (SCOPE RESTRICTION)

* **Límite de Desarrollo:** RESTRINGIR la generación de código única y exclusivamente a la capa Backend (Lógica de Negocio, Controladores y Persistencia).
* **Omisión de UI:** PROHIBIR la generación de código de interfaz de usuario, maquetación, vistas web (HTML/CSS/JS) o componentes gráficos nativos durante esta fase.
* **Contrato de Integración Frontend:** EXIGIR que la IA deje constancia explícita y documentada de cada endpoint creado, definiendo un contrato de API claro para la posterior y futura incorporación del Frontend.

## 2. DOCUMENTACIÓN DE ENDPOINTS (API CONTRACT OBLIGATORIO)

* Para cada servicio expuesto, la IA DEBERÁ generar un bloque de documentación estructurada (tipo Swagger/OpenAPI simplificado) que contenga:
1. **Ruta/URL:** Endpoint exacto del recurso.
2. **Verbo HTTP:** (GET, POST, PUT, DELETE).
3. **Jerarquía de Acceso:** Rol requerido (Admin/Directivo, Preceptor, Docente, Alumno).


4. **Cuerpo de Petición (Request Body):** Estructura JSON con los nombres explicativos de las variables esperadas.
5. **Respuesta Esperada (Response):** Estructura JSON de éxito o error.



## 3. REGLAS GLOBALES DE DESARROLLO (IMPERATIVOS STRICTOS)

* **Nomenclatura:** IMPLEMENTAR nombres de variables, clases, atributos y métodos que sean estrictamente explicativos y descriptivos; PROHIBIDO utilizar abreviaturas ambiguas.
* **Documentación:** REDACTAR comentarios obligatorios que expliquen la función de cada método de una clase externa o librería que no haya sido desarrollada dentro del proyecto.
* **Paradigma:** ESTRUCTURAR el código exclusivamente bajo Programación Orientada a Objetos (POO).
* **Arquitectura:** APLICAR Diseño en Capas Multitier (Modelos, Repositorios/DAO, Servicios, Controladores) para separar la lógica de negocio del enrutamiento HTTP y el acceso a datos.

## 4. REQUISITOS TÉCNICOS FUNCIONALES OBLIGATORIOS

* IMPLEMENTAR un sistema de seguridad y autenticación basado en jerarquía de roles: Admin/Directivo, Preceptor, Docente y Alumno.


* DISEÑAR la persistencia de datos mediante un SGBD relacional o no relacional que esté completamente normalizado.


* CONFIGURAR restricciones de integridad referencial obligatorias a nivel de base de datos para asegurar la consistencia institucional.


* DESARROLLAR un módulo de reportabilidad transversal que permita la exportación automatizada de datos a formatos PDF o Excel.



## 5. PATRONES DE DISEÑO REQUERIDOS

* **Patrón Repository / Data Access Object (DAO):** UTILIZAR para aislar y encapsular todas las consultas a la base de datos, separando los modelos de la lógica de negocio.
* **Patrón Strategy:** APLICAR para abstraer los algoritmos de cálculo. Definir estrategias independientes para el cálculo de porcentajes de asistencia estudiantil y el cómputo automatizado de horas cátedra docentes.
* **Patrón Observer (Publicador/Suscriptor):** IMPLEMENTAR para el sistema de alertas. El servicio de registro de asistencia debe notificar automáticamente a los tableros de control cuando un estudiante acumula inasistencias consecutivas.



## 6. ESTRUCTURA DE MÓDULOS (ENTIDADES Y SERVICIOS)

### MÓDULO 1: CONTROL DE ASISTENCIA DE ESTUDIANTES

* **Entidades Principales:** `Estudiante`, `RegistroAsistenciaEstudiantil`.
* **Estados Permitidos:** LIMITAR estrictamente la asistencia a: Presente, Ausente, Justificado, Tarde.


* **Capa de Servicios (Lógica Backend):**
* CREAR procesador para la carga diaria estructurada por divisiones, asignaturas, fechas y estados.


* DESARROLLAR motor de procesamiento que calcule (en tiempo real) los porcentajes de asistencia acumulada agrupados por alumno, por curso y por períodos académicos.


* PROGRAMAR evento condicional que dispare alertas si un estudiante cae por debajo del límite de regularidad institucional.





### MÓDULO 2: ASISTENCIA Y PUNTUALIDAD DOCENTE

* **Entidades Principales:** `Docente`, `FirmaAsistencia`, `IncidenciaHoraria`, `GrillaHorariaInstitucional`.
* **Capa de Servicios (Lógica Backend):**
* DISEÑAR sistema de validación de identidad para el ingreso y egreso del personal docente.


* IMPLEMENTAR captura automatizada de horarios mediante marcas de tiempo (timestamps) fijas del servidor.


* DESARROLLAR algoritmo evaluador que detecte discrepancias de tiempo para registrar incidencias (tardanzas, salidas anticipadas o licencias).


* CREAR procesador matemático que cruce el presentismo detectado con el diseño de la grilla horaria para emitir un balance automatizado de horas cátedra efectivamente laboradas.