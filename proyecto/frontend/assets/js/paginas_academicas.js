/* ==========================================================================
   Páginas de administración y estructura académica.
   ========================================================================== */

(function () {
  "use strict";

  const C = Componentes;
  const U = Paginas.util;
  const ROLES = ["Admin/Directivo", "Preceptor", "Docente", "Alumno"];
  const ESTADOS_INSCRIPCION = ["Activo", "Inactivo"];

  function opcionesCursos(cursos) {
    return C.opcionesSelect(cursos, {
      texto: (curso) => curso.nombre_completo || curso.nombre,
    });
  }

  function opcionesDocentes(docentes) {
    return C.opcionesSelect(docentes, {
      texto: (docente) =>
        (docente.nombre_completo || "") + (docente.legajo ? " (" + docente.legajo + ")" : ""),
    });
  }

  function opcionesEstudiantes(estudiantes) {
    return C.opcionesSelect(estudiantes, {
      texto: (estudiante) =>
        (estudiante.nombre_completo || "") + (estudiante.legajo ? " (" + estudiante.legajo + ")" : ""),
    });
  }

  function opcionesMaterias(materias) {
    return C.opcionesSelect(materias, {
      texto: (materia) => (materia.codigo ? materia.codigo + " · " : "") + materia.nombre,
    });
  }

  function nombreUsuario(usuario) {
    return usuario ? C.texto(usuario.nombre_usuario) : "—";
  }

  function correoUsuario(usuario) {
    return usuario ? C.texto(usuario.correo_electronico) : "—";
  }

  function estadoCuenta(usuario) {
    return usuario
      ? C.insigniaBooleano(usuario.activo, "Activa", "Inactiva")
      : C.insignia("Sin cuenta", "neutra");
  }

  /* ------------------------------------------------------------------ Usuarios */

  async function renderUsuarios(contenedor) {
    await U.paginaListado(contenedor, {
      titulo: "Usuarios",
      descripcion: "Consultá las cuentas del sistema, creá usuarios y cambiá su estado.",
      filtros: [
        {
          nombre: "rol",
          etiqueta: "Rol",
          tipo: "select",
          vacio: "Todos los roles",
          opcionesHtml: C.opcionesDeLista(ROLES),
        },
        {
          nombre: "activo",
          etiqueta: "Estado",
          tipo: "select",
          vacio: "Todos",
          opcionesHtml: C.opcionesDeLista(["true", "false"], {
            etiquetasOpciones: { true: "Activas", false: "Inactivas" },
          }),
        },
      ],
      cargar: (parametros) => API.get("/usuarios", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Usuario", valor: (fila) => C.texto(fila.nombre_usuario) },
        { titulo: "Correo", valor: (fila) => C.texto(fila.correo_electronico) },
        { titulo: "Rol", valor: (fila) => C.insignia(fila.rol, "info") },
        { titulo: "Estado", valor: (fila) => C.insigniaBooleano(fila.activo, "Activa", "Inactiva") },
        { titulo: "Creado en", valor: (fila) => C.fechaHora(fila.creado_en) },
      ],
      vacio: "No hay usuarios que coincidan con los filtros",
      detalleVacio: "Probá limpiar los filtros o creá una cuenta nueva.",
      acciones: (fila, contexto) => {
        const acciones = [
          {
            texto: "Ver detalle",
            ejecutar: async () => {
              try {
                const usuario = (await API.get("/usuarios/" + fila.id)).datos;
                C.dialogoInformacion(
                  "Usuario: " + usuario.nombre_usuario,
                  '<dl class="definicion">' +
                    "<dt>Nombre de usuario</dt><dd>" + C.texto(usuario.nombre_usuario) + "</dd>" +
                    "<dt>Correo electrónico</dt><dd>" + C.texto(usuario.correo_electronico) + "</dd>" +
                    "<dt>Rol</dt><dd>" + C.insignia(usuario.rol, "info") + "</dd>" +
                    "<dt>Estado</dt><dd>" + C.insigniaBooleano(usuario.activo, "Activa", "Inactiva") + "</dd>" +
                    "<dt>Creado en</dt><dd>" + C.fechaHora(usuario.creado_en) + "</dd>" +
                    "</dl>"
                );
              } catch (error) {
                C.avisar("error", C.mensajeDetallado(error));
              }
            },
          },
        ];
        acciones.push({
          texto: fila.activo ? "Desactivar" : "Activar",
          clase: fila.activo ? "peligro" : "sutil",
          ejecutar: async () => {
            const accion = fila.activo ? "desactivar" : "activar";
            if (!window.confirm("¿Querés " + accion + " la cuenta de " + fila.nombre_usuario + "?")) {
              return;
            }
            try {
              const respuesta = await API.patch("/usuarios/" + fila.id + "/estado", {
                activo: !fila.activo,
              });
              C.avisar("exito", respuesta.mensaje || "Estado de la cuenta actualizado.");
              contexto.recargar();
            } catch (error) {
              C.avisar("error", C.mensajeDetallado(error));
            }
          },
        });
        return acciones;
      },
      crear: {
        texto: "Nuevo usuario",
        titulo: "Nuevo usuario",
        descripcion: "La contraseña debe tener al menos 8 caracteres.",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre_usuario", etiqueta: "Nombre de usuario", requerido: true, maxLongitud: 80, ayuda: "3 a 80 caracteres: letras, números, puntos, guiones y guiones bajos." },
          { nombre: "correo_electronico", etiqueta: "Correo electrónico", tipo: "email", requerido: true, maxLongitud: 255 },
          { nombre: "contrasena", etiqueta: "Contraseña", tipo: "password", requerido: true, maxLongitud: 128 },
          { nombre: "rol", etiqueta: "Rol", tipo: "select", requerido: true, vacio: "Seleccioná un rol", opcionesHtml: C.opcionesDeLista(ROLES) },
        ],
        enviar: (datos) => API.post("/usuarios", datos),
      },
    });
  }

  /* --------------------------------------------------------------- Estudiantes */

  async function renderEstudiantes(contenedor) {
    const catalogos = await U.catalogs(["cursos"]);
    await U.paginaListado(contenedor, {
      titulo: "Estudiantes",
      descripcion: "Padrón de estudiantes y sus cuentas asociadas.",
      nota:
        "El filtro por curso incluye estudiantes con matrícula en ese curso, aunque la matrícula no esté activa. Para el padrón de asistencia usá Inscripciones y filtrá estado Activo.",
      filtros: [
        {
          nombre: "curso_id",
          etiqueta: "Curso",
          tipo: "select",
          vacio: "Todos los cursos",
          opcionesHtml: opcionesCursos(catalogos.cursos),
        },
      ],
      cargar: (parametros) => API.get("/estudiantes", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Legajo", valor: (fila) => C.texto(fila.legajo) },
        { titulo: "Estudiante", valor: (fila) => C.texto(fila.nombre_completo) },
        { titulo: "Nacimiento", valor: (fila) => C.fecha(fila.fecha_nacimiento) },
        { titulo: "Usuario", valor: (fila) => nombreUsuario(fila.usuario) },
        { titulo: "Correo", valor: (fila) => correoUsuario(fila.usuario) },
        { titulo: "Cuenta", valor: (fila) => estadoCuenta(fila.usuario) },
      ],
      vacio: "No hay estudiantes para los filtros seleccionados",
      detalleVacio: "Probá con otro curso o creá un estudiante.",
      crear: {
        texto: "Nuevo estudiante",
        titulo: "Nuevo estudiante",
        descripcion: "Se crea la cuenta de acceso y los datos del estudiante en una sola operación.",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre_usuario", etiqueta: "Usuario", requerido: true, maxLongitud: 80 },
          { nombre: "correo_electronico", etiqueta: "Correo electrónico", tipo: "email", requerido: true, maxLongitud: 255 },
          { nombre: "contrasena", etiqueta: "Contraseña", tipo: "password", requerido: true, maxLongitud: 128, ayuda: "Mínimo 8 caracteres." },
          { nombre: "legajo", etiqueta: "Legajo", requerido: true, maxLongitud: 30 },
          { nombre: "nombres", etiqueta: "Nombres", requerido: true, maxLongitud: 120 },
          { nombre: "apellidos", etiqueta: "Apellidos", requerido: true, maxLongitud: 120 },
          { nombre: "fecha_nacimiento", etiqueta: "Fecha de nacimiento", tipo: "date", max: C.hoyServidor().fecha },
        ],
        enviar: (datos) => API.post("/estudiantes", datos),
      },
    });
  }

  /* ------------------------------------------------------------------ Docentes */

  async function renderDocentes(contenedor) {
    await U.paginaListado(contenedor, {
      titulo: "Docentes",
      descripcion: "Plantel docente y sus cuentas asociadas.",
      filtros: [
        { nombre: "buscar", etiqueta: "Buscar", tipo: "search", local: true, placeholder: "Legajo, nombre o título" },
      ],
      filtrarLocal: (valores, filas) => {
        const termino = (valores.buscar || "").toLowerCase();
        if (!termino) {
          return filas;
        }
        return filas.filter((fila) =>
          [
            fila.legajo,
            fila.nombre_completo,
            fila.nombres,
            fila.apellidos,
            fila.titulo_habilitante,
            fila.usuario && fila.usuario.nombre_usuario,
            fila.usuario && fila.usuario.correo_electronico,
          ]
            .filter(Boolean)
            .some((valor) => String(valor).toLowerCase().indexOf(termino) !== -1)
        );
      },
      cargar: () => API.get("/docentes").then((r) => r.datos || []),
      columnas: [
        { titulo: "Legajo", valor: (fila) => C.texto(fila.legajo) },
        { titulo: "Docente", valor: (fila) => C.texto(fila.nombre_completo) },
        { titulo: "Título habilitante", valor: (fila) => C.texto(fila.titulo_habilitante) },
        { titulo: "Usuario", valor: (fila) => nombreUsuario(fila.usuario) },
        { titulo: "Correo", valor: (fila) => correoUsuario(fila.usuario) },
        { titulo: "Cuenta", valor: (fila) => estadoCuenta(fila.usuario) },
      ],
      vacio: "Todavía no hay docentes registrados",
      detalleVacio: "Creá el primer docente para comenzar.",
      crear: {
        texto: "Nuevo docente",
        titulo: "Nuevo docente",
        descripcion: "Se crea la cuenta de acceso y los datos del docente.",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre_usuario", etiqueta: "Usuario", requerido: true, maxLongitud: 80 },
          { nombre: "correo_electronico", etiqueta: "Correo electrónico", tipo: "email", requerido: true, maxLongitud: 255 },
          { nombre: "contrasena", etiqueta: "Contraseña", tipo: "password", requerido: true, maxLongitud: 128, ayuda: "Mínimo 8 caracteres." },
          { nombre: "legajo", etiqueta: "Legajo", requerido: true, maxLongitud: 30 },
          { nombre: "nombres", etiqueta: "Nombres", requerido: true, maxLongitud: 120 },
          { nombre: "apellidos", etiqueta: "Apellidos", requerido: true, maxLongitud: 120 },
          { nombre: "titulo_habilitante", etiqueta: "Título habilitante", maxLongitud: 255 },
        ],
        enviar: (datos) => API.post("/docentes", datos),
      },
    });
  }

  /* -------------------------------------------------------------------- Cursos */

  async function renderCursos(contenedor) {
    await U.paginaListado(contenedor, {
      titulo: "Cursos",
      descripcion: "Catálogo de cursos por año lectivo.",
      filtros: [
        { nombre: "anio_lectivo", etiqueta: "Año lectivo", tipo: "number", min: 2000, max: 2200, placeholder: "2026" },
      ],
      cargar: (parametros) =>
        API.get("/cursos", parametros).then((r) =>
          (r.datos || [])
            .slice()
            .sort(
              (a, b) => b.anio_lectivo - a.anio_lectivo || a.nombre.localeCompare(b.nombre)
            )
        ),
      columnas: [
        { titulo: "Curso", valor: (fila) => C.texto(fila.nombre_completo) },
        { titulo: "Nombre", valor: (fila) => C.texto(fila.nombre) },
        { titulo: "División", valor: (fila) => C.texto(fila.division) },
        { titulo: "Turno", valor: (fila) => C.texto(fila.turno) },
        { titulo: "Año lectivo", valor: (fila) => C.texto(fila.anio_lectivo), clase: "numerico" },
      ],
      vacio: "No hay cursos para el año lectivo seleccionado",
      detalleVacio: "Probá con otro año o creá un curso.",
      crear: {
        texto: "Nuevo curso",
        titulo: "Nuevo curso",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre", etiqueta: "Nombre", requerido: true, maxLongitud: 80, placeholder: "1° Año" },
          { nombre: "division", etiqueta: "División", requerido: true, maxLongitud: 20, placeholder: "A" },
          { nombre: "anio_lectivo", etiqueta: "Año lectivo", tipo: "number", requerido: true, min: 2000, max: 2200, valor: C.hoyServidor().fecha.slice(0, 4) },
          { nombre: "turno", etiqueta: "Turno", requerido: true, maxLongitud: 40, placeholder: "Mañana" },
        ],
        enviar: (datos) =>
          API.post("/cursos", {
            nombre: datos.nombre,
            division: datos.division,
            anio_lectivo: Number(datos.anio_lectivo),
            turno: datos.turno,
          }),
      },
    });
  }

  /* ------------------------------------------------------------------ Materias */

  async function renderMaterias(contenedor) {
    await U.paginaListado(contenedor, {
      titulo: "Materias",
      descripcion: "Catálogo de materias de la institución.",
      filtros: [
        { nombre: "buscar", etiqueta: "Buscar", tipo: "search", local: true, placeholder: "Código o nombre" },
      ],
      filtrarLocal: (valores, filas) => {
        const termino = (valores.buscar || "").toLowerCase();
        if (!termino) {
          return filas;
        }
        return filas.filter(
          (fila) =>
            String(fila.nombre).toLowerCase().indexOf(termino) !== -1 ||
            String(fila.codigo).toLowerCase().indexOf(termino) !== -1
        );
      },
      cargar: () => API.get("/materias").then((r) => r.datos || []),
      columnas: [
        { titulo: "Código", valor: (fila) => C.texto(fila.codigo) },
        { titulo: "Nombre", valor: (fila) => C.texto(fila.nombre) },
      ],
      vacio: "Todavía no hay materias registradas",
      detalleVacio: "Creá la primera materia para comenzar.",
      crear: {
        texto: "Nueva materia",
        titulo: "Nueva materia",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre", etiqueta: "Nombre", requerido: true, maxLongitud: 120, placeholder: "Matemática" },
          { nombre: "codigo", etiqueta: "Código", requerido: true, maxLongitud: 30, placeholder: "MAT-01" },
        ],
        enviar: (datos) => API.post("/materias", datos),
      },
    });
  }

  /* ---------------------------------------------------------------- Períodos */

  async function renderPeriodos(contenedor) {
    const hoy = C.hoyServidor().fecha;
    await U.paginaListado(contenedor, {
      titulo: "Períodos académicos",
      descripcion: "Períodos usados en resúmenes, balances y reportes.",
      filtros: [
        { nombre: "anio_lectivo", etiqueta: "Año lectivo", tipo: "number", min: 2000, max: 2200, placeholder: "2026" },
      ],
      cargar: (parametros) => API.get("/periodos-academicos", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Período", valor: (fila) => C.texto(fila.nombre) },
        { titulo: "Inicio", valor: (fila) => C.fecha(fila.fecha_inicio) },
        { titulo: "Fin", valor: (fila) => C.fecha(fila.fecha_fin) },
        { titulo: "Año lectivo", valor: (fila) => C.texto(fila.anio_lectivo), clase: "numerico" },
        {
          titulo: "Situación",
          valor: (fila) =>
            fila.fecha_inicio <= hoy && hoy <= fila.fecha_fin
              ? C.insignia("Vigente", "ok")
              : C.insignia("Fuera de vigencia", "neutra"),
        },
      ],
      vacio: "No hay períodos para el año lectivo seleccionado",
      detalleVacio: "Probá con otro año o creá un período.",
      crear: {
        texto: "Nuevo período",
        titulo: "Nuevo período académico",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "nombre", etiqueta: "Nombre", requerido: true, maxLongitud: 100 },
          { nombre: "fecha_inicio", etiqueta: "Fecha de inicio", tipo: "date", requerido: true },
          { nombre: "fecha_fin", etiqueta: "Fecha de fin", tipo: "date", requerido: true },
          { nombre: "anio_lectivo", etiqueta: "Año lectivo", tipo: "number", requerido: true, min: 2000, max: 2200, valor: C.hoyServidor().fecha.slice(0, 4) },
        ],
        enviar: (datos) => {
          if (datos.fecha_fin < datos.fecha_inicio) {
            throw new Error("La fecha de fin no puede ser anterior a la de inicio.");
          }
          return API.post("/periodos-academicos", {
            nombre: datos.nombre,
            fecha_inicio: datos.fecha_inicio,
            fecha_fin: datos.fecha_fin,
            anio_lectivo: Number(datos.anio_lectivo),
          });
        },
      },
    });
  }

  /* ------------------------------------------------------------- Inscripciones */

  async function renderInscripciones(contenedor) {
    const catalogos = await U.catalogs(["cursos", "estudiantes"]);
    await U.paginaListado(contenedor, {
      titulo: "Inscripciones",
      descripcion: "Matrículas de estudiantes en cursos.",
      filtros: [
        { nombre: "curso_id", etiqueta: "Curso", tipo: "select", vacio: "Todos los cursos", opcionesHtml: opcionesCursos(catalogos.cursos) },
        { nombre: "estudiante_id", etiqueta: "Estudiante", tipo: "select", vacio: "Todos los estudiantes", opcionesHtml: opcionesEstudiantes(catalogos.estudiantes) },
      ],
      cargar: (parametros) => API.get("/inscripciones", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Estudiante", valor: (fila) => (fila.estudiante ? C.texto(fila.estudiante.legajo) + " · " + C.texto(fila.estudiante.nombre_completo) : "—") },
        { titulo: "Curso", valor: (fila) => C.texto(fila.curso && fila.curso.nombre_completo) },
        { titulo: "Fecha", valor: (fila) => C.fecha(fila.fecha_inscripcion) },
        { titulo: "Estado", valor: (fila) => C.insignia(fila.estado, fila.estado === "Activo" ? "ok" : "neutra") },
      ],
      vacio: "No hay matrículas que coincidan con los filtros",
      detalleVacio: "Probá con otro curso o creá una inscripción.",
      crear: {
        texto: "Nueva inscripción",
        titulo: "Nueva inscripción",
        permitido: U.puedeGestionarInscripciones(),
        campos: [
          { nombre: "estudiante_id", etiqueta: "Estudiante", tipo: "select", requerido: true, vacio: "Seleccioná un estudiante", opcionesHtml: opcionesEstudiantes(catalogos.estudiantes) },
          { nombre: "curso_id", etiqueta: "Curso", tipo: "select", requerido: true, vacio: "Seleccioná un curso", opcionesHtml: opcionesCursos(catalogos.cursos) },
          { nombre: "fecha_inscripcion", etiqueta: "Fecha de inscripción", tipo: "date", valor: C.hoyServidor().fecha },
          { nombre: "estado", etiqueta: "Estado", tipo: "select", opcionesHtml: C.opcionesDeLista(ESTADOS_INSCRIPCION, { seleccionado: "Activo" }) },
        ],
        enviar: (datos) =>
          API.post("/inscripciones", {
            estudiante_id: Number(datos.estudiante_id),
            curso_id: Number(datos.curso_id),
            fecha_inscripcion: datos.fecha_inscripcion || undefined,
            estado: datos.estado || "Activo",
          }),
      },
    });
  }

  /* ------------------------------------------------------------- Asignaciones */

  async function renderAsignaciones(contenedor) {
    const catalogos = await U.catalogs(["cursos", "materias", "docentes"]);
    await U.paginaListado(contenedor, {
      titulo: "Asignaciones docentes",
      descripcion: "Vínculo entre docente, curso y materia. Debe existir antes de crear bloques de grilla.",
      filtros: [
        { nombre: "docente_id", etiqueta: "Docente", tipo: "select", vacio: "Todos los docentes", opcionesHtml: opcionesDocentes(catalogos.docentes) },
        { nombre: "curso_id", etiqueta: "Curso", tipo: "select", vacio: "Todos los cursos", opcionesHtml: opcionesCursos(catalogos.cursos) },
        { nombre: "materia_id", etiqueta: "Materia", tipo: "select", vacio: "Todas las materias", opcionesHtml: opcionesMaterias(catalogos.materias) },
      ],
      cargar: (parametros) => API.get("/asignaciones-docentes", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Docente", valor: (fila) => (fila.docente ? C.texto(fila.docente.legajo) + " · " + C.texto(fila.docente.nombre_completo) : "—") },
        { titulo: "Curso", valor: (fila) => C.texto(fila.curso && fila.curso.nombre_completo) },
        { titulo: "Materia", valor: (fila) => (fila.materia ? C.texto((fila.materia.codigo ? fila.materia.codigo + " · " : "") + fila.materia.nombre) : "—") },
      ],
      vacio: "No hay asignaciones docente-materia-curso",
      detalleVacio: "Creá una asignación para habilitar la grilla y las firmas.",
      crear: {
        texto: "Nueva asignación",
        titulo: "Nueva asignación docente",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "docente_id", etiqueta: "Docente", tipo: "select", requerido: true, vacio: "Seleccioná un docente", opcionesHtml: opcionesDocentes(catalogos.docentes) },
          { nombre: "curso_id", etiqueta: "Curso", tipo: "select", requerido: true, vacio: "Seleccioná un curso", opcionesHtml: opcionesCursos(catalogos.cursos) },
          { nombre: "materia_id", etiqueta: "Materia", tipo: "select", requerido: true, vacio: "Seleccioná una materia", opcionesHtml: opcionesMaterias(catalogos.materias) },
        ],
        enviar: (datos) =>
          API.post("/asignaciones-docentes", {
            docente_id: Number(datos.docente_id),
            curso_id: Number(datos.curso_id),
            materia_id: Number(datos.materia_id),
          }),
      },
    });
  }

  /* -------------------------------------------------------------------- Grilla */

  async function renderGrilla(contenedor) {
    const catalogos = await U.catalogs(["cursos", "materias", "docentes"]);
    const dias = C.NOMBRES_DIA.slice(1).map((nombre, indice) => ({ valor: indice + 1, texto: nombre }));
    await U.paginaListado(contenedor, {
      titulo: "Grilla horaria",
      descripcion: "Horario institucional por curso, materia y docente.",
      filtros: [
        { nombre: "docente_id", etiqueta: "Docente", tipo: "select", vacio: "Todos los docentes", opcionesHtml: opcionesDocentes(catalogos.docentes) },
        { nombre: "curso_id", etiqueta: "Curso", tipo: "select", vacio: "Todos los cursos", opcionesHtml: opcionesCursos(catalogos.cursos) },
        { nombre: "materia_id", etiqueta: "Materia", tipo: "select", vacio: "Todas las materias", opcionesHtml: opcionesMaterias(catalogos.materias) },
        { nombre: "anio_lectivo", etiqueta: "Año lectivo", tipo: "number", min: 2000, max: 2200, placeholder: "2026" },
        { nombre: "dia_semana", etiqueta: "Día", tipo: "select", vacio: "Todos los días", opcionesHtml: C.opcionesSelect(dias, { valor: (d) => d.valor, texto: (d) => d.texto }) },
      ],
      cargar: (parametros) => API.get("/grillas-horarias", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Día", valor: (fila) => C.esc(C.nombreDia(fila.dia_semana)) },
        { titulo: "Hora", valor: (fila) => C.esc(fila.hora_inicio + " – " + fila.hora_fin) },
        { titulo: "Curso", valor: (fila) => C.texto(fila.curso && fila.curso.nombre_completo) },
        { titulo: "Materia", valor: (fila) => C.texto(fila.materia && fila.materia.nombre) },
        { titulo: "Docente", valor: (fila) => C.texto(fila.docente && fila.docente.nombre_completo) },
        { titulo: "Aula", valor: (fila) => C.texto(fila.aula) },
      ],
      vacio: "No hay bloques horarios para los filtros seleccionados",
      detalleVacio: "Creá un bloque después de registrar la asignación docente correspondiente.",
      crear: {
        texto: "Nuevo bloque",
        titulo: "Nuevo bloque horario",
        descripcion: "El docente debe tener una asignación previa para ese curso y materia.",
        permitido: U.esAdmin(),
        campos: [
          { nombre: "curso_id", etiqueta: "Curso", tipo: "select", requerido: true, vacio: "Seleccioná un curso", opcionesHtml: opcionesCursos(catalogos.cursos) },
          { nombre: "materia_id", etiqueta: "Materia", tipo: "select", requerido: true, vacio: "Seleccioná una materia", opcionesHtml: opcionesMaterias(catalogos.materias) },
          { nombre: "docente_id", etiqueta: "Docente", tipo: "select", requerido: true, vacio: "Seleccioná un docente", opcionesHtml: opcionesDocentes(catalogos.docentes) },
          { nombre: "dia_semana", etiqueta: "Día de la semana", tipo: "select", requerido: true, vacio: "Seleccioná un día", opcionesHtml: C.opcionesSelect(dias, { valor: (d) => d.valor, texto: (d) => d.texto }) },
          { nombre: "hora_inicio", etiqueta: "Hora de inicio", tipo: "time", requerido: true },
          { nombre: "hora_fin", etiqueta: "Hora de fin", tipo: "time", requerido: true },
          { nombre: "aula", etiqueta: "Aula", maxLongitud: 50 },
        ],
        enviar: (datos) => {
          if (datos.hora_inicio >= datos.hora_fin) {
            throw new Error("La hora de inicio debe ser anterior a la hora de fin.");
          }
          return API.post("/grillas-horarias", {
            curso_id: Number(datos.curso_id),
            materia_id: Number(datos.materia_id),
            docente_id: Number(datos.docente_id),
            dia_semana: Number(datos.dia_semana),
            hora_inicio: datos.hora_inicio,
            hora_fin: datos.hora_fin,
            aula: datos.aula || undefined,
          });
        },
      },
    });
  }

  Object.assign(Paginas, {
    usuarios: renderUsuarios,
    estudiantes: renderEstudiantes,
    docentes: renderDocentes,
    cursos: renderCursos,
    materias: renderMaterias,
    periodos: renderPeriodos,
    inscripciones: renderInscripciones,
    asignaciones: renderAsignaciones,
    grilla: renderGrilla,
  });
})();
