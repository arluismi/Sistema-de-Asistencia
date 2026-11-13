/* ==========================================================================
   Núcleo de páginas: utilidades compartidas, panel, perfil y horario personal.
   Cada archivo de páginas agrega sus funciones al objeto global `Paginas`.
   ========================================================================== */

const Paginas = {};

(function () {
  "use strict";

  const C = Componentes;

  function rol() {
    return API.SESION.rol();
  }

  function esAdmin() {
    return rol() === "Admin/Directivo";
  }

  function esPreceptor() {
    return rol() === "Preceptor";
  }

  function esDocente() {
    return rol() === "Docente";
  }

  function esAlumno() {
    return rol() === "Alumno";
  }

  function puedeGestionarInscripciones() {
    return esAdmin() || esPreceptor();
  }

  function marco(titulo, descripcion, contenido, acciones) {
    return (
      '<section class="pagina"><div class="pagina-encabezado"><div><h1>' +
      C.esc(titulo) +
      "</h1>" +
      (descripcion ? "<p>" + descripcion + "</p>" : "") +
      '</div><div class="acciones">' +
      (acciones || "") +
      "</div></div>" +
      contenido +
      "</section>"
    );
  }

  function indicador(etiqueta, valor, detalle, clase) {
    return (
      '<div class="indicador ' +
      (clase || "") +
      '"><span class="etiqueta">' +
      C.esc(etiqueta) +
      '</span><span class="valor">' +
      valor +
      "</span>" +
      (detalle ? '<span class="detalle">' + detalle + "</span>" : "") +
      "</div>"
    );
  }

  function tarjetasResumen(resumen, opciones) {
    const ajustes = opciones || {};
    if (!resumen) {
      return C.estadoVacio("Sin datos de resumen");
    }
    return (
      '<div class="grilla-tarjetas">' +
      indicador("Registros", C.numero(resumen.total_registros, 0), "Total considerados") +
      indicador("Presentes", C.numero(resumen.presentes, 0)) +
      indicador("Ausentes", C.numero(resumen.ausentes, 0)) +
      indicador("Justificados", C.numero(resumen.justificados, 0)) +
      indicador("Tardes", C.numero(resumen.tardes, 0)) +
      indicador("Asistencia", C.porcentaje(resumen.porcentaje_asistencia), "Sobre el total", "destacado") +
      indicador(
        "Presentismo efectivo",
        C.porcentaje(resumen.porcentaje_presentismo_efectivo),
        "Excluye justificados (estrategia institucional)"
      ) +
      indicador("Umbral", C.porcentaje(resumen.umbral_regularidad_porcentaje), "Mínimo configurado") +
      indicador(
        "Regularidad",
        C.insigniaRegularidad(resumen.estado_regularidad),
        ajustes.detalleRegularidad || ""
      ) +
      "</div>"
    );
  }

  async function resultadoSeguro(promesa) {
    try {
      return { ok: true, valor: await promesa };
    } catch (error) {
      return { ok: false, error: error };
    }
  }

  async function catalogs(necesarios) {
    const cargadores = {
      cursos: () => API.get("/cursos").then((r) => r.datos || []),
      materias: () => API.get("/materias").then((r) => r.datos || []),
      periodos: () => API.get("/periodos-academicos").then((r) => r.datos || []),
      estudiantes: () => API.get("/estudiantes").then((r) => r.datos || []),
      docentes: () => API.get("/docentes").then((r) => r.datos || []),
    };
    const claves = necesarios || Object.keys(cargadores);
    const resultados = await Promise.allSettled(claves.map((clave) => cargadores[clave]()));
    const salida = {};
    claves.forEach((clave, indice) => {
      salida[clave] =
        resultados[indice].status === "fulfilled" ? resultados[indice].value : [];
    });
    return salida;
  }

  async function resolverDocenteId() {
    const guardado = API.SESION.docenteId();
    if (guardado) {
      return guardado;
    }
    try {
      const perfil = API.SESION.perfil();
      if (!perfil) {
        return null;
      }
      const docentes = (await API.get("/docentes")).datos || [];
      const propio = docentes.find(
        (docente) => docente.usuario && Number(docente.usuario.id) === Number(perfil.id)
      );
      if (propio) {
        API.SESION.guardarDocenteId(propio.id);
        return propio.id;
      }
    } catch (error) {
      return null;
    }
    return null;
  }

  async function resolverCursoAlumno() {
    const guardado = API.SESION.cursoAlumno();
    if (guardado) {
      return guardado;
    }
    try {
      const registros = (await API.get("/asistencias-estudiantes")).datos || [];
      const conCurso = registros.find((registro) => registro.curso);
      if (conCurso) {
        API.SESION.guardarCursoAlumno(conCurso.curso);
        return conCurso.curso;
      }
    } catch (error) {
      return null;
    }
    return null;
  }

  /* ------------------------------------------------------- Listado reutilizable */

  async function paginaListado(contenedor, configuracion) {
    const config = configuracion;
    const filtros = config.filtros || [];
    const htmlBotonCrear = config.crear
      ? '<button type="button" class="boton primario" id="boton-crear">+ ' +
        C.esc(config.crear.texto || "Nuevo") +
        "</button>"
      : "";

    contenedor.innerHTML = marco(
      config.titulo,
      config.descripcion,
      (filtros.length
        ? '<form class="filtros" id="form-filtros">' +
          C.camposDeFiltro(filtros) +
          '<div class="acciones-filtros"><button type="submit" class="boton primario">Filtrar</button>' +
          '<button type="reset" class="boton">Limpiar</button></div></form>'
        : "") +
        (config.nota ? '<p class="nota">' + config.nota + "</p>" : "") +
        '<div id="zona-listado">' +
        C.esqueleto() +
        "</div>",
      (config.botonesExtra || "") + htmlBotonCrear
    );

    const zona = contenedor.querySelector("#zona-listado");
    const formularioFiltros = contenedor.querySelector("#form-filtros");
    const botonCrear = contenedor.querySelector("#boton-crear");
    let filas = [];
    let permisoCreacion = config.crear && (config.crear.permitido === undefined || config.crear.permitido);

    async function recargar() {
      const valores = formularioFiltros ? C.leerFormulario(formularioFiltros) : {};
      const parametros = {};
      filtros.forEach((filtro) => {
        if (!filtro.local && valores[filtro.nombre]) {
          parametros[filtro.nombre] = valores[filtro.nombre];
        }
      });
      zona.innerHTML = C.esqueleto();
      zona.setAttribute("aria-busy", "true");
      try {
        filas = await config.cargar(parametros);
        if (config.filtrarLocal) {
          filas = config.filtrarLocal(valores, filas) || [];
        }
        const columnasBase =
          typeof config.columnas === "function" ? config.columnas(filas) : config.columnas;
        const columnas = columnasBase.slice();
        if (config.acciones) {
          columnas.push({
            titulo: "Acciones",
            valor: (fila) => C.botonesDeAcciones(config.acciones(fila, { recargar: recargar })),
          });
        }
        zona.innerHTML =
          C.tabla({
            columnas: columnas,
            filas: filas,
            caption: config.titulo,
            clase: config.claseTabla,
            vacio: config.vacio || "Sin resultados",
            detalleVacio: config.detalleVacio,
            claseFila: config.claseFila,
          }) +
          (filas.length
            ? '<div class="tabla-pie"><span>Mostrando ' +
              filas.length +
              ' resultado' +
              (filas.length === 1 ? "" : "s") +
              '</span><button type="button" class="boton chico" id="boton-actualizar">Actualizar</button></div>'
            : "");
        C.conectarAcciones(zona, filas, (fila) =>
          config.acciones(fila, { recargar: recargar })
        );
        const actualizar = zona.querySelector("#boton-actualizar");
        if (actualizar) {
          actualizar.addEventListener("click", recargar);
        }
      } catch (error) {
        zona.innerHTML =
          '<div class="tarjeta"><div class="error-formulario">' +
          C.esc(C.mensajeDetallado(error)) +
          '</div><div class="form-acciones"><button type="button" class="boton" id="boton-reintentar">Reintentar</button></div></div>';
        const reintentar = zona.querySelector("#boton-reintentar");
        if (reintentar) {
          reintentar.addEventListener("click", recargar);
        }
      } finally {
        zona.setAttribute("aria-busy", "false");
      }
    }

    if (formularioFiltros) {
      formularioFiltros.addEventListener("submit", (evento) => {
        evento.preventDefault();
        recargar();
      });
      formularioFiltros.addEventListener("reset", () => window.setTimeout(recargar, 0));
    }

    if (botonCrear) {
      botonCrear.addEventListener("click", async () => {
        const resultado = await C.dialogoFormulario({
          titulo: config.crear.titulo || config.crear.texto,
          descripcion: config.crear.descripcion,
          campos: config.crear.campos,
          contenidoExtra: config.crear.contenidoExtra,
          textoBoton: config.crear.textoBoton || "Guardar",
          enviar: config.crear.enviar,
        });
        if (resultado) {
          C.avisar(
            "exito",
            (resultado && resultado.mensaje) || config.crear.mensajeExito || "Registro creado correctamente."
          );
          recargar();
        }
      });
      if (!permisoCreacion) {
        botonCrear.remove();
      }
    }

    await recargar();
  }

  /* ------------------------------------------------------------------- Panel */

  function accesosDirectos(enlaces) {
    return (
      '<div class="tarjeta"><h2>Accesos rápidos</h2><div class="pila-chica">' +
      enlaces
        .map(
          (enlace) =>
            '<a class="boton" href="' +
            enlace.ruta +
            '">' +
            C.esc(enlace.texto) +
            "</a>"
        )
        .join("") +
      "</div></div>"
    );
  }

  async function panelAlumno(zona, hoy) {
    const [resumen, asistencias, curso] = await Promise.all([
      resultadoSeguro(API.get("/asistencias-estudiantes/resumen")),
      resultadoSeguro(API.get("/asistencias-estudiantes")),
      resultadoSeguro(resolverCursoAlumno()),
    ]);

    const tarjetas = [];
    if (resumen.ok) {
      const datos = resumen.valor.datos;
      tarjetas.push(
        indicador(
          "Regularidad",
          C.insigniaRegularidad(datos.resumen.estado_regularidad),
          (datos.periodo ? datos.periodo.nombre : "Todos los registros"),
          "destacado"
        ),
        indicador("Asistencia", C.porcentaje(datos.resumen.porcentaje_asistencia)),
        indicador("Presentismo efectivo", C.porcentaje(datos.resumen.porcentaje_presentismo_efectivo)),
        indicador("Registros", C.numero(datos.resumen.total_registros, 0))
      );
    } else {
      tarjetas.push(indicador("Mi regularidad", "Sin datos", C.esc(resumen.error.message)));
    }

    let bloques = "";
    if (curso.ok && curso.valor) {
      const grilla = await resultadoSeguro(
        API.get("/grillas-horarias", { curso_id: curso.valor.id, dia_semana: hoy.diaSemana })
      );
      if (grilla.ok) {
        const clases = (grilla.valor.datos || []).sort((a, b) =>
          a.hora_inicio.localeCompare(b.hora_inicio)
        );
        bloques =
          '<div class="tarjeta"><h2>Clases de hoy · ' +
          C.esc(curso.valor.nombre_completo) +
          "</h2>" +
          (clases.length
            ? '<ul class="lista-simple">' +
              clases
                .map(
                  (clase) =>
                    "<li><strong>" +
                    C.esc(clase.hora_inicio + "–" + clase.hora_fin + " · " + (clase.materia ? clase.materia.nombre : "Materia")) +
                    "</strong><span>" +
                    C.esc((clase.aula ? clase.aula + " · " : "") + (clase.docente ? clase.docente.nombre_completo : "")) +
                    "</span></li>"
                )
                .join("") +
              "</ul>"
            : '<p class="texto-suave">No hay clases programadas para hoy.</p>') +
          "</div>";
      }
    }

    const listaAsistencias = asistencias.ok ? (asistencias.valor.datos || []).slice(0, 5) : [];
    zona.innerHTML =
      (tarjetas.length ? '<div class="grilla-tarjetas">' + tarjetas.join("") + "</div>" : "") +
      bloques +
      '<div class="tarjeta"><div class="tarjeta-titulo"><h2>Últimos registros</h2><a href="#/mi-asistencia">Ver todos</a></div>' +
      C.tabla({
        columnas: [
          { titulo: "Fecha", valor: (fila) => C.fecha(fila.fecha) },
          { titulo: "Materia", valor: (fila) => C.texto(fila.materia && fila.materia.nombre) },
          { titulo: "Estado", valor: (fila) => C.insigniaAsistencia(fila.estado) },
        ],
        filas: listaAsistencias,
        caption: "Últimos registros de asistencia",
        vacio: "Todavía no hay registros de asistencia",
        detalleVacio: "Cuando se cargue tu asistencia, aparecerá acá.",
      }) +
      "</div>" +
      accesosDirectos([
        { texto: "Mi asistencia", ruta: "#/mi-asistencia" },
        { texto: "Mi regularidad", ruta: "#/mi-regularidad" },
        { texto: "Mi horario", ruta: "#/mi-horario" },
      ]);
  }

  async function panelAdministrativo(zona, hoy, esDocentePropio) {
    const consultas = [
      resultadoSeguro(API.get("/alertas", { activa: true, leida: false })),
      resultadoSeguro(API.get("/periodos-academicos")),
      resultadoSeguro(API.get("/cursos")),
    ];
    let docenteId = null;
    if (esDocentePropio) {
      docenteId = await resolverDocenteId();
    }
    if (docenteId) {
      consultas.push(
        resultadoSeguro(API.get("/grillas-horarias", { docente_id: docenteId, dia_semana: hoy.diaSemana })),
        resultadoSeguro(
          API.get("/asistencias-docentes/firmas", {
            docente_id: docenteId,
            fecha_desde: hoy.fecha,
            fecha_hasta: hoy.fecha,
          })
        )
      );
    }

    const [alertas, periodos, cursos, grilla, firmas] = await Promise.all(consultas);
    const tarjetas = [];
    if (alertas.ok) {
      tarjetas.push(
        indicador(
          "Alertas sin leer",
          C.numero((alertas.valor.datos || []).length, 0),
          '<a href="#/alertas">Revisar alertas</a>',
          "destacado"
        )
      );
    } else {
      tarjetas.push(indicador("Alertas sin leer", "—", C.esc(alertas.error.message)));
    }
    if (periodos.ok) {
      const vigente = (periodos.valor.datos || []).find(
        (periodo) => periodo.fecha_inicio <= hoy.fecha && hoy.fecha <= periodo.fecha_fin
      );
      tarjetas.push(
        indicador(
          "Período vigente",
          vigente ? C.esc(vigente.nombre) : "Ninguno",
          vigente ? C.fecha(vigente.fecha_inicio) + " — " + C.fecha(vigente.fecha_fin) : "Sin período activo",
          vigente ? "" : "deficit"
        )
      );
    }
    if (cursos.ok) {
      tarjetas.push(indicador("Cursos", C.numero((cursos.valor.datos || []).length, 0)));
    }

    let bloqueClases = "";
    if (docenteId) {
      if (grilla.ok && firmas.ok) {
        const bloques = grilla.valor.datos || [];
        const registros = firmas.valor.datos || [];
        const firmasPorGrilla = {};
        registros.forEach((firma) => {
          const id = firma.grilla_horaria && typeof firma.grilla_horaria === "object"
            ? firma.grilla_horaria.id
            : firma.grilla_horaria;
          firmasPorGrilla[id] = firmasPorGrilla[id] || [];
          firmasPorGrilla[id].push(firma.tipo_firma);
        });
        const completas = bloques.filter((bloque) => {
          const tipos = firmasPorGrilla[bloque.id] || [];
          return tipos.indexOf("Ingreso") !== -1 && tipos.indexOf("Egreso") !== -1;
        }).length;
        tarjetas.push(
          indicador("Clases de hoy", C.numero(bloques.length, 0)),
          indicador("Firmas completas", C.numero(completas, 0), "de " + bloques.length + " bloques")
        );
        bloqueClases =
          '<div class="tarjeta"><div class="tarjeta-titulo"><h2>Mis clases de hoy</h2><a href="#/firmas">Firmar asistencia</a></div>' +
          (bloques.length
            ? C.tabla({
                columnas: [
                  { titulo: "Hora", valor: (b) => C.esc(b.hora_inicio + " – " + b.hora_fin) },
                  { titulo: "Curso", valor: (b) => C.texto(b.curso && b.curso.nombre_completo) },
                  { titulo: "Materia", valor: (b) => C.texto(b.materia && b.materia.nombre) },
                  {
                    titulo: "Firmas",
                    valor: (b) => {
                      const tipos = firmasPorGrilla[b.id] || [];
                      const ingreso = tipos.indexOf("Ingreso") !== -1;
                      const egreso = tipos.indexOf("Egreso") !== -1;
                      return ingreso && egreso
                        ? C.insignia("Completo", "ok")
                        : C.insignia(ingreso ? "Falta egreso" : "Sin ingreso", "alerta");
                    },
                  },
                ],
                filas: bloques,
                caption: "Clases de hoy",
                vacio: "No hay clases programadas para hoy",
              })
            : '<p class="texto-suave">No hay bloques en tu grilla para hoy.</p>') +
          "</div>";
      } else {
        bloqueClases =
          '<div class="tarjeta"><p class="texto-suave">No se pudieron cargar las clases de hoy.</p></div>';
      }
    }

    const enlaces =
      esDocentePropio
        ? [
            { texto: "Cargar asistencia", ruta: "#/cargar-asistencia" },
            { texto: "Mis firmas", ruta: "#/firmas" },
            { texto: "Mi balance de horas", ruta: "#/balance" },
            { texto: "Mi horario", ruta: "#/mi-horario" },
          ]
        : [
            { texto: "Cargar asistencia", ruta: "#/cargar-asistencia" },
            { texto: "Resumen y regularidad", ruta: "#/resumen" },
            { texto: "Alertas", ruta: "#/alertas" },
            { texto: puedeGestionarInscripciones() ? "Reportes" : "Grilla horaria", ruta: puedeGestionarInscripciones() ? "#/reportes" : "#/grilla" },
          ];

    zona.innerHTML =
      '<div class="grilla-tarjetas">' +
      tarjetas.join("") +
      "</div>" +
      bloqueClases +
      accesosDirectos(enlaces);
  }

  async function renderPanel(contenedor) {
    const hoy = C.hoyServidor();
    contenedor.innerHTML = marco(
      "Panel",
      "Hoy es " + C.esc(hoy.nombreDia.toLowerCase()) + " " + C.fecha(hoy.fecha) + ".",
      '<div id="panel-zona">' + C.esqueleto() + "</div>"
    );
    const zona = contenedor.querySelector("#panel-zona");
    try {
      await C.cargarSalud();
    } catch (error) {
      /* el panel funciona aunque el endpoint de salud falle */
    }
    const diaActual = C.hoyServidor();
    if (esAlumno()) {
      await panelAlumno(zona, diaActual);
    } else {
      await panelAdministrativo(zona, diaActual, esDocente());
    }
  }

  /* ------------------------------------------------------------------ Perfil */

  async function renderPerfil(contenedor) {
    contenedor.innerHTML = marco("Mi perfil", "Identidad y rol con los que opera la sesión.", C.esqueleto());
    try {
      const perfil = (await API.get("/autenticacion/perfil")).datos;
      API.SESION.guardarPerfil(perfil);
      contenedor.innerHTML = marco(
        "Mi perfil",
        "Vista de sólo lectura: la edición de datos personales no está disponible.",
        '<div class="tarjeta"><dl class="definicion">' +
          "<dt>Nombre de usuario</dt><dd>" + C.texto(perfil.nombre_usuario) + "</dd>" +
          "<dt>Correo electrónico</dt><dd>" + C.texto(perfil.correo_electronico) + "</dd>" +
          "<dt>Rol</dt><dd>" + C.insignia(perfil.rol, "info") + "</dd>" +
          "<dt>Estado de la cuenta</dt><dd>" + C.insigniaBooleano(perfil.activo, "Activa", "Inactiva") + "</dd>" +
          "<dt>Creada en</dt><dd>" + C.fechaHora(perfil.creado_en) + "</dd>" +
          "</dl></div>",
        '<button type="button" class="boton peligro" id="cerrar-sesion-perfil">Cerrar sesión</button>'
      );
      const boton = contenedor.querySelector("#cerrar-sesion-perfil");
      if (boton) {
        boton.addEventListener("click", () => {
          document.dispatchEvent(new CustomEvent("cerrar-sesion"));
        });
      }
    } catch (error) {
      contenedor.innerHTML = marco(
        "Mi perfil",
        "",
        '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>"
      );
    }
  }

  /* ---------------------------------------------------------------- Mi horario */

  function vistaSemana(bloques) {
    if (!bloques.length) {
      return C.estadoVacio(
        "No hay bloques horarios para mostrar",
        esAlumno()
          ? "No se pudo determinar tu curso o no tiene horario cargado."
          : "No hay bloques asignados."
      );
    }
    const porDia = {};
    bloques.forEach((bloque) => {
      const dia = Number(bloque.dia_semana);
      porDia[dia] = porDia[dia] || [];
      porDia[dia].push(bloque);
    });
    const dias = Object.keys(porDia)
      .map(Number)
      .sort((a, b) => a - b);
    return (
      '<div class="semana">' +
      dias
        .map((dia) => {
          const clases = porDia[dia].sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio));
          return (
            '<div class="dia-horario"><h3>' +
            C.esc(C.nombreDia(dia)) +
            "</h3><ul>" +
            clases
              .map(
                (clase) =>
                  "<li><strong>" +
                  C.esc(clase.hora_inicio + " – " + clase.hora_fin + " · " + (clase.materia ? clase.materia.nombre : "Materia")) +
                  "</strong><span>" +
                  C.esc(
                    [
                      clase.curso && clase.curso.nombre_completo,
                      clase.aula,
                      !esDocente() && clase.docente ? clase.docente.nombre_completo : "",
                    ]
                      .filter(Boolean)
                      .join(" · ")
                  ) +
                  "</span></li>"
              )
              .join("") +
            "</ul></div>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  async function renderMiHorario(contenedor) {
    contenedor.innerHTML = marco("Mi horario", "Bloques semanales que te corresponden.", C.esqueleto());
    try {
      let parametros = {};
      let detalle = "";
      if (esDocente()) {
        const docenteId = await resolverDocenteId();
        if (!docenteId) {
          contenedor.innerHTML = marco(
            "Mi horario",
            "",
            '<div class="tarjeta">' +
              C.estadoVacio(
                "No se pudo identificar tu legajo docente",
                "Consultá con administración si tu cuenta está vinculada a un docente."
              ) +
              "</div>"
          );
          return;
        }
        parametros = { docente_id: docenteId };
      } else if (esAlumno()) {
        const curso = await resolverCursoAlumno();
        if (!curso) {
          contenedor.innerHTML = marco(
            "Mi horario",
            "",
            '<div class="tarjeta">' +
              C.estadoVacio(
                "Todavía no se pudo determinar tu curso",
                "Cuando tengas registros de asistencia o matrícula activa, se mostrará tu horario."
              ) +
              "</div>"
          );
          return;
        }
        parametros = { curso_id: curso.id };
        detalle = "Curso: " + C.esc(curso.nombre_completo);
      }
      const bloques = (await API.get("/grillas-horarias", parametros)).datos || [];
      contenedor.innerHTML = marco("Mi horario", detalle || "Bloques semanales que te corresponden.", vistaSemana(bloques));
    } catch (error) {
      contenedor.innerHTML = marco(
        "Mi horario",
        "",
        '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>"
      );
    }
  }

  Paginas.util = {
    rol,
    esAdmin,
    esPreceptor,
    esDocente,
    esAlumno,
    puedeGestionarInscripciones,
    marco,
    indicador,
    tarjetasResumen,
    resultadoSeguro,
    catalogs,
    paginaListado,
    resolverDocenteId,
    resolverCursoAlumno,
    vistaSemana,
  };

  Paginas.panel = renderPanel;
  Paginas.perfil = renderPerfil;
  Paginas["mi-horario"] = renderMiHorario;
})();
