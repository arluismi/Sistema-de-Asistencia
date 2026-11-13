/* ==========================================================================
   Cliente HTTP y almacenamiento de sesión.
   La API es la única fuente de datos: aquí no se calculan reglas de negocio.
   ========================================================================== */

const API = (function () {
  "use strict";

  // Si la aplicación se sirve desde el mismo puerto del backend (5000) se usa
  // una ruta relativa; en caso contrario se apunta al backend en el mismo host
  // desde el que se abrió la página (localhost o una IP de la red local), para
  // que también funcione desde otros dispositivos.
  const NOMBRE_HOST = window.location.hostname || "localhost";
  const ORIGEN_API =
    window.location.port === "5000" ? "" : "http://" + NOMBRE_HOST + ":5000";
  const URL_BASE = ORIGEN_API + "/api/v1";

  const CLAVES = {
    token: "asistencia.token",
    usuario: "asistencia.usuario",
    perfil: "asistencia.perfil",
    docenteId: "asistencia.docenteId",
    cursoAlumno: "asistencia.cursoAlumno",
  };

  function leerJson(clave) {
    try {
      const valor = window.sessionStorage.getItem(clave);
      return valor ? JSON.parse(valor) : null;
    } catch (error) {
      return null;
    }
  }

  function guardarJson(clave, valor) {
    if (valor === null || valor === undefined) {
      window.sessionStorage.removeItem(clave);
    } else {
      window.sessionStorage.setItem(clave, JSON.stringify(valor));
    }
  }

  const SESION = {
    iniciar(datosDeSesion) {
      window.sessionStorage.setItem(CLAVES.token, datosDeSesion.token_acceso);
      guardarJson(CLAVES.usuario, datosDeSesion.usuario || null);
    },
    token() {
      return window.sessionStorage.getItem(CLAVES.token) || "";
    },
    haySesion() {
      return Boolean(this.token());
    },
    usuario() {
      return leerJson(CLAVES.usuario);
    },
    perfil() {
      return leerJson(CLAVES.perfil);
    },
    guardarPerfil(perfil) {
      guardarJson(CLAVES.perfil, perfil);
      if (perfil) {
        guardarJson(CLAVES.usuario, perfil);
      }
    },
    rol() {
      const perfil = this.perfil() || this.usuario();
      return perfil ? perfil.rol : "";
    },
    docenteId() {
      return leerJson(CLAVES.docenteId);
    },
    guardarDocenteId(identificador) {
      guardarJson(CLAVES.docenteId, identificador);
    },
    cursoAlumno() {
      return leerJson(CLAVES.cursoAlumno);
    },
    guardarCursoAlumno(curso) {
      guardarJson(CLAVES.cursoAlumno, curso);
    },
    limpiar() {
      Object.values(CLAVES).forEach((clave) => window.sessionStorage.removeItem(clave));
    },
  };

  class ErrorAPI extends Error {
    constructor(mensaje, codigo, detalles, estado) {
      super(mensaje);
      this.name = "ErrorAPI";
      this.codigo = codigo || "error_desconocido";
      this.detalles = detalles;
      this.estado = estado || 0;
    }
  }

  function construirUrl(ruta, parametros) {
    const url = new URL(URL_BASE + ruta, window.location.href);
    if (parametros) {
      Object.entries(parametros).forEach(([clave, valor]) => {
        if (valor !== null && valor !== undefined && String(valor).trim() !== "") {
          url.searchParams.set(clave, String(valor).trim());
        }
      });
    }
    return url.toString();
  }

  function mensajeDeError(cuerpo, respuesta) {
    if (cuerpo && cuerpo.error) {
      return new ErrorAPI(
        cuerpo.error.mensaje || "Ocurrió un error al procesar la solicitud.",
        cuerpo.error.codigo,
        cuerpo.error.detalles,
        respuesta.status
      );
    }
    return new ErrorAPI(
      respuesta.status === 401
        ? "La sesión venció. Volvé a iniciar sesión."
        : "No se pudo completar la operación (HTTP " + respuesta.status + ").",
      respuesta.status === 401 ? "no_autenticado" : "error_http",
      null,
      respuesta.status
    );
  }

  async function solicitar(ruta, opciones) {
    const configuracion = opciones || {};
    const encabezados = { Accept: "application/json" };
    const token = SESION.token();
    if (token) {
      encabezados.Authorization = "Bearer " + token;
    }
    if (configuracion.cuerpo !== undefined && configuracion.cuerpo !== null) {
      encabezados["Content-Type"] = "application/json";
    }

    let respuesta;
    try {
      respuesta = await fetch(construirUrl(ruta, configuracion.parametros), {
        method: configuracion.metodo || "GET",
        headers: encabezados,
        body:
          configuracion.cuerpo !== undefined && configuracion.cuerpo !== null
            ? JSON.stringify(configuracion.cuerpo)
            : undefined,
      });
    } catch (error) {
      throw new ErrorAPI(
        "No se pudo conectar con el servidor. Verificá que el backend esté en ejecución.",
        "error_de_red",
        null,
        0
      );
    }

    const tipoContenido = respuesta.headers.get("content-type") || "";
    let cuerpo = null;
    if (tipoContenido.indexOf("application/json") !== -1) {
      cuerpo = await respuesta.json().catch(() => null);
    }

    if (respuesta.status === 401) {
      const habiaToken = Boolean(token);
      SESION.limpiar();
      if (habiaToken) {
        document.dispatchEvent(new CustomEvent("sesion-expirada"));
      }
      throw mensajeDeError(cuerpo, respuesta);
    }

    if (!respuesta.ok) {
      throw mensajeDeError(cuerpo, respuesta);
    }

    return cuerpo || { datos: null };
  }

  async function descargar(ruta, parametros) {
    const encabezados = { Accept: "*/*" };
    const token = SESION.token();
    if (token) {
      encabezados.Authorization = "Bearer " + token;
    }

    let respuesta;
    try {
      respuesta = await fetch(construirUrl(ruta, parametros), { headers: encabezados });
    } catch (error) {
      throw new ErrorAPI(
        "No se pudo conectar con el servidor para generar el reporte.",
        "error_de_red",
        null,
        0
      );
    }

    if (respuesta.status === 401) {
      const habiaToken = Boolean(token);
      SESION.limpiar();
      if (habiaToken) {
        document.dispatchEvent(new CustomEvent("sesion-expirada"));
      }
    }

    const tipoContenido = respuesta.headers.get("content-type") || "";
    if (!respuesta.ok || tipoContenido.indexOf("application/json") !== -1) {
      const cuerpo = tipoContenido.indexOf("application/json") !== -1
        ? await respuesta.json().catch(() => null)
        : null;
      throw mensajeDeError(cuerpo, respuesta);
    }

    const disposicion = respuesta.headers.get("content-disposition") || "";
    const coincidencia = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposicion);
    return {
      blob: await respuesta.blob(),
      nombre: coincidencia ? decodeURIComponent(coincidencia[1]) : null,
    };
  }

  return {
    URL_BASE,
    SESION,
    ErrorAPI,
    solicitar,
    descargar,
    get(ruta, parametros) {
      return solicitar(ruta, { parametros });
    },
    post(ruta, cuerpo) {
      return solicitar(ruta, { metodo: "POST", cuerpo });
    },
    put(ruta, cuerpo) {
      return solicitar(ruta, { metodo: "PUT", cuerpo });
    },
    patch(ruta, cuerpo) {
      return solicitar(ruta, { metodo: "PATCH", cuerpo: cuerpo || null });
    },
  };
})();
