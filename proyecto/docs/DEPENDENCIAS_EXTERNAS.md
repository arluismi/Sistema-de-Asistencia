# Uso de Librerías Externas

Este documento complementa los comentarios del código y cumple el requisito de explicar la
función de los métodos de clases y librerías que no fueron desarrolladas dentro del proyecto.
Los comentarios inline se encuentran junto a cada llamada relevante.

## 1. Flask

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `Flask(__name__, instance_relative_config=True)` | Crea la aplicación WSGI y habilita la carpeta `instance/` | `aplicacion/__init__.py` |
| `app.config.from_object(clase)` | Carga atributos de configuración desde una clase | `aplicacion/__init__.py` |
| `app.json.ensure_ascii` | Controla si los acentos se escapan en JSON | `aplicacion/__init__.py` |
| `app.register_blueprint(bp, url_prefix=...)` | Monta un grupo de rutas bajo un prefijo | `aplicacion/__init__.py` |
| `Blueprint(name, __name__)` | Agrupa endpoints relacionados | `controladores/*.py` |
| `@blueprint.get/post/put/patch` | Declara una ruta y su verbo HTTP | `controladores/*.py` |
| `request.get_json(silent=True)` | Obtiene el cuerpo JSON sin lanzar excepción si es inválido | `utilidades/validadores.py` |
| `request.args`, `request.headers`, `request.path` | Acceden a parámetros, encabezados y ruta de la petición | controladores y seguridad |
| `jsonify(diccionario)` | Serializa a JSON y fija el `Content-Type` | `utilidades/respuestas.py` |
| `g.get(...)`, `g.usuario_actual` | Almacenamiento con alcance de una petición | `seguridad/autenticacion.py` |
| `current_app.config` | Accede a la configuración desde cualquier módulo | seguridad, servicios y utilidades |
| `send_file(BytesIO, mimetype, as_attachment, download_name)` | Envía un archivo binario como descarga | `controladores/controlador_reportes.py` |
| `app.test_client()` | Cliente HTTP interno usado por las pruebas | `pruebas/conftest.py` |
| `app.app_context()` | Crea contexto de aplicación fuera de una petición | comandos y pruebas |
| `app.cli.command(nombre)` | Expone una función como comando de terminal | `aplicacion/comandos/__init__.py` |
| `app.logger.exception/warning` | Registra errores en el log de Flask | `aplicacion/errores/manejadores.py` |

## 2. Flask-SQLAlchemy y SQLAlchemy

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `SQLAlchemy()` | Crea la extensión sin asociarla aún a una aplicación | `aplicacion/extenciones.py` |
| `db.init_app(app)` | Vincula la extensión y la cadena de conexión a Flask | `aplicacion/__init__.py` |
| `db.Model` | Clase base declarativa de los modelos | `modelos/base.py` |
| `db.Column(...)` | Declara una columna con tipo y restricciones | todos los modelos |
| `db.ForeignKey(..., ondelete=...)` | Declara una clave foránea y su acción de borrado | modelos |
| `db.relationship(...)` | Define la navegación entre entidades | modelos |
| `db.Enum(..., values_callable=..., native_enum=False)` | Almacena enums como texto con `CHECK` | `modelos/columnas_enum.py` |
| `db.UniqueConstraint`, `db.CheckConstraint`, `db.Index` | Declaran restricciones e índices a nivel de tabla | modelos |
| `db.DateTime(default=..., onupdate=...)` | Asigna marcas de auditoría al insertar/actualizar | `modelos/base.py` |
| `db.session.get(modelo, id)` | Busca por clave primaria usando el mapa de identidad | `repositorios/repositorio_base.py` |
| `db.session.add(entidad)` / `add_all(lista)` | Marca entidades nuevas para inserción | repositorios |
| `db.session.delete(entidad)` | Marca una entidad para eliminación | `repositorios/repositorio_base.py` |
| `db.session.commit()` | Confirma la transacción | repositorios |
| `db.session.flush()` | Envía cambios pendientes sin cerrar la transacción | servicios de asistencia |
| `db.session.rollback()` | Revierte la transacción ante errores | `errores/manejadores.py` |
| `db.session.remove()` | Descarta la sesión al final de un contexto | pruebas |
| `db.create_all()` / `db.drop_all()` | Crea o elimina las tablas declaradas | comandos y pruebas |
| `select(Modelo)` | Construye consultas tipadas de SQLAlchemy 2.x | repositorios |
| `.where(...)`, `.join(...)`, `.order_by(...)`, `.limit(...)` | Componen la consulta SQL | repositorios |
| `.execute(consulta).scalars().all()` | Ejecuta y materializa entidades | repositorios |
| `.scalar_one_or_none()`, `.first()` | Devuelven uno o ningún resultado | repositorios |
| `event.listens_for(Engine, "connect")` | Ejecuta código en cada conexión nueva | `aplicacion/extenciones.py` |
| `IntegrityError` | Excepción por violación de restricciones | manejadores y pruebas |

## 3. PyJWT

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `jwt.encode(payload, clave, algorithm)` | Firma el token con HS256 | `seguridad/tokens.py` |
| `jwt.decode(token, clave, algorithms=[...])` | Verifica firma y expiración | `seguridad/tokens.py` |
| `jwt.ExpiredSignatureError` | Indica token expirado | `seguridad/tokens.py` |
| `jwt.InvalidTokenError` | Indica token mal formado o firma inválida | `seguridad/tokens.py` |

## 4. Werkzeug

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `generate_password_hash(contrasena)` | Genera hash con sal para almacenar contraseñas | `seguridad/contrasenas.py` |
| `check_password_hash(hash, contrasena)` | Compara una contraseña con el hash en tiempo constante | `seguridad/contrasenas.py` |

## 5. Flask-Cors

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `CORS(app, resources={...})` | Agrega encabezados CORS para el futuro frontend | `aplicacion/__init__.py` |

## 6. python-dotenv

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `load_dotenv(ruta)` | Carga variables desde `.env` sin sobreescribir el entorno | `configuracion.py` |

## 7. ReportLab

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `SimpleDocTemplate(buffer, pagesize, margins, title)` | Administra el documento PDF y sus márgenes | `reportes/generador_pdf.py` |
| `documento.build(elementos)` | Procesa el flujo y escribe el PDF en el buffer | `reportes/generador_pdf.py` |
| `Paragraph(texto, estilo)` | Agrega texto con formato | `reportes/generador_pdf.py` |
| `Spacer(ancho, alto)` | Inserta espacio vertical | `reportes/generador_pdf.py` |
| `Table(datos, repeatRows=1)` | Construye la tabla y repite el encabezado por página | `reportes/generador_pdf.py` |
| `TableStyle([...])` | Define colores, fuentes, bordes y alineación | `reportes/generador_pdf.py` |
| `getSampleStyleSheet()` | Devuelve los estilos estándar (título, normal) | `reportes/generador_pdf.py` |
| `colors.HexColor`, `A4`, `landscape`, `cm` | Colores y unidades de página | `reportes/generador_pdf.py` |

## 8. openpyxl

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `Workbook()` | Crea un libro Excel vacío | `reportes/generador_excel.py` |
| `libro.active` | Obtiene la hoja activa | `reportes/generador_excel.py` |
| `hoja.title` | Asigna el nombre de la hoja | `reportes/generador_excel.py` |
| `hoja.cell(row, column, value)` | Escribe o lee una celda | `reportes/generador_excel.py` |
| `Font`, `PatternFill`, `Alignment`, `Border`, `Side` | Estilos de texto, fondo, alineación y bordes | `reportes/generador_excel.py` |
| `hoja.column_dimensions[...]` | Ajusta el ancho de las columnas | `reportes/generador_excel.py` |
| `get_column_letter(numero)` | Convierte un índice de columna en letra Excel | `reportes/generador_excel.py` |
| `hoja.freeze_panes` | Fija encabezados al desplazar la hoja | `reportes/generador_excel.py` |
| `libro.save(buffer)` | Serializa el libro `.xlsx` en el buffer | `reportes/generador_excel.py` |

## 9. pytest (sólo pruebas)

| Elemento externo | Función | Dónde se usa |
|---|---|---|
| `@pytest.fixture()` | Declara datos y aplicaciones reutilizables | `pruebas/conftest.py` |
| `monkeypatch.setattr(...)` | Reemplaza temporalmente el reloj del servidor | pruebas de firmas |
| `pytest.raises(...)` | Verifica que se lance una excepción esperada | prueba de integridad |
| `pytest.approx(...)` | Compara números flotantes con tolerancia | prueba de balance |

## 10. tzdata

`tzdata` provee la base de datos IANA en sistemas Windows, donde `zoneinfo` no encuentra
las zonas horarias instaladas por el sistema operativo. No se invoca directamente: lo
consume `zoneinfo.ZoneInfo`.
