/* ==========================================================================
   Páginas de operación diaria: asistencias, resumen, alertas, reportes y
   configuración institucional.
   ========================================================================== */

(function () {
  "use strict";

  const C = Componentes;
  const U = Paginas.util;
  const ESTADOS_ASISTENCIA = ["Presente", "Ausente", "Justificado", "Tarde"];

  function opcionesCursos(cursos) {
    return C.opcionesSelect(cursos, { texto: (curso) => curso.nombre_completo || curso.nombre });
  }

  function opcionesMaterias(materias) {
    return C.opcionesSelect(materias, {
      texto: (materia) => (materia.codigo ? materia.codigo + " · " : "") + materia.nombre,
    });
  }

  function opcionesEstudiantes(estudiantes) {
    return C.opcionesSelect(estudiantes, {
      texto: (estudiante) => estudiante.nombre_completo + (estudiante.legajo ? " (" + estudiante.legajo + ")" : ""),
    });
  }

  function opcionesPeriodos(periodos) {
    return C.opcionesSelect(periodos, {
      texto: (periodo) => periodo.nombre + " (" + periodo.anio_lectivo + ")",
    });
  }

  /* ------------------------------------------------------ Consulta de asistencias */

  async function renderAsistencias(contenedor) {
    const alumno = U.esAlumno();
    const catalogos = await U.catalogs(
      alumno ? ["cursos", "materias"] : ["cursos", "materias", "estudiantes"]
    );
    const filtros = [];
    if (!alumno) {
      filtros.push({
        nombre: "estudiante_id",
        etiqueta: "Estudiante",
        tipo: "select",
        vacio: "Todos los estudiantes",
        opcionesHtml: opcionesEstudiantes(catalogos.estudiantes),
      });
    }
    filtros.push(
      { nombre: "curso_id", etiqueta: "Curso", tipo: "select", vacio: "Todos los cursos", opcionesHtml: opcionesCursos(catalogos.cursos) },
      { nombre: "materia_id", etiqueta: "Materia", tipo: "select", vacio: "Todas las materias", opcionesHtml: opcionesMaterias(catalogos.materias) },
      { nombre: "fecha", etiqueta: "Fecha exacta", tipo: "date" },
      { nombre: "fecha_desde", etiqueta: "Desde", tipo: "date" },
      { nombre: "fecha_hasta", etiqueta: "Hasta", tipo: "date" }
    );

    await U.paginaListado(contenedor, {
      titulo: alumno ? "Mi asistencia" : "Consulta de asistencias",
      descripcion: alumno
        ? "Registros propios de asistencia. El servidor limita la consulta a tu identidad."
        : "Consulta histórica de asistencia por estudiante, curso, materia y fechas.",
      nota: alumno
        ? "No podés consultar registros de otros estudiantes."
        : "Para corregir un registro, volvé a Cargar asistencia: la operación actualiza el registro existente.",
      filtros: filtros,
      botonesExtra: U.esAlumno()
        ? ""
        : '<a class="boton" href="#/cargar-asistencia">Cargar asistencia</a>',
      cargar: (parametros) => {
        if (
          parametros.fecha_desde &&
          parametros.fecha_hasta &&
          parametros.fecha_desde > parametros.fecha_hasta
        ) {
          throw new Error("La fecha desde no puede ser posterior a la fecha hasta.");
        }
        return API.get("/asistencias-estudiantes", parametros).then((r) => r.datos || []);
      },
      columnas: [
        { titulo: "Fecha", valor: (fila) => C.fecha(fila.fecha) },
        { titulo: "Estudiante", valor: (fila) => (fila.estudiante ? C.texto(fila.estudiante.legajo) + " · " + C.texto(fila.estudiante.nombre_completo) : "—") },
        { titulo: "Curso", valor: (fila) => C.texto(fila.curso && fila.curso.nombre_completo) },
        { titulo: "Materia", valor: (fila) => (fila.materia ? C.texto((fila.materia.codigo ? fila.materia.codigo + " · " : "") + fila.materia.nombre) : "—") },
        { titulo: "Estado", valor: (fila) => C.insigniaAsistencia(fila.estado) },
        { titulo: "Observación", valor: (fila) => C.texto(fila.observacion) },
        { titulo: "Registrado por", valor: (fila) => C.numero(fila.registrado_por_usuario_id, 0), clase: "numerico" },
      ],
      vacio: "No hay registros de asistencia para los filtros seleccionados",
      detalleVacio: alumno ? "Todavía no tenés registros de asistencia." : "Probá ampliar el rango de fechas.",
    });
  }

  /* ----------------------------------------------------- Carga de asistencia */

  async function renderCargaAsistencia(contenedor) {
    const hoy = C.hoyServidor();
    const catalogos = await U.catalogs(["cursos", "materias"]);
    const docente = U.esDocente();
    let docenteId = null;
    let asignaciones = [];
    let avisoDocente = "";

    if (docente) {
      docenteId = await U.resolverDocenteId();
      if (!docenteId) {
        avisoDocente =
          "No se pudo identificar tu legajo docente. Consultá con administración para vincular tu cuenta.";
      } else {
        try {
          asignaciones = (await API.get("/asignaciones-docentes", { docente_id: docenteId })).datos || [];
        } catch (error) {
          avisoDocente = "No se pudieron cargar tus asignaciones: " + C.mensajeDetallado(error);
        }
        if (!asignaciones.length) {
          avisoDocente = "No tenés materias asignadas todavía. No podés cargar asistencia.";
        }
      }
    }

    contenedor.innerHTML = U.marco(
      "Cargar asistencia",
      "Registrá o actualizá la asistencia de una clase completa.",
      '<div class="tarjeta"><form id="form-carga" class="filtros">' +
        '<div class="campo"><label for="carga-curso">Curso</label><select id="carga-curso" name="curso_id" required><option value="">Seleccioná un curso</option>' +
        opcionesCursos(catalogos.cursos) +
        "</select></div>" +
        '<div class="campo"><label for="carga-materia">Materia</label><select id="carga-materia" name="materia_id" required><option value="">Seleccioná una materia</option>' +
        opcionesMaterias(docente ? [] : catalogos.materias) +
        "</select></div>" +
        '<div class="campo"><label for="carga-fecha">Fecha</label><input id="carga-fecha" name="fecha" type="date" required max="' +
        hoy.fecha +
        '" value="' +
        hoy.fecha +
        '" /></div>' +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Cargar padrón</button></div>' +
        "</form>" +
        '<p class="nota" style="margin-top: 12px">La operación es idempotente: si ya existe un registro para la misma fecha, curso, materia y estudiante, se actualiza. Guardar puede generar alertas automáticas.</p>' +
        (avisoDocente ? '<div class="error-formulario" style="margin-top: 12px">' + C.esc(avisoDocente) + "</div>" : "") +
        '</div><div id="zona-padron"></div>'
    );

    const formulario = contenedor.querySelector("#form-carga");
    const selectCurso = contenedor.querySelector("#carga-curso");
    const selectMateria = contenedor.querySelector("#carga-materia");
    const zona = contenedor.querySelector("#zona-padron");

    function materiasPermitidas() {
      if (!docente) {
        return catalogos.materias;
      }
      const cursoId = Number(selectCurso.value);
      const ids = new Set(
        asignaciones
          .filter((asignacion) => asignacion.curso && Number(asignacion.curso.id) === cursoId)
          .map((asignacion) => asignacion.materia && asignacion.materia.id)
      );
      return catalogos.materias.filter((materia) => ids.has(materia.id));
    }

    function refrescarMaterias() {
      const disponibles = materiasPermitidas();
      selectMateria.innerHTML =
        '<option value="">' +
        (disponibles.length ? "Seleccioná una materia" : "Sin materias disponibles para el curso") +
        "</option>" + opcionesMaterias(disponibles);
    }

    selectCurso.addEventListener("change", refrescarMaterias);

    function contarEstados() {
      const conteos = {};
      ESTADOS_ASISTENCIA.forEach((estado) => (conteos[estado] = 0));
      zona.querySelectorAll("input[type=radio]:checked").forEach((radio) => {
        if (conteos[radio.value] !== undefined) {
          conteos[radio.value] += 1;
        }
      });
      const resumen = zona.querySelector("#resumen-en-vivo");
      if (resumen) {
        resumen.innerHTML = ESTADOS_ASISTENCIA.map(
          (estado) => "<span>" + C.esc(estado) + ": " + conteos[estado] + "</span>"
        ).join("");
      }
    }

    async function cargarPadron() {
      const cursoId = selectCurso.value;
      const materiaId = selectMateria.value;
      const fecha = contenedor.querySelector("#carga-fecha").value;
      if (!cursoId || !materiaId || !fecha) {
        C.avisar("advertencia", "Seleccioná curso, materia y fecha.");
        return;
      }
      if (fecha > C.hoyServidor().fecha) {
        C.avisar("advertencia", "La fecha de la clase no puede ser futura.");
        return;
      }
      if (docente) {
        const habilitada = asignaciones.some(
          (asignacion) =>
            Number(asignacion.curso && asignacion.curso.id) === Number(cursoId) &&
            Number(asignacion.materia && asignacion.materia.id) === Number(materiaId)
        );
        if (!habilitada) {
          C.avisar("error", "No tenés asignada esa materia en el curso seleccionado.");
          return;
        }
      }

      zona.innerHTML = C.esqueleto();
      try {
        const [inscripciones, existentes] = await Promise.all([
          API.get("/inscripciones", { curso_id: cursoId }).then((r) => r.datos || []),
          API.get("/asistencias-estudiantes", {
            curso_id: cursoId,
            materia_id: materiaId,
            fecha: fecha,
          }).then((r) => r.datos || []),
        ]);
        const activos = inscripciones.filter((inscripcion) => inscripcion.estado === "Activo");
        if (!activos.length) {
          zona.innerHTML =
            '<div class="tarjeta">' +
            C.estadoVacio(
              "No hay estudiantes con matrícula activa en este curso",
              "Registrá las inscripciones correspondientes antes de cargar asistencia."
            ) +
            "</div>";
          return;
        }
        const porEstudiante = {};
        existentes.forEach((registro) => {
          if (registro.estudiante) {
            porEstudiante[registro.estudiante.id] = registro;
          }
        });

        const filas = activos
          .map((inscripcion) => {
            const estudiante = inscripcion.estudiante;
            if (!estudiante) {
              return "";
            }
            const registro = porEstudiante[estudiante.id];
            const estadoActual = registro ? registro.estado : "Presente";
            const opciones = ESTADOS_ASISTENCIA.map((estado) => {
              const id = "estado-" + estudiante.id + "-" + estado.replace(/\s/g, "");
              return (
                '<label class="opcion-estado" for="' +
                id +
                '"><input id="' +
                id +
                '" type="radio" name="estado-' +
                estudiante.id +
                '" value="' +
                C.esc(estado) +
                '"' +
                (estado === estadoActual ? " checked" : "") +
                ' /><span>' +
                C.esc(estado) +
                "</span></label>"
              );
            }).join("");
            return (
              '<tr data-estudiante-id="' +
              estudiante.id +
              '"><td><strong>' +
              C.texto(estudiante.nombre_completo) +
              '</strong><br /><span class="texto-suave texto-chico">' +
              C.texto(estudiante.legajo) +
              "</span></td>" +
              '<td class="opciones">' +
              opciones +
              "</td>" +
              '<td><input class="observacion" type="text" maxlength="500" aria-label="Observación de ' +
              C.esc(estudiante.nombre_completo) +
              '" value="' +
              C.esc(registro && registro.observacion ? registro.observacion : "") +
              '" placeholder="Opcional" /></td></tr>'
            );
          })
          .join("");

        zona.innerHTML =
          '<div class="tarjeta mt-0" style="padding: 0">' +
          '<div class="barra-asistencia"><div class="acciones">' +
          '<button type="button" class="boton chico" id="marcar-presentes">Marcar todos presentes</button>' +
          '<button type="button" class="boton chico" id="restablecer">Restablecer</button>' +
          '<span class="texto-suave texto-chico">' +
          activos.length +
          " estudiantes activos" +
          (existentes.length ? " · " + existentes.length + " registros previos se actualizarán" : "") +
          '</span></div><div class="resumen-en-vivo" id="resumen-en-vivo" aria-live="polite"></div></div>' +
          '<div class="tabla-desplazable"><table class="tabla asistencia"><caption class="solo-lectores">Asistencia de la clase</caption>' +
          "<thead><tr><th scope=\"col\">Estudiante</th><th scope=\"col\">Estado</th><th scope=\"col\">Observación</th></tr></thead>" +
          "<tbody>" +
          filas +
          "</tbody></table></div>" +
          '<div class="guardar-fijo"><span class="texto-suave texto-chico">Los estados seleccionados se envían completos al guardar.</span>' +
          '<button type="button" class="boton primario" id="guardar-asistencia">Guardar asistencia</button></div>' +
          "</div>" +
          '<div id="resultado-guardado" aria-live="polite" style="margin-top: 14px"></div>';

        contarEstados();
        zona.querySelectorAll("input[type=radio]").forEach((radio) =>
          radio.addEventListener("change", contarEstados)
        );

        zona.querySelector("#marcar-presentes").addEventListener("click", () => {
          zona.querySelectorAll("tr[data-estudiante-id]").forEach((fila) => {
            const radio = fila.querySelector('input[type=radio][value="Presente"]');
            if (radio) {
              radio.checked = true;
            }
          });
          contarEstados();
        });

        zona.querySelector("#restablecer").addEventListener("click", () => {
          zona.querySelectorAll("tr[data-estudiante-id]").forEach((fila) => {
            const id = fila.getAttribute("data-estudiante-id");
            const registro = porEstudiante[id];
            const estado = registro ? registro.estado : "Presente";
            const radio = fila.querySelector('input[type=radio][value="' + estado + '"]');
            if (radio) {
              radio.checked = true;
            }
            const observacion = fila.querySelector(".observacion");
            if (observacion) {
              observacion.value = registro && registro.observacion ? registro.observacion : "";
            }
          });
          contarEstados();
        });

        zona.querySelector("#guardar-asistencia").addEventListener("click", async (evento) => {
          const boton = evento.currentTarget;
          const registros = [];
          let incompleto = false;
          zona.querySelectorAll("tr[data-estudiante-id]").forEach((fila) => {
            const estudianteId = Number(fila.getAttribute("data-estudiante-id"));
            const seleccionado = fila.querySelector("input[type=radio]:checked");
            if (!seleccionado) {
              incompleto = true;
              return;
            }
            const observacion = fila.querySelector(".observacion");
            registros.push({
              estudiante_id: estudianteId,
              estado: seleccionado.value,
              observacion: observacion && observacion.value ? observacion.value : null,
            });
          });
          if (incompleto) {
            C.avisar("advertencia", "Marcá un estado para todos los estudiantes.");
            return;
          }
          if (!registros.length) {
            C.avisar("advertencia", "No hay registros para guardar.");
            return;
          }
          boton.disabled = true;
          boton.textContent = "Guardando…";
          try {
            const respuesta = await API.post("/asistencias-estudiantes", {
              curso_id: Number(cursoId),
              materia_id: Number(materiaId),
              fecha: fecha,
              registros: registros,
            });
            const datos = respuesta.datos || {};
            C.avisar("exito", respuesta.mensaje || "Asistencia registrada correctamente.");
            const resultado = zona.querySelector("#resultado-guardado");
            if (resultado) {
              resultado.innerHTML =
                '<div class="tarjeta"><h2>Resultado del guardado</h2><p>Creados: <strong>' +
                C.numero(datos.creados, 0) +
                "</strong> · Actualizados: <strong>" +
                C.numero(datos.actualizados, 0) +
                "</strong></p><p class=\"texto-suave texto-chico\">La operación pudo generar alertas automáticas.</p></div>";
            }
          } catch (error) {
            C.avisar("error", C.mensajeDetallado(error));
          } finally {
            boton.disabled = false;
            boton.textContent = "Guardar asistencia";
          }
        });
      } catch (error) {
        zona.innerHTML =
          '<div class="tarjeta"><div class="error-formulario">' +
          C.esc(C.mensajeDetallado(error)) +
          "</div></div>";
      }
    }

    formulario.addEventListener("submit", (evento) => {
      evento.preventDefault();
      cargarPadron();
    });

    refrescarMaterias();
  }

  /* ------------------------------------------------------ Resumen y regularidad */

  async function renderResumen(contenedor) {
    const alumno = U.esAlumno();
    const catalogos = await U.catalogs(
      alumno ? ["cursos", "materias", "periodos"] : ["cursos", "materias", "estudiantes", "periodos"]
    );
    const puedeElegirEstrategia = U.esAdmin() || U.esPreceptor();
    let modo = "estudiante";

    const tabs = alumno
      ? ""
      : '<div class="fila" id="tabs-resumen" role="tablist" aria-label="Alcance del resumen">' +
        '<button type="button" class="boton primario" data-modo="estudiante" role="tab" aria-selected="true">Por estudiante</button>' +
        '<button type="button" class="boton" data-modo="curso" role="tab" aria-selected="false">Por curso</button>' +
        "</div>";

    contenedor.innerHTML = U.marco(
      "Resumen y regularidad",
      "Porcentajes, umbral y estado de regularidad calculados por el servidor.",
      tabs +
        '<div class="tarjeta"><form id="form-resumen" class="filtros">' +
        '<div class="campo' +
        (alumno ? " oculto" : "") +
        '" id="campo-estudiante"><label for="resumen-estudiante">Estudiante</label><select id="resumen-estudiante" name="estudiante_id"><option value="">Seleccioná un estudiante</option>' +
        opcionesEstudiantes(catalogos.estudiantes) +
        "</select></div>" +
        '<div class="campo oculto" id="campo-curso"><label for="resumen-curso">Curso</label><select id="resumen-curso" name="curso_id"><option value="">Seleccioná un curso</option>' +
        opcionesCursos(catalogos.cursos) +
        "</select></div>" +
        '<div class="campo"><label for="resumen-periodo">Período</label><select id="resumen-periodo" name="periodo_id"><option value="">Todos los registros</option>' +
        opcionesPeriodos(catalogos.periodos) +
        "</select></div>" +
        '<div class="campo"><label for="resumen-materia">Materia</label><select id="resumen-materia" name="materia_id"><option value="">Todas las materias</option>' +
        opcionesMaterias(catalogos.materias) +
        "</select></div>" +
        (puedeElegirEstrategia
          ? '<div class="campo"><label for="resumen-estrategia">Estrategia</label><select id="resumen-estrategia" name="estrategia"><option value="">Configurada</option><option value="institucional">Institucional</option><option value="estricta">Estricta</option></select></div>'
          : "") +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Consultar</button></div>' +
        "</form>" +
        '<p class="nota" style="margin-top: 12px">El umbral de regularidad proviene de la configuración institucional. El presentismo efectivo excluye los justificados en la estrategia institucional.</p></div>' +
        '<div id="zona-resumen"></div>'
    );

    const zona = contenedor.querySelector("#zona-resumen");
    const formulario = contenedor.querySelector("#form-resumen");

    function aplicarModo(nuevoModo) {
      modo = nuevoModo;
      const campEstudiante = contenedor.querySelector("#campo-estudiante");
      const campCurso = contenedor.querySelector("#campo-curso");
      if (campEstudiante) {
        campEstudiante.classList.toggle("oculto", alumno || modo !== "estudiante");
      }
      if (campCurso) {
        campCurso.classList.toggle("oculto", modo !== "curso");
      }
      contenedor.querySelectorAll("#tabs-resumen [data-modo]").forEach((boton) => {
        const activo = boton.getAttribute("data-modo") === modo;
        boton.classList.toggle("primario", activo);
        boton.setAttribute("aria-selected", activo ? "true" : "false");
      });
    }

    contenedor.querySelectorAll("#tabs-resumen [data-modo]").forEach((boton) => {
      boton.addEventListener("click", () => aplicarModo(boton.getAttribute("data-modo")));
    });
    aplicarModo(modo);

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const valores = C.leerFormulario(formulario);
      if (modo === "estudiante" && !alumno && !valores.estudiante_id) {
        C.avisar("advertencia", "Seleccioná un estudiante o cambiá a la vista por curso.");
        return;
      }
      if (modo === "curso" && !valores.curso_id) {
        C.avisar("advertencia", "Seleccioná un curso.");
        return;
      }
      const parametros = {};
      if (modo === "estudiante" && !alumno) {
        parametros.estudiante_id = valores.estudiante_id;
      }
      if (modo === "curso") {
        parametros.curso_id = valores.curso_id;
      }
      if (valores.periodo_id) {
        parametros.periodo_id = valores.periodo_id;
      }
      if (valores.materia_id) {
        parametros.materia_id = valores.materia_id;
      }
      if (valores.estrategia) {
        parametros.estrategia = valores.estrategia;
      }

      zona.innerHTML = C.esqueleto();
      try {
        const datos = (await API.get("/asistencias-estudiantes/resumen", parametros)).datos;
        const contexto =
          '<p class="nota">Período: <strong>' +
          C.esc(datos.periodo ? datos.periodo.nombre : "Todos los registros") +
          "</strong> · Estrategia: <strong>" +
          C.esc(datos.estrategia) +
          "</strong></p>";

        if (datos.alcance === "estudiante") {
          const detalle = (datos.detalle_por_materia || []).map((fila) => ({
            materia: fila.materia,
            resumen: fila.resumen,
          }));
          zona.innerHTML =
            '<div class="tarjeta"><div class="tarjeta-titulo"><h2>' +
            C.esc(datos.estudiante ? datos.estudiante.nombre_completo : "Estudiante") +
            "</h2>" +
            C.insigniaRegularidad(datos.resumen.estado_regularidad) +
            "</div>" +
            contexto +
            "</div>" +
            U.tarjetasResumen(datos.resumen) +
            '<div class="tarjeta"><h2>Detalle por materia</h2>' +
            C.tabla({
              columnas: [
                { titulo: "Materia", valor: (fila) => (fila.materia ? C.texto((fila.materia.codigo ? fila.materia.codigo + " · " : "") + fila.materia.nombre) : "—") },
                { titulo: "Registros", valor: (fila) => C.numero(fila.resumen.total_registros, 0), clase: "numerico" },
                { titulo: "Presentes", valor: (fila) => C.numero(fila.resumen.presentes, 0), clase: "numerico" },
                { titulo: "Ausentes", valor: (fila) => C.numero(fila.resumen.ausentes, 0), clase: "numerico" },
                { titulo: "Justificados", valor: (fila) => C.numero(fila.resumen.justificados, 0), clase: "numerico" },
                { titulo: "Tardes", valor: (fila) => C.numero(fila.resumen.tardes, 0), clase: "numerico" },
                { titulo: "Asistencia", valor: (fila) => C.porcentaje(fila.resumen.porcentaje_asistencia), clase: "numerico" },
                { titulo: "Regularidad", valor: (fila) => C.insigniaRegularidad(fila.resumen.estado_regularidad) },
              ],
              filas: detalle,
              caption: "Detalle por materia",
              vacio: "Sin detalle por materia",
            }) +
            "</div>";
        } else {
          const estudiantes = (datos.estudiantes || []).slice().sort((a, b) => {
            const orden = { "En riesgo": 0, Regular: 1, "Sin datos": 2 };
            const diferencia =
              (orden[a.resumen.estado_regularidad] || 3) - (orden[b.resumen.estado_regularidad] || 3);
            if (diferencia !== 0) {
              return diferencia;
            }
            return (a.estudiante ? a.estudiante.nombre_completo : "").localeCompare(
              b.estudiante ? b.estudiante.nombre_completo : ""
            );
          });
          zona.innerHTML =
            '<div class="tarjeta"><div class="tarjeta-titulo"><h2>' +
            C.esc(datos.curso ? datos.curso.nombre_completo : "Curso") +
            "</h2>" +
            C.insigniaRegularidad(datos.resumen_general.estado_regularidad) +
            "</div>" +
            contexto +
            "</div>" +
            '<h2 class="mt-0">Resumen general</h2>' +
            U.tarjetasResumen(datos.resumen_general) +
            '<div class="tarjeta"><h2>Estudiantes</h2>' +
            C.tabla({
              columnas: [
                { titulo: "Legajo", valor: (fila) => C.texto(fila.estudiante && fila.estudiante.legajo) },
                { titulo: "Estudiante", valor: (fila) => C.texto(fila.estudiante && fila.estudiante.nombre_completo) },
                { titulo: "Registros", valor: (fila) => C.numero(fila.resumen.total_registros, 0), clase: "numerico" },
                { titulo: "Presentes", valor: (fila) => C.numero(fila.resumen.presentes, 0), clase: "numerico" },
                { titulo: "Ausentes", valor: (fila) => C.numero(fila.resumen.ausentes, 0), clase: "numerico" },
                { titulo: "Asistencia", valor: (fila) => C.porcentaje(fila.resumen.porcentaje_asistencia), clase: "numerico" },
                { titulo: "Presentismo", valor: (fila) => C.porcentaje(fila.resumen.porcentaje_presentismo_efectivo), clase: "numerico" },
                { titulo: "Regularidad", valor: (fila) => C.insigniaRegularidad(fila.resumen.estado_regularidad) },
              ],
              filas: estudiantes,
              caption: "Resumen por estudiante",
              vacio: "El curso no tiene estudiantes con registros",
            }) +
            "</div>";
        }
      } catch (error) {
        zona.innerHTML = '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>";
      }
    });

    if (alumno) {
      formulario.requestSubmit();
    }
  }

  /* ------------------------------------------------------------------- Alertas */

  async function renderAlertas(contenedor) {
    const catalogos = await U.catalogs(["estudiantes"]);
    await U.paginaListado(contenedor, {
      titulo: "Alertas",
      descripcion: "Alertas generadas automáticamente por inasistencias y riesgo de regularidad.",
      nota: "Las alertas las genera el backend: no se crean, editan ni eliminan desde la interfaz.",
      filtros: [
        { nombre: "estudiante_id", etiqueta: "Estudiante", tipo: "select", vacio: "Todos los estudiantes", opcionesHtml: opcionesEstudiantes(catalogos.estudiantes) },
        { nombre: "activa", etiqueta: "Activa", tipo: "select", vacio: "Todas", opcionesHtml: C.opcionesDeLista(["true", "false"], { etiquetasOpciones: { true: "Activas", false: "Inactivas" } }) },
        { nombre: "leida", etiqueta: "Lectura", tipo: "select", vacio: "Todas", opcionesHtml: C.opcionesDeLista(["true", "false"], { etiquetasOpciones: { true: "Leídas", false: "No leídas" } }) },
      ],
      cargar: (parametros) =>
        API.get("/alertas", parametros).then((r) =>
          (r.datos || []).slice().sort((a, b) => {
            if (a.fecha_generacion !== b.fecha_generacion) {
              return String(b.fecha_generacion).localeCompare(String(a.fecha_generacion));
            }
            return String(a.nivel).localeCompare(String(b.nivel));
          })
        ),
      claseFila: (fila) => (!fila.leida ? "no-leida" : ""),
      columnas: [
        { titulo: "Generada", valor: (fila) => C.fechaHora(fila.fecha_generacion) },
        { titulo: "Estudiante", valor: (fila) => (fila.estudiante ? C.texto(fila.estudiante.nombre_completo) + "<br /><span class=\"texto-suave texto-chico\">" + C.texto(fila.estudiante.legajo) + "</span>" : "—") },
        { titulo: "Tipo", valor: (fila) => C.texto(fila.tipo) },
        { titulo: "Nivel", valor: (fila) => C.insigniaNivel(fila.nivel) },
        { titulo: "Mensaje", valor: (fila) => C.texto(fila.mensaje) },
        { titulo: "Asistencia", valor: (fila) => C.porcentaje(fila.porcentaje_asistencia), clase: "numerico" },
        {
          titulo: "Estado",
          valor: (fila) =>
            C.insigniaBooleano(fila.activa, "Activa", "Inactiva") +
            " " +
            C.insignia(fila.leida ? "Leída" : "No leída", fila.leida ? "neutra" : "alerta"),
        },
      ],
      acciones: (fila, contexto) =>
        fila.leida
          ? []
          : [
              {
                texto: "Marcar como leída",
                ejecutar: async () => {
                  try {
                    await API.patch("/alertas/" + fila.id + "/marcar-leida");
                    C.avisar("exito", "Alerta marcada como leída.");
                    contexto.recargar();
                  } catch (error) {
                    C.avisar("error", C.mensajeDetallado(error));
                  }
                },
              },
            ],
      vacio: "No hay alertas para los filtros seleccionados",
      detalleVacio: "Cuando el backend detecte inasistencias relevantes, aparecerán acá.",
    });
  }

  /* ------------------------------------------------------------------ Reportes */

  async function renderReportes(contenedor) {
    const catalogos = await U.catalogs(["cursos", "periodos"]);
    contenedor.innerHTML = U.marco(
      "Reportes",
      "Descargas formales en PDF y Excel. El archivo se genera en el servidor.",
      '<div class="tarjeta"><h2>Asistencia de estudiantes</h2><form id="reporte-asistencia" class="filtros">' +
        '<div class="campo"><label for="rep-curso">Curso<span class="obligatorio" aria-hidden="true">*</span></label><select id="rep-curso" name="curso_id" required><option value="">Seleccioná un curso</option>' +
        opcionesCursos(catalogos.cursos) +
        "</select></div>" +
        '<div class="campo"><label for="rep-periodo">Período<span class="obligatorio" aria-hidden="true">*</span></label><select id="rep-periodo" name="periodo_id" required><option value="">Seleccioná un período</option>' +
        opcionesPeriodos(catalogos.periodos) +
        "</select></div>" +
        '<div class="campo"><label for="rep-estrategia">Estrategia</label><select id="rep-estrategia" name="estrategia"><option value="">Configurada</option><option value="institucional">Institucional</option><option value="estricta">Estricta</option></select></div>' +
        '<div class="acciones-filtros"><button type="button" class="boton primario" data-formato="pdf">Descargar PDF</button><button type="button" class="boton" data-formato="xlsx">Descargar Excel</button></div>' +
        "</form></div>" +
        '<div class="tarjeta"><h2>Horas docentes</h2><form id="reporte-horas" class="filtros">' +
        '<div class="campo"><label for="hor-periodo">Período<span class="obligatorio" aria-hidden="true">*</span></label><select id="hor-periodo" name="periodo_id" required><option value="">Seleccioná un período</option>' +
        opcionesPeriodos(catalogos.periodos) +
        "</select></div>" +
        '<div class="campo"><label for="hor-estrategia">Estrategia</label><select id="hor-estrategia" name="estrategia"><option value="">Configurada</option><option value="exacta">Exacta</option><option value="por_bloques">Por bloques</option></select></div>' +
        '<div class="acciones-filtros"><button type="button" class="boton primario" data-formato="pdf">Descargar PDF</button><button type="button" class="boton" data-formato="xlsx">Descargar Excel</button></div>' +
        "</form></div>" +
        '<p class="nota">No existe vista previa ni historial de reportes. Las descargas requieren sesión activa.</p>'
    );

    async function descargar(boton, ruta, parametros, nombreSugerido) {
      const textoOriginal = boton.textContent;
      boton.disabled = true;
      boton.textContent = "Generando…";
      try {
        const archivo = await API.descargar(ruta, parametros);
        C.descargarBlob(archivo.blob, archivo.nombre || nombreSugerido);
        C.avisar("exito", "Descarga iniciada: " + (archivo.nombre || nombreSugerido));
      } catch (error) {
        C.avisar("error", C.mensajeDetallado(error));
      } finally {
        boton.disabled = false;
        boton.textContent = textoOriginal;
      }
    }

    const formAsistencia = contenedor.querySelector("#reporte-asistencia");
    formAsistencia.querySelectorAll("[data-formato]").forEach((boton) => {
      boton.addEventListener("click", () => {
        const datos = C.leerFormulario(formAsistencia);
        if (!datos.curso_id || !datos.periodo_id) {
          C.avisar("advertencia", "Seleccioná curso y período para generar el reporte.");
          return;
        }
        const formato = boton.getAttribute("data-formato");
        descargar(
          boton,
          "/reportes/asistencia-estudiantes." + formato,
          { curso_id: datos.curso_id, periodo_id: datos.periodo_id, estrategia: datos.estrategia || undefined },
          "reporte_asistencia_estudiantes_curso_" + datos.curso_id + "_periodo_" + datos.periodo_id + "." + formato
        );
      });
    });

    const formHoras = contenedor.querySelector("#reporte-horas");
    formHoras.querySelectorAll("[data-formato]").forEach((boton) => {
      boton.addEventListener("click", () => {
        const datos = C.leerFormulario(formHoras);
        if (!datos.periodo_id) {
          C.avisar("advertencia", "Seleccioná un período para generar el reporte.");
          return;
        }
        const formato = boton.getAttribute("data-formato");
        descargar(
          boton,
          "/reportes/horas-docentes." + formato,
          { periodo_id: datos.periodo_id, estrategia: datos.estrategia || undefined },
          "reporte_horas_docentes_periodo_" + datos.periodo_id + "." + formato
        );
      });
    });
  }

  /* ------------------------------------------------------------ Configuración */

  async function renderConfiguracion(contenedor) {
    contenedor.innerHTML = U.marco("Configuración institucional", "Parámetros que afectan cálculos y alertas.", C.esqueleto());
    try {
      const datos = (await API.get("/configuracion")).datos || {};
      const parametros = datos.parametros || [];
      const aplicados = datos.valores_aplicados || {};
      const grupos = [
        { titulo: "Reglas de asistencia", claves: ["umbral_regularidad_porcentaje", "estrategia_calculo_asistencia"] },
        { titulo: "Reglas de alertas", claves: ["limite_inasistencias_consecutivas"] },
        { titulo: "Reglas de horas docentes", claves: ["minutos_hora_catedra", "estrategia_calculo_horas", "tolerancia_minutos_firma"] },
      ];

      function control(clave, valor) {
        const id = "param-" + clave;
        if (clave === "estrategia_calculo_asistencia") {
          return '<select id="' + id + '" data-clave="' + C.esc(clave) + '">' +
            C.opcionesDeLista(["institucional", "estricta"], { seleccionado: valor }) + "</select>";
        }
        if (clave === "estrategia_calculo_horas") {
          return '<select id="' + id + '" data-clave="' + C.esc(clave) + '">' +
            C.opcionesDeLista(["exacta", "por_bloques"], { seleccionado: valor }) + "</select>";
        }
        const minimo = clave === "tolerancia_minutos_firma" ? 0 : 1;
        const maximo = clave === "umbral_regularidad_porcentaje" ? 100 : "";
        return '<input id="' + id + '" data-clave="' + C.esc(clave) + '" type="number" min="' + minimo + '"' +
          (maximo !== "" ? ' max="' + maximo + '"' : "") + ' step="1" value="' + C.esc(valor) + '" />';
      }

      const porClave = {};
      parametros.forEach((parametro) => (porClave[parametro.clave] = parametro));

      const bloques = grupos
        .map((grupo) => {
          const filas = grupo.claves
            .filter((clave) => porClave[clave])
            .map((clave) => {
              const parametro = porClave[clave];
              return (
                '<div class="campo"><label for="param-' +
                C.esc(clave) +
                '">' +
                C.esc(clave) +
                "</label>" +
                control(clave, aplicados[clave] !== undefined ? aplicados[clave] : parametro.valor) +
                (parametro.descripcion ? '<span class="ayuda">' + C.esc(parametro.descripcion) + "</span>" : "") +
                '<div><button type="button" class="boton chico" data-guardar="' + C.esc(clave) + '">Guardar</button></div>' +
                "</div>"
              );
            });
          return filas.length
            ? '<div class="tarjeta"><h2>' + C.esc(grupo.titulo) + '</h2><div class="form-grilla">' + filas.join("") + "</div></div>"
            : "";
        })
        .join("");

      contenedor.innerHTML = U.marco(
        "Configuración institucional",
        "Los cambios afectan cálculos futuros y pueden alterar la interpretación de datos existentes.",
        bloques +
          '<div class="tarjeta"><h2>Valores aplicados</h2><dl class="definicion">' +
          Object.entries(aplicados)
            .map(([clave, valor]) => "<dt>" + C.esc(clave) + "</dt><dd>" + C.texto(valor) + "</dd>")
            .join("") +
          "<dt>zona_horaria_institucional</dt><dd>" +
          C.texto(aplicados.zona_horaria_institucional || "America/Argentina/Buenos_Aires") +
          " (sólo lectura)</dd></dl></div>"
      );

      contenedor.querySelectorAll("[data-guardar]").forEach((boton) => {
        boton.addEventListener("click", async () => {
          const clave = boton.getAttribute("data-guardar");
          const campo = contenedor.querySelector('[data-clave="' + clave + '"]');
          if (!campo) {
            return;
          }
          const valor = String(campo.value).trim();
          if (!valor) {
            C.avisar("advertencia", "Ingresá un valor para " + clave + ".");
            return;
          }
          if (clave.indexOf("estrategia") === -1 && Number.isNaN(Number(valor))) {
            C.avisar("advertencia", "El valor de " + clave + " debe ser numérico.");
            return;
          }
          boton.disabled = true;
          boton.textContent = "Guardando…";
          try {
            const respuesta = await API.put("/configuracion/" + encodeURIComponent(clave), { valor: valor });
            C.avisar("exito", respuesta.mensaje || "Parámetro actualizado correctamente.");
            await renderConfiguracion(contenedor);
          } catch (error) {
            C.avisar("error", C.mensajeDetallado(error));
            boton.disabled = false;
            boton.textContent = "Guardar";
          }
        });
      });
    } catch (error) {
      contenedor.innerHTML = U.marco(
        "Configuración institucional",
        "",
        '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>"
      );
    }
  }

  Object.assign(Paginas, {
    asistencias: renderAsistencias,
    "mi-asistencia": renderAsistencias,
    "cargar-asistencia": renderCargaAsistencia,
    resumen: renderResumen,
    "mi-regularidad": renderResumen,
    alertas: renderAlertas,
    reportes: renderReportes,
    configuracion: renderConfiguracion,
  });
})();
