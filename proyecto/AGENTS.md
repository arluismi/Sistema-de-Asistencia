# Guía de trabajo para agentes de IA

Este archivo es el punto de entrada para cualquier agente que trabaje dentro de
`proyecto/`. Antes de modificar código, leer:

1. `proyecto/ia/ORDENES_PERSISTENTES.md` — registro obligatorio de órdenes permanentes.
2. `proyecto/liniamientos.md` — especificación de arquitectura y alcance.
3. `docs/CONTRATO_API.md` — contrato de los endpoints implementados.
4. `docs/ARQUITECTURA.md` — capas, patrones y decisiones de diseño.

## Reglas permanentes del proyecto

- El alcance es exclusivamente **backend**. No generar vistas, HTML, CSS, JavaScript de
  interfaz ni componentes gráficos.
- Todo endpoint nuevo o modificado debe documentarse en `docs/CONTRATO_API.md` con ruta,
  verbo HTTP, roles autorizados, cuerpo de petición y respuesta esperada.
- Usar Programación Orientada a Objetos y nombres descriptivos en español; prohibidas las
  abreviaturas ambiguas.
- Respetar la arquitectura en capas: `modelos` → `repositorios` → `servicios` →
  `controladores`. Los controladores no ejecutan consultas directamente.
- Comentar el uso de métodos de librerías externas (Flask, SQLAlchemy, PyJWT, reportlab,
  openpyxl) explicando qué hace cada llamada relevante.
- Registrar toda nueva orden persistente en `proyecto/ia/ORDENES_PERSISTENTES.md`, sin
  borrar entradas previas.

## Comandos de referencia

```powershell
# Crear entorno e instalar dependencias
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Inicializar la base de datos y cargar datos de demostración
.\.venv\Scripts\python.exe run.py inicializar-base-de-datos
.\.venv\Scripts\python.exe run.py sembrar-datos-demostracion

# Ejecutar el servidor de desarrollo
.\.venv\Scripts\python.exe run.py

# Ejecutar las pruebas
.\.venv\Scripts\python.exe -m pytest
```
