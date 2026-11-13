/* ==========================================================================
   Arranque de la aplicación: sesión, navegación por rol y enrutador por hash.
   ========================================================================== */

(function () {
  "use strict";

  const C = Componentes;
  const U = Paginas.util;

  const PAGINAS_INFO = {
    panel: { titulo: "Panel", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    perfil: { titulo: "Mi perfil", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    usuarios: { titulo: "Usuarios", roles: ["Admin/Directivo"] },
    estudiantes: { titulo: "Estudiantes", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    docentes: { titulo: "Docentes", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    cursos: { titulo: "Cursos", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    materias: { titulo: "Materias", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    periodos: { titulo: "Períodos académicos", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    inscripciones: { titulo: "Inscripciones", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    asignaciones: { titulo: "Asignaciones docentes", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    grilla: { titulo: "Grilla horaria", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    "cargar-asistencia": { titulo: "Cargar asistencia", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    asistencias: { titulo: "Consulta de asistencias", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    "mi-asistencia": { titulo: "Mi asistencia", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    resumen: { titulo: "Resumen y regularidad", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    "mi-regularidad": { titulo: "Mi regularidad", roles: ["Admin/Directivo", "Preceptor", "Docente", "Alumno"] },
    alertas: { titulo: "Alertas", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    firmas: { titulo: "Firmas docentes", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    incidencias: { titulo: "Incidencias docentes", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    licencias: { titulo: "Licencias docentes", roles: ["Admin/Directivo", "Preceptor"] },
    balance: { titulo: "Balance de horas cátedra", roles: ["Admin/Directivo", "Preceptor", "Docente"] },
    reportes: { titulo: "Reportes", roles: ["Admin/Directivo", "Preceptor"] },
    configuracion: { titulo: "Configuración institucional", roles: ["Admin/Directivo"] },
    "mi-horario": { titulo: "Mi horario", roles: ["Docente", "Alumno"] },
  };

  const ETIQUETAS = {
    panel: "Panel",
    perfil: "Mi perfil",
    usuarios: "Usuarios",
    estudiantes: "Estudiantes",
    docentes: "Docentes",
    cursos: "Cursos",
    materias: "Materias",
    periodos: "Períodos académicos",
    inscripciones: "Inscripciones",
    asignaciones: "Asignaciones docentes",
    grilla: "Grilla horaria",
    "cargar-asistencia": "Cargar asistencia",
    asistencias: "Consulta de asistencias",
    "mi-asistencia": "Mi asistencia",
    resumen: "Resumen y regularidad",
    "mi-regularidad": "Mi regularidad",
    alertas: "Alertas",
    firmas: "Firmas docentes",
    incidencias: "Incidencias docentes",
    licencias: "Licencias docentes",
    balance: "Balance de horas",
    reportes: "Reportes",
    configuracion: "Configuración",
    "mi-horario": "Mi horario",
  };

  const MENUS = {
    "Admin/Directivo": [
      { titulo: "Principal", paginas: ["panel", "perfil"] },
      { titulo: "Operación diaria", paginas: ["cargar-asistencia", "asistencias", "resumen", "alertas"] },
      { titulo: "Asistencia docente", paginas: ["firmas", "incidencias", "licencias", "balance"] },
      {
        titulo: "Gestión académica",
        paginas: [
          "estudiantes",
          "docentes",
          "cursos",
          "materias",
          "periodos",
          "inscripciones",
          "asignaciones",
          "grilla",
        ],
      },
      { titulo: "Administración", paginas: ["usuarios", "reportes", "configuracion"] },
    ],
    Preceptor: [
      { titulo: "Principal", paginas: ["panel", "perfil"] },
      { titulo: "Operación diaria", paginas: ["cargar-asistencia", "asistencias", "resumen", "alertas"] },
      { titulo: "Asistencia docente", paginas: ["firmas", "incidencias", "licencias", "balance"] },
      {
        titulo: "Gestión académica",
        paginas: [
          "estudiantes",
          "docentes",
          "cursos",
          "materias",
          "periodos",
          "inscripciones",
          "asignaciones",
          "grilla",
        ],
      },
      { titulo: "Administración", paginas: ["reportes"] },
    ],
    Docente: [
      { titulo: "Principal", paginas: ["panel", "perfil"] },
      { titulo: "Operación diaria", paginas: ["cargar-asistencia", "asistencias", "resumen", "alertas"] },
      { titulo: "Asistencia docente", paginas: ["firmas", "incidencias", "balance"] },
      { titulo: "Mi espacio", paginas: ["mi-horario"] },
      {
        titulo: "Consulta",
        paginas: [
          "estudiantes",
          "docentes",
          "cursos",
          "materias",
          "periodos",
          "inscripciones",
          "asignaciones",
          "grilla",
        ],
      },
    ],
    Alumno: [
      { titulo: "Principal", paginas: ["panel", "perfil"] },
      { titulo: "Mi asistencia", paginas: ["mi-asistencia", "mi-regularidad", "mi-horario"] },
    ],
  };

  const CREDENCIALES_DEMOSTRACION = [
    { rol: "Admin/Directivo", usuario: "direccion", contrasena: "Admin123!" },
    { rol: "Preceptor", usuario: "preceptoria", contrasena: "Preceptor123!" },
    { rol: "Docente", usuario: "docente.martinez", contrasena: "Docente123!" },
    { rol: "Alumno", usuario: "alumno.perez", contrasena: "Alumno123!" },
  ];

  const aplicacion = document.getElementById("aplicacion");
  let montada = false;

  function esEntornoLocal() {
    return ["localhost", "127.0.0.1", "[::1]", ""].indexOf(window.location.hostname) !== -1;
  }

  function rutaPorDefecto() {
    return API.SESION.rol() === "Alumno" ? "#/mi-asistencia" : "#/panel";
  }

  function analizarRuta() {
    const hash = window.location.hash.replace(/^#\/?/, "");
    const separador = hash.indexOf("?");
    const identificador = (separador === -1 ? hash : hash.slice(0, separador)) || "panel";
    const parametros = new URLSearchParams(separador === -1 ? "" : hash.slice(separador + 1));
    return { identificador: identificador, parametros: parametros };
  }

  function navegar(destino) {
    if (window.location.hash === destino) {
      renderRuta();
    } else {
      window.location.hash = destino;
    }
  }

  /* -------------------------------------------------------------------- Login */

  function mostrarLogin(mensaje, tipo) {
    montada = false;
    document.body.classList.add("login");
    document.title = "Iniciar sesión · Sistema de Asistencia";

    aplicacion.innerHTML =
      '<main id="contenido" class="login-contenedor" tabindex="-1"><div class="login-tarjeta">' +
      '<div class="login-marca"><span class="marca-insignia" aria-hidden="true">SA</span><div class="marca-texto"><strong>Sistema de Asistencia</strong><span>Gestión institucional</span></div></div>' +
      "<h1>Iniciar sesión</h1>" +
      "<p>Ingresá con la cuenta que te asignó la institución.</p>" +
      '<form id="form-login" class="pila" novalidate>' +
      (mensaje
        ? '<div class="mensaje-login ' + C.esc(tipo || "info") + '" role="status">' + C.esc(mensaje) + "</div>"
        : "") +
      '<div class="error-formulario" role="alert"></div>' +
      '<div class="campo"><label for="login-usuario">Usuario</label><input id="login-usuario" name="nombre_usuario" type="text" autocomplete="username" required autofocus /></div>' +
      '<div class="campo"><label for="login-contrasena">Contraseña</label><input id="login-contrasena" name="contrasena" type="password" autocomplete="current-password" required /></div>' +
      '<div class="login-opciones"><button type="button" class="ver-contrasena" id="ver-contrasena">Mostrar contraseña</button></div>' +
      '<button type="submit" class="boton primario ancho" id="boton-login">Ingresar</button>' +
      "</form>" +
      '<div class="estado-servicio"><span class="punto-estado" id="punto-servicio"></span><span id="texto-servicio">Verificando disponibilidad del servicio…</span></div>' +
      (esEntornoLocal()
        ? '<div class="credenciales-demo"><strong>Credenciales de demostración</strong><table><tbody>' +
          CREDENCIALES_DEMOSTRACION.map(
            (cred) =>
              '<tr><td>' +
              C.esc(cred.rol) +
              '</td><td><button type="button" data-demo-usuario="' +
              C.esc(cred.usuario) +
              '" data-demo-contrasena="' +
              C.esc(cred.contrasena) +
              '">' +
              C.esc(cred.usuario) +
              " · " +
              C.esc(cred.contrasena) +
              "</button></td></tr>"
          ).join("") +
          "</tbody></table></div>"
        : "") +
      "</div></main>";

    const formulario = document.getElementById("form-login");
    const cajaError = formulario.querySelector(".error-formulario");
    const campoUsuario = formulario.querySelector("#login-usuario");
    const campoContrasena = formulario.querySelector("#login-contrasena");
    const boton = formulario.querySelector("#boton-login");

    document.getElementById("ver-contrasena").addEventListener("click", (evento) => {
      const visible = campoContrasena.type === "text";
      campoContrasena.type = visible ? "password" : "text";
      evento.currentTarget.textContent = visible ? "Mostrar contraseña" : "Ocultar contraseña";
    });

    aplicacion.querySelectorAll("[data-demo-usuario]").forEach((elemento) => {
      elemento.addEventListener("click", () => {
        campoUsuario.value = elemento.getAttribute("data-demo-usuario");
        campoContrasena.value = elemento.getAttribute("data-demo-contrasena");
        campoContrasena.focus();
      });
    });

    fetch(API.URL_BASE + "/salud", { headers: { Accept: "application/json" } })
      .then((respuesta) => respuesta.json())
      .then((cuerpo) => {
        const punto = document.getElementById("punto-servicio");
        const texto = document.getElementById("texto-servicio");
        if (punto && texto) {
          punto.classList.add("ok");
          texto.textContent =
            "Servicio operativo · hora del servidor " +
            C.fechaHora(cuerpo.datos && cuerpo.datos.marca_temporal_servidor);
        }
      })
      .catch(() => {
        const punto = document.getElementById("punto-servicio");
        const texto = document.getElementById("texto-servicio");
        if (punto && texto) {
          punto.classList.add("error");
          texto.textContent = "No se pudo contactar al servidor en " + API.URL_BASE + ".";
        }
      });

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      cajaError.textContent = "";
      const nombreUsuario = campoUsuario.value.trim();
      const contrasena = campoContrasena.value;
      if (!nombreUsuario || !contrasena) {
        cajaError.textContent = "Ingresá usuario y contraseña.";
        return;
      }
      boton.disabled = true;
      boton.textContent = "Ingresando…";
      try {
        const respuesta = await API.post("/autenticacion/iniciar-sesion", {
          nombre_usuario: nombreUsuario,
          contrasena: contrasena,
        });
        API.SESION.iniciar(respuesta.datos);
        const perfil = (await API.get("/autenticacion/perfil")).datos;
        API.SESION.guardarPerfil(perfil);
        if (perfil.rol === "Docente") {
          try {
            await U.resolverDocenteId();
          } catch (error) {
            /* la resolución del legajo docente no bloquea el ingreso */
          }
        }
        montarShell(true);
      } catch (error) {
        cajaError.textContent =
          error && error.estado === 401
            ? "Usuario o contraseña incorrectos."
            : C.mensajeDetallado(error);
        boton.disabled = false;
        boton.textContent = "Ingresar";
      }
    });
  }

  function cerrarSesion() {
    API.SESION.limpiar();
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
    mostrarLogin("Cerraste la sesión.", "info");
  }

  /* -------------------------------------------------------------------- Shell */

  function construirMenu(rol, activo) {
    const grupos = MENUS[rol] || [];
    return grupos
      .map(
        (grupo) =>
          "<h2>" +
          C.esc(grupo.titulo) +
          "</h2><ul>" +
          grupo.paginas
            .filter((pagina) => PAGINAS_INFO[pagina])
            .map(
              (pagina) =>
                '<li><a href="#/' +
                pagina +
                '"' +
                (pagina === activo ? ' aria-current="page"' : "") +
                ">" +
                C.esc(ETIQUETAS[pagina]) +
                "</a></li>"
            )
            .join("") +
          "</ul>"
      )
      .join("");
  }

  function montarShell(desdeLogin) {
    montada = true;
    document.body.classList.remove("login");
    const perfil = API.SESION.perfil() || API.SESION.usuario() || {};
    const rol = perfil.rol || "";
    const ruta = analizarRuta();

    aplicacion.innerHTML =
      '<header class="cabecera">' +
      '<button type="button" class="menu-boton" id="menu-boton" aria-expanded="false" aria-controls="navegacion" aria-label="Abrir menú de navegación">☰</button>' +
      '<div class="marca"><span class="marca-insignia" aria-hidden="true">SA</span><div class="marca-texto"><strong>Sistema de Asistencia</strong><span>Gestión institucional</span></div></div>' +
      '<div class="cabecera-derecha"><div class="identidad"><strong>' +
      C.esc(perfil.nombre_usuario || "Sesión") +
      "</strong><span>" +
      C.esc(rol) +
      '</span></div><button type="button" class="boton chico" id="boton-salir">Salir</button></div>' +
      "</header>" +
      '<div class="cuerpo-aplicacion"><nav class="navegacion" id="navegacion" aria-label="Navegación principal">' +
      construirMenu(rol, ruta.identificador) +
      '</nav><main id="contenido" class="contenido" tabindex="-1"></main></div>';

    const botonMenu = document.getElementById("menu-boton");
    const navegacion = document.getElementById("navegacion");
    botonMenu.addEventListener("click", () => {
      const abierta = navegacion.classList.toggle("abierta");
      botonMenu.setAttribute("aria-expanded", abierta ? "true" : "false");
    });
    navegacion.addEventListener("click", (evento) => {
      if (evento.target.closest("a")) {
        navegacion.classList.remove("abierta");
        botonMenu.setAttribute("aria-expanded", "false");
      }
    });
    document.getElementById("boton-salir").addEventListener("click", cerrarSesion);

    if (desdeLogin) {
      navegar(rutaPorDefecto());
    } else {
      navegar(window.location.hash || rutaPorDefecto());
    }
  }

  /* ----------------------------------------------------------------- Enrutador */

  function actualizarNavegacion(identificador) {
    const navegacion = document.getElementById("navegacion");
    if (!navegacion) {
      return;
    }
    navegacion.querySelectorAll("a").forEach((enlace) => {
      const destino = enlace.getAttribute("href").replace("#/", "");
      if (destino === identificador) {
        enlace.setAttribute("aria-current", "page");
      } else {
        enlace.removeAttribute("aria-current");
      }
    });
  }

  function paginaNoDisponible(titulo, mensaje) {
    const contenido = document.getElementById("contenido");
    if (!contenido) {
      return;
    }
    contenido.innerHTML = U.marco(
      titulo,
      "",
      '<div class="tarjeta"><p>' +
        C.esc(mensaje) +
        '</p><p style="margin-top: 12px"><a class="boton" href="' +
        rutaPorDefecto() +
        '">Volver al inicio</a></p></div>'
    );
  }

  function renderRuta() {
    const contenido = document.getElementById("contenido");
    if (!contenido || !montada) {
      return;
    }
    const ruta = analizarRuta();
    const info = PAGINAS_INFO[ruta.identificador];
    const rol = API.SESION.rol();
    actualizarNavegacion(ruta.identificador);

    if (!info) {
      document.title = "Página no encontrada · Sistema de Asistencia";
      paginaNoDisponible("Página no encontrada", "La dirección solicitada no corresponde a una pantalla del sistema.");
      return;
    }
    if (info.roles.indexOf(rol) === -1) {
      document.title = "Sin acceso · Sistema de Asistencia";
      paginaNoDisponible("No tenés acceso a esta sección", "Tu rol no permite usar esta pantalla.");
      return;
    }
    const renderizar = Paginas[ruta.identificador];
    if (typeof renderizar !== "function") {
      paginaNoDisponible("Pantalla no implementada", "Esta pantalla todavía no está disponible.");
      return;
    }

    document.title = info.titulo + " · Sistema de Asistencia";
    contenido.innerHTML = C.esqueleto();
    Promise.resolve()
      .then(() => renderizar(contenido, ruta.parametros))
      .catch((error) => {
        contenido.innerHTML = U.marco(
          info.titulo,
          "",
          '<div class="tarjeta"><div class="error-formulario">' +
            C.esc(C.mensajeDetallado(error)) +
            '</div><div class="form-acciones"><button type="button" class="boton" id="reintentar-pagina">Reintentar</button></div></div>'
        );
        const boton = contenido.querySelector("#reintentar-pagina");
        if (boton) {
          boton.addEventListener("click", renderRuta);
        }
      });
  }

  /* ----------------------------------------------------------------- Arranque */

  document.addEventListener("sesion-expirada", () => {
    if (document.body.classList.contains("login") && document.getElementById("form-login")) {
      return;
    }
    mostrarLogin("La sesión venció. Volvé a iniciar sesión.", "advertencia");
  });

  document.addEventListener("cerrar-sesion", cerrarSesion);

  window.addEventListener("hashchange", renderRuta);

  async function iniciar() {
    if (!API.SESION.haySesion()) {
      mostrarLogin("");
      return;
    }
    try {
      const perfil = (await API.get("/autenticacion/perfil")).datos;
      API.SESION.guardarPerfil(perfil);
      if (perfil.rol === "Docente") {
        try {
          await U.resolverDocenteId();
        } catch (error) {
          /* no bloquea el arranque */
        }
      }
      montarShell(false);
    } catch (error) {
      if (!document.getElementById("form-login")) {
        mostrarLogin("La sesión guardada ya no es válida. Volvé a iniciar sesión.", "error");
      }
    }
  }

  iniciar();
})();
