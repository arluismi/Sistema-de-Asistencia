/* ==========================================================================
   Páginas de asistencia y puntualidad docente: firmas, incidencias,
   licencias y balance de horas cátedra.
   ========================================================================== */

(function () {
  "use strict";

  const C = Componentes;
  const U = Paginas.util;
  const TIPOS_INCIDENCIA = ["Tardanza", "Salida anticipada", "Ausencia", "Licencia"];

  function opcionesDocentes(docentes) {
    return C.opcionesSelect(docentes, {
      texto: (docente) =>
        (docente.nombre_completo || "") + (docente.legajo ? " (" + docente.legajo + ")" : ""),
    });
  }

  function opcionesPeriodos(periodos) {
    return C.opcionesSelect(periodos, {
      texto: (periodo) => periodo.nombre + " (" + periodo.anio_lectivo + ")",
    });
  }

  function idDeGrilla(firma) {
    if (!firma) {
      return null;
    }
    return firma.grilla_horaria && typeof firma.grilla_horaria === "object"
      ? firma.grilla_horaria.id
      : firma.grilla_horaria;
  }

  function descripcionBloque(firma) {
    if (!firma) {
      return "—";
    }
    const grilla = firma.grilla_horaria;
    if (grilla && typeof grilla === "object") {
      return (
        C.nombreDia(grilla.dia_semana) +
        " " +
        (grilla.hora_inicio || "") +
        "–" +
        (grilla.hora_fin || "")
      );
    }
    return "Bloque " + grilla;
  }

  /* -------------------------------------------------------------------- Firmas */

  async function renderFirmas(contenedor) {
    const gestiona = U.esAdmin() || U.esPreceptor();
    const catalogos = gestiona ? await U.catalogs(["docentes"]) : { docentes: [] };
    const hoy = C.hoyServidor();
    let docenteId = U.esDocente() ? await U.resolverDocenteId() : null;

    contenedor.innerHTML = U.marco(
      "Firmas docentes",
      "Registrá ingreso y egreso de los bloques de hoy y consultá el historial.",
      '<div class="tarjeta"><div class="tarjeta-titulo"><h2>Bloques de hoy · ' +
        C.esc(hoy.nombreDia) +
        " " +
        C.fecha(hoy.fecha) +
        "</h2></div>" +
        (gestiona
          ? '<div class="campo" style="max-width: 360px"><label for="firmas-docente">Docente</label><select id="firmas-docente"><option value="">Seleccioná un docente</option>' +
            opcionesDocentes(catalogos.docentes) +
            "</select></div>"
          : "") +
        '<div id="bloques-hoy" style="margin-top: 14px"></div></div>' +
        '<div class="tarjeta"><div class="tarjeta-titulo"><h2>Historial de firmas</h2></div>' +
        '<form id="form-historial" class="filtros">' +
        (gestiona
          ? '<div class="campo"><label for="hist-docente">Docente</label><select id="hist-docente" name="docente_id"><option value="">Todos los docentes</option>' +
            opcionesDocentes(catalogos.docentes) +
            "</select></div>"
          : "") +
        '<div class="campo"><label for="hist-desde">Desde</label><input id="hist-desde" name="fecha_desde" type="date" /></div>' +
        '<div class="campo"><label for="hist-hasta">Hasta</label><input id="hist-hasta" name="fecha_hasta" type="date" /></div>' +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Filtrar</button><button type="reset" class="boton">Limpiar</button></div>' +
        "</form>" +
        '<div id="zona-historial" style="margin-top: 14px">' +
        C.esqueleto() +
        "</div></div>"
    );

    const zonaBloques = contenedor.querySelector("#bloques-hoy");
    const zonaHistorial = contenedor.querySelector("#zona-historial");
    const formHistorial = contenedor.querySelector("#form-historial");
    const selectorDocente = contenedor.querySelector("#firmas-docente");

    if (gestiona && selectorDocente) {
      selectorDocente.addEventListener("change", () => {
        docenteId = selectorDocente.value ? Number(selectorDocente.value) : null;
        cargarHoy();
      });
    }

    async function firmar(tipo, bloque) {
      const etiqueta = tipo === "Ingreso" ? "ingreso" : "egreso";
      if (
        !window.confirm(
          "¿Confirmás la firma de " + etiqueta + " para " + (bloque.materia ? bloque.materia.nombre : "el bloque") + "?"
        )
      ) {
        return;
      }
      const cuerpo = { tipo_firma: tipo, grilla_horaria_id: bloque.id };
      if (gestiona) {
        cuerpo.docente_id = docenteId;
      }
      try {
        const respuesta = await API.post("/asistencias-docentes/firmas", cuerpo);
        C.avisar("exito", respuesta.mensaje || "Firma registrada correctamente.");
        const incidencia = respuesta.datos && respuesta.datos.incidencia;
        if (incidencia) {
          C.dialogoInformacion(
            "Incidencia registrada",
            '<dl class="definicion">' +
              "<dt>Tipo</dt><dd>" + C.insignia(incidencia.tipo, "alerta") + "</dd>" +
              "<dt>Minutos de desviación</dt><dd>" + C.minutos(incidencia.minutos_desviacion) + "</dd>" +
              "<dt>Descripción</dt><dd>" + C.texto(incidencia.descripcion) + "</dd>" +
              "</dl>"
          );
        }
      } catch (error) {
        C.avisar("error", C.mensajeDetallado(error));
      }
      cargarHoy();
      cargarHistorial();
    }

    async function cargarHoy() {
      if (!docenteId) {
        zonaBloques.innerHTML = C.estadoVacio(
          "Seleccioná un docente",
          "Elegí el docente para ver sus bloques y firmar."
        );
        return;
      }
      zonaBloques.innerHTML = C.esqueleto();
      try {
        const [grilla, firmas] = await Promise.all([
          API.get("/grillas-horarias", { docente_id: docenteId, dia_semana: hoy.diaSemana }),
          API.get("/asistencias-docentes/firmas", {
            docente_id: docenteId,
            fecha_desde: hoy.fecha,
            fecha_hasta: hoy.fecha,
          }),
        ]);
        const bloques = (grilla.datos || []).slice().sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio));
        const registros = firmas.datos || [];
        if (!bloques.length) {
          zonaBloques.innerHTML = C.estadoVacio(
            "No hay bloques para hoy",
            "El docente no tiene clases programadas para " + hoy.nombreDia.toLowerCase() + "."
          );
          return;
        }
        const porGrilla = {};
        registros.forEach((firma) => {
          const id = idDeGrilla(firma);
          porGrilla[id] = porGrilla[id] || [];
          porGrilla[id].push(firma);
        });

        zonaBloques.innerHTML =
          '<div class="tabla-contenedor"><div class="tabla-desplazable"><table class="tabla"><caption class="solo-lectores">Bloques de hoy</caption>' +
          '<thead><tr><th scope="col">Hora</th><th scope="col">Curso</th><th scope="col">Materia</th><th scope="col">Aula</th><th scope="col">Estado</th><th scope="col">Acción</th></tr></thead><tbody>' +
          bloques
            .map((bloque) => {
              const firmasBloque = porGrilla[bloque.id] || [];
              const ingreso = firmasBloque.find((firma) => firma.tipo_firma === "Ingreso");
              const egreso = firmasBloque.find((firma) => firma.tipo_firma === "Egreso");
              let estado;
              let accion = "";
              if (ingreso && egreso) {
                estado = C.insignia("Completo", "ok");
              } else if (ingreso) {
                estado = C.insignia("Falta egreso", "alerta");
                accion =
                  '<button type="button" class="boton chico primario" data-firmar="Egreso" data-bloque="' +
                  bloque.id +
                  '">Firmar egreso</button>';
              } else {
                estado = C.insignia("Sin ingreso", "neutra");
                accion =
                  '<button type="button" class="boton chico primario" data-firmar="Ingreso" data-bloque="' +
                  bloque.id +
                  '">Firmar ingreso</button>';
              }
              const detalleFirmas = [ingreso, egreso]
                .filter(Boolean)
                .map((firma) => C.esc(firma.tipo_firma) + " " + C.fechaHora(firma.marca_temporal))
                .join("<br />");
              return (
                "<tr><td>" +
                C.esc(bloque.hora_inicio + " – " + bloque.hora_fin) +
                "</td><td>" +
                C.texto(bloque.curso && bloque.curso.nombre_completo) +
                "</td><td>" +
                C.texto(bloque.materia && bloque.materia.nombre) +
                "</td><td>" +
                C.texto(bloque.aula) +
                "</td><td>" +
                estado +
                (detalleFirmas ? '<br /><span class="texto-suave texto-chico">' + detalleFirmas + "</span>" : "") +
                "</td><td>" +
                (accion || C.insignia("Sin acciones", "neutra")) +
                "</td></tr>"
              );
            })
            .join("") +
          "</tbody></table></div></div>";

        zonaBloques.querySelectorAll("[data-firmar]").forEach((boton) => {
          boton.addEventListener("click", async () => {
            const tipo = boton.getAttribute("data-firmar");
            const id = Number(boton.getAttribute("data-bloque"));
            const bloque = bloques.find((elemento) => elemento.id === id);
            if (!bloque) {
              return;
            }
            boton.disabled = true;
            boton.textContent = "Registrando…";
            await firmar(tipo, bloque);
            if (boton.isConnected) {
              boton.disabled = false;
              boton.textContent = tipo === "Ingreso" ? "Firmar ingreso" : "Firmar egreso";
            }
          });
        });
      } catch (error) {
        zonaBloques.innerHTML =
          '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>";
      }
    }

    async function cargarHistorial() {
      const valores = C.leerFormulario(formHistorial);
      const parametros = {};
      if (gestiona && valores.docente_id) {
        parametros.docente_id = valores.docente_id;
      }
      if (valores.fecha_desde) {
        parametros.fecha_desde = valores.fecha_desde;
      }
      if (valores.fecha_hasta) {
        parametros.fecha_hasta = valores.fecha_hasta;
      }
      zonaHistorial.innerHTML = C.esqueleto();
      try {
        const firmas = (await API.get("/asistencias-docentes/firmas", parametros)).datos || [];
        zonaHistorial.innerHTML = C.tabla({
          columnas: [
            { titulo: "Fecha", valor: (firma) => C.fecha(firma.fecha) },
            { titulo: "Docente", valor: (firma) => C.texto(firma.docente && firma.docente.nombre_completo) },
            { titulo: "Bloque", valor: (firma) => C.esc(descripcionBloque(firma)) },
            { titulo: "Tipo", valor: (firma) => C.insignia(firma.tipo_firma, firma.tipo_firma === "Ingreso" ? "info" : "ok") },
            { titulo: "Marca temporal", valor: (firma) => C.fechaHora(firma.marca_temporal) },
            { titulo: "Observación", valor: (firma) => C.texto(firma.observacion) },
          ],
          filas: firmas,
          caption: "Historial de firmas",
          vacio: "No hay firmas para los filtros seleccionados",
        });
      } catch (error) {
        zonaHistorial.innerHTML =
          '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>";
      }
    }

    formHistorial.addEventListener("submit", (evento) => {
      evento.preventDefault();
      cargarHistorial();
    });
    formHistorial.addEventListener("reset", () => window.setTimeout(cargarHistorial, 0));

    await cargarHoy();
    await cargarHistorial();
  }

  /* --------------------------------------------------------------- Incidencias */

  async function renderIncidencias(contenedor) {
    const gestiona = U.esAdmin() || U.esPreceptor();
    const catalogos = gestiona ? await U.catalogs(["docentes"]) : { docentes: [] };
    const filtros = [];
    if (gestiona) {
      filtros.push({
        nombre: "docente_id",
        etiqueta: "Docente",
        tipo: "select",
        vacio: "Todos los docentes",
        opcionesHtml: opcionesDocentes(catalogos.docentes),
      });
    }
    filtros.push(
      { nombre: "tipo", etiqueta: "Tipo", tipo: "select", vacio: "Todos los tipos", opcionesHtml: C.opcionesDeLista(TIPOS_INCIDENCIA) },
      { nombre: "fecha_desde", etiqueta: "Desde", tipo: "date" },
      { nombre: "fecha_hasta", etiqueta: "Hasta", tipo: "date" }
    );

    await U.paginaListado(contenedor, {
      titulo: "Incidencias docentes",
      descripcion: "Tardanzas, salidas anticipadas, ausencias y licencias registradas.",
      nota: "Vista de sólo lectura. Las incidencias automáticas las genera el servidor al firmar.",
      filtros: filtros,
      cargar: (parametros) => API.get("/asistencias-docentes/incidencias", parametros).then((r) => r.datos || []),
      columnas: [
        { titulo: "Fecha", valor: (fila) => C.fecha(fila.fecha) },
        { titulo: "Docente", valor: (fila) => C.texto(fila.docente && fila.docente.nombre_completo) },
        { titulo: "Tipo", valor: (fila) => C.insignia(fila.tipo, fila.tipo === "Licencia" ? "info" : "alerta") },
        { titulo: "Desviación", valor: (fila) => C.minutos(fila.minutos_desviacion), clase: "numerico" },
        { titulo: "Descripción", valor: (fila) => C.texto(fila.descripcion) },
        { titulo: "Automática", valor: (fila) => C.insigniaBooleano(fila.generada_automaticamente, "Sí", "No") },
        { titulo: "Registrada por", valor: (fila) => C.numero(fila.registrado_por_usuario_id, 0), clase: "numerico" },
        { titulo: "Bloque", valor: (fila) => C.numero(fila.grilla_horaria_id, 0), clase: "numerico" },
      ],
      vacio: "No hay incidencias para los filtros seleccionados",
      detalleVacio: "Probá ampliar el rango de fechas.",
    });
  }

  /* ----------------------------------------------------------------- Licencias */

  async function renderLicencias(contenedor) {
    const catalogos = await U.catalogs(["docentes"]);
    const hoy = C.hoyServidor();
    contenedor.innerHTML = U.marco(
      "Licencias docentes",
      "Registrá licencias y consultá las existentes.",
      '<div class="tarjeta"><h2>Nueva licencia</h2><form id="form-licencia" class="filtros">' +
        '<div class="campo"><label for="lic-docente">Docente<span class="obligatorio" aria-hidden="true">*</span></label><select id="lic-docente" name="docente_id" required><option value="">Seleccioná un docente</option>' +
        opcionesDocentes(catalogos.docentes) +
        "</select></div>" +
        '<div class="campo"><label for="lic-fecha">Fecha<span class="obligatorio" aria-hidden="true">*</span></label><input id="lic-fecha" name="fecha" type="date" required value="' + hoy.fecha + '" /></div>' +
        '<div class="campo"><label for="lic-bloque">Bloque (opcional)</label><select id="lic-bloque" name="grilla_horaria_id"><option value="">Sin bloque específico</option></select></div>' +
        '<div class="campo ancho-completo"><label for="lic-motivo">Motivo<span class="obligatorio" aria-hidden="true">*</span></label><textarea id="lic-motivo" name="motivo" maxlength="500" required></textarea><span class="ayuda" id="contador-motivo">0 / 500 caracteres</span></div>' +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Registrar licencia</button></div>' +
        "</form></div>" +
        '<div class="tarjeta"><div class="tarjeta-titulo"><h2>Licencias registradas</h2></div>' +
        '<form id="form-licencias-filtros" class="filtros">' +
        '<div class="campo"><label for="licf-docente">Docente</label><select id="licf-docente" name="docente_id"><option value="">Todos los docentes</option>' +
        opcionesDocentes(catalogos.docentes) +
        "</select></div>" +
        '<div class="campo"><label for="licf-desde">Desde</label><input id="licf-desde" name="fecha_desde" type="date" /></div>' +
        '<div class="campo"><label for="licf-hasta">Hasta</label><input id="licf-hasta" name="fecha_hasta" type="date" /></div>' +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Filtrar</button></div>' +
        "</form>" +
        '<div id="zona-licencias" style="margin-top: 14px">' +
        C.esqueleto() +
        "</div></div>"
    );

    const formulario = contenedor.querySelector("#form-licencia");
    const selectDocente = contenedor.querySelector("#lic-docente");
    const selectBloque = contenedor.querySelector("#lic-bloque");
    const motivo = contenedor.querySelector("#lic-motivo");
    const contador = contenedor.querySelector("#contador-motivo");
    const zona = contenedor.querySelector("#zona-licencias");
    const filtrosLista = contenedor.querySelector("#form-licencias-filtros");

    motivo.addEventListener("input", () => {
      contador.textContent = motivo.value.length + " / 500 caracteres";
    });

    async function cargarBloques() {
      selectBloque.innerHTML = '<option value="">Sin bloque específico</option>';
      if (!selectDocente.value) {
        return;
      }
      try {
        const bloques = (await API.get("/grillas-horarias", { docente_id: selectDocente.value })).datos || [];
        selectBloque.innerHTML += bloques
          .map(
            (bloque) =>
              '<option value="' +
              bloque.id +
              '">' +
              C.esc(
                C.nombreDia(bloque.dia_semana) +
                  " " +
                  bloque.hora_inicio +
                  "–" +
                  bloque.hora_fin +
                  " · " +
                  (bloque.materia ? bloque.materia.nombre : "") +
                  " · " +
                  (bloque.curso ? bloque.curso.nombre_completo : "")
              ) +
              "</option>"
          )
          .join("");
      } catch (error) {
        C.avisar("error", C.mensajeDetallado(error));
      }
    }

    selectDocente.addEventListener("change", cargarBloques);

    async function cargarLista() {
      const valores = C.leerFormulario(filtrosLista);
      const parametros = { tipo: "Licencia" };
      if (valores.docente_id) {
        parametros.docente_id = valores.docente_id;
      }
      if (valores.fecha_desde) {
        parametros.fecha_desde = valores.fecha_desde;
      }
      if (valores.fecha_hasta) {
        parametros.fecha_hasta = valores.fecha_hasta;
      }
      zona.innerHTML = C.esqueleto();
      try {
        const licencias = (await API.get("/asistencias-docentes/incidencias", parametros)).datos || [];
        zona.innerHTML = C.tabla({
          columnas: [
            { titulo: "Fecha", valor: (fila) => C.fecha(fila.fecha) },
            { titulo: "Docente", valor: (fila) => C.texto(fila.docente && fila.docente.nombre_completo) },
            { titulo: "Tipo", valor: (fila) => C.insignia(fila.tipo, "info") },
            { titulo: "Descripción", valor: (fila) => C.texto(fila.descripcion) },
            { titulo: "Bloque", valor: (fila) => C.numero(fila.grilla_horaria_id, 0), clase: "numerico" },
          ],
          filas: licencias,
          caption: "Licencias registradas",
          vacio: "No hay licencias para los filtros seleccionados",
        });
      } catch (error) {
        zona.innerHTML = '<div class="error-formulario">' + C.esc(C.mensajeDetallado(error)) + "</div>";
      }
    }

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const datos = C.leerFormulario(formulario);
      if (!datos.docente_id || !datos.fecha || !datos.motivo) {
        C.avisar("advertencia", "Docente, fecha y motivo son obligatorios.");
        return;
      }
      const boton = formulario.querySelector('[type="submit"]');
      boton.disabled = true;
      boton.textContent = "Registrando…";
      try {
        const cuerpo = {
          docente_id: Number(datos.docente_id),
          fecha: datos.fecha,
          motivo: datos.motivo,
        };
        if (datos.grilla_horaria_id) {
          cuerpo.grilla_horaria_id = Number(datos.grilla_horaria_id);
        }
        const respuesta = await API.post("/asistencias-docentes/licencias", cuerpo);
        C.avisar("exito", respuesta.mensaje || "Licencia registrada correctamente.");
        motivo.value = "";
        contador.textContent = "0 / 500 caracteres";
        selectBloque.innerHTML = '<option value="">Sin bloque específico</option>';
        cargarLista();
      } catch (error) {
        C.avisar("error", C.mensajeDetallado(error));
      } finally {
        boton.disabled = false;
        boton.textContent = "Registrar licencia";
      }
    });

    filtrosLista.addEventListener("submit", (evento) => {
      evento.preventDefault();
      cargarLista();
    });

    await cargarLista();
  }

  /* ------------------------------------------------------------ Balance de horas */

  async function renderBalance(contenedor) {
    const gestiona = U.esAdmin() || U.esPreceptor();
    const catalogos = await U.catalogs(gestiona ? ["docentes", "periodos"] : ["periodos"]);
    contenedor.innerHTML = U.marco(
      "Balance de horas cátedra",
      "Horas esperadas, laboradas, saldo y cumplimiento por período.",
      '<div class="tarjeta"><form id="form-balance" class="filtros">' +
        '<div class="campo"><label for="bal-periodo">Período</label><select id="bal-periodo" name="periodo_id"><option value="">Período vigente</option>' +
        opcionesPeriodos(catalogos.periodos) +
        "</select></div>" +
        (gestiona
          ? '<div class="campo"><label for="bal-docente">Docente</label><select id="bal-docente" name="docente_id"><option value="">Todos los docentes</option>' +
            opcionesDocentes(catalogos.docentes) +
            "</select></div>"
          : "") +
        '<div class="campo"><label for="bal-estrategia">Estrategia</label><select id="bal-estrategia" name="estrategia"><option value="">Configurada</option><option value="exacta">Exacta</option><option value="por_bloques">Por bloques</option></select></div>' +
        '<div class="acciones-filtros"><button type="submit" class="boton primario">Consultar</button></div>' +
        "</form></div>" +
        '<div id="zona-balance"></div>'
    );

    const formulario = contenedor.querySelector("#form-balance");
    const zona = contenedor.querySelector("#zona-balance");

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const valores = C.leerFormulario(formulario);
      const parametros = {};
      if (valores.periodo_id) {
        parametros.periodo_id = valores.periodo_id;
      }
      if (gestiona && valores.docente_id) {
        parametros.docente_id = valores.docente_id;
      }
      if (valores.estrategia) {
        parametros.estrategia = valores.estrategia;
      }
      zona.innerHTML = C.esqueleto();
      try {
        const datos = (await API.get("/asistencias-docentes/balance-horas", parametros)).datos;
        const balances = datos.balances || [];
        if (!balances.length) {
          zona.innerHTML = '<div class="tarjeta">' + C.estadoVacio("No hay clases en el período seleccionado") + "</div>";
          return;
        }
        zona.innerHTML =
          '<div class="tarjeta"><h2>Período aplicado</h2><p>' +
          C.esc(datos.periodo ? datos.periodo.nombre : "—") +
          (datos.periodo
            ? ' <span class="texto-suave">(' +
              C.fecha(datos.periodo.fecha_inicio) +
              " — " +
              C.fecha(datos.periodo.fecha_fin) +
              ")</span>"
            : "") +
          "</p></div>" +
          balances
            .map((elemento) => {
              const balance = elemento.balance;
              const clases = balance.detalle_clases || [];
              return (
                '<div class="tarjeta"><div class="tarjeta-titulo"><h2>' +
                C.esc(elemento.docente ? elemento.docente.nombre_completo : "Docente") +
                "</h2>" +
                C.insignia(balance.estrategia, "info") +
                "</div>" +
                '<div class="grilla-tarjetas">' +
                U.indicador("Clases esperadas", C.numero(balance.clases_esperadas, 0)) +
                U.indicador("Completas", C.numero(balance.clases_completas, 0)) +
                U.indicador("Incompletas", C.numero(balance.clases_incompletas, 0)) +
                U.indicador("Sin firma", C.numero(balance.clases_sin_firma, 0)) +
                U.indicador("Horas esperadas", C.horasCatedra(balance.horas_catedra_esperadas)) +
                U.indicador("Horas laboradas", C.horasCatedra(balance.horas_catedra_laboradas)) +
                U.indicador(
                  "Saldo",
                  C.horasCatedra(balance.saldo_horas_catedra),
                  balance.saldo_horas_catedra < 0 ? "Déficit" : "Excedente",
                  balance.saldo_horas_catedra < 0 ? "deficit" : "excedente"
                ) +
                U.indicador("Cumplimiento", C.porcentaje(balance.porcentaje_cumplimiento), "Hora cátedra: " + C.minutos(balance.minutos_hora_catedra), "destacado") +
                "</div>" +
                '<p class="nota" style="margin: 12px 0">Minutos esperados: ' +
                C.numero(balance.minutos_esperados, 0) +
                " · Minutos laborados: " +
                C.numero(balance.minutos_laborados, 0) +
                "</p>" +
                C.tabla({
                  columnas: [
                    { titulo: "Fecha", valor: (clase) => C.fecha(clase.fecha) },
                    { titulo: "Curso", valor: (clase) => C.texto(clase.curso) },
                    { titulo: "Materia", valor: (clase) => C.texto(clase.materia) },
                    { titulo: "Hora", valor: (clase) => C.esc(clase.hora_inicio + " – " + clase.hora_fin) },
                    { titulo: "Min. esperados", valor: (clase) => C.numero(clase.minutos_esperados, 0), clase: "numerico" },
                    { titulo: "Min. laborados", valor: (clase) => C.numero(clase.minutos_laborados, 0), clase: "numerico" },
                    { titulo: "Estado", valor: (clase) => C.insignia(clase.estado, clase.estado === "Completa" ? "ok" : clase.estado === "Incompleta" ? "alerta" : "neutra") },
                  ],
                  filas: clases,
                  caption: "Detalle de clases",
                  vacio: "Sin clases en el período",
                }) +
                "</div>"
              );
            })
            .join("");
      } catch (error) {
        zona.innerHTML =
          '<div class="tarjeta"><div class="error-formulario">' +
          C.esc(C.mensajeDetallado(error)) +
          "</div><p class=\"nota\" style=\"margin-top: 10px\">Si no hay período vigente, seleccioná un período explícitamente.</p></div>";
      }
    });

    formulario.requestSubmit();
  }

  Object.assign(Paginas, {
    firmas: renderFirmas,
    incidencias: renderIncidencias,
    licencias: renderLicencias,
    balance: renderBalance,
  });
})();
