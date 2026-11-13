/* ==========================================================================
   Componentes reutilizables: formato, tablas, formularios, avisos y diálogos.
   Todo el texto proveniente del servidor se escapa antes de insertarse.
   ========================================================================== */

const Componentes = (function () {
  "use strict";

  const NOMBRES_DIA = [
    "",
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
  ];

  let promesaSalud = null;
  let saludGuardada = null;

  function esc(valor) {
    return String(valor === null || valor === undefined ? "" : valor)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function texto(valor, defecto) {
    const reemplazo = defecto === undefined ? "—" : defecto;
    return valor === null || valor === undefined || valor === ""
      ? esc(reemplazo)
      : esc(valor);
  }

  function partesFecha(valor) {
    const coincidencia = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(valor || ""));
    if (!coincidencia) {
      return null;
    }
    return {
      anio: Number(coincidencia[1]),
      mes: Number(coincidencia[2]),
      dia: Number(coincidencia[3]),
    };
  }

  function fecha(valor) {
    const partes = partesFecha(valor);
    if (!partes) {
      return valor ? esc(valor) : "—";
    }
    const dos = (numero) => String(numero).padStart(2, "0");
    return dos(partes.dia) + "/" + dos(partes.mes) + "/" + partes.anio;
  }

  function fechaHora(valor) {
    const coincidencia = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(valor || ""));
    if (!coincidencia) {
      return fecha(valor);
    }
    return (
      coincidencia[3] +
      "/" +
      coincidencia[2] +
      "/" +
      coincidencia[1] +
      " " +
      coincidencia[4] +
      ":" +
      coincidencia[5]
    );
  }

  function numero(valor, decimales) {
    if (valor === null || valor === undefined || valor === "") {
      return "—";
    }
    const cantidad = Number(valor);
    if (Number.isNaN(cantidad)) {
      return esc(valor);
    }
    return cantidad.toLocaleString("es-AR", {
      minimumFractionDigits: decimales || 0,
      maximumFractionDigits: decimales === undefined ? 2 : decimales,
    });
  }

  function porcentaje(valor) {
    if (valor === null || valor === undefined) {
      return "—";
    }
    return numero(valor, 2) + " %";
  }

  function horasCatedra(valor) {
    if (valor === null || valor === undefined) {
      return "—";
    }
    return numero(valor, 2) + " h";
  }

  function minutos(valor) {
    if (valor === null || valor === undefined) {
      return "—";
    }
    return numero(valor, 0) + " min";
  }

  function insignia(etiqueta, tipo) {
    return (
      '<span class="insignia ' + (tipo || "neutra") + '">' + esc(etiqueta) + "</span>"
    );
  }

  function insigniaBooleano(valor, etiquetaVerdadera, etiquetaFalsa) {
    return valor
      ? insignia(etiquetaVerdadera || "Sí", "ok")
      : insignia(etiquetaFalsa || "No", "neutra");
  }

  function insigniaRegularidad(estado) {
    if (estado === "Regular") {
      return insignia("Regular", "ok");
    }
    if (estado === "En riesgo") {
      return insignia("En riesgo", "error");
    }
    return insignia(estado || "Sin datos", "neutra");
  }

  function insigniaNivel(nivel) {
    return insignia(nivel || "—", nivel === "Alta" ? "error" : "alerta");
  }

  function insigniaAsistencia(estado) {
    const mapa = {
      Presente: "ok",
      Ausente: "error",
      Justificado: "alerta",
      Tarde: "info",
    };
    return insignia(estado || "—", mapa[estado] || "neutra");
  }

  function opcionesSelect(elementos, configuracion) {
    const ajustes = configuracion || {};
    const valorDe = ajustes.valor || ((elemento) => elemento.id);
    const textoDe = ajustes.texto || ((elemento) => elemento.nombre_completo || elemento.nombre);
    let html = "";
    if (ajustes.vacio !== undefined) {
      html +=
        '<option value="">' + esc(ajustes.vacio) + "</option>";
    }
    (elementos || []).forEach((elemento) => {
      const valor = valorDe(elemento);
      const seleccionado = String(valor) === String(ajustes.seleccionado) ? " selected" : "";
      html +=
        '<option value="' +
        esc(valor) +
        '"' +
        seleccionado +
        ">" +
        esc(textoDe(elemento)) +
        "</option>";
    });
    return html;
  }

  function opcionesDeLista(valores, configuracion) {
    const ajustes = configuracion || {};
    return valores
      .map((valor) => {
        const etiqueta = ajustes.etiquetas && ajustes.etiquetas[valor] ? ajustes.etiquetas[valor] : valor;
        const seleccionado = String(valor) === String(ajustes.seleccionado) ? " selected" : "";
        return '<option value="' + esc(valor) + '"' + seleccionado + ">" + esc(etiqueta) + "</option>";
      })
      .join("");
  }

  function campoFormulario(campo) {
    const id = "campo-" + campo.nombre;
    const requerido = campo.requerido ? ' required aria-required="true"' : "";
    const marcaObligatorio = campo.requerido
      ? '<span class="obligatorio" aria-hidden="true">*</span><span class="solo-lectores"> (obligatorio)</span>'
      : "";
    const ayuda = campo.ayuda ? '<span class="ayuda">' + esc(campo.ayuda) + "</span>" : "";
    let control = "";

    if (campo.tipo === "select") {
      const opciones = campo.opcionesHtml !== undefined
        ? campo.opcionesHtml
        : opcionesDeLista(campo.opciones || [], {
            seleccionado: campo.valor,
            etiquetas: campo.etiquetasOpciones,
          });
      const vacio =
        campo.vacio !== undefined ? '<option value="">' + esc(campo.vacio) + "</option>" : "";
      control =
        '<select id="' +
        id +
        '" name="' +
        esc(campo.nombre) +
        '"' +
        requerido +
        ">" +
        vacio +
        opciones +
        "</select>";
    } else if (campo.tipo === "textarea") {
      control =
        '<textarea id="' +
        id +
        '" name="' +
        esc(campo.nombre) +
        '"' +
        requerido +
        (campo.maxLongitud ? ' maxlength="' + Number(campo.maxLongitud) + '"' : "") +
        ">" +
        esc(campo.valor || "") +
        "</textarea>";
    } else {
      control =
        '<input id="' +
        id +
        '" name="' +
        esc(campo.nombre) +
        '" type="' +
        esc(campo.tipo || "text") +
        '"' +
        (campo.valor !== undefined && campo.valor !== null
          ? ' value="' + esc(campo.valor) + '"'
          : "") +
        (campo.maxLongitud ? ' maxlength="' + Number(campo.maxLongitud) + '"' : "") +
        (campo.min !== undefined ? ' min="' + esc(campo.min) + '"' : "") +
        (campo.max !== undefined ? ' max="' + esc(campo.max) + '"' : "") +
        (campo.paso !== undefined ? ' step="' + esc(campo.paso) + '"' : "") +
        (campo.placeholder ? ' placeholder="' + esc(campo.placeholder) + '"' : "") +
        requerido +
        " />";
    }

    return (
      '<div class="campo' +
      (campo.anchoCompleto ? " ancho-completo" : "") +
      '"><label for="' +
      id +
      '">' +
      esc(campo.etiqueta) +
      marcaObligatorio +
      "</label>" +
      control +
      ayuda +
      "</div>"
    );
  }

  function formulario(campos, configuracion) {
    const ajustes = configuracion || {};
    return (
      '<form id="' +
      esc(ajustes.id || "formulario") +
      '" class="pila"' +
      (ajustes.validacionNativa === false ? " novalidate" : "") +
      '><div class="error-formulario" role="alert"></div><div class="form-grilla">' +
      campos.map(campoFormulario).join("") +
      "</div>" +
      (ajustes.acciones
        ? '<div class="form-acciones">' + ajustes.acciones + "</div>"
        : "") +
      "</form>"
    );
  }

  function camposDeFiltro(campos) {
    return campos
      .map((campo) => {
        const id = "filtro-" + campo.nombre;
        const ayuda = campo.ayuda ? '<span class="ayuda">' + esc(campo.ayuda) + "</span>" : "";
        let control;
        if (campo.tipo === "select") {
          control =
            '<select id="' +
            id +
            '" name="' +
            esc(campo.nombre) +
            '">' +
            (campo.vacio !== undefined
              ? '<option value="">' + esc(campo.vacio) + "</option>"
              : "") +
            (campo.opcionesHtml !== undefined
              ? campo.opcionesHtml
              : opcionesDeLista(campo.opciones || [], {
                  seleccionado: campo.valor,
                  etiquetas: campo.etiquetasOpciones,
                })) +
            "</select>";
        } else {
          control =
            '<input id="' +
            id +
            '" name="' +
            esc(campo.nombre) +
            '" type="' +
            esc(campo.tipo || "text") +
            '"' +
            (campo.placeholder ? ' placeholder="' + esc(campo.placeholder) + '"' : "") +
            (campo.max !== undefined ? ' max="' + esc(campo.max) + '"' : "") +
            (campo.min !== undefined ? ' min="' + esc(campo.min) + '"' : "") +
            (campo.valor !== undefined && campo.valor !== null
              ? ' value="' + esc(campo.valor) + '"'
              : "") +
            " />";
        }
        return (
          '<div class="campo"><label for="' +
          id +
          '">' +
          esc(campo.etiqueta) +
          "</label>" +
          control +
          ayuda +
          "</div>"
        );
      })
      .join("");
  }

  function estadoVacio(mensaje, detalle) {
    return (
      '<div class="estado-vacio"><strong>' +
      esc(mensaje || "Sin resultados") +
      "</strong>" +
      (detalle ? "<span>" + esc(detalle) + "</span>" : "") +
      "</div>"
    );
  }

  function tabla(configuracion) {
    const ajustes = configuracion || {};
    const filas = ajustes.filas || [];
    if (!filas.length) {
      return estadoVacio(ajustes.vacio || "Sin resultados", ajustes.detalleVacio);
    }
    const columnas = ajustes.columnas || [];
    const encabezados = columnas
      .map(
        (columna) =>
          '<th scope="col"' +
          (columna.clase ? ' class="' + esc(columna.clase) + '"' : "") +
          ">" +
          esc(columna.titulo) +
          "</th>"
      )
      .join("");
    const cuerpo = filas
      .map((fila, indice) => {
        const claseFila = ajustes.claseFila ? ajustes.claseFila(fila) : "";
        const celdas = columnas
          .map(
            (columna) =>
              '<td' +
              (columna.clase ? ' class="' + esc(columna.clase) + '"' : "") +
              ">" +
              (columna.valor ? columna.valor(fila, indice) : "") +
              "</td>"
          )
          .join("");
        return '<tr' + (claseFila ? ' class="' + esc(claseFila) + '"' : "") + ">" + celdas + "</tr>";
      })
      .join("");
    return (
      '<div class="tabla-contenedor"><div class="tabla-desplazable"><table class="tabla' +
      (ajustes.clase ? " " + esc(ajustes.clase) : "") +
      '"><caption class="solo-lectores">' +
      esc(ajustes.caption || ajustes.titulo || "Resultados") +
      '</caption><thead><tr>' +
      encabezados +
      "</tr></thead><tbody>" +
      cuerpo +
      "</tbody></table></div></div>"
    );
  }

  function conectarAcciones(contenedor, filas, obtenerAcciones) {
    if (!contenedor || !obtenerAcciones) {
      return;
    }
    contenedor.querySelectorAll("[data-accion]").forEach((boton) => {
      boton.addEventListener("click", () => {
        const indiceFila = Number(boton.getAttribute("data-fila"));
        const indiceAccion = Number(boton.getAttribute("data-accion"));
        const acciones = obtenerAcciones(filas[indiceFila], indiceFila);
        if (acciones && acciones[indiceAccion] && acciones[indiceAccion].ejecutar) {
          acciones[indiceAccion].ejecutar();
        }
      });
    });
  }

  function botonesDeAcciones(acciones) {
    return (
      '<div class="acciones-fila">' +
      acciones
        .map(
          (accion, indice) =>
            '<button type="button" class="boton chico ' +
            (accion.clase || "sutil") +
            '" data-accion="' +
            indice +
            '">' +
            esc(accion.texto) +
            "</button>"
        )
        .join("") +
      "</div>"
    );
  }

  function avisar(tipo, mensaje, duracion) {
    const contenedor = document.getElementById("avisos");
    if (!contenedor) {
      return;
    }
    const aviso = document.createElement("div");
    aviso.className = "aviso " + (tipo || "info");
    aviso.textContent = mensaje;
    aviso.title = "Clic para cerrar";
    aviso.addEventListener("click", () => aviso.remove());
    contenedor.appendChild(aviso);
    window.setTimeout(() => aviso.remove(), duracion || 5000);
  }

  function esqueleto() {
    return '<div class="esqueleto" aria-busy="true"><span></span><span></span><span></span></div>';
  }

  function mensajeDetallado(error) {
    let mensaje = (error && error.message) || "Ocurrió un error inesperado.";
    if (error && error.detalles) {
      let detalles = error.detalles;
      if (Array.isArray(detalles)) {
        detalles = detalles.join(" ");
      } else if (typeof detalles === "object") {
        detalles = Object.entries(detalles)
          .map(([clave, valor]) => clave + ": " + valor)
          .join(" ");
      }
      if (detalles) {
        mensaje += " " + detalles;
      }
    }
    return mensaje;
  }

  function leerFormulario(formularioElemento) {
    const datos = {};
    const formData = new FormData(formularioElemento);
    formData.forEach((valor, clave) => {
      datos[clave] = typeof valor === "string" ? valor.trim() : valor;
    });
    return datos;
  }

  function partesDelServidor() {
    return saludGuardada ? saludGuardada.marca_temporal_servidor : null;
  }

  async function cargarSalud(forzar) {
    if (!promesaSalud || forzar) {
      promesaSalud = API.get("/salud")
        .then((respuesta) => {
          saludGuardada = respuesta.datos;
          return saludGuardada;
        })
        .catch((error) => {
          promesaSalud = null;
          throw error;
        });
    }
    return promesaSalud;
  }

  function hoyServidor() {
    const marca = partesDelServidor();
    const partes = marca
      ? partesFecha(marca)
      : (function () {
          const ahora = new Date();
          return {
            anio: ahora.getFullYear(),
            mes: ahora.getMonth() + 1,
            dia: ahora.getDate(),
          };
        })();
    const dos = (valor) => String(valor).padStart(2, "0");
    const valorFecha = partes.anio + "-" + dos(partes.mes) + "-" + dos(partes.dia);
    const objetoFecha = new Date(partes.anio, partes.mes - 1, partes.dia);
    const diaSemana = objetoFecha.getDay() === 0 ? 7 : objetoFecha.getDay();
    return { fecha: valorFecha, diaSemana: diaSemana, nombreDia: NOMBRES_DIA[diaSemana] };
  }

  function nombreDia(numeroDia) {
    return NOMBRES_DIA[Number(numeroDia)] || "—";
  }

  function descargarBlob(blob, nombre) {
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombre || "reporte";
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 2000);
  }

  function abrirDialogo(configuracion) {
    const dialogo = document.createElement("dialog");
    dialogo.className = "dialogo";
    dialogo.innerHTML =
      '<div class="dialogo-encabezado"><div><h2>' +
      esc(configuracion.titulo) +
      "</h2>" +
      (configuracion.descripcion
        ? '<p class="texto-suave texto-chico">' + esc(configuracion.descripcion) + "</p>"
        : "") +
      '</div><button type="button" class="cerrar-dialogo" aria-label="Cerrar">✕</button></div>' +
      '<div class="dialogo-cuerpo">' +
      configuracion.contenido +
      "</div>" +
      (configuracion.pie ? '<div class="dialogo-pie">' + configuracion.pie + "</div>" : "");
    document.body.appendChild(dialogo);
    dialogo.querySelector(".cerrar-dialogo").addEventListener("click", () => dialogo.close());
    dialogo.addEventListener("close", () => dialogo.remove());
    dialogo.showModal();
    return dialogo;
  }

  function dialogoFormulario(configuracion) {
    return new Promise((resolver) => {
      let resuelto = false;
      const camposHtml = (configuracion.campos || []).map(campoFormulario).join("");
      const dialogo = abrirDialogo({
        titulo: configuracion.titulo,
        descripcion: configuracion.descripcion,
        contenido:
          '<form id="formulario-dialogo" class="pila"><div class="error-formulario" role="alert"></div>' +
          (configuracion.contenidoExtra || "") +
          '<div class="form-grilla">' +
          camposHtml +
          "</div></form>",
        pie:
          '<button type="button" class="boton" data-cancelar>Cancelar</button>' +
          '<button type="submit" form="formulario-dialogo" class="boton primario">' +
          esc(configuracion.textoBoton || "Guardar") +
          "</button>",
      });

      const formularioElemento = dialogo.querySelector("form");
      const cajaError = dialogo.querySelector(".error-formulario");
      const botonEnviar = dialogo.querySelector('[type="submit"]');

      function finalizar(valor) {
        if (resuelto) {
          return;
        }
        resuelto = true;
        if (dialogo.open) {
          dialogo.close();
        }
        resolver(valor);
      }

      dialogo.querySelector("[data-cancelar]").addEventListener("click", () => finalizar(null));
      dialogo.addEventListener("close", () => finalizar(null));

      formularioElemento.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        cajaError.textContent = "";
        botonEnviar.disabled = true;
        const textoOriginal = botonEnviar.textContent;
        botonEnviar.textContent = "Guardando…";
        try {
          const datos = leerFormulario(formularioElemento);
          const resultado = await configuracion.enviar(datos);
          finalizar(resultado === undefined ? datos : resultado);
        } catch (error) {
          cajaError.textContent = mensajeDetallado(error);
          botonEnviar.disabled = false;
          botonEnviar.textContent = textoOriginal;
        }
      });
    });
  }

  function dialogoInformacion(titulo, contenido) {
    const dialogo = abrirDialogo({
      titulo: titulo,
      contenido: contenido,
      pie: '<button type="button" class="boton primario" data-cerrar>Entendido</button>',
    });
    dialogo.querySelector("[data-cerrar]").addEventListener("click", () => dialogo.close());
    return dialogo;
  }

  return {
    esc,
    texto,
    fecha,
    fechaHora,
    numero,
    porcentaje,
    horasCatedra,
    minutos,
    insignia,
    insigniaBooleano,
    insigniaRegularidad,
    insigniaNivel,
    insigniaAsistencia,
    nombreDia,
    opcionesSelect,
    opcionesDeLista,
    campoFormulario,
    formulario,
    camposDeFiltro,
    estadoVacio,
    tabla,
    conectarAcciones,
    botonesDeAcciones,
    avisar,
    esqueleto,
    mensajeDetallado,
    leerFormulario,
    cargarSalud,
    hoyServidor,
    descargarBlob,
    abrirDialogo,
    dialogoFormulario,
    dialogoInformacion,
    NOMBRES_DIA,
  };
})();
