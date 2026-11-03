"use strict";
// ---------------------------------------------------------------- utilidades
const S = { caminos: {}, camino0: "", tema: "oscuro", idioma: "es", usuario: null, productos: [], pid: null, pestana: "generar", cat: null, marca: "Vibovapp", avanzado: false };
const $ = (s, r = document) => r.querySelector(s);
const t = (k, v) => {
  let s = (TEXTOS[S.idioma] && TEXTOS[S.idioma][k]) || TEXTOS.es[k] || k;
  if (v) for (const x in v) s = s.replace("{" + x + "}", v[x]);
  return s;
};
// «¿Qué quieres hacer?» se recuerda por proyecto (los proyectos viejos usan la última elección)
Object.defineProperty(S, "camino", {
  get() { return (S.pid && S.caminos[S.pid]) || S.camino0 || ""; },
  set(v) { if (S.pid) { S.caminos[S.pid] = v; api("POST", "/api/config", { caminos: S.caminos }).catch(() => {}); } S.camino0 = v; },
});
function h(tag, attrs, ...hijos) {
  const e = document.createElement(tag);
  for (const k in (attrs || {})) {
    const v = attrs[k];
    if (v === false || v == null) continue;
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "value") e.value = v;
    else if (k === "checked") e.checked = !!v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of hijos.flat(9)) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
}
async function api(metodo, url, cuerpo, crudo) {
  const op = { method: metodo, headers: {} };
  if (cuerpo instanceof FormData) op.body = cuerpo;
  else if (cuerpo !== undefined) { op.body = JSON.stringify(cuerpo); op.headers["Content-Type"] = "application/json"; }
  const r = await fetch(url, op);
  if (!r.ok) {
    let msg = "Error " + r.status, j = null;
    try { j = await r.json(); msg = j.error || msg; } catch (e) {}
    const m = /^\/api\/productos\/([^\/]+)\//.exec(url);      // petición tardía de un proyecto que ya no está abierto (cambio de usuario): no se avisa
    if (!(r.status === 404 && m && decodeURIComponent(m[1]) !== S.pid)) toast(msg, true, j); const er = new Error(msg); er.info = j; throw er;
  }
  return crudo ? r : r.json();
}
function toast(msg, mal, info) {
  const con = !!(mal && info && info.codigo);
  const e = h("div", { class: "toast" + (mal ? " mal" : ""), style: con ? "cursor:pointer" : "", title: con ? t("err_click") : "", onclick: con ? () => { e.remove(); detalleError(info); } : null },
    msg, con ? h("div", { class: "chico", style: "opacity:.85;margin-top:4px" }, t("err_codigo") + ": " + info.codigo + " · " + t("err_click")) : null);
  $("#avisos").append(e); setTimeout(() => e.remove(), con ? 14000 : mal ? 6000 : 2600);
}
// cualquier fallo inesperado de la pantalla también se avisa con su código
let _ultFalloUI = 0;
function falloPantalla(msg) {
  if (/ResizeObserver|Script error|AudioContext/i.test(String(msg)) || Date.now() - _ultFalloUI < 4000) return;
  _ultFalloUI = Date.now();
  toast(t("err_pantalla"), true, { error: t("err_pantalla"), codigo: "VV-30-000", paso: "Funcionamiento de la pantalla", paso_en: "Screen behavior" });
}
window.addEventListener("error", ev => falloPantalla(ev.message));
window.addEventListener("unhandledrejection", ev => { if (!(ev.reason && ev.reason.info)) falloPantalla(ev.reason && ev.reason.message); });
// explica un error: qué falló, en qué paso del proceso y su código
function detalleError(d) {
  const paso = (S.idioma === "en" && d.paso_en) || d.paso || "";
  const copiar = async () => { try { await navigator.clipboard.writeText(`${d.codigo} · ${paso}`); toast(t("err_copiado")); } catch (e) {} };
  modal([h("h2", {}, "⚠ " + t("err_t")), h("p", {}, d.error || ""),
    h("div", { class: "tarjeta", style: "margin:10px 0" },
      h("div", { class: "chico suave" }, t("err_paso")), h("div", { style: "font-weight:600;margin-bottom:8px" }, paso),
      h("div", { class: "chico suave" }, t("err_codigo")), h("code", { style: "font-size:1.1rem" }, d.codigo)),
    h("p", { class: "chico suave" }, t("err_ayuda")),
    h("div", { class: "acciones" }, h("button", { onclick: copiar }, t("err_copiar")), h("button", { class: "primario", onclick: cerrarModal }, t("cerrar")))]);
}
// opts: fijo (no se puede cerrar de otra forma que con sus botones), sinX (ya trae su propio botón de cerrar), alCerrar (qué hacer si lo cierran sin elegir)
let _opcsModal = null;
function modal(contenido, opts) {
  opts = opts || {}; _opcsModal = opts;
  const m = $("#modal"); m.innerHTML = ""; m.classList.remove("oculto");
  const caja = h("div", { class: "caja" + (opts.ancha ? " ancha" : "") }, contenido);
  if (!opts.fijo && !opts.sinX) caja.prepend(h("button", { class: "x-cerrar", title: t("cerrar"), "aria-label": t("cerrar"), onclick: descartarModal }, "✕"));
  m.append(caja);
}
const cerrarModal = () => { _opcsModal = null; $("#modal").classList.add("oculto"); };
// cierra con la ✕, con un clic fuera del cuadro o con Esc (si el cuadro lo permite)
function descartarModal() {
  const o = _opcsModal; if (!o || o.fijo) return;
  cerrarModal();
  if (o.alCerrar) { try { o.alCerrar(); } catch (e) {} }
}
(function () {
  const m = $("#modal"); let abajo = false;
  m.addEventListener("mousedown", e => { abajo = e.target === m; });
  m.addEventListener("click", e => { if (e.target === m && abajo) descartarModal(); abajo = false; });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !m.classList.contains("oculto")) descartarModal(); });
})();
function confirmar(texto, boton) {
  return new Promise(res => {
    modal([h("p", {}, texto), h("div", { class: "acciones" },
      h("button", { onclick: () => { cerrarModal(); res(false); } }, t("cancelar")),
      h("button", { class: "primario", onclick: () => { cerrarModal(); res(true); } }, boton || t("si_borrar")))], { alCerrar: () => res(false) });
  });
}
// cambiar nombre con doble clic (en el mismo lugar) o con clic derecho (menú)
function editarEnLinea(el, actual, guardar) {
  if (!el || el.querySelector("input")) return;
  const texto = el.textContent; let listo = false;
  const inp = h("input", { type: "text", value: actual, class: "edit-nombre" });
  const cerrar = async ok => {
    if (listo) return; listo = true;
    const v = inp.value.trim();
    el.textContent = texto;
    if (ok && v && v !== actual) { try { await guardar(v); } catch (e) {} }
  };
  inp.addEventListener("keydown", e => { e.stopPropagation(); if (e.key === "Enter") cerrar(true); else if (e.key === "Escape") cerrar(false); });
  inp.addEventListener("blur", () => cerrar(true));
  inp.addEventListener("click", e => e.stopPropagation());
  inp.addEventListener("dblclick", e => e.stopPropagation());
  el.textContent = ""; el.append(inp); inp.focus(); inp.select();
}
function menuCtx(e, items) {
  e.preventDefault(); e.stopPropagation();
  document.querySelectorAll(".menu-ctx").forEach(m => m.remove());
  const m = h("div", { class: "menu-ctx" }, items.filter(Boolean).map(([txt, fn, peligro]) =>
    h("button", { class: peligro ? "peligro" : "", onclick: ev => { ev.stopPropagation(); m.remove(); fn(); } }, txt)));
  document.body.append(m);
  const x = Math.min(e.clientX, innerWidth - m.offsetWidth - 8), y = Math.min(e.clientY, innerHeight - m.offsetHeight - 8);
  m.style.left = Math.max(4, x) + "px"; m.style.top = Math.max(4, y) + "px";
  const quitar = ev => { if (!m.contains(ev.target) || ev.type === "scroll") { m.remove(); off(); } };
  const tecla = ev => { if (ev.key === "Escape") { m.remove(); off(); } };
  const off = () => { document.removeEventListener("mousedown", quitar, true); document.removeEventListener("keydown", tecla, true); removeEventListener("scroll", quitar, true); };
  setTimeout(() => { document.addEventListener("mousedown", quitar, true); document.addEventListener("keydown", tecla, true); addEventListener("scroll", quitar, true); }, 0);
}
function renombrable(zona, nombreEl, actual, guardar, extras) {
  nombreEl.title = t("dbl_renombrar");
  nombreEl.classList.add("renombrable");
  nombreEl.addEventListener("dblclick", e => { e.preventDefault(); e.stopPropagation(); editarEnLinea(nombreEl, actual, guardar); });
  zona.addEventListener("contextmenu", e => {
    if (e.target.closest("video, input")) return;      // el reproductor conserva su propio menú
    menuCtx(e, [[t("renombrar"), () => editarEnLinea(nombreEl, actual, guardar)], ...(extras || [])]);
  });
}
function pedirTexto(titulo, etiqueta, valor, extra, boton) {
  return new Promise(res => {
    const inp = h("input", { type: "text", value: valor || "", placeholder: t("nombre_ej") });
    const chk = extra ? h("input", { type: "checkbox" }) : null;
    const ok = () => { const v = inp.value.trim(); if (!v) return; cerrarModal(); res({ valor: v, extra: chk && chk.checked }); };
    inp.addEventListener("keydown", e => { if (e.key === "Enter") ok(); });
    modal([h("h2", {}, titulo), h("label", { class: "suave chico" }, etiqueta), inp,
      extra ? h("label", { class: "fila chico", style: "margin-top:12px" }, chk, extra) : null,
      h("div", { class: "acciones" },
        h("button", { onclick: () => { cerrarModal(); res(null); } }, t("cancelar")),
        h("button", { class: "primario", onclick: ok }, boton || t("crear")))], { alCerrar: () => res(null) });
    setTimeout(() => inp.focus(), 50);
  });
}
const kb = n => n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
const base = () => `/api/productos/${S.pid}`;
const prod = () => S.productos.find(p => p.id === S.pid);

// zona para arrastrar o elegir archivos
// rueda de carga: la V del logo con un aro de los colores del logo girando
function rueda(tam) {
  return h("span", { class: "rueda", style: `--d:${tam || 44}px` }, h("span", { class: "aro" }), h("img", { src: "/web/favicon.png", alt: "" }));
}
// grabar un video con la cámara (celular: abre la cámara del teléfono; computadora: ventanita con vista previa)
const ES_TACTIL = () => { try { return matchMedia("(pointer:coarse)").matches; } catch (e) { return false; } };
function puedeGrabar() { return ES_TACTIL() || !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder); }
function grabarVideo(alTerminar, soloAudio) {
  if (ES_TACTIL()) {
    const inp = h("input", { type: "file", accept: soloAudio ? "audio/*" : "video/*", capture: soloAudio ? true : "user", style: "display:none" });
    inp.addEventListener("change", () => { const f = inp.files[0]; if (f) alTerminar([f]); });
    document.body.append(inp); inp.click(); setTimeout(() => inp.remove(), 120000); return;
  }
  const vid = soloAudio ? h("div", { style: "font-size:56px;text-align:center;padding:10px" }, "🎙") : h("video", { autoplay: true, muted: true, playsinline: true, style: "width:100%;border-radius:10px;background:#000" });
  const info = h("div", { class: "chico suave" }, t("grab_pide"));
  let flujo = null, rec = null, trozos = [], t0 = 0, reloj = null, usar = true;
  const parar = () => { if (reloj) clearInterval(reloj); if (flujo) flujo.getTracks().forEach(x => x.stop()); };
  const btn = h("button", { class: "primario", disabled: true }, "⏺ " + t("grab_empezar"));
  const cancelar = h("button", { onclick: () => { usar = false; if (rec && rec.state === "recording") rec.stop(); parar(); cerrarModal(); } }, t("cancelar"));
  modal([h("h2", {}, (soloAudio ? "🎙 " : "🎥 ") + t(soloAudio ? "grab_ta" : "grab_t")), vid, info, h("div", { class: "acciones" }, cancelar, btn)]);
  navigator.mediaDevices.getUserMedia({ video: !soloAudio, audio: true }).then(f => {
    flujo = f; if (!soloAudio) vid.srcObject = f; btn.disabled = false; info.textContent = t("grab_listo");
    btn.onclick = () => {
      if (rec && rec.state === "recording") { rec.stop(); return; }
      rec = new MediaRecorder(f); trozos = [];
      rec.ondataavailable = e => { if (e.data.size) trozos.push(e.data); };
      rec.onstop = () => { parar(); cerrarModal(); if (usar && trozos.length) alTerminar([new File(trozos, (soloAudio ? "audio_" : "grabacion_") + Date.now() + (soloAudio ? ".weba" : ".webm"), { type: soloAudio ? "audio/webm" : "video/webm" })]); };
      rec.start(); t0 = Date.now(); btn.textContent = "⏹ " + t("grab_parar");
      reloj = setInterval(() => { info.textContent = "● " + Math.round((Date.now() - t0) / 1000) + " s"; }, 500);
    };
  }).catch(() => { info.textContent = t("grab_sin_camara"); });
}
let progresoSubida = null;
const SONIDO_CLAVES = ["burbuja_sonido", "sonido_transicion", "sonido_titulo", "sonido_cta"];
// botón pequeño para elegir archivos y subirlos (sin zona grande)
function botonSubir(texto, aceptar, subir) {
  const inp = h("input", { type: "file", multiple: true, accept: aceptar, style: "display:none" });
  const b = h("button", { class: "chico", onclick: () => inp.click() }, texto, inp);
  const enviar = async fs => { if (!fs.length) return; b.disabled = true; try { await subir(fs); } catch (e) { toast(String(e.message || e), true); } b.disabled = false; };
  inp.addEventListener("change", async () => { const fs = [...inp.files]; inp.value = ""; await enviar(fs); });
  if (/video/.test(aceptar) && puedeGrabar()) return h("span", { style: "display:inline-flex;gap:6px;flex-wrap:wrap" }, b, h("button", { class: "chico", onclick: () => grabarVideo(enviar) }, "🎥 " + t("grab_btn")));
  return b;
}
let ULTIMA_ZONA = null;
// Ctrl+V: pega archivos (copiados en el Explorador, o una captura) en la zona de subida que corresponda
document.addEventListener("paste", e => {
  const el = e.target;
  if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) && !(el.type === "file")) return;     // en una caja de texto, Ctrl+V pega texto
  const fs = [...((e.clipboardData && e.clipboardData.files) || [])];
  if (!fs.length) return;
  const vivas = [...document.querySelectorAll(".soltar")].filter(z => z.pegar && z.offsetParent !== null && !z.classList.contains("ocupada"));
  const mod = document.querySelector("#modal");
  if ((!mod || mod.classList.contains("oculto")) && vivas.length) {
    const z = vivas.find(x => x.matches(":hover")) || (ULTIMA_ZONA && vivas.includes(ULTIMA_ZONA) ? ULTIMA_ZONA : null) || vivas.find(x => x.prioridad) || (vivas.length === 1 ? vivas[0] : null);
    e.preventDefault();
    if (z) z.pegar(fs); else toast(t("pegar_elige"), true);
  }
});
function zonaSubir(texto, aceptar, subir, prioridad) {
  const inp = h("input", { type: "file", multiple: true, accept: aceptar, style: "display:none" });
  const z = h("div", { class: "soltar", onclick: async () => {
    if (z.classList.contains("ocupada")) return;
    const fs = typeof guiaElegir === "function" ? await guiaElegir() : null;       // práctica guiada: el selector abre ya en la carpeta del material
    if (fs === null) inp.click(); else if (fs.length) enviar(fs);
  } }, texto, inp);
  const hayV = /video/.test(aceptar), hayA = !hayV && /audio/.test(aceptar) && /\.txt/.test(aceptar);      // el audio suelto solo se graba en la zona de guiones
  const grab = (hayV || hayA) && puedeGrabar() ? h("button", { class: "chico", style: "margin-top:8px", onclick: ev => { ev.stopPropagation(); grabarVideo(fs => enviar(fs), hayA); } }, (hayA ? "🎙 " + t("grab_audio") : "🎥 " + t("grab_btn"))) : null;
  const contenido = () => [texto, h("div", { class: "chico suave pegar-hint" }, t("pegar_hint")), grab, inp].filter(Boolean);
  z.replaceChildren(...contenido());
  z.pegar = fs => enviar(fs); z.prioridad = !!prioridad;
  z.addEventListener("mouseenter", () => { ULTIMA_ZONA = z; });
  const enviar = async fs => {
    if (!fs.length || z.classList.contains("ocupada")) return;
    const n = fs.length;
    z.classList.add("ocupada"); z.classList.remove("arriba");
    const txt = h("span", {}, t("subiendo"));
    z.replaceChildren(rueda(46), h("div", { class: "sub-txt" }, txt));
    progresoSubida = p => { txt.textContent = p >= 1 ? t("guardando_arch", { n }) : `${t("subiendo")} ${Math.round(p * 100)}% · ${n}`; };
    try { await subir([...fs]); }
    catch (e) { z.classList.remove("ocupada"); z.replaceChildren(...contenido()); }
    progresoSubida = null;
  };
  inp.addEventListener("change", () => { enviar(inp.files); inp.value = ""; });
  z.addEventListener("dragover", e => { e.preventDefault(); z.classList.add("arriba"); });
  z.addEventListener("dragleave", () => z.classList.remove("arriba"));
  z.addEventListener("drop", e => { e.preventDefault(); z.classList.remove("arriba"); enviar(e.dataTransfer.files); });
  return z;
}
function enviarConProgreso(url, fd, alProgreso) {
  return new Promise((ok, mal) => {
    const x = new XMLHttpRequest();
    x.open("POST", url);
    if (alProgreso) x.upload.onprogress = e => { if (e.lengthComputable) alProgreso(e.loaded / e.total); };
    x.upload.onload = () => alProgreso && alProgreso(1);
    x.onload = () => {
      let d = {}; try { d = JSON.parse(x.responseText); } catch (e) {}
      if (x.status >= 200 && x.status < 300) ok(d);
      else { const msg = d.error || "Error " + x.status; toast(msg, true, d); mal(new Error(msg)); }
    };
    x.onerror = () => { toast(t("error"), true); mal(new Error("red")); };
    x.send(fd);
  });
}
async function subirArchivos(seccion, tema, archivos) {
  const cb = progresoSubida;
  const fd = new FormData();
  archivos.forEach(f => fd.append("archivos", f));
  const r = await enviarConProgreso(`${base()}/archivos/${seccion}` + (tema ? "?tema=" + encodeURIComponent(tema) : ""), fd, cb);
  (r.errores || []).forEach(e => toast(e, true));
  if (r.subidos.length) toast(t("subidos") + ": " + r.subidos.length);
  if ((r.repetidos || []).length) toast(t("repetidos_no", { n: r.repetidos.length }), true);
  await refrescarProductos();
  return r.subidos || [];
}
// lista con buscador y selección múltiple (sirve para archivos y para videos)
function listaBuscable({ items, texto, pintar, borrar, extra }) {
  const est = { q: "", modo: false, sel: new Set() };
  const visibles = () => items.filter(i => texto(i).toLowerCase().includes(est.q.trim().toLowerCase()));
  const buscar = h("input", { type: "text", placeholder: "🔍 " + t("bus_ph"), style: "flex:1;min-width:150px;max-width:340px", oninput: e => { est.q = e.target.value; repintar(); } });
  const info = h("span", { class: "suave chico" });
  const btnSel = h("button", { class: "chico", onclick: () => { est.modo = !est.modo; est.sel.clear(); repintar(); } });
  const btnTodo = h("button", { class: "chico", onclick: () => { visibles().forEach(i => est.sel.add(i.nombre)); repintar(); } }, t("sel_todo"));
  const btnNada = h("button", { class: "chico", onclick: () => { est.sel.clear(); repintar(); } }, t("sel_ninguno"));
  const btnBorrar = h("button", { class: "chico peligro", onclick: async () => {
    if (!est.sel.size) return;
    if (!await confirmar(t("sel_conf", { n: est.sel.size }), t("borrar"))) return;
    const n = await borrar([...est.sel]); toast(t("sel_borrados", { n })); } });
  const cuerpo = h("div", {});
  est.contar = () => { btnBorrar.textContent = t("sel_borrar", { n: est.sel.size }); btnBorrar.disabled = !est.sel.size; };
  function repintar() {
    const vis = visibles();
    cuerpo.innerHTML = "";
    if (!vis.length) poner(cuerpo, h("div", { class: "vacio chico" }, t("bus_nada")));
    else poner(cuerpo, pintar(vis, est));
    info.textContent = est.q.trim() ? t("bus_res", { n: vis.length, m: items.length }) : "";
    btnSel.textContent = est.modo ? t("sel_cancelar") : "☑ " + t("sel_modo");
    btnTodo.hidden = btnNada.hidden = btnBorrar.hidden = !est.modo;
    est.contar();
  }
  est.repintar = repintar;
  repintar();
  return h("div", {}, h("div", { class: "fila", style: "margin:8px 0" }, buscar, btnSel, btnTodo, btnNada, btnBorrar, info, extra || null), cuerpo);
}
function tocarSel(est, nombre, nodo) { est.sel.has(nombre) ? est.sel.delete(nombre) : est.sel.add(nombre); nodo.classList.toggle("sel", est.sel.has(nombre)); est.contar(); }
function galeria(seccion, tema, items, recargar) {
  if (!items.length) return h("div", { class: "vacio chico" }, t("cl_sin_clips"));
  const q0 = tema ? "?tema=" + encodeURIComponent(tema) : "";
  const limpiar = h("button", { class: "link chico", onclick: async () => {
    if (!await confirmar(t("dup_conf"), t("dup_quitar"))) return;
    const r = await api("POST", `${base()}/archivos/${seccion}/duplicados${q0}`);
    toast(r.borrados ? t("dup_borrados", { n: r.borrados }) : t("dup_ninguno")); await refrescarProductos(); recargar(); } }, t("dup_quitar"));
  return listaBuscable({
    items, texto: it => it.nombre, extra: limpiar,
    borrar: async nombres => { const r = await api("POST", `${base()}/archivos/${seccion}/borrar${q0}`, { nombres }); await refrescarProductos(); recargar(); return r.borrados; },
    pintar: (vis, est) => h("div", { class: "mini" }, vis.map(it => {
      const q = `?nombre=${encodeURIComponent(it.nombre)}` + (tema ? "&tema=" + encodeURIComponent(tema) : "");
      const nombreA = h("small", {}, it.nombre);
      const borrarA = async () => { await api("DELETE", `${base()}/archivos/${seccion}${q}`); await refrescarProductos(); recargar(); };
      const nodo = h("div", { class: "it" + (est.sel.has(it.nombre) ? " sel" : "") },
        it.tipo === "audio" ? h("div", { class: "sinimg" }, "♪") :
          h("img", { loading: "lazy", src: `${base()}/miniatura/${seccion}${q}`, alt: "", onerror: e => e.target.replaceWith(h("div", { class: "sinimg" }, it.tipo === "video" ? "▶" : "🖼")) }),
        est.modo ? h("div", { class: "capa", onclick: () => tocarSel(est, it.nombre, nodo) }) : [
          h("button", { class: "x", title: t("borrar"), onclick: borrarA }, "×"),
        ],
        nombreA);
      if (!est.modo) renombrable(nodo, nombreA, it.nombre.replace(/\.[^.]+$/, ""),
        async v => { await api("POST", `${base()}/archivos/${seccion}/renombrar${q0}`, { nombre: it.nombre, nuevo: v }); recargar(); }, [[t("borrar"), borrarA, true]]);
      return nodo;
    })) });
}
async function refrescarProductos() { S.productos = await api("GET", "/api/productos"); }

// ---------------------------------------------------------------- barra
// agrega hijos ignorando null/false (el append nativo escribiria la palabra "null")
function poner(el, ...hijos) { for (const c of hijos.flat(9)) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(c)); }
function barra() {
  const b = $("#barra"); b.innerHTML = "";
  poner(b, h("img", { class: "logo", src: "/web/logo.png", alt: S.marca, title: S.marca, onclick: () => { if (S.usuario) irInicio(); } }),
    h("span", { class: "suave" }, S.pid && prod() ? "/ " + prod().nombre : ""),
    h("div", { class: "espacio" }),
    S.usuario && ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname) ? h("button", { title: t("cel_ay"), onclick: ventanaCelular }, "📱 " + t("cel_btn")) : null,
    S.usuario ? h("button", { onclick: () => { S.vista = S.vista === "historial" ? null : "historial"; render(); } }, "📋 " + t("historial")) : null,
    S.usuario ? h("button", { onclick: tutorial }, t("ayuda")) : null,
    h("button", { onclick: configuracion }, "⚙ " + t("cfg_btn")),
    S.ventanaPropia ? null : h("button", { title: t("salir"), onclick: salir }, "✕ " + t("salir")));
}
function configuracion() {
  const selT = h("select", { onchange: async e => { aplicarTema(e.target.value); await api("POST", "/api/config", { tema: S.tema }); } },
    [["oscuro", "tema_oscuro"], ["claro", "tema_claro"], ["auto", "tema_auto"]].map(o => h("option", { value: o[0], selected: S.tema === o[0] }, t(o[1]))));
  const selI = h("select", { onchange: async e => { S.idioma = e.target.value; await api("POST", "/api/config", { idioma: S.idioma }); document.documentElement.lang = S.idioma; cerrarModal(); if (S.usuario) render(); else pantallaUsuarios(); } },
    h("option", { value: "es", selected: S.idioma === "es" }, "Español"), h("option", { value: "en", selected: S.idioma === "en" }, "English"));
  modal([h("h2", {}, "⚙ " + t("cfg_btn")),
    h("label", { class: "chico suave" }, t("tema_lbl")), selT,
    h("label", { class: "chico suave", style: "display:block;margin-top:12px" }, t("idioma")), selI,
    S.usuario ? h("button", { style: "width:100%;margin-top:16px", onclick: () => { cerrarModal(); miPlan(); } }, "⭐ " + t("plan_btn") + (S.plan ? ": " + S.plan.nombre : "")) : null,
    S.usuario ? h("button", { style: "width:100%;margin-top:8px", onclick: () => { cerrarModal(); elegirCamino(); } }, t("cm_elegir")) : null,
    h("button", { style: "width:100%;margin-top:8px", onclick: () => { cerrarModal(); elegirInicio(true); } }, t("cfg_bienv")),
    S.usuario ? h("button", { style: "width:100%;margin-top:8px", title: t("cfg_nuevo_ay"), onclick: async () => {
      if (!confirm(t("cfg_nuevo_conf"))) return;
      await api("POST", "/api/config", { aviso_aceptado: false, tutorial_visto: false, camino: "", version_vista: "" });
      location.reload();
    } }, "🆕 " + t("cfg_nuevo")) : null,
    S.usuario ? h("div", { class: "chico suave", style: "margin-top:4px" }, t("cfg_nuevo_ay")) : null,
    h("div", { class: "acciones" }, h("button", { class: "primario", onclick: cerrarModal }, t("cerrar")))]);
}
function ventanaCelular() {
  modal([h("h2", {}, "📱 " + t("cel_btn")), h("div", { id: "cel-caja" }),
    h("div", { class: "acciones" }, h("button", { class: "primario", onclick: cerrarModal }, t("cerrar")))]);
  pintarCelular();
}
let _celTimer = null;
async function pintarCelular() {
  clearTimeout(_celTimer);
  const caja = $("#cel-caja"); if (!caja) return;
  _celTimer = setTimeout(() => { if ($("#cel-caja") && !$("#modal").classList.contains("oculto")) pintarCelular(); }, 2500);
  let d; try { d = await api("GET", "/api/celular"); } catch (e) { return; }
  if (d.solo_pc) { caja.remove(); return; }      // desde el celular esta sección no aparece
  caja.innerHTML = "";
  const cambiar = async activo => { try { await api("POST", "/api/celular", { activo }); } catch (e) { toast(e.message || String(e), false); } pintarCelular(); };
  if (!d.activo) {
    caja.append(h("button", { style: "width:100%", onclick: () => cambiar(true) }, "📱 " + t("cel_ver")), h("div", { class: "chico suave", style: "margin-top:4px" }, t("cel_ay")));
    return;
  }
  const qr = h("div", { style: "background:#fff;padding:6px;border-radius:10px;width:fit-content;margin:8px auto" });
  qr.innerHTML = d.qr || "";
  caja.append(...[h("b", {}, "📱 " + t("cel_ver")), h("p", { class: "chico" }, t("cel_pasos")), d.qr ? qr : null,
    h("div", { style: "text-align:center" }, h("code", { style: "font-size:15px;word-break:break-all" }, d.url_qr || d.url), h("div", { style: "font-size:26px;letter-spacing:6px;margin:6px 0" }, d.pin)),
    h("div", { style: "margin:10px 0" }, h("b", { class: "chico" }, t("cel_disp")),
      ...(d.dispositivos.length ? d.dispositivos.map(x => h("div", { class: "fila chico", style: "padding:3px 0" }, h("span", {}, (x.en_linea ? "🟢 " : "⚪ ") + x.nombre), h("span", { class: "suave" }, x.en_linea ? t("cel_en_linea") : t("cel_hace", { s: Math.max(1, Math.round(x.hace / 60)) })), h("div", { class: "espacio" }),
        h("button", { class: "chico", onclick: async () => { await api("POST", "/api/celular", { desconectar: x.id }); pintarCelular(); } }, t("cel_sacar")))) : [h("div", { class: "chico suave" }, t("cel_nadie"))]),
      d.dispositivos.length ? h("button", { class: "chico", onclick: async () => { await api("POST", "/api/celular", { desconectar: "todos" }); pintarCelular(); } }, t("cel_sacar_todos")) : null),
    h("div", { style: "margin:10px 0;padding:10px;border:1px dashed var(--borde,#4a5a86);border-radius:10px" },
      d.remoto.estado === "listo" ? h("div", {}, h("b", { class: "chico" }, "🌎 " + t("cel_remoto_on")), h("div", { class: "chico suave" }, t("cel_remoto_aviso")),
          h("button", { class: "chico", style: "margin-top:6px", onclick: async () => { await api("POST", "/api/celular", { remoto: false }); pintarCelular(); } }, t("cel_remoto_off")))
        : d.remoto.estado === "preparando" ? h("div", { class: "chico" }, "⏳ " + t("cel_remoto_prep"))
        : h("div", {}, h("button", { style: "width:100%", onclick: async () => { try { await api("POST", "/api/celular", { remoto: true }); } catch (e) {} pintarCelular(); } }, "🌎 " + t("cel_remoto")),
          h("div", { class: "chico suave", style: "margin-top:4px" }, d.remoto.error || t("cel_remoto_ay")))),
    h("button", { style: "width:100%", onclick: () => cambiar(false) }, t("cel_apagar")), h("div", { class: "chico suave", style: "margin-top:4px" }, t("cel_aviso"))].filter(Boolean));
}
function aplicarTema(v) {
  S.tema = ["oscuro", "claro", "auto"].includes(v) ? v : "oscuro";
  document.documentElement.setAttribute("data-tema", S.tema);
}
async function salir() {
  const cerrar = async forzar => {
    try {
      const r = await fetch("/api/salir", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ forzar }) });
      if (r.status === 409) { const d = await r.json(); if (d.ocupado && await confirmar(d.error, t("salir_igual"))) return cerrar(true); return; }
      document.body.innerHTML = `<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;font:18px system-ui;color:#e8ecf7;background:#0c172e;padding:20px"><div><img src="/web/logo.png" style="height:44px;margin-bottom:18px"><p>${t("salio")}</p></div></div>`;
    } catch (e) { toast(t("salio"), false); }
  };
  if (!await confirmar(t("salir_conf"), t("salir"))) return;
  cerrar(false);
}
// ---------------------------------------------------------------- usuarios
async function cambiarUsuario() {
  try { sessionStorage.removeItem("rm_entro"); } catch (e) {}
  await api("POST", "/api/usuarios/cerrar"); S.usuario = null; S.pid = null; pantallaUsuarios();
}
async function pantallaUsuarios() {
  barra();
  try { await api("POST", "/api/usuarios/unico"); await entrarUsuario(); return; } catch (e) {}      // un solo usuario por computadora: se entra directo
  const app = $("#app"); app.innerHTML = "";
  const lista = await api("GET", "/api/usuarios");
  const g = h("div", { class: "rejilla" });
  lista.usuarios.forEach(u => g.append(h("div", { class: "tarjeta producto", onclick: async () => { await api("POST", "/api/usuarios/activar", { id: u.id }); await entrarUsuario(); } },
    h("b", {}, "👤 " + u.nombre),
    h("div", { class: "fila", onclick: e => e.stopPropagation() },
      h("button", { class: "chico", onclick: async () => { const r = await pedirTexto(t("renombrar"), t("usr_nombre"), u.nombre, null, t("guardar")); if (!r) return; await api("POST", "/api/usuarios/renombrar", { id: u.id, nombre: r.valor }); pantallaUsuarios(); } }, t("renombrar")),
      h("button", { class: "chico peligro", onclick: async () => { if (!await confirmar(t("usr_conf_borrar", { n: u.nombre }))) return; await api("DELETE", `/api/usuarios/${encodeURIComponent(u.id)}`); pantallaUsuarios(); } }, t("borrar"))))));
  g.append(h("div", { class: "tarjeta nuevo", style: "cursor:pointer", onclick: async () => { const r = await pedirTexto(t("usr_nuevo_t"), t("usr_nombre")); if (!r) return; const { id } = await api("POST", "/api/usuarios", { nombre: r.valor }); await api("POST", "/api/usuarios/activar", { id }); await entrarUsuario(); } }, t("usr_nuevo")));
  poner(app, h("h1", {}, t("usr_quien")), h("p", { class: "suave" }, t("usr_ayuda")), g,
    lista.usuarios.length ? null : h("div", { class: "vacio" }, t("usr_ninguno")));
}
async function entrarUsuario(restaurar) {
  S.vista = null;
  try { sessionStorage.setItem("rm_entro", "1"); } catch (e) {}
  const d = await api("GET", "/api/inicio");
  aplicarTema(d.tema); S.idioma = d.config.idioma || "es"; S.usuario = d.usuario; S.productos = d.productos; S.caminos = d.config.caminos || {}; S.camino0 = d.config.camino || ""; S.verTodo = false; document.documentElement.lang = S.idioma;
  try { S.fuentesPropias = (await api("GET", "/api/fuentes")).propias; } catch (e) {}      // tipografías que subió esta persona
  const ses = restaurar ? (d.config.sesion || {}) : {};   // solo al recargar la página (F5) vuelve a donde estabas; al abrir el programa se empieza limpio
  S.pid = ses.pid && S.productos.some(p => p.id === ses.pid) ? ses.pid : null;
  S.pestana = PESTANAS.includes(ses.pestana) ? ses.pestana : ses.pestana === "hablado" ? "hablando" : "generar";
  if (ses.guion) guionSel = ses.guion;
  render();
  if (!d.config.aviso_aceptado) {
    modal([h("h2", {}, t("av_titulo")), ...t("av_txt").split("\n\n").map(p => h("p", {}, p)),
      h("div", { class: "acciones" }, h("button", { class: "primario", onclick: async () => { await api("POST", "/api/config", { aviso_aceptado: true }); cerrarModal(); tutorialPrimeraVez(); } }, t("av_acepto")))], { fijo: true });
  } else if (!d.config.tutorial_visto) { tutorialPrimeraVez(); api("POST", "/api/config", { version_vista: d.version }); }      // usuario nuevo: ya empieza con lo último
  else if (d.config.version_vista !== d.version) novedadesTrasActualizar(d.config.version_vista);
}
let tmSesion;
function guardarSesion() {
  if (!S.usuario) return;
  clearTimeout(tmSesion);
  tmSesion = setTimeout(() => fetch("/api/config", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sesion: { pid: S.pid || "", pestana: S.pestana, guion: guionSel || "" } }) }).catch(() => {}), 400);
}
function irInicio() { S.pid = null; S.vista = null; render(); }

// ---------------------------------------------------------------- autoguardado
// Guarda solo, un momento después de que dejas de cambiar algo. Cada cosa tiene su clave; si vuelves a cambiar, se reinicia la espera.
const AUTO = new Map();
function autoguardar(clave, fn, ms = 700) {
  const a = AUTO.get(clave); if (a) clearTimeout(a.tm);
  AUTO.set(clave, { fn, tm: setTimeout(() => { AUTO.delete(clave); Promise.resolve().then(fn).catch(() => {}); }, ms) });
}
function cancelarAuto(clave) { const a = AUTO.get(clave); if (a) { clearTimeout(a.tm); AUTO.delete(clave); } }
function vaciarAuto() {   // al cambiar de pestaña o cerrar: guarda ya lo que esté esperando
  const fs = [...AUTO.values()]; AUTO.forEach(a => clearTimeout(a.tm)); AUTO.clear();
  fs.forEach(a => Promise.resolve().then(a.fn).catch(() => {}));
}
document.addEventListener("visibilitychange", () => { if (document.hidden) vaciarAuto(); });
window.addEventListener("pagehide", vaciarAuto);
function horaCorta() { return new Date().toLocaleTimeString(S.idioma === "en" ? "en-US" : "es-MX", { hour: "2-digit", minute: "2-digit" }); }

// ---------------------------------------------------------------- tutorial
// Temas del recorrido: [id, cuantas pantallas tiene, pestaña a la que lleva (null = ninguna)]
const TEMAS_TOUR = [["empezar", 3, null], ["producto", 2, null], ["guiones", 4, "guiones"], ["burbujas", 4, "guiones"], ["clips", 4, "clips"],
  ["musica", 1, "musica"], ["capas", 3, "capas"], ["estilo", 8, "estilo"], ["crear", 3, "generar"], ["hablado", 7, "hablando"], ["videos", 3, "videos"], ["papelera", 1, "papelera"], ["referencia", 3, null], ["app", 4, null], ["plan", 2, null]];
// Primera vez: bienvenida corta con tres caminos (recorrido, video de muestra u omitir)
function tutorialPrimeraVez() {
  api("POST", "/api/config", { tutorial_visto: true });
  modal([h("h2", {}, t("tour_bienvenida_t", { m: S.marca })), h("p", {}, t("tour_bienvenida", { m: S.marca })),
    h("div", { style: "display:flex;flex-direction:column;gap:8px;margin-top:12px" },
      h("button", { class: "primario grande btn-practica-bienv", onclick: iniciarPractica }, t("tour_b_muestra")),
      h("button", { onclick: () => tour(TEMAS_TOUR.map(x => x[0])) }, t("tour_b_recorrido")),
      h("button", { class: "link", onclick: cerrarModal }, t("tour_b_omitir")))]);
}
// Menú de ayuda: ver todo, o elegir un tema
function tutorial() {
  modal([h("div", { class: "fila" }, h("h2", { style: "margin:0" }, t("tour_ayuda_t")), h("div", { class: "espacio" }), h("button", { class: "link", onclick: cerrarModal }, t("cerrar") + " ✕")),
    h("p", { class: "suave" }, t("tour_ayuda_txt")),
    cmCamino() ? h("button", { class: "primario", style: "width:100%", onclick: () => recorrido(0) }, "🧭 " + t("cm_recorrido") + ": " + cmNombre(cmCamino())) : null,
    h("button", { style: "width:100%;margin-top:8px", onclick: elegirCamino }, t("cm_elegir")),
    h("button", { style: "width:100%;margin-top:8px", onclick: iniciarPractica }, t("tour_b_muestra")),
    h("button", { style: "width:100%;margin-top:8px", onclick: () => tour(TEMAS_TOUR.map(x => x[0])) }, t("tour_todo")),
    h("button", { class: "btn-faq", style: "width:100%;margin-top:8px", onclick: abrirFaq }, t("faq_btn")),
    h("button", { class: "btn-ayuda-asistente", style: "width:100%;margin-top:8px", onclick: asistente }, "💬 " + t("as_titulo")),
    h("h3", { style: "margin:16px 0 6px" }, t("tour_temas")),
    h("div", { style: "display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px" },
      TEMAS_TOUR.map(([id], k) => h("button", { style: "text-align:left", onclick: () => tour([id], true) }, `${k + 1}. ` + t(`tour_${id}_t`))))], { sinX: true });
}
// Recorrido: lista de temas a mostrar, uno tras otro. solo = true cuando se eligió un solo tema desde el menú.
function tour(ids, solo) {
  const pantallas = [];
  ids.forEach(id => { const [, n, pest] = TEMAS_TOUR.find(x => x[0] === id); for (let k = 1; k <= n; k++) pantallas.push({ id, k, n, pest }); });
  let i = 0;
  const pintar = () => {
    const x = pantallas[i], ultimo = i === pantallas.length - 1;
    modal([
      h("div", { class: "fila" }, h("span", { class: "insignia" }, solo ? t("tour_pag", { a: x.k, b: x.n }) : `${i + 1} / ${pantallas.length}`), h("div", { class: "espacio" }),
        h("button", { class: "link", onclick: tutorial }, "☰ " + t("ayuda").replace(/^\?\s*/, "")), h("button", { class: "link", onclick: cerrarModal }, t("tour_omitir") + " ✕")),
      h("h2", { style: "margin-top:8px" }, t(`tour_${x.id}_t`)),
      h("p", { style: "font-size:1.05em;line-height:1.5" }, t(`tour_${x.id}_${x.k}`)),
      x.id === "empezar" && x.k === x.n ? h("button", { class: "primario", style: "margin:4px 0 10px", onclick: iniciarPractica }, t("tour_b_muestra")) : null,
      h("div", { class: "acciones", style: "justify-content:space-between" },
        h("button", { disabled: i === 0, onclick: () => { i--; pintar(); } }, "← " + t("tour_anterior")),
        h("div", { class: "fila" },
          x.pest && S.pid && x.k === x.n ? h("button", { onclick: () => { cerrarModal(); S.pestana = x.pest; render(); } }, t("tour_ir")) : null,
          ultimo ? h("button", { class: "primario", onclick: solo ? tutorial : cerrarModal }, solo ? t("tour_volver_temas") : t("tour_fin"))
            : h("button", { class: "primario", onclick: () => { i++; pintar(); } }, t("tour_siguiente") + " →")))], { sinX: true });
  };
  pintar();
}
// (ya no se usa en los menús) Crea el producto de muestra y va a "Crear videos"
async function crearMuestra() {
  modal([h("h2", {}, t("muestra_creando")), h("div", { style: "display:flex;justify-content:center;padding:16px" }, rueda(56))], { fijo: true });
  try {
    const r = await api("POST", "/api/muestra");
    await refrescarProductos(); S.pid = r.id; S.pestana = "generar"; S.vista = null; cerrarModal(); render();
  } catch (e) { cerrarModal(); }
}

// ---------------------------------------------------------------- inicio
const selP = { modo: false, sel: new Set() };   // selección múltiple de productos
const fProd = { q: "", filtro: "", orden: "az" };   // búsqueda, filtro y orden de "Mis productos" (se recuerdan mientras la app está abierta)
const FILTROS_PROD = [["", "fp_todos"], ["videos", "fp_con_videos"], ["sin_videos", "fp_sin_videos"], ["sin_guiones", "fp_sin_guiones"], ["sin_clips", "fp_sin_clips"]];
const ORDENES_PROD = [["az", "op_az"], ["za", "op_za"], ["videos", "op_videos"], ["clips", "op_clips"], ["guiones", "op_guiones"]];
function productosVisibles() {
  const q = fProd.q.trim().toLowerCase();
  const ok = p => (!q || p.nombre.toLowerCase().includes(q)) && (fProd.filtro === "" || (fProd.filtro === "videos" ? p.videos > 0 : fProd.filtro === "sin_videos" ? p.videos === 0 : fProd.filtro === "sin_guiones" ? p.guiones === 0 : p.clips === 0));
  const cmp = { az: (a, b) => a.nombre.localeCompare(b.nombre), za: (a, b) => b.nombre.localeCompare(a.nombre), videos: (a, b) => b.videos - a.videos, clips: (a, b) => b.clips - a.clips, guiones: (a, b) => b.guiones - a.guiones }[fProd.orden];
  return S.productos.filter(ok).sort(cmp);
}
async function borrarProductos(lista) {
  let n = 0;
  for (const p of lista) { try { await api("DELETE", `/api/productos/${p.id}`); n++; } catch (e) {} }
  selP.modo = false; selP.sel.clear(); await refrescarProductos(); toast(t("pr_borrados", { n })); inicio();
}
async function verBorrados() {
  let l = []; try { l = await api("GET", "/api/proyectos_borrados"); } catch (e) {}
  modal([h("h2", {}, "♻ " + t("pb_titulo")), h("p", { class: "suave chico" }, t("pb_ay")),
    ...(l.length ? l.map(p => h("div", { style: "display:flex;gap:8px;align-items:center;margin:6px 0" },
      h("span", { style: "flex:1" }, p.nombre, h("span", { class: "suave chico" }, "  · " + t("pb_dias", { n: p.dias }))),
      h("button", { class: "chico", onclick: async () => { try { await api("POST", "/api/proyectos_borrados/recuperar", { clave: p.clave }); await refrescarProductos(); cerrarModal(); toast(t("pb_ok")); inicio(); } catch (e) { toast(e.message || String(e), false); } } }, t("pb_rec"))))
      : [h("p", {}, t("pb_nada"))]),
    h("div", { class: "acciones" }, h("button", { onclick: cerrarModal }, t("cerrar")))]);
}
function inicio() {
  const app = $("#app"); app.innerHTML = "";
  app.append(h("h1", {}, t("mis_productos")), h("p", { class: "suave" }, t("inicio_elige")), h("button", { class: "chico", style: "margin-bottom:8px", onclick: verBorrados }, "♻ " + t("pb_btn")), " ", h("button", { class: "chico", style: "margin-bottom:8px", onclick: referencias }, "🎯 " + t("ref_btn")));
  // siempre a la vista: video de prueba / tutorial paso a paso (por si lo quieren hacer o se les olvidó)
  app.append(h("div", { class: "banner-practica" },
    h("button", { class: "primario btn-practica-inicio", onclick: iniciarPractica }, t("ini_practica")),
    h("span", { class: "suave chico" }, t("ini_practica_d"))));
  const g = h("div", { class: "rejilla" });
  const info = h("span", { class: "suave chico" });
  const btnBorrar = h("button", { class: "chico peligro btn-borrar-productos", hidden: !selP.modo, onclick: async () => {
    const lista = S.productos.filter(p => selP.sel.has(p.id));
    if (!lista.length) return;
    if (!await confirmar(t("pr_sel_conf", { n: lista.length }), t("borrar"))) return;
    await borrarProductos(lista); } });
  const contar = () => { btnBorrar.textContent = t("pr_sel_borrar", { n: selP.sel.size }); btnBorrar.disabled = !selP.sel.size; };
  // solo se vuelve a dibujar la rejilla (así el cuadro de búsqueda no pierde el cursor al escribir)
  const pintarRejilla = () => {
    g.innerHTML = "";
    const vis = productosVisibles();
    vis.forEach(p => {
      const nodo = h("div", { class: "tarjeta producto" + (selP.sel.has(p.id) ? " sel" : ""), onclick: () => {
        if (!selP.modo) { S.pid = p.id; S.pestana = "generar"; render(); return; }
        selP.sel.has(p.id) ? selP.sel.delete(p.id) : selP.sel.add(p.id);
        nodo.classList.toggle("sel", selP.sel.has(p.id)); contar(); } },
        h("b", {}, p.nombre),
        h("div", { class: "cifras" }, h("span", {}, `${p.guiones} ${t("guiones")}`), h("span", {}, `${p.clips} ${t("clips")}`), h("span", {}, `${p.videos} ${t("videos")}`)),
        selP.modo ? null : h("button", { class: "chico peligro btn-borrar-prod-uno", title: t("borrar"), style: "position:absolute;right:10px;bottom:10px;padding:2px 8px", onclick: async e => {
          e.stopPropagation();
          if (!await confirmar(t("conf_borrar_prod", { n: p.nombre }), t("borrar"))) return;
          await api("DELETE", `/api/productos/${p.id}`); selP.sel.delete(p.id); await refrescarProductos(); toast(t("pr_borrados", { n: 1 })); inicio(); } }, "🗑"));
      g.append(nodo);
    });
    if (!vis.length && S.productos.length) g.append(h("div", { class: "vacio chico", style: "grid-column:1/-1" }, t("bus_nada")));
    if (!selP.modo && !fProd.q.trim() && fProd.filtro === "") g.append(h("div", { class: "tarjeta nuevo", style: "cursor:pointer", onclick: nuevoProducto }, t("nuevo_producto")));
    info.textContent = (fProd.q.trim() || fProd.filtro) ? t("bus_res", { n: vis.length, m: S.productos.length }) : "";
    contar();
  };
  if (S.productos.length) {
    const buscar = h("input", { type: "text", class: "inp-buscar-prod", value: fProd.q, placeholder: "🔍 " + t("bus_ph"), style: "flex:1;min-width:150px;max-width:300px", oninput: e => { fProd.q = e.target.value; pintarRejilla(); } });
    const selFiltro = h("select", { class: "sel-filtro-prod", style: "width:auto", title: t("fp_titulo"), onchange: e => { fProd.filtro = e.target.value; pintarRejilla(); } },
      FILTROS_PROD.map(([v, k]) => h("option", { value: v, selected: fProd.filtro === v }, t(k))));
    const selOrden = h("select", { class: "sel-orden-prod", style: "width:auto", title: t("op_titulo"), onchange: e => { fProd.orden = e.target.value; pintarRejilla(); } },
      ORDENES_PROD.map(([v, k]) => h("option", { value: v, selected: fProd.orden === v }, t(k))));
    app.append(h("div", { class: "fila", style: "margin:8px 0" }, buscar, selFiltro, selOrden, info),
      h("div", { class: "fila", style: "margin:8px 0" },
        h("button", { class: "chico", onclick: () => { selP.modo = !selP.modo; selP.sel.clear(); inicio(); } }, selP.modo ? t("sel_cancelar") : "☑ " + t("pr_sel_modo")),
        h("button", { class: "chico", hidden: !selP.modo, onclick: () => { productosVisibles().forEach(p => selP.sel.add(p.id)); inicio(); } }, t("pr_sel_todos")),
        h("button", { class: "chico", hidden: !selP.modo, onclick: () => { selP.sel.clear(); inicio(); } }, t("sel_ninguno")),
        btnBorrar));
  }
  app.append(g);
  pintarRejilla();
  if (!S.productos.length) app.append(h("div", { class: "vacio" }, t("prod_vacio")));
  app.append(h("p", { class: "chico suave", style: "margin-top:30px" }, t("recordatorio")));
}
async function nuevoProducto() {
  if (!(typeof G !== "undefined" && G.activa) && typeof elegirCaminoNuevo === "function") { if (!await elegirCaminoNuevo()) return; }      // lo primero: ¿qué quieres hacer?
  const r = await pedirTexto(t("nuevo_producto").replace("+ ", ""), t("nombre_producto"));
  if (!r) return;
  const practica = typeof G !== "undefined" && G.activa && G.i === 1;      // creado dentro de la práctica guiada: no cuenta en el límite del plan
  const { id } = await api("POST", "/api/productos", { nombre: r.valor, practica });
  await refrescarProductos(); if (S.camino0 && !practica) { S.caminos[id] = S.camino0; api("POST", "/api/config", { caminos: S.caminos }).catch(() => {}); } S.pid = id; S.pestana = "guiones"; render();
}

// ---------------------------------------------------------------- producto
// Dibuja una pestaña completa en un contenedor aparte y la pone al final: si dos cargas se cruzan, gana la última.
async function montar(c, fn) {
  const mi = c._v = (c._v || 0) + 1;
  const out = h("div", {});
  if (!c.children.length) c.append(h("div", { class: "cargando-pag" }, rueda(56)));
  await fn(out, () => montar(c, fn));
  if (c._v === mi) c.replaceChildren(out);
}
const PESTANAS = ["guiones", "escenas", "clips", "musica", "hablando", "capas", "estilo", "generar", "videos", "papelera"];
const T_PEST = { generar: "t_generar", escenas: "t_escenas", guiones: "t_guiones", clips: "t_clips", kit: "t_kit", musica: "t_musica", hablando: "t_hablando", capas: "t_capas", estilo: "t_estilo", videos: "t_videos", papelera: "t_papelera" };
// Pestañas principales, en este orden; cada una agrupa las páginas internas que le tocan.
const GRUPOS = [["guiones", ["guiones", "escenas"], "t_guion"], ["musica", ["clips", "musica"], "t_multimedia"], ["estilo", ["estilo", "capas"], "t_estilodis"], ["generar", ["generar"], "t_generar"], ["videos", ["videos", "papelera"], "t_carpeta"]];
function producto() {
  if (S.pestana === "hablando") S.pestana = "clips";   // «Mis videos en cámara» ya no es una pestaña aparte: está dentro de «Clips y palabras clave»
  if (S.pestana === "kit") { S.pestana = "clips"; S.abiertos = S.abiertos || {}; S.abiertos[S.pid + ":sel"] = "kit"; }
  const app = $("#app"); app.innerHTML = "";
  const p = prod();
  if (!p) { irInicio(); return; }
  app.append(
    h("div", { class: "fila" },
      h("button", { class: "link", onclick: irInicio }, t("volver")), h("div", { class: "espacio" }),
      h("button", { onclick: async () => { const r = await pedirTexto(t("duplicar_titulo"), t("nombre_copia"), p.nombre + " 2", t("con_material")); if (!r) return; const { id } = await api("POST", "/api/productos", { nombre: r.valor, copiar_de: p.id, con_material: r.extra }); await refrescarProductos(); S.pid = id; S.pestana = "estilo"; render(); } }, t("duplicar")),
      h("button", { onclick: async () => { const r = await pedirTexto(t("renombrar"), t("nombre_producto"), p.nombre); if (!r) return; await api("POST", `${base()}/renombrar`, { nombre: r.valor }); await refrescarProductos(); render(); } }, t("renombrar")),
      h("button", { class: "peligro", onclick: async () => { if (!await confirmar(t("conf_borrar_prod", { n: p.nombre }))) return; await api("DELETE", base()); await refrescarProductos(); irInicio(); } }, t("borrar"))),
    h("h1", {}, p.nombre), cmBarra(),
    h("div", { class: "pestanas" }, gruposVisibles().map(([k, ps, tt]) => h("button", { "data-g": k, class: ps.includes(S.pestana) ? "on" : "", onclick: () => { if (!ps.includes(S.pestana)) S.pestana = ps[0]; guardarSesion(); producto(); barra(); } }, t(tt))), cmBotonMas()),
    (() => { const g = gruposVisibles().find(x => x[1].includes(S.pestana)); return g && g[1].length > 1 ? h("div", { class: "pestanas sub" }, g[1].map(k => h("button", { "data-p": k, class: S.pestana === k ? "on" : "", onclick: () => { S.pestana = k; guardarSesion(); producto(); barra(); } }, k === "papelera" ? "🗑 " + t(T_PEST[k]) + (prod().papelera ? ` (${prod().papelera})` : "") : k === "hablando" ? "🎞 " + t(T_PEST[k]) : t(T_PEST[k])))) : document.createTextNode(""); })(),
    h("div", { id: "contenido" }));
  cmOfrecer();
  const c = $("#contenido");
  const P = { generar: pGenerar, escenas: pEscenas, guiones: pGuiones, clips: pClips, kit: pKit, musica: pMusica, capas: pCapas, estilo: pEstilo, hablando: pHablando, videos: pVideos, papelera: pPapelera }[S.pestana];
  montar(c, P);
}

// ---------------------------------------------------------------- generar
let sondeo = null;
async function pGenerar(c, recG) {
  const p = prod();
  const aj = await api("GET", `${base()}/ajustes`);
  const guiones = (p.guiones || p.hablando) ? (await api("GET", `${base()}/guiones?generar=1`)).filter(g => g.activo) : [];
  const SIN = "__sin_guion__";
  const PB = await api("GET", `${base()}/peso_base`).catch(() => ({ k: 0.12, n: 0 }));
  const plsEsc = ((await api("GET", `${base()}/escenas`).catch(() => ({ plantillas: [] }))).plantillas || []).filter(x => x.escenas.length);
  const selG = h("select", { style: "max-width:300px" }, guiones.length ? h("option", { value: "" }, t("gen_auto")) : null, guiones.map(g => h("option", { value: g.nombre }, (g.hablando ? "🎞 " : "") + g.nombre.replace(/\.[^.]+$/, ""))), plsEsc.map(x => h("option", { value: "__esc__:" + x.id }, "🎬 " + x.nombre + " (" + t("esc_tag") + ")")), h("option", { value: SIN }, t("gen_sin_guion")));
  const esEsc = () => selG.value.startsWith("__esc__:");
  const plSel = () => plsEsc.find(x => "__esc__:" + x.id === selG.value);
  if (!guiones.length) selG.value = plsEsc.length ? "__esc__:" + plsEsc[0].id : SIN;   // sin guiones: el modo "sin guion" es el unico y ya viene elegido
  const inpSeg = h("input", { type: "number", min: 5, max: 600, value: 30, style: "width:100px" });
  const inpTit = h("input", { type: "text", placeholder: t("sg_titulo_ph"), style: "max-width:300px;width:100%" });
  const cajaSG = h("div", { class: "tarjeta", style: "margin:6px 0 10px" }, h("div", { class: "chico suave", style: "margin-bottom:8px" }, t("gen_sin_guion_ayuda")),
    h("div", { class: "fila", style: "margin:6px 0" }, h("label", {}, t("sg_segundos")), inpSeg), h("div", { class: "fila", style: "margin:6px 0" }, h("label", {}, t("sg_titulo")), inpTit));
  const selPV = h("select", { style: "max-width:300px" }, h("option", { value: "" }, t("gen_esc_auto")), plsEsc.map(x => h("option", { value: x.id }, "🎬 " + x.nombre)));
  const filaPV = h("div", { class: "fila", style: "margin:6px 0" }, h("label", {}, t("gen_esc_voz")), selPV);
  const verPV = () => { filaPV.hidden = !plsEsc.length || selG.value === SIN || esEsc(); };
  selG.addEventListener("change", verPV); verPV();
  const verSG = () => { cajaSG.hidden = selG.value !== SIN; };
  selG.addEventListener("change", verSG); verSG();
  // formatos: todos se pueden marcar o desmarcar; el de Estilo solo viene marcado como sugerencia
  const oF = S.cat.ajustes.find(a => a.clave === "formato_video").opciones;
  const guardados = String(aj.formatos_crear || "").split(",").filter(Boolean);
  const P = (await cargarPlan()) || { limites: {}, videos_restantes: null };
  const sel = new Set(guardados.length ? guardados : [aj.formato_video]);
  if (!(P.limites || {}).multiformato && sel.size > 1) [...sel].slice(1).forEach(x => sel.delete(x));   // el plan crea un formato a la vez
  // tamaño propio: el que está guardado en Estilo > Avanzado (ancho × alto); si es el de un formato normal, se propone 1200 × 800
  const estandar = [[1080, 1920], [1080, 1350], [1080, 1080], [1920, 1080]];
  const esEst = (w, h) => estandar.some(m => m[0] === w && m[1] === h);
  let w0 = Math.round(+aj.ancho) || 1200, h0 = Math.round(+aj.alto) || 800;
  if (aj.formato_video !== "personalizado" && esEst(w0, h0)) { w0 = 1200; h0 = 800; }
  const inpW = h("input", { type: "number", min: 240, max: 4320, step: 2, value: w0, style: "width:86px", "aria-label": t("gen_ancho") });
  const inpH = h("input", { type: "number", min: 240, max: 4320, step: 2, value: h0, style: "width:86px", "aria-label": t("gen_alto") });
  const tamano = () => ({ ancho: Math.max(240, Math.min(4320, Math.round(+inpW.value || 1200))), alto: Math.max(240, Math.min(4320, Math.round(+inpH.value || 800))) });
  const guardarSel = () => api("PUT", `${base()}/ajustes`, { valores: { formatos_crear: oF.map(x => x[0]).filter(x => sel.has(x)).join(",") } });
  let tmPrev = null;
  const cajaPrev = h("div", { class: "previas-fmt" });
  const urlsPrev = {};
  const pintarPrevias = () => {
    clearTimeout(tmPrev);
    tmPrev = setTimeout(async () => {
      const orden = oF.map(x => x[0]).filter(x => sel.has(x));
      cajaPrev.hidden = !orden.length;
      const tz = tamano();
      const figs = orden.map(f => {
        const o = oF.find(x => x[0] === f), nombre = (S.idioma === "en" ? o[2] : o[1]).replace(/\s*\(.*$/, "");
        const dim = f === "personalizado" ? `${tz.ancho}×${tz.alto}` : ((/\((\d+×\d+)\)/.exec(o[1]) || [])[1] || "");
        const img = h("img", { alt: nombre, class: "previa-fmt-img" });
        return { f, el: h("figure", { class: "previa-fmt" }, h("div", { class: "previa-fmt-caja" }, img), h("figcaption", {}, h("b", {}, nombre), dim ? h("div", { class: "chico suave" }, dim) : null)), img };
      });
      cajaPrev.replaceChildren(...figs.map(x => x.el));
      figs.forEach(async x => {
        try {
          const r = await fetch(`${base()}/previa_formato`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ formato: x.f, tamano: tz }) });
          if (!r.ok) return;
          const u = URL.createObjectURL(await r.blob());
          if (urlsPrev[x.f]) URL.revokeObjectURL(urlsPrev[x.f]);
          urlsPrev[x.f] = u; x.img.src = u;
        } catch (e) {}
      });
    }, 250);
  };
  const multiOk = () => !!((P.limites || {}).multiformato || (usaCr() && (P.limites_pro || {}).multiformato));
  const cajasF = h("div", { class: "checks" }, oF.map(o => {
    const sugerido = aj.formato_video === o[0], pers = o[0] === "personalizado";
    return h("label", {}, h("input", { type: "checkbox", checked: sel.has(o[0]),
      onchange: async e => {
        if (e.target.checked && sel.size >= 1 && !multiOk()) { e.target.checked = false; toast(t("pp_solo_uno"), true); return; }
        e.target.checked ? sel.add(o[0]) : sel.delete(o[0]); resumenGen(); pintarPrevias(); await guardarSel(); } }),
      " " + (pers ? t("gen_personalizado") : (S.idioma === "en" ? o[2] : o[1])) + (sugerido ? " ★" : ""),
      pers ? h("span", { style: "margin-left:8px;white-space:nowrap" }, inpW, " × ", inpH, " px") : null);
  }));
  const cambioTam = () => { if (!sel.has("personalizado")) { sel.add("personalizado"); const c = cajasF.querySelectorAll("input[type=checkbox]"); c[oF.findIndex(x => x[0] === "personalizado")].checked = true; resumenGen(); guardarSel(); } pintarPrevias(); clearTimeout(cambioTam.t); cambioTam.t = setTimeout(() => { const z = tamano(); if (z.ancho >= 360 && z.ancho <= 2160 && z.alto >= 640 && z.alto <= 3840) fetch(`${base()}/ajustes`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ valores: { ancho: z.ancho, alto: z.alto } }) }).catch(() => {}); }, 600); };
  inpW.addEventListener("input", cambioTam); inpH.addEventListener("input", cambioTam);
  inpW.addEventListener("click", e => e.stopPropagation()); inpH.addEventListener("click", e => e.stopPropagation());
  pintarPrevias();
  const infoAuto = h("div", { class: "chico", style: "margin:-4px 0 8px" });
  const verAuto = () => {
    infoAuto.textContent = !selG.value && selG.value !== SIN && p.guion_siguiente
      ? t("gen_auto_usa", { a: p.guion_siguiente }) + (p.guion_despues ? " " + t("gen_auto_luego", { b: p.guion_despues }) : "") : "";
  };
  selG.addEventListener("change", verAuto); verAuto();
  const creds = P.creditos || 0, agotado = P.videos_restantes != null && P.videos_restantes <= 0;
  const chkCr = h("input", { type: "checkbox", checked: agotado && creds > 0, onchange: () => { pintarCal(); resumenGen(); } });
  const usaCr = () => chkCr.checked;
  const selC = h("select", { style: "max-width:240px", onchange: async e => { await api("PUT", `${base()}/ajustes`, { valores: { calidad: e.target.value } }); } });
  const oC = S.cat.ajustes.find(a => a.clave === "calidad").opciones;
  const pintarCal = () => {
    const maxCal = usaCr() ? (P.limites_pro || {}).calidad || 2160 : P.limites.calidad || 2160;
    const actual = selC.value || String(aj.calidad || 1080);
    selC.innerHTML = "";
    oC.forEach(o => selC.append(h("option", { value: o[0], disabled: +o[0] > maxCal, selected: String(Math.min(+actual, maxCal)) === o[0] },
      (S.idioma === "en" ? o[2] : o[1]) + (+o[0] > maxCal ? " " + t("cal_bloq") : ""))));
  };
  pintarCal();
  const infoPlan = [P.videos_restantes != null ? t("gen_quedan", { n: P.videos_restantes }) : t("gen_quedan_sin", { p: P.nombre }),
    P.limites.duracion ? t("gen_dur_max", { d: fmtSeg(P.limites.duracion) }) : ""].filter(Boolean).join(" ");
  const faltas = [];
  if (!p.clips && !p.hablando) faltas.push(h("li", {}, h("button", { class: "link", onclick: () => { S.pestana = "clips"; producto(); } }, t("falta_clips"))));
  const cant = h("input", { type: "number", min: 1, max: 50, value: 1, style: "width:100px" });
  const caja = h("div", { id: "progreso" });
  // aviso: cuántos archivos de video se van a entregar (videos × formatos)
  const resumen = h("div", { class: "resumen-gen" });
  const resumenGen = () => {
    const n = Math.max(1, Math.min(1000, Math.floor(+cant.value) || 1)), f = sel.size;
    const nombres = oF.filter(o => sel.has(o[0])).map(o => (S.idioma === "en" ? o[2] : o[1]).replace(/\s*\(.*$/, ""));
    resumen.className = "resumen-gen" + (f ? "" : " vacio");
    resumen.textContent = "";
    resumen.textContent = f ? t("gen_resumen", { n: n * f, v: n, f, lista: nombres.join(", ") }) : t("gen_resumen_0");
    if (f && usaCr()) resumen.textContent += " " + (n * f > creds ? t("cr_faltan", { n: n * f, t: creds }) : t("cr_gastan", { n: n * f }));
    const tope = (usaCr() ? (P.limites_pro || {}).tanda : (P.limites || {}).tanda) || 50;
    if (f && n * f > tope) resumen.append(h("div", { class: "aviso", style: "margin-top:6px" }, t("gen_tanda_max", { m: tope, n: n * f })));
    else if (f) { let sa = 0; try { sa = +localStorage.getItem("vib_seg_archivo") || 0; } catch (e) {} if (sa) { const mins = Math.max(1, Math.round(sa * n * f / 60)); resumen.append(h("div", { class: "chico suave", style: "margin-top:4px" }, "⏱ " + t("gen_tiempo", { m: mins }))); } }
    // peso aproximado: duración × megapíxeles × lo que pesaron tus videos anteriores
    let durs = esEsc() ? [plSel().duracion] : selG.value === SIN ? [Math.max(5, Math.min(600, +inpSeg.value || 30))] : selG.value ? [guiones.find(g => g.nombre === selG.value)?.duracion] : guiones.map(g => g.duracion);
    durs = durs.filter(x => x > 0);
    if (f && durs.length) {
      const esc = (+selC.value || 1080) / 1080, dim = o => { if (o === "personalizado") { const m = tamano(); return m.ancho * m.alto; } const mm = (oF.find(x => x[0] === o)[1].match(/(\d+)×(\d+)/) || []); return (+mm[1] || 1080) * (+mm[2] || 1920); };
      const por = (d) => [...sel].reduce((a, o) => a + (dim(o) * esc * esc / 1e6 * PB.k + 0.024) * d, 0);
      const mn = Math.min(...durs), mx = Math.max(...durs), fmt = v => v >= 1000 ? (v / 1000).toFixed(1) + " GB" : (v < 10 ? v.toFixed(1) : Math.round(v)) + " MB";
      const uno = por(mn) * n, dos = por(mx) * n;
      resumen.append(h("div", { class: "chico suave", style: "margin-top:4px" }, "💾 " + t("gen_peso", { p: Math.abs(dos - uno) < uno * 0.1 ? fmt(uno) : fmt(uno) + " – " + fmt(dos) }) + (PB.n ? "" : " " + t("gen_peso_t"))));
    }
  };
  cant.addEventListener("input", resumenGen); selG.addEventListener("change", resumenGen); inpSeg.addEventListener("input", resumenGen); selC.addEventListener("change", resumenGen); resumenGen();
  c.append(h("div", { class: "tarjeta" },
    h("h2", {}, t("gen_titulo")),
    h("p", { class: "suave" }, `${t("gen_siguiente")} ${String(p.siguiente).padStart(3, "0")}`),
    p.id === "muestra" ? h("div", { class: "aviso" }, t("muestra_banner")) : null,
    faltas.length ? h("div", { class: "aviso" }, t("gen_faltan"), h("ul", {}, faltas)) : null,
    h("div", { style: "margin:14px 0 6px" }, h("b", {}, t("gen_formatos")), h("div", { class: "chico suave", style: "margin:2px 0 6px" }, t("gen_formatos_ayuda")), cajasF, cajaPrev),
    (creds > 0 || agotado) ? h("div", { class: agotado ? "aviso" : "", style: "margin:10px 0" },
      agotado ? h("div", { style: "margin-bottom:6px" }, t("cr_agotado")) : null,
      creds > 0 ? h("label", { class: "fila", style: "gap:8px;align-items:center" }, chkCr, h("b", {}, "🎟 " + t("cr_usar")), h("span", { class: "suave" }, "· " + t("cr_tienes", { n: creds })))
        : h("div", {}, t("cr_sin") + " ", h("button", { class: "link", onclick: miPlan }, t("cr_canjear")), P.compra_creditos ? [" · ", h("a", { href: P.compra_creditos, target: "_blank" }, t("cr_comprar_link"))] : null),
      creds > 0 ? h("div", { class: "chico suave", style: "margin-top:4px" }, t("cr_usar_ayuda")) : null) : null,
    h("div", { class: "fila", style: "margin:10px 0" }, h("label", {}, t("cal_lbl")), selC),
    h("div", { class: "chico suave", style: "margin-bottom:6px" }, t("cal_ayuda")),
    h("div", { class: "fila", style: "margin:10px 0" }, h("label", {}, t("gen_guion")), selG), filaPV,
    infoAuto, cajaSG,
    h("div", { class: "chico suave", style: "margin-bottom:10px" }, t("gen_guion_ayuda")),
    h("div", { class: "fila barra-crear" }, h("label", {}, t("gen_cuantos")), cant,
      h("button", { class: "primario grande", disabled: !!faltas.length, onclick: async () => {
        if (!sel.size) { modal([h("h2", {}, t("gen_elige_fmt_t")), h("p", {}, t("gen_elige_fmt")), h("div", { class: "acciones" }, h("button", { class: "primario", onclick: cerrarModal }, t("cerrar_modal")))]); return; }
        const sg = esEsc() ? { plantilla: plSel().id, titulo: "" } : selG.value === SIN ? { segundos: Math.max(5, Math.min(600, +inpSeg.value || 30)), titulo: inpTit.value.trim() } : null;
        window.__gen = { t0: Date.now(), archivos: Math.max(1, Math.floor(+cant.value) || 1) * sel.size };
        try { await api("POST", "/api/generar", { producto: S.pid, cantidad: +cant.value || 1, guion: sg ? "" : selG.value, sin_guion: sg, formatos: [...sel], tamano: sel.has("personalizado") ? tamano() : null, usar_creditos: usaCr(), plantilla_voz: !sg && selPV.value ? selPV.value : "" }); } catch (e) { return; }
        sondear(); } }, t("gen_boton"))),
    h("p", { class: "chico suave" }, t("recordatorio"))),
    h("details", { class: "mas-opciones" }, h("summary", {}, t("mas_opciones")),
      h("div", { class: "tarjeta", style: "margin-top:8px" },
        h("h3", { style: "margin-top:0" }, t("reiniciar")), h("p", { class: "suave chico" }, t("reiniciar_txt")),
        h("button", { onclick: async () => { if (!await confirmar(t("reiniciar_conf"), t("reiniciar"))) return; await api("POST", `${base()}/reiniciar`); await refrescarProductos(); producto(); } }, t("reiniciar")))));
  const tarj = c.querySelector(".barra-crear")?.closest(".tarjeta");      // el avance se ve a la derecha del generador (en pantallas angostas queda abajo)
  if (tarj) {      // a la derecha: el botón de crear videos, el resumen y el avance con la rueda del logo (siempre a la vista)
    const grid = h("div", { class: "gen-grid" }), barra = tarj.querySelector(".barra-crear");
    tarj.replaceWith(grid);
    grid.append(tarj, h("div", { class: "gen-der" }, h("div", { class: "gen-panel" }, h("h3", { style: "margin:0 0 8px" }, "🎬 " + t("gen_boton")), barra, resumen, h("div", { class: "chico suave", style: "margin-top:6px" }, infoPlan)), caja));
  }
  const ult = h("div", {});
  c.append(h("h3", { style: "margin-top:26px" }, "🎬 " + t("gen_ultimos")), ult,
    h("div", { class: "fila", style: "margin-top:10px" }, h("button", { class: "chico", onclick: () => { S.pestana = "videos"; producto(); } }, t("gen_ver_todos"))));
  pVideos(ult, () => recG && recG(), 6).catch(() => {});
  sondear(true);
}
async function sondear(unaVez) {
  clearInterval(sondeo);
  const paso = async () => {
    const e = await fetch("/api/generar/estado").then(r => r.json());
    const caja = $("#progreso");
    if (!caja) { clearInterval(sondeo); return; }
    caja.innerHTML = "";
    if (!e.activo && !e.terminado) { clearInterval(sondeo); return; }
    const vid = Math.min(e.hechos + 1, e.total), esc = e.escena;
    let frac = e.total ? (e.hechos + (esc[1] ? Math.min(esc[0] / esc[1], .98) : 0)) / e.total : 0;
    if (e.terminado && !e.error && !e.cancelado) frac = 1;
    caja.append(h("div", {},
      e.activo ? h("div", { class: "fila", style: "gap:12px;align-items:center" }, rueda(40), h("div", {}, h("b", {}, t("gen_video_de", { a: vid, b: e.total }) + (esc[1] ? " · " + t("gen_escena", { a: esc[0], b: esc[1] }) : "")),
        h("div", { class: "suave chico" }, t("gen_trabajando")))) : null,
      h("div", { class: "barra" }, h("div", { style: `width:${Math.round(frac * 100)}%` })),
      e.activo ? h("button", { onclick: () => api("POST", "/api/generar/cancelar") }, t("gen_detener")) : null,
      e.error ? h("div", { class: "aviso", style: "background:#fde4e4;color:#8a1f1f" + (e.codigo ? ";cursor:pointer" : ""), onclick: e.codigo ? () => detalleError({ error: e.error, codigo: e.codigo, paso: e.paso, paso_en: e.paso_en }) : null },
        e.error, e.codigo ? h("div", { class: "chico", style: "margin-top:4px" }, t("err_codigo") + ": " + e.codigo + " · " + t("err_click")) : null) : null,
      e.cancelado ? h("div", { class: "aviso" }, t("gen_detenido")) : null,
      e.terminado && !e.error && !e.cancelado ? h("div", {}, h("b", {}, t("gen_listo")), " ", h("button", { class: "primario", onclick: () => { S.pestana = "videos"; producto(); } }, t("gen_ver"))) : null,
      e.error ? h("details", {}, h("summary", { class: "chico suave" }, t("gen_detalles")), h("div", { class: "log" }, e.log.join("\n"))) : null));
    if (!e.activo) {
      clearInterval(sondeo);
      if (window.__gen && e.terminado && !e.error && !e.cancelado) { try { localStorage.setItem("vib_seg_archivo", String(Math.round((Date.now() - window.__gen.t0) / 1000 / window.__gen.archivos))); } catch (x) {} }
      window.__gen = null;
      await refrescarProductos();
    }
  };
  await paso();
  if (!unaVez || true) sondeo = setInterval(paso, 1000);
}

// ---------------------------------------------------------------- guiones
let guionSel = null;
// lo que dice el audio de un guion (sin título, sin marcas de burbuja y sin las burbujas que no se dicen): sirve para leerlo al grabar
function textoHablado(txt) {
  return String(txt || "").split(/\r?\n/).filter(l => !l.trim().startsWith("#")).join(" ")
    .replace(/\{[^}]*\}/g, " ").replace(/\(\s*[*/]\s*\d{1,2}\s*\)/g, " ").replace(/(?<![\w/*])[*/]\d{1,2}(?![\w/*])/g, " ")
    .replace(/[«»]/g, "").replace(/\bCliente:\s*/gi, "").replace(/\s+/g, " ").trim();
}
// "Grabar mi voz": graba con el micrófono mientras lees el texto y lo guarda como el audio del guion
function grabadora(actual, getTexto, guardarTodo, recargar) {
  const tiene = actual.tiene_audio !== false;
  let mr = null, flujo = null, trozos = [], blob = null, t0 = 0, reloj = null;
  const leer = h("div", { class: "leer-guion", style: "font-size:1.2em;line-height:1.65;padding:14px 16px;border-radius:12px;background:var(--papel-2,rgba(127,127,127,.12));max-height:260px;overflow:auto;white-space:pre-wrap" });
  const tiempo = h("span", { class: "chico suave", style: "min-width:44px" }, "0:00");
  const msg = h("div", { class: "chico", style: "margin-top:8px" });
  const player = h("audio", { controls: true, style: "width:100%;display:none;margin-top:10px" });
  const btnRec = h("button", { class: "primario btn-grabar" }, "● " + t("gr_grabar"));
  const btnUsar = h("button", { class: "primario btn-usar-grab", disabled: true }, "✓ " + t("gr_usar"));
  const fmt = ms => { const sg = Math.floor(ms / 1000); return Math.floor(sg / 60) + ":" + String(sg % 60).padStart(2, "0"); };
  const pintarTexto = () => { leer.textContent = textoHablado(getTexto()) || t("gr_sin_texto"); };
  const parar = () => { clearInterval(reloj); if (mr && mr.state === "recording") mr.stop(); else if (flujo) flujo.getTracks().forEach(x => x.stop()); };
  const alternar = async () => {
    if (mr && mr.state === "recording") { parar(); return; }
    msg.textContent = ""; msg.style.color = "";
    if (!navigator.mediaDevices || !window.MediaRecorder) { msg.style.color = "var(--mal)"; msg.textContent = t("gr_no_soportado"); return; }
    try { flujo = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }); }
    catch (e) { msg.style.color = "var(--mal)"; msg.textContent = t("gr_sin_permiso"); return; }
    const tipo = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"].find(x => MediaRecorder.isTypeSupported(x));
    mr = new MediaRecorder(flujo, tipo ? { mimeType: tipo } : undefined); trozos = []; blob = null;
    mr.ondataavailable = e => { if (e.data && e.data.size) trozos.push(e.data); };
    mr.onstop = () => {
      flujo.getTracks().forEach(x => x.stop());
      blob = new Blob(trozos, { type: mr.mimeType || "audio/webm" });
      player.src = URL.createObjectURL(blob); player.style.display = "";
      btnUsar.disabled = false; btnRec.textContent = "● " + t("gr_repetir"); msg.textContent = "";
    };
    mr.start(); t0 = Date.now(); btnUsar.disabled = true; player.style.display = "none";
    btnRec.textContent = "■ " + t("gr_detener"); msg.textContent = "🔴 " + t("gr_grabando");
    reloj = setInterval(() => { tiempo.textContent = fmt(Date.now() - t0); }, 250);
  };
  btnRec.onclick = alternar;
  btnUsar.onclick = async () => {
    if (!blob) return;
    if (tiene && !await confirmar(t("gr_reemplazar_conf"), t("voz_reemplazar"))) return;
    btnUsar.disabled = true; btnUsar.textContent = "⏳ " + t("voz_generando");
    try {
      await guardarTodo();
      const r = await fetch(`${base()}/guiones/grabacion?nombre=${encodeURIComponent(guionSel)}&reemplazar=${tiene ? 1 : 0}`, { method: "POST", headers: { "Content-Type": blob.type || "application/octet-stream" }, body: blob });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { toast(d.error || "Error " + r.status, true); btnUsar.disabled = false; btnUsar.textContent = "✓ " + t("gr_usar"); return; }
      toast(t("gr_lista")); guionSel = d.nombre; guardarSesion(); await refrescarProductos(); recargar();
    } catch (e) { btnUsar.disabled = false; btnUsar.textContent = "✓ " + t("gr_usar"); }
  };
  return {
    pintar: pintarTexto, detener: parar,
    el: h("div", {}, h("div", { class: "chico suave", style: "margin-bottom:8px" }, t("gr_ayuda")), leer,
      h("div", { class: "fila", style: "margin-top:10px" }, btnRec, tiempo, btnUsar), player, msg),
  };
}
// "Voz del guion": narra el texto con una voz de Windows (gratis) o, en planes de pago, con la cuenta propia de ElevenLabs
function panelVoz(actual, guardarTodo, recargar, getTexto) {
  const tiene = actual.tiene_audio !== false;
  const etqBtn = "🔊 " + t(tiene ? "voz_cambiar" : "voz_generar");
  let motor = "windows", D = null, EL = null;      // D = lo que dice /api/voces; EL = voces y cuota de ElevenLabs
  const rec = grabadora(actual, getTexto || (() => ""), guardarTodo, recargar);
  const cuerpo = h("div", {});
  const vel = h("input", { type: "range", min: -5, max: 5, step: 1, value: 0, style: "width:140px" });
  const velTxt = h("span", { class: "chico suave", style: "min-width:26px" }, "0");
  vel.addEventListener("input", () => { velTxt.textContent = (+vel.value > 0 ? "+" : "") + vel.value; });
  const btn = h("button", { class: "primario btn-generar-voz", disabled: true }, etqBtn);
  const selWin = h("select", { class: "sel-voz-win", style: "max-width:320px" });
  const selEl = h("select", { class: "sel-voz-el", style: "max-width:320px" });
  const msg = h("div", { class: "chico suave", style: "margin-top:6px" });
  const pestanas = h("div", { class: "fila", style: "margin-bottom:8px", role: "tablist" });
  const nVel = () => (+vel.value > 0 ? "+" : "") + vel.value;
  btn.onclick = async () => {
    if (tiene && !await confirmar(t("voz_reemplazar_conf"), t("voz_reemplazar"))) return;
    btn.disabled = true; btn.textContent = "⏳ " + t("voz_generando");
    try {
      await guardarTodo();
      const r = await api("POST", `${base()}/guiones/voz`, { nombre: guionSel, voz: motor === "elevenlabs" ? selEl.value : selWin.value, velocidad: +vel.value, reemplazar: tiene, motor });
      toast(t("voz_lista")); guionSel = r.nombre; guardarSesion(); await refrescarProductos(); recargar();
    } catch (e) { btn.disabled = false; btn.textContent = etqBtn; }
  };
  const cargarEL = async () => {
    try { EL = await api("GET", "/api/elevenlabs/voces"); } catch (e) { EL = null; }
    pintar();
  };
  const conectar = async clave => {
    try { EL = await api("POST", "/api/elevenlabs/clave", { clave }); } catch (e) { return; }
    D.el.conectado = true; D.el.clave_final = clave.slice(-4); toast(t("voz_el_conectada")); pintar();
  };
  const pintar = () => {
    pestanas.innerHTML = "";
    [["grabar", "voz_m_grab"], ["windows", "voz_m_win"], ["elevenlabs", "voz_m_el"]].forEach(([id, k]) => pestanas.append(h("button", { class: "chico " + (motor === id ? "on" : ""), "data-motor": id, onclick: () => { if (motor === "grabar" && id !== "grabar") rec.detener(); motor = id; pintar(); if (id === "elevenlabs" && D && D.el.conectado && !EL) cargarEL(); } }, t(k))));
    cuerpo.innerHTML = ""; msg.textContent = ""; btn.disabled = true;
    if (motor === "grabar") { rec.pintar(); cuerpo.append(rec.el); return; }
    if (!D) { cuerpo.append(h("div", { class: "chico suave" }, t("voz_cargando"))); return; }
    const fila = sel => h("div", { class: "fila", style: "margin-top:8px" }, sel, h("span", { class: "chico suave" }, t("voz_vel")), vel, velTxt, btn);
    if (motor === "windows") {
      cuerpo.append(fila(selWin));
      if (D.error || !D.voces.length) { msg.textContent = D.error || t("voz_ninguna"); }
      else { btn.disabled = false; if (!D.voces.some(v => v.es)) msg.textContent = t("voz_sin_es"); }
      return;
    }
    cuerpo.append(h("div", { class: "aviso chico aviso-el", style: "margin-bottom:8px" }, t("voz_el_aviso", { m: S.marca })));
    if (!D.el.permitido) {
      cuerpo.append(h("div", { class: "fila" }, h("span", {}, t("voz_el_bloqueado")), h("button", { class: "chico", onclick: () => { cerrarModal(); miPlan(); } }, t("voz_el_ver_planes"))));
      return;
    }
    if (!D.el.conectado) {
      const inp = h("input", { type: "password", class: "inp-clave-el", placeholder: t("voz_el_clave_ph"), autocomplete: "off", style: "flex:1;min-width:220px" });
      cuerpo.append(h("div", { class: "fila" }, inp, h("button", { class: "primario btn-conectar-el", onclick: () => conectar(inp.value.trim()) }, t("voz_el_conectar"))),
        h("div", { class: "chico suave", style: "margin-top:6px" }, t("voz_el_ayuda")));
      return;
    }
    const cuota = EL && EL.cuota && EL.cuota.limite ? " · " + t("voz_el_cuota", { a: EL.cuota.usados, b: EL.cuota.limite }) : "";
    cuerpo.append(h("div", { class: "chico suave", style: "margin-bottom:4px" }, t("voz_el_ok", { f: D.el.clave_final }) + cuota + " ",
      h("button", { class: "link chico", onclick: async () => { await api("DELETE", "/api/elevenlabs/clave"); D.el.conectado = false; D.el.clave_final = ""; EL = null; toast(t("voz_el_desconectada")); pintar(); } }, t("voz_el_desconectar"))));
    if (!EL) { cuerpo.append(h("div", { class: "chico suave" }, t("voz_cargando"))); return; }
    selEl.innerHTML = "";
    const hay = EL.voces.some(v => v.id === D.el_id);
    EL.voces.forEach((v, k) => selEl.append(h("option", { value: v.id, selected: hay ? v.id === D.el_id : k === 0 }, v.nombre + (v.categoria && v.categoria !== "premade" ? " ⭐ " + t("voz_el_tuya") : ""))));
    cuerpo.append(fila(selEl));
    if (!EL.voces.length) msg.textContent = t("voz_ninguna"); else btn.disabled = false;
  };
  (async () => {
    try { D = await api("GET", "/api/voces"); } catch (e) { return; }
    selWin.innerHTML = "";
    D.voces.forEach((v, i) => selWin.append(h("option", { value: v.nombre, selected: D.voces.some(x => x.nombre === D.nombre) ? v.nombre === D.nombre : i === 0 }, v.nombre + " (" + v.cultura + ")")));
    vel.value = D.velocidad || 0; velTxt.textContent = nVel();
    if (motor !== "grabar") motor = D.motor === "elevenlabs" && D.el.permitido ? "elevenlabs" : "windows";
    pintar();
    if (motor === "elevenlabs" && D.el.conectado) cargarEL();
  })();
  pintar();
  return h("div", { class: "tarjeta", style: "margin:12px 0" },
    h("b", {}, "🔊 " + t("voz_titulo")), h("div", { class: "chico suave", style: "margin:2px 0 8px" }, t(tiene ? "voz_ayuda_con" : "voz_ayuda_sin")),
    pestanas, cuerpo, msg);
}
const guiSel = { modo: false, sel: new Set() };   // selección múltiple de guiones
const guiF = { q: "", f: "" };   // búsqueda y filtro de la lista de guiones
const FILTROS_GUI = [["", "gf_todos"], ["audio", "gf_audio"], ["texto", "gf_texto"], ["on", "gf_on"], ["off", "gf_off"]];
const guionVisible = g => {
  const q = guiF.q.trim().toLowerCase();
  return (!q || g.nombre.toLowerCase().includes(q)) && (guiF.f === "" || (guiF.f === "audio" ? g.tiene_audio !== false : guiF.f === "texto" ? g.tiene_audio === false : guiF.f === "on" ? g.tiene_audio !== false && g.activo : g.tiene_audio !== false && !g.activo));
};
// pregunta qué borrar de los guiones elegidos: audio y texto, solo texto o solo audio. Devuelve "ambos" | "texto" | "audio" | null
function elegirBorrado(items) {
  return new Promise(res => {
    const cerrar = v => { cerrarModal(); res(v); };
    const hayAmbos = items.some(g => g.tiene_audio !== false && g.tiene_texto);
    const opcion = (clave, extraClase) => h("button", { class: "opcion-borrar " + (extraClase || ""), onclick: () => cerrar(clave) },
      h("b", {}, t("gui_b_" + clave)), h("span", { class: "chico suave" }, t("gui_b_" + clave + "_d")));
    modal([h("h3", {}, t("gui_b_titulo")),
      h("p", { class: "suave" }, items.length === 1 ? t("gui_b_uno", { n: items[0].nombre }) : t("gui_b_varios", { n: items.length })),
      h("div", { class: "opciones-borrar" }, hayAmbos ? [opcion("ambos"), opcion("texto"), opcion("audio")]
        : h("button", { class: "opcion-borrar", onclick: () => cerrar("ambos") }, h("b", {}, t("gui_b_unico")))),
      h("p", { class: "chico suave" }, t("gui_b_ayuda")),
      h("div", { class: "acciones" }, h("button", { onclick: () => cerrar(null) }, t("cancelar")))], { alCerrar: () => res(null) });
  });
}
async function borrarGuiones(items, recargar) {
  const que = await elegirBorrado(items);
  if (!que) return;
  const r = await api("POST", `${base()}/archivos/guiones/borrar`, { nombres: items.map(g => g.nombre), que });
  toast(r.borrados ? t("gui_b_hecho", { n: r.borrados }) : t("gui_b_nada"), !r.borrados);
  guiSel.sel.clear(); guiSel.modo = false;
  if (items.some(g => g.nombre === guionSel)) { guionSel = null; guardarSesion(); }
  await refrescarProductos(); recargar();
}
async function renombrarGuion(g, recargar) {
  const r = await pedirTexto(t("renombrar"), t("gui_nombre_lbl"), g.nombre.replace(/\.[^.]+$/, ""), null, t("guardar"));
  if (!r || !r.valor.trim()) return;
  try { const x = await api("POST", `${base()}/guiones/renombrar`, { nombre: g.nombre, nuevo: r.valor }); if (guionSel === g.nombre) guionSel = x.nombre; guardarSesion(); await refrescarProductos(); toast(t("gui_renombrado")); recargar(); } catch (e) {}
}
async function pGuiones(c, recargar) {
  const lista = await api("GET", `${base()}/guiones`);
  [...guiSel.sel].forEach(n => { if (!lista.some(g => g.nombre === n)) guiSel.sel.delete(n); });
  if (!lista.length) guiSel.modo = false;
  const tocar = g => { guiSel.sel.has(g.nombre) ? guiSel.sel.delete(g.nombre) : guiSel.sel.add(g.nombre); recargar(); };
  const barraSel = !lista.length ? null : h("div", { class: "fila", style: "margin:0 0 8px;flex-wrap:wrap;gap:6px" },
    h("button", { class: "chico btn-sel-guiones", onclick: () => { guiSel.modo = !guiSel.modo; guiSel.sel.clear(); recargar(); } }, guiSel.modo ? t("gui_sel_cancelar") : "☑ " + t("gui_sel_modo")),
    guiSel.modo ? [
      h("button", { class: "chico", onclick: () => { lista.filter(guionVisible).forEach(g => guiSel.sel.add(g.nombre)); recargar(); } }, t("gui_sel_todos")),
      h("button", { class: "chico", onclick: () => { guiSel.sel.clear(); recargar(); } }, t("gui_sel_ninguno")),
      h("button", { class: "chico peligro btn-borrar-guiones", disabled: !guiSel.sel.size, onclick: () => borrarGuiones(lista.filter(g => guiSel.sel.has(g.nombre)), recargar) }, t("gui_sel_borrar", { n: guiSel.sel.size }))] : null);
  const der = h("div", {});
  if (guionSel && lista.some(g => g.nombre === guionSel)) {
    const actual = lista.find(g => g.nombre === guionSel);
    const ta = h("textarea", { spellcheck: false, placeholder: t("gui_placeholder") });
    // el título va en su propio cuadro; en el .txt se guarda como primera línea con #
    const crudo = (await api("GET", `${base()}/guiones/texto?nombre=${encodeURIComponent(guionSel)}`)).texto || "";
    const lineas = crudo.split(/\r?\n/); const k = lineas.findIndex(l => l.trim().startsWith("#"));
    const TI = { ...(await api("GET", `${base()}/guiones/titulo?nombre=${encodeURIComponent(guionSel)}`)), texto: k >= 0 ? lineas[k].replace(/^\s*#+\s*/, "").trim() : "" };
    if (k >= 0) lineas.splice(k, 1);
    ta.value = lineas.join("\n").replace(/^\s+/, "");
    const G = { previa: null };
    const N0 = guionSel, B0 = base();   // el guion y el producto de ESTA pantalla (el guardado automático no se equivoca si cambias de guion)
    const estadoG = h("span", { class: "chico suave" });
    const cambio = () => { G.previa && G.previa(); estadoG.textContent = ""; autoguardar("guion:" + B0 + N0, guardarAuto); };
    const info = h("div", { class: "chico suave" });
    const ver = async () => { const a = await api("POST", "/api/analizar", { texto: ta.value }); info.textContent = `${a.palabras} ${t("gui_palabras")} · ${a.burbujas + (a.marcas_pos || 0)} ${t("gui_burbujas")}` + (a.avisos.length ? " · ⚠ " + t("gui_av_cerrar") : ""); };
    let tm; ta.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(ver, 400); });
    const tieneAudio = actual.tiene_audio !== false;
    const audio = tieneAudio ? h("audio", { controls: true, style: "width:100%;margin-bottom:10px", src: `${base()}/archivo/guiones?nombre=${encodeURIComponent(guionSel)}` }) : null;
    // título + su posición y estilo
    const nTit = h("span", { class: "chico suave" });
    const contarTit = () => { const n = TI.texto.trim() ? TI.texto.trim().split(/\s+/).length : 0; nTit.textContent = n ? t("gui_titulo_n", { n }) : ""; nTit.style.color = n && (n < 6 || n > 8) ? "var(--mal)" : ""; };
    const inpTit = h("input", { type: "text", value: TI.texto, placeholder: t("gui_titulo_ph"), style: "width:100%", oninput: e => { TI.texto = e.target.value; contarTit(); cambio(); } });
    contarTit();
    const numT = (v, paso, f, min) => h("input", { type: "number", value: v, step: paso, min, style: "width:90px", oninput: e => { if (e.target.value !== "") { f(+e.target.value); cambio(); } } });
    const campoT = (etq, ctl) => h("div", { class: "ajuste", style: "padding:6px 0" }, h("label", { class: "n chico" }, etq), ctl);
    const colorT = () => {
      const txt = h("input", { type: "text", value: TI.color || "", placeholder: t("bu_igual_estilo"), style: "width:150px" });
      const pk = h("input", { type: "color", value: aHex(TI.color || "#ffffff") });
      pk.addEventListener("input", () => { txt.value = pk.value; TI.color = pk.value; cambio(); });
      txt.addEventListener("input", () => { TI.color = txt.value.trim(); if (!txt.value || /^#[0-9a-f]{6}$/i.test(txt.value)) { if (txt.value) pk.value = txt.value; cambio(); } });
      return h("div", { class: "ctl" }, pk, txt, h("button", { class: "chico", title: t("bu_igual_estilo"), onclick: () => { TI.color = ""; txt.value = ""; cambio(); } }, "↺"));
    };
    const tituloCaja = h("div", { class: "tarjeta", style: "margin:12px 0" },
      h("b", {}, t("gui_titulo_lbl")), h("div", { class: "chico suave", style: "margin:2px 0 8px" }, t("gui_titulo_ayuda")), inpTit, h("div", { style: "margin-top:4px" }, nTit),
      h("details", { style: "margin-top:8px", open: !!(TI.x || TI.y || TI.tam || TI.color || TI.fuente || TI.trazo !== "") },
        h("summary", { style: "cursor:pointer;font-weight:600" }, t("ti_posicion")),
        campoT(t("ti_y"), numT(TI.y || 0, 10, v => { TI.y = v; })),
        campoT(t("ti_x"), numT(TI.x || 0, 10, v => { TI.x = v; })),
        campoT(t("ti_tam"), numT(TI.tam || 0, 2, v => { TI.tam = v; }, 0)),
        campoT(t("ti_color"), colorT()),
        campoT(t("bu_fuente"), h("div", { class: "ctl" }, h("input", { type: "text", list: "bu_fuentes", value: TI.fuente || "", placeholder: t("bu_igual_estilo"), onchange: e => { TI.fuente = e.target.value.trim(); cambio(); } }),
          h("datalist", { id: "bu_fuentes" }, S.cat.fuentes.map(f => h("option", { value: f }))))),
        campoT(t("ti_trazo"), numT(TI.trazo, 1, v => { TI.trazo = v; }, 0)),
        h("button", { class: "chico", style: "margin-top:8px", onclick: () => { Object.assign(TI, { x: 0, y: 0, tam: 0, color: "", fuente: "", trazo: "" }); cambio(); recargar(); } }, t("ti_reset"))));
    const guardarTodo = async () => {
      const texto = (TI.texto.trim() ? "# " + TI.texto.trim() + "\n" : "") + ta.value;
      await api("PUT", `${B0}/guiones/texto`, { nombre: N0, texto });
      await api("PUT", `${B0}/guiones/titulo`, { nombre: N0, titulo: TI });
    };
    const guardarAuto = async () => { await guardarTodo(); estadoG.textContent = t("auto_guardado") + " · " + horaCorta(); };
    ta.addEventListener("input", cambio);
    const bur = { raiz: null, vista: null, previa: () => {} };      // las burbujas ya no se editan aquí: se ponen desde las marcas del texto y se ven en Estilo
    const marcasP = tieneAudio ? null : panelMarcas(ta, cambio);
    G.previa = bur.previa;
    const editor = h("div", {}, h("h2", {}, guionSel), audio,
      ...(!tieneAudio ? [h("div", { class: "aviso", style: "margin-bottom:10px" }, t("gui_sin_audio_aviso"))] : []),
      h("details", { style: "margin:4px 0 12px", open: true }, h("summary", {}, t("gui_ayuda_titulo")),
        h("ul", { class: "suave ayuda-guion" }, [1, 2].map(k => h("li", {}, t("gui_ay" + k)))),
        h("div", { class: "ejemplo-guion" },
          h("div", { class: "ej-tit" }, t("gui_ej_intro")),
          h("div", {}, h("b", {}, t("gui_ej_l1")), " El mensaje que evita recorridos cancelados"),
          h("div", {}, h("b", {}, t("gui_ej_l2")), " ", t("gui_ej_texto")))),
      ...(actual && !actual.tiene_texto ? [h("div", { class: "aviso", style: "margin-bottom:10px" }, t("gui_sin_txt_aviso"))] : []),
      panelVoz(actual, guardarTodo, recargar, () => ta.value), tituloCaja, h("b", {}, t("gui_texto_lbl")), ta, info, marcasP,
      h("div", { class: "fila", style: "margin-top:10px" },
        h("button", { class: "primario", onclick: async () => { await guardarTodo(); toast(t("gui_guardado")); recargar(); } }, t("guardar")),
        h("button", { class: "btn-renombrar-uno", onclick: () => renombrarGuion(actual, recargar) }, "✏️ " + t("renombrar")),
        h("button", { class: "peligro btn-borrar-uno", onclick: () => borrarGuiones([actual], recargar) }, t("borrar")), estadoG),
      bur.raiz && (((actual.analisis || {}).burbujas || 0) + ((actual.analisis || {}).marcas_pos || 0)) > 0 ? h("details", { style: "margin-top:14px", open: true }, h("summary", { style: "cursor:pointer;font-weight:600" }, "💬 " + t("bu_avanzado")), bur.raiz) : null);
    der.append(h("div", { class: "guion-ed" }, editor, bur.vista));
    ver();
  }
  const filaGuion = g => { const abierto = guionSel === g.nombre && !guiSel.modo; return h("div", { class: "item-guion" + (abierto ? " abierto" : "") }, h("div", { class: "fila-guion" },
    guiSel.modo ? h("input", { type: "checkbox", class: "casilla-guion", checked: guiSel.sel.has(g.nombre), onchange: () => tocar(g), style: "width:18px;height:18px;flex:none" })
      : g.tiene_audio === false ? h("span", { style: "width:42px;flex:none" })
      : h("label", { class: "sw", title: t("gui_activo_tip") }, h("input", { type: "checkbox", checked: g.activo, onchange: async e => { await api("POST", `${base()}/guiones/activo`, { nombre: g.nombre, activo: e.target.checked }); await refrescarProductos(); recargar(); } }), h("span")),
    h("button", { class: (guionSel === g.nombre && !guiSel.modo ? "on " : "") + (guiSel.modo && guiSel.sel.has(g.nombre) ? "on " : "") + (g.activo || g.tiene_audio === false ? "" : "apagado"), style: "flex:1;text-align:left", onclick: () => { if (guiSel.modo) return tocar(g); guionSel = abierto ? null : g.nombre; guardarSesion(); recargar(); } },
      h("span", { class: "flecha-guion" }, abierto ? "▾" : "▸"), " ", g.nombre, " ", g.activo || g.tiene_audio === false ? "" : h("span", { class: "insignia" }, t("gui_apagado")), g.tiene_audio === false ? h("span", { class: "insignia" }, t("gui_sin_audio")) : "", g.tiene_texto ? "" : h("span", { class: "insignia" }, t("gui_sin_texto"))),
    guiSel.modo ? null : h("button", { class: "chico btn-renombrar-guion", style: "flex:none;width:38px;padding:6px 0;text-align:center", title: t("renombrar"), onclick: () => renombrarGuion(g, recargar) }, "✏️"),
    guiSel.modo ? null : h("button", { class: "peligro chico btn-borrar-guion", style: "flex:none;width:38px;padding:6px 0;text-align:center", title: t("borrar"), onclick: () => borrarGuiones([g], recargar) }, "🗑")), abierto ? der : null); };
  const contenedorLista = h("div", { class: "lista" });
  const pintarListaGuiones = () => {
    const vis = lista.filter(guionVisible);
    contenedorLista.replaceChildren(...(vis.length ? vis.map(filaGuion) : [h("div", { class: "vacio chico" }, lista.length ? t("bus_nada") : t("gui_ninguno"))]));
  };
  pintarListaGuiones();
  const barraBuscar = lista.length < 2 ? null : h("div", { class: "fila", style: "margin:0 0 8px;gap:6px" },
    h("input", { type: "text", class: "inp-buscar-guion", value: guiF.q, placeholder: "🔍 " + t("bus_ph"), style: "flex:1;min-width:120px", oninput: e => { guiF.q = e.target.value; pintarListaGuiones(); } }),
    h("select", { class: "sel-filtro-guion", style: "width:auto", title: t("gf_titulo"), onchange: e => { guiF.f = e.target.value; pintarListaGuiones(); } },
      FILTROS_GUI.map(([v, kk]) => h("option", { value: v, selected: guiF.f === v }, t(kk)))));
  const GL = await api("GET", "/api/guiones_listos").catch(() => ({ lista: [], permitido: false }));
  const listos = !GL.lista.length ? null : h("details", { class: "guiones-listos", style: "margin-top:12px" },
    h("summary", {}, "📚 " + t("gl_titulo") + (GL.permitido ? "" : " 🔒")),
    h("div", { class: "chico suave", style: "margin:6px 0 10px" }, t("gl_ayuda") + (GL.permitido ? "" : " " + t("gl_bloq"))),
    h("div", { class: "rejilla-gl" }, GL.lista.map(g => h("div", { class: "gl-card" },
      h("span", { class: "insignia" }, g.tipo === "burbujas" ? "💬 " + t("gl_con_burb") : "🎙️ " + t("gl_basico")),
      h("b", {}, g.nombre), h("div", { class: "chico suave gl-txt" }, g.texto.replace(/\*\d+|\/\d+/g, "").replace(/\s+/g, " ").trim().slice(0, 130) + "…"),
      h("button", { class: "chico " + (GL.permitido ? "primario" : ""), onclick: async () => {
        if (!GL.permitido) { toast(t("gl_bloq_toast"), true); return; }
        try { const r = await api("POST", `${base()}/guiones/listo`, { id: g.id }); guionSel = r.nombre; guiSel.modo = false; guardarSesion(); await refrescarProductos(); toast(t("gl_agregado")); recargar(); } catch (e) {}
      } }, GL.permitido ? t("gl_usar") : "🔒 " + t("gl_pro"))))));
  const subirNuevo = h("div", { class: "subir-guiones tarjeta" }, h("b", {}, t("gui_subir_titulo")), h("div", { class: "chico suave", style: "margin:2px 0 8px" }, "ℹ️ " + t("gui_opcional")),
    h("button", { class: "chico btn-nuevo-guion", style: "margin-top:8px", onclick: async () => { const r = await api("POST", `${base()}/guiones/nuevo`, {}); guionSel = r.nombre; guiSel.modo = false; guiSel.sel.clear(); guardarSesion(); await refrescarProductos(); toast(t("gui_nuevo_hecho")); recargar(); } }, t("gui_nuevo")),
    h("div", { style: "margin-top:10px" }, zonaSubir(t("gui_subir"), "audio/*,.mp3,.wav,.m4a,.aac,.ogg,.oga,.opus,.flac,.wma,.amr,.weba,.3ga,.txt", async fs => { const nuevos = await subirArchivos("guiones", null, fs); const aud = nuevos.map(n => String(n.nombre || n)).filter(n => /\.(mp3|wav|m4a|aac|ogg|flac)$/i.test(n)); const sinTxt = aud.find(n => !nuevos.some(x => String(x.nombre || x).toLowerCase() === n.replace(/\.[^.]+$/, "").toLowerCase() + ".txt")); if (sinTxt) { guionSel = sinTxt; guardarSesion(); } recargar(); })), listos);
  const izq = h("div", {}, subirNuevo, h("h3", { style: "margin:18px 0 8px" }, t("gui_tus_guiones", { n: lista.length })), barraSel, barraBuscar, contenedorLista);
  c.append(h("p", { class: "suave" }, t("gui_intro")), h("div", { class: "guion guion-una" }, izq));
}

// ---------------------------------------------------------------- burbujas de un guion
// marcas de burbuja escritas en el texto del guion: (*1) = mensaje 1 de la Persona 1, (/2) = mensaje 2 de la Persona 2
function marcasDelTexto(texto) {
  const cuerpo = texto.split(/\r?\n/).filter(l => !l.trim().startsWith("#")).join(" ");
  const re = /\(\s*([*/])\s*(\d{1,2})\s*\)|(?<![\w/*])([*/])(\d{1,2})(?![\w/*])/g;
  const lim = cuerpo.replace(re, (m, s1, n1, s2, n2) => ` \u0000${s1 || s2}${n1 || n2}\u0000 `).replace(/[«»{}]/g, "").replace(/\bCliente:/gi, " ");
  const toks = lim.split(/\s+/).filter(Boolean);
  const palabras = toks.filter(x => !/^\u0000/.test(x)).length || 1;
  const sal = []; let antes = 0;
  for (const x of toks) {
    const m = /^\u0000([*/])(\d+)\u0000$/.exec(x);
    if (m) sal.push({ lado: m[1] === "/" ? "receptor" : "emisor", n: +m[2], frac: antes / palabras }); else antes++;
  }
  return sal;
}
async function pBurbujas(nombre, audio, taGuion, TI) {
  const info = await api("GET", `${base()}/guiones/burbujas?nombre=${encodeURIComponent(nombre)}`);
  const estilo = await api("GET", `${base()}/ajustes`);
  // aquí solo van el texto, el tipo (persona 1 o 2), el número y el momento; lo visual (tamaño, colores, letra, posición, efectos) está en «Estilo»
  let B = info.burbujas.map(b => ({ lado: b.lado === "receptor" ? "receptor" : "emisor", texto: b.texto || "", inicio: b.inicio || 0, duracion: b.duracion || 3 })), modo = info.modo, tiempo = null;
  const durTotal = () => info.duracion || 30;
  let MP = marcasDelTexto(taGuion.value);
  const simbolo = b => (b.lado === "receptor" ? "/" : "*");
  const ordinal = i => B.slice(0, i + 1).filter(x => (x.lado === "receptor") === (B[i].lado === "receptor")).length;
  const marcaDe = i => `${simbolo(B[i])}${ordinal(i)}`;
  const posDe = i => MP.find(m => (m.lado === "receptor") === (B[i].lado === "receptor") && m.n === ordinal(i));
  // para la vista previa: si la marca está en el guion, el momento se calcula con ella
  const conTiempos = () => B.map((b, i) => { const p = posDe(i); return p ? { ...b, inicio: Math.round(p.frac * durTotal() * 10) / 10 } : b; });
  const raiz = h("div", { class: "tarjeta", style: "margin-top:18px" });
  const vista = h("div", { class: "previa-burb" });
  const img = h("img", { alt: "", style: "width:100%;display:block" });
  const aviso = h("div", { class: "aviso", style: "display:none;margin-top:8px" }, t("bu_no_caben"));
  let tm;
  const previa = () => { clearTimeout(tm); tm = setTimeout(async () => {
    const r = await fetch(`${base()}/previa`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ valores: estilo, burbujas: conTiempos(), tiempo, titulo: TI }) });
    if (r.ok) { img.src = URL.createObjectURL(await r.blob()); aviso.style.display = r.headers.get("X-Aviso-Burbujas") === "1" ? "" : "none"; }
  }, 300); };
  // autoguardado de las burbujas: cada cambio se guarda solo (sin repintar, para no quitarte el cursor)
  const API0 = base();
  const estadoB = h("span", { class: "chico suave" });
  const guardarB = async () => { if (modo === "texto" && !B.length) return; /* usa las marcas del texto: no se toca hasta que agregues burbujas */ const r = await api("PUT", `${API0}/guiones/burbujas`, { nombre, burbujas: B }); modo = r.modo; estadoB.textContent = t("auto_guardado") + " · " + horaCorta(); };
  const editado = () => { previa(); estadoB.textContent = ""; autoguardar("burb:" + API0 + nombre, guardarB); };
  const num = (valor, paso, alCambiar, min) => h("input", { type: "number", value: valor, step: paso, min, style: "width:90px", oninput: e => { if (e.target.value !== "") alCambiar(+e.target.value); } });
  const nueva = lado => { const ult = B[B.length - 1]; return { lado: lado || (ult && ult.lado !== "receptor" ? "receptor" : "emisor"), texto: "", inicio: ult ? Math.round((ult.inicio + 2) * 10) / 10 : 1, duracion: 3 }; };
  const agregar = lado => { if (B.length >= 12) return; B.push(nueva(lado)); modo = "editor"; pintar(); editado(); };
  const pintar = () => {
    raiz.innerHTML = "";
    const n1 = B.filter(b => b.lado !== "receptor").length, n2 = B.length - n1;
    const cant = h("input", { type: "number", min: 0, max: 12, value: B.length, style: "width:80px", onchange: async e => {
      const n = Math.max(0, Math.min(12, +e.target.value || 0));
      if (n < B.length) { if (!await confirmar(t("bu_conf_menos"), t("bu_quitar"))) { e.target.value = B.length; return; } B = B.slice(0, n); }
      while (B.length < n) B.push(nueva());
      modo = "editor"; pintar(); editado(); } });
    raiz.append(h("h3", { style: "margin-top:0" }, t("bu_titulo")), h("p", { class: "suave chico" }, t("bu_intro"), " ", t("bu_apiladas")),
      modo === "texto" ? h("div", { class: "aviso", style: "margin-bottom:10px" }, t("bu_modo_texto", { n: info.marcas_texto })) : h("div", { class: "chico suave", style: "margin-bottom:10px" }, t("bu_modo_editor")),
      h("div", { class: "fila", style: "margin-bottom:6px" }, h("label", {}, t("bu_cantidad") + ":"), cant,
        h("span", { class: "insignia" }, `${t("bu_p1")}: ${n1}`), h("span", { class: "insignia" }, `${t("bu_p2")}: ${n2}`)),
      h("div", { class: "fila", style: "margin-bottom:12px" },
        h("button", { onclick: () => agregar("emisor") }, "+ " + t("bu_p1")), h("button", { onclick: () => agregar("receptor") }, "+ " + t("bu_p2"))));
    raiz.append(h("div", { class: "aviso", style: "margin-bottom:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap" },
      h("span", { style: "flex:1;min-width:220px" }, t("bu_solo_estilo")),
      h("button", { class: "chico primario", onclick: () => { S.pestana = "estilo"; producto(); } }, t("bu_ir_estilo"))));
    const huerf = MP.filter(m => m.n > B.filter(b => (b.lado === "receptor") === (m.lado === "receptor")).length).map(m => `${m.lado === "receptor" ? "/" : "*"}${m.n}`);
    if (huerf.length) raiz.append(h("div", { class: "aviso", style: "margin-bottom:10px" }, t("bu_huerfanas", { l: [...new Set(huerf)].join(" ") })));
    if (!B.length) raiz.append(h("div", { class: "vacio chico" }, t("bu_sin")));
    const izq = h("div", {});
    raiz.append(izq);
    B.forEach((b, i) => {
      const p2 = b.lado === "receptor";
      izq.append(h("div", { class: "tema", style: "border-left:5px solid " + (p2 ? "#9aa2b6" : "#7bc67b") },
        h("header", {}, h("b", {}, t("bu_n", { n: i + 1 })), h("span", { class: "insignia" }, p2 ? t("bu_p2") : t("bu_p1")),
          h("code", { class: "marca-pos" }, marcaDe(i)),
          h("button", { class: "chico", onclick: async () => { try { await navigator.clipboard.writeText(marcaDe(i)); } catch (e) {} toast(t("bu_marca_copiada", { m: marcaDe(i) })); } }, t("bu_copiar_marca")),
          h("button", { onclick: () => { if (B.length >= 12) return; B.splice(i + 1, 0, { ...b }); pintar(); editado(); } }, t("duplicar")),
          h("button", { class: "peligro", onclick: () => { B.splice(i, 1); pintar(); editado(); } }, t("bu_quitar"))),
        h("div", { class: "fila", style: "margin-bottom:8px" }, h("label", { class: "chico" }, t("bu_tipo")),
          h("select", { style: "flex:1;min-width:220px", onchange: e => { b.lado = e.target.value; pintar(); editado(); } },
            h("option", { value: "emisor", selected: !p2 }, t("bu_emisor")), h("option", { value: "receptor", selected: p2 }, t("bu_receptor")))),
        h("textarea", { style: "min-height:64px;font-family:inherit", placeholder: t("bu_texto"), oninput: e => { b.texto = e.target.value; editado(); } }, b.texto),
        h("div", { class: "chico " + (posDe(i) ? "marca-ok" : "marca-falta"), style: "margin-top:6px" }, posDe(i) ? t("bu_en_guion", { m: marcaDe(i) }) : t("bu_no_guion", { m: marcaDe(i) })),
        h("details", { style: "margin-top:8px", open: !posDe(i) && !!b.texto },
          h("summary", { class: "chico", style: "cursor:pointer" }, t("bu_ajuste_seg")),
        h("div", { class: "fila", style: "margin-top:8px" },
          h("label", { class: "chico" }, t("bu_inicio")), num(b.inicio, 0.1, v => { b.inicio = v; editado(); }, 0),
          h("button", { class: "chico", onclick: () => { b.inicio = Math.round(audio.currentTime * 10) / 10; pintar(); editado(); } }, t("bu_usar_seg")),
          h("label", { class: "chico" }, t("bu_dura")), num(b.duracion, 0.5, v => { b.duracion = v; editado(); }, 0.5)))));
    });
    const dur = info.duracion || 30;
    vista.replaceChildren(h("b", {}, t("es_previa")),
      h("div", { class: "fila", style: "margin:8px 0" }, h("label", { class: "chico" }, t("bu_ver_en")),
        h("input", { type: "range", min: 0, max: dur, step: 0.1, value: tiempo ?? 0, style: "flex:1;min-width:120px;accent-color:var(--acento)", oninput: e => { tiempo = +e.target.value; $("#bu_t").textContent = tiempo.toFixed(1) + " s"; previa(); } }),
        h("span", { id: "bu_t", class: "chico" }, tiempo == null ? "" : tiempo.toFixed(1) + " s"),
        h("button", { class: "chico", onclick: () => { tiempo = null; pintar(); previa(); } }, t("bu_todas"))), img, aviso);
    raiz.append(h("div", { class: "fila", style: "margin-top:14px" }, estadoB,
        h("button", { class: "primario", onclick: async () => { const r = await api("PUT", `${base()}/guiones/burbujas`, { nombre, burbujas: B }); B = r.burbujas; modo = r.modo; toast(t("bu_guardadas")); pintar(); } }, t("bu_guardar")),
        modo === "editor" ? h("button", { class: "link", onclick: async () => { cancelarAuto("burb:" + API0 + nombre); const r = await api("PUT", `${base()}/guiones/burbujas`, { nombre, usar_texto: true }); B = []; modo = r.modo; info.marcas_texto = r.marcas_texto; pintar(); previa(); } }, t("bu_volver_texto")) : null));
  };
  let firma = JSON.stringify(MP), tmm;
  taGuion.addEventListener("input", () => { clearTimeout(tmm); tmm = setTimeout(() => {
    MP = marcasDelTexto(taGuion.value); const f = JSON.stringify(MP);
    if (f !== firma) { firma = f; pintar(); editado(); } }, 600); });
  pintar(); previa();
  return { raiz, vista, previa };
}

// ---------------------------------------------------------------- importar carpetas
const EXT_MEDIA = /\.(mp4|mov|m4v|webm|mkv|avi|3gp|3g2|mpe?g|wmv|flv|png|jpe?g|jfif|webp|bmp|gif)$/i;
async function leerArrastre(dt) {
  const res = [];
  const leerDir = r => new Promise(ok => { const todo = []; const paso = () => r.readEntries(es => { if (!es.length) ok(todo); else { todo.push(...es); paso(); } }, () => ok(todo)); paso(); });
  const recorrer = async (en, ruta) => {
    if (en.isFile) { await new Promise(ok => en.file(f => { res.push({ file: f, ruta: ruta + f.name }); ok(); }, ok)); }
    else if (en.isDirectory) { for (const h2 of await leerDir(en.createReader())) await recorrer(h2, ruta + en.name + "/"); }
  };
  const ents = [...dt.items].map(i => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
  for (const e of ents) await recorrer(e, "");
  return res;
}
function palabrasDeTxt(texto) {
  return [...new Set(texto.split(/\r?\n/).map(l => (l.includes(":") ? l.slice(l.indexOf(":") + 1) : l)).join(",").split(/[,;\t ]+/).map(x => x.trim().toLowerCase().replace(/^[#\-•*"“”']+|["“”'.]+$/g, "")).filter(x => x && x.length <= 40))];
}
async function analizarImportacion(items) {
  const med = items.filter(i => EXT_MEDIA.test(i.ruta)), txts = items.filter(i => /\.txt$/i.test(i.ruta));
  const partes = r => r.split("/");
  const conCarpeta = med.filter(m => partes(m.ruta).length > 1);
  const tops = [...new Set(conCarpeta.map(m => partes(m.ruta)[0]))];
  const unTop = tops.length === 1 && conCarpeta.length === med.length;
  const directos = unTop && conCarpeta.some(m => partes(m.ruta).length === 2);
  const claveDe = i => { const p = partes(i.ruta); if (p.length === 1) return ""; return unTop && !directos && p.length >= 3 ? p[0] + "/" + p[1] : p[0]; };
  const grupos = new Map();
  for (const i of med) { const k = claveDe(i); if (!k) continue; if (!grupos.has(k)) grupos.set(k, { nombre: k.split("/").pop(), clave: k, archivos: [], palabras: [], palabrasTxt: false }); grupos.get(k).archivos.push(i.file); }
  const sueltos = med.filter(i => !claveDe(i)).map(i => i.file);
  const lectura = async f => { try { return await f.text(); } catch (e) { return ""; } };
  const sinCarpeta = [];
  for (const tx of txts) {
    const p = partes(tx.ruta); const contenido = await lectura(tx.file);
    const dueno = [...grupos.values()].filter(g => tx.ruta.startsWith(g.clave + "/")).sort((x, y) => y.clave.length - x.clave.length)[0];
    if (dueno) { dueno.palabras.push(...palabrasDeTxt(contenido)); dueno.palabrasTxt = true; continue; }
    const lineas = contenido.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (lineas.some(l => /^[^:]{1,40}:\s*\S/.test(l))) {
      for (const l of lineas) { const m = /^([^:]{1,40}):\s*(.+)$/.exec(l); if (m) sinCarpeta.push({ nombre: m[1].trim(), archivos: [], palabras: palabrasDeTxt(m[2]), palabrasTxt: true }); }
    } else sinCarpeta.push({ nombre: p[p.length - 1].replace(/\.txt$/i, ""), archivos: [], palabras: palabrasDeTxt(contenido), palabrasTxt: true });
  }
  const lista = [...grupos.values()];
  for (const s of sinCarpeta) { const ya = lista.find(g => g.nombre.toLowerCase() === s.nombre.toLowerCase()); if (ya) { ya.palabras.push(...s.palabras); ya.palabrasTxt = true; } else lista.push(s); }
  for (const g of lista) g.palabras = [...new Set(g.palabras)];
  return { temas: lista, sueltos };
}
async function importarCarpetas(temas, guardarTemas, recargar) {
  const dueño = w => Object.keys(temas).find(n => temas[n].includes(w));
  const zona = h("div", { class: "soltar", style: "margin:10px 0" }, t("imp_soltar"));
  const inpDir = h("input", { type: "file", webkitdirectory: true, multiple: true, style: "display:none" });
  const inpTxt = h("input", { type: "file", accept: ".txt", multiple: true, style: "display:none" });
  const inpArch = h("input", { type: "file", multiple: true, accept: "video/*,image/*,.mp4,.mov,.m4v,.webm,.mkv,.avi,.3gp,.3g2,.mpeg,.mpg,.wmv,.flv,.jpg,.jpeg,.jfif,.png,.webp,.bmp,.gif,.txt", style: "display:none" });
  const cuerpo = h("div", {});
  let analisis = null;
  const mostrar = async items => {
    analisis = await analizarImportacion(items);
    cuerpo.replaceChildren();
    if (!analisis.temas.length && !analisis.sueltos.length) { cuerpo.append(h("div", { class: "aviso" }, t("imp_nada"))); return; }
    const filas = analisis.temas.map(g => {
      const esKit = /^(kit|producto|producto \/ servicio)$/i.test(g.nombre);
      const existe = esKit ? "kit" : (Object.keys(temas).find(n => n.toLowerCase() === g.nombre.toLowerCase()) || "");
      const auto = g.nombre.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim().split(" ")[0];
      const pal = g.palabras.length ? g.palabras : (g.nombre.toLowerCase() === "general" || existe ? [] : [auto]);
      g.palabrasFinal = pal; g.existe = existe;
      return h("div", { class: "tema", style: "margin-bottom:8px" },
        h("div", { class: "fila" }, h("b", {}, "📁 " + g.nombre), h("span", { class: "insignia" }, existe ? t("imp_se_agrega") : t("imp_nueva")), h("div", { class: "espacio" }), h("span", { class: "suave chico" }, `${g.archivos.length} ${t("cl_n")}`)),
        h("div", { class: "suave chico", style: "margin-top:4px" }, pal.length ? t("imp_palabras") + " " + pal.join(", ") + (g.palabrasTxt ? "" : " " + t("imp_palabras_auto")) : t("imp_sin_pal")));
    });
    cuerpo.append(h("p", { class: "suave chico" }, t("imp_resumen", { n: analisis.temas.length })), ...filas,
      ...(analisis.sueltos.length ? [h("div", { class: "chico suave", style: "margin-bottom:8px" }, t("imp_sueltos", { n: analisis.sueltos.length }))] : []),
      h("div", { class: "acciones" }, h("button", { class: "primario", onclick: ejecutar }, t("imp_importar"))));
  };
  const ejecutar = async () => {
    const A = analisis;
    const aviso = h("div", { class: "suave chico" });
    modal([h("h2", {}, t("imp_importando")), h("div", { class: "fila", style: "gap:14px" }, rueda(46), aviso)], { fijo: true });
    let omitidas = 0, importados = 0;
    try {
      for (const g of A.temas) {
        const esKit = g.existe === "kit", esGen = g.nombre.toLowerCase() === "general";
        const nombre = g.existe || g.nombre;
        if (!esKit && !esGen) {
          if (!temas[nombre]) temas[nombre] = [];
          for (const w of g.palabrasFinal) { const o = dueño(w); if (o && o !== nombre) { omitidas++; continue; } if (!temas[nombre].includes(w)) temas[nombre].push(w); }
          if (!temas[nombre].length) temas[nombre].push(nombre.toLowerCase().split(/\s+/)[0]);
        } else if (esKit) { for (const w of g.palabrasFinal) { const o = dueño(w); if (o && o !== "kit") { omitidas++; continue; } if (!temas.kit.includes(w)) temas.kit.push(w); } }
      }
      await guardarTemas();
      const tareas = A.temas.map(g => ({ seccion: g.existe === "kit" ? "kit" : "clips", tema: g.existe === "kit" ? null : (g.nombre.toLowerCase() === "general" ? "general" : (g.existe || g.nombre)), archivos: g.archivos, nombre: g.nombre }));
      if (A.sueltos.length) tareas.push({ seccion: "clips", tema: "general", archivos: A.sueltos, nombre: t("cl_general") });
      const totalArch = tareas.reduce((s, x) => s + x.archivos.length, 0); let hechos = 0;
      for (const tk of tareas) {
        for (let i = 0; i < tk.archivos.length;) {
          const lote = []; let bytes = 0;
          while (i < tk.archivos.length && lote.length < 40 && (bytes + tk.archivos[i].size < 250e6 || !lote.length)) { bytes += tk.archivos[i].size; lote.push(tk.archivos[i++]); }
          const fd = new FormData(); lote.forEach(f => fd.append("archivos", f));
          const base0 = hechos;
          const resp = await enviarConProgreso(`${base()}/archivos/${tk.seccion}` + (tk.tema ? "?tema=" + encodeURIComponent(tk.tema) : ""), fd,
            p => { aviso.textContent = t("imp_progreso", { tema: tk.nombre, a: Math.min(totalArch, base0 + Math.round(lote.length * p)), b: totalArch }); });
          importados += (resp.subidos || []).length; hechos += lote.length;
        }
      }
    } catch (e) { cerrarModal(); recargar(); return; }
    await refrescarProductos(); cerrarModal();
    toast((importados ? t("imp_listo", { n: importados }) : t("imp_listo_pal")) + (omitidas ? " · " + t("imp_omitidas", { n: omitidas }) : ""));
    recargar();
  };
  const arranque = async items => { try { await mostrar(items); } catch (e) { cuerpo.replaceChildren(h("div", { class: "aviso" }, t("imp_nada"))); } };
  inpDir.addEventListener("change", () => arranque([...inpDir.files].map(f => ({ file: f, ruta: f.webkitRelativePath || f.name }))));
  inpTxt.addEventListener("change", () => arranque([...inpTxt.files].map(f => ({ file: f, ruta: f.name }))));
  inpArch.addEventListener("change", () => arranque([...inpArch.files].map(f => ({ file: f, ruta: f.name }))));
  zona.addEventListener("dragover", e => { e.preventDefault(); zona.classList.add("arriba"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("arriba"));
  zona.addEventListener("drop", async e => { e.preventDefault(); zona.classList.remove("arriba"); arranque(await leerArrastre(e.dataTransfer)); });
  modal([h("h2", {}, t("imp_titulo")), h("p", { class: "suave chico" }, t("imp_ayuda")),
    zona,
    h("div", { class: "fila" }, h("button", { class: "primario", onclick: () => inpDir.click() }, "📁 " + t("imp_elegir_carpeta")), h("button", { onclick: () => inpTxt.click() }, "📄 " + t("imp_elegir_txt")), h("button", { onclick: () => inpArch.click() }, "🎞 " + t("imp_elegir_arch")), inpDir, inpTxt, inpArch),
    cuerpo, h("div", { class: "acciones" }, h("button", { onclick: cerrarModal }, t("cerrar_modal_cancelar")))]);
}

// ---------------------------------------------------------------- clips y palabras clave
async function pClips(c, recargar) {
  const temas = await api("GET", `${base()}/temas`);
  const guardarTemas = async () => { await api("PUT", `${base()}/temas`, { temas }); };
  const dueño = w => Object.keys(temas).find(n => temas[n].includes(w));
  // etiquetas de palabras de un tema (se guardan al instante)
  const etiquetas = nombre => {
    const etqs = h("div", { class: "etiquetas" });
    const pintar = () => {
      etqs.innerHTML = "";
      temas[nombre].forEach((w, i) => etqs.append(h("span", { class: "etq" }, w, h("button", { onclick: async () => {
        if (temas[nombre].length === 1 && nombre !== "kit") { toast(t("pal_minimo"), true); return; }
        temas[nombre].splice(i, 1); await guardarTemas(); pintar(); } }, "×"))));
      const inp = h("input", { type: "text", placeholder: t("cl_agregar_pal") });
      inp.addEventListener("keydown", async e => {
        if (e.key !== "Enter" && e.key !== ",") return; e.preventDefault();
        const nuevas = [];
        for (const x of inp.value.split(/[,\s]+/).map(x => x.trim().toLowerCase()).filter(Boolean)) {
          const o = dueño(x);
          if (o && o !== nombre) { toast(t("pal_repetida", { p: x, t: o }), true); continue; }
          if (temas[nombre].includes(x)) { toast(t("pal_ya_aqui", { p: x }), true); continue; }
          if (!nuevas.includes(x)) nuevas.push(x);
        }
        if (!nuevas.length) return; temas[nombre].push(...nuevas); await guardarTemas(); pintar(); setTimeout(() => $("input", etqs).focus(), 20);
      });
      etqs.append(inp);
    };
    pintar();
    return h("div", {}, etqs, h("div", { class: "suave chico", style: "margin-top:8px" }, t("cl_una_palabra")));
  };
  c.append(h("p", { class: "suave" }, t("cl_intro"), " ", t("cl_sin_limite")));
  const cuerpoH = h("div", { class: "seccion-hablando" });
  c.append(h("details", { class: "mas-opciones", style: "margin:8px 0 14px", open: ["presentador", "podcast"].includes(S.camino) }, h("summary", {}, "🎞 " + t("t_hablando")), h("p", { class: "suave chico", style: "margin:6px 0" }, t("cm_hablando_para")), cuerpoH));
  try { await pHablando(cuerpoH, recargar); } catch (e) {}
  // plantillas de temas y palabras clave (de arranque o guardadas por ti)
  const pls = await api("GET", "/api/plantillas");
  const selP = h("select", { style: "flex:1;min-width:200px" },
    pls.some(x => x.tipo === "mia") ? h("optgroup", { label: t("pl_mias") }, pls.filter(x => x.tipo === "mia").map(x => h("option", { value: x.id }, x.nombre))) : null,
    h("optgroup", { label: t("pl_arranque") }, pls.filter(x => x.tipo === "base").map(x => h("option", { value: x.id }, x.nombre))));
  const aplicar = async modo => {
    if (modo === "reemplazar" && !await confirmar(t("pl_conf_reemplazar"), t("pl_reemplazar"))) return;
    await api("POST", `${base()}/plantillas/aplicar`, { id: selP.value, modo }); toast(t("pl_aplicada")); recargar();
  };
  const sinTemas = Object.keys(temas).filter(n => n !== "kit").length === 0;
  const tarjetaPl = (h("div", { class: "tarjeta", style: "margin:8px 0 16px" + (sinTemas ? ";border-color:var(--acento)" : "") },
    h("div", { class: "fila" }, h("b", {}, t("pl_titulo")), selP,
      h("button", { class: "primario", onclick: () => aplicar("sumar") }, t("pl_sumar")),
      h("button", { onclick: () => aplicar("reemplazar") }, t("pl_reemplazar")),
      h("button", { class: "peligro", title: t("borrar"), onclick: async () => { const x = pls.find(p => p.id === selP.value); if (!x || x.tipo !== "mia") { toast(t("pl_no_borrar"), true); return; } if (!await confirmar(t("borrar") + " “" + x.nombre + "”?")) return; await api("DELETE", `/api/plantillas/${encodeURIComponent(x.id)}`); recargar(); } }, "×")),
    h("div", { class: "chico suave", style: "margin:8px 0" }, sinTemas ? t("pl_empieza") : t("pl_ayuda")),
    h("button", { onclick: async () => { const r = await pedirTexto(t("pl_guardar"), t("pl_nombre")); if (!r) return; await api("POST", "/api/plantillas", { producto: S.pid, nombre: r.valor }); toast(t("pl_guardada")); recargar(); } }, t("pl_guardar"))));
  c.append(sinTemas ? tarjetaPl : h("details", { class: "mas-opciones" }, h("summary", {}, "📋 " + t("pl_titulo")), tarjetaPl));
  S.abiertos = S.abiertos || {};
  // bloque fijo: crear carpeta nueva
  const fijo = h("div", { class: "fijo-clips" });
  const nuevo = h("input", { type: "text", placeholder: t("cl_nombre_tema") });
  const crear = async () => {
    const n = nuevo.value.trim(); if (!n) return;
    const id = n.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "");
    if (id === "kit") { toast(t("kit_reservado"), true); return; }
    if (id === "general") { toast(t("general_reservado"), true); return; }
    if (!id) return;
    const o = dueño(id); if (o) { toast(t("pal_repetida", { p: id, t: o }), true); return; }
    temas[n] = [id.replace(/_/g, " ").split(" ")[0]]; S.abiertos[S.pid + ":" + n] = true; await guardarTemas(); recargar();
  };
  nuevo.addEventListener("keydown", e => { if (e.key === "Enter") crear(); });
  fijo.append(h("div", { class: "tema", style: "border-style:dashed" }, h("div", { class: "fila" }, h("div", { style: "flex:1;min-width:200px" }, nuevo), h("button", { class: "primario", onclick: crear }, t("cl_tema_nuevo")), h("button", { onclick: () => importarCarpetas(temas, guardarTemas, recargar) }, "📥 " + t("imp_boton")))));
  c.append(fijo);
  // carpetas de palabras clave: cuadritos en filas; al darle clic se abre su contenido justo debajo de su fila
  let porFila = 4;
  try { porFila = Math.max(1, Math.min(10, +localStorage.getItem("rm_por_fila") || 4)); } catch (e) {}
  const rejilla = h("div", { class: "rejilla-carpetas" });
  const selFila = h("select", { style: "width:auto", onchange: e => { porFila = +e.target.value; try { localStorage.setItem("rm_por_fila", porFila); } catch (x) {} ajustar(); } },
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => h("option", { value: n, selected: n === porFila }, String(n))));
  const barraCarpetas = h("div", { class: "fila", style: "margin:6px 0 10px" }, h("label", { class: "chico suave" }, t("cl_por_fila")), selFila);
  const abierta = () => S.abiertos[S.pid + ":sel"] || "";
  const efectivas = () => { const w = rejilla.clientWidth || window.innerWidth; const max = w < 460 ? 1 : w < 700 ? 2 : w < 900 ? 3 : w < 1100 ? 4 : w < 1300 ? 6 : 10; return Math.max(1, Math.min(porFila, max)); };
  let panel = null;
  let vista = false;
  const ajustar = () => {
    if (!rejilla.isConnected) { if (vista) window.removeEventListener("resize", ajustar); return; }
    vista = true;
    const n = efectivas();
    rejilla.style.setProperty("--cols", n);
    if (!panel) return;
    const tiles = [...rejilla.querySelectorAll(".carpeta-tile")];
    const idx = tiles.findIndex(x => x.dataset.k === abierta());
    if (idx < 0) { panel.remove(); return; }
    const fin = Math.min(tiles.length - 1, idx - (idx % n) + n - 1);
    tiles[fin].after(panel);
  };
  window.addEventListener("resize", ajustar);
  const abrirCarpeta = k => { S.abiertos[S.pid + ":sel"] = abierta() === k ? "" : k; recargar(); };
  const tile = (k, titulo, cuenta, sub, borrar, renom) => {
    let espera = null;
    const nom = h("div", { class: "ct-nom", title: titulo }, titulo);
    const nodo = h("div", { class: "carpeta-tile" + (abierta() === k ? " abierta" : ""), "data-k": k,
      onclick: e => { if (e.target.closest("button, input")) return; clearTimeout(espera); espera = setTimeout(() => abrirCarpeta(k), renom ? 230 : 0); } },
      h("div", { class: "ct-top" }, h("span", { class: "ct-ico" }, abierta() === k ? "📂" : "📁"), borrar || null),
      nom, h("div", { class: "ct-sub" }, cuenta), sub ? h("div", { class: "ct-pal", title: sub }, sub) : null);
    if (renom) {
      renombrable(nodo, nom, titulo, renom, borrar ? [[t("borrar"), () => borrar.click(), true]] : []);
      nom.addEventListener("dblclick", () => clearTimeout(espera), true);
    }
    return nodo;
  };
  let cuerpoAbierto = null;
  if (temas.kit) {
    const imgs = await api("GET", `${base()}/archivos/kit`);
    rejilla.append(tile("kit", "★ " + t("kit_tema_nombre"), `${imgs.length} ${t("kit_n_img")}`, (temas.kit || []).join(", "), null));
    if (abierta() === "kit") cuerpoAbierto = h("div", {},
      h("p", { class: "suave chico", style: "margin:0 0 8px" }, t("kit_tema_ayuda")),
      temas.kit.length ? null : h("div", { class: "aviso chico", style: "margin-bottom:8px" }, t("kit_vacio")),
      etiquetas("kit"),
      h("p", { class: "suave chico", style: "margin:14px 0 8px" }, t("kit_intro")),
      zonaSubir(t("kit_subir"), "video/*,image/*,.mp4,.mov,.m4v,.webm,.mkv,.avi,.3gp,.3g2,.mpeg,.mpg,.wmv,.flv,.jpg,.jpeg,.jfif,.png,.webp,.bmp,.gif", async fs => { await subirArchivos("kit", null, fs); recargar(); }),
      galeria("kit", null, imgs, recargar));
  }
  for (const nombre of Object.keys(temas)) {
    if (nombre === "kit") continue;
    const items = await api("GET", `${base()}/archivos/clips?tema=${encodeURIComponent(nombre)}`);
    const borrar = h("button", { class: "peligro chico ct-x", title: t("borrar"), onclick: () => {
      const elegir = modo => async () => { cerrarModal(); await api("DELETE", `${base()}/temas/${encodeURIComponent(nombre)}?modo=${modo}`); if (abierta() === nombre) S.abiertos[S.pid + ":sel"] = ""; await refrescarProductos(); toast(t("tema_enviado")); recargar(); };
      modal([h("h2", {}, t("tema_q", { n: nombre })), h("p", { class: "suave" }, t("tema_ayuda")),
        h("div", { class: "opciones-borrar" },
          h("button", { onclick: elegir("todo") }, h("b", {}, t("tema_todo")), h("span", { class: "chico suave" }, t("tema_todo_d", { n: items.length }))),
          h("button", { onclick: elegir("archivos") }, h("b", {}, t("tema_archivos")), h("span", { class: "chico suave" }, t("tema_archivos_d"))),
          h("button", { onclick: elegir("palabras") }, h("b", {}, t("tema_palabras")), h("span", { class: "chico suave" }, t("tema_palabras_d")))),
        h("div", { class: "acciones" }, h("button", { class: "primario", onclick: cerrarModal }, t("tema_cancelar")))]); } }, "🗑");
    const renom = async v => {
      const res = await api("POST", `${base()}/temas/${encodeURIComponent(nombre)}/renombrar`, { nuevo: v });
      if (abierta() === nombre) S.abiertos[S.pid + ":sel"] = res.nombre; await refrescarProductos(); recargar(); };
    rejilla.append(tile(nombre, nombre, `${items.length} ${t("cl_n")}`, (temas[nombre] || []).join(", "), borrar, renom));
    if (abierta() === nombre) cuerpoAbierto = h("div", {},
      etiquetas(nombre),
      h("div", { style: "margin-top:12px" }, zonaSubir(t("cl_subir"), "video/*,image/*,.mp4,.mov,.m4v,.webm,.mkv,.avi,.3gp,.3g2,.mpeg,.mpg,.wmv,.flv,.jpg,.jpeg,.jfif,.png,.webp,.bmp,.gif", async fs => { await subirArchivos("clips", nombre, fs); recargar(); }, true)),
      galeria("clips", nombre, items, recargar));
  }
  const gen = await api("GET", `${base()}/archivos/clips?tema=general`);
  rejilla.append(tile("general", t("cl_general"), `${gen.length} ${t("cl_n")}`, "", null));
  if (abierta() === "general") cuerpoAbierto = h("div", {},
    h("div", { class: "suave chico", style: "margin-bottom:10px" }, t("cl_general_ayuda")),
    zonaSubir(t("cl_subir"), "video/*,image/*,.mp4,.mov,.m4v,.webm,.mkv,.avi,.3gp,.3g2,.mpeg,.mpg,.wmv,.flv,.jpg,.jpeg,.jfif,.png,.webp,.bmp,.gif", async fs => { await subirArchivos("clips", "general", fs); recargar(); }),
    galeria("clips", "general", gen, recargar));
  if (cuerpoAbierto) {
    const k = abierta();
    panel = h("div", { class: "carpeta-panel" },
      h("div", { class: "fila", style: "margin-bottom:10px" }, h("b", {}, k === "general" ? t("cl_general") : k === "kit" ? "★ " + t("kit_tema_nombre") : k), h("div", { class: "espacio" }),
        h("button", { class: "chico", onclick: () => abrirCarpeta(k) }, t("cl_cerrar_carpeta"))), cuerpoAbierto);
    rejilla.append(panel);
  }
  c.append(barraCarpetas, rejilla);
  setTimeout(() => { ajustar(); if (panel) panel.scrollIntoView({ block: "nearest", behavior: "smooth" }); }, 60);
}

// ---------------------------------------------------------------- kit y musica
async function pKit(c, rec) {
  const items = await api("GET", `${base()}/archivos/kit`);
  c.append(h("p", { class: "suave" }, t("kit_intro")), zonaSubir(t("kit_subir"), "video/*,image/*,.mp4,.mov,.m4v,.webm,.mkv,.avi,.3gp,.3g2,.mpeg,.mpg,.wmv,.flv,.jpg,.jpeg,.jfif,.png,.webp,.bmp,.gif", async fs => { await subirArchivos("kit", null, fs); rec(); }), galeria("kit", null, items, rec));
}
async function pMusica(c, rec) {
  const items = await api("GET", `${base()}/archivos/musica`);
  const aj = await api("GET", `${base()}/ajustes`);
  const sel = h("select", { onchange: async e => { await api("PUT", `${base()}/ajustes`, { valores: { musica_archivo: e.target.value } }); toast(t("es_ok")); } },
    h("option", { value: "" }, t("mu_azar")), items.map(i => h("option", { value: i.nombre, selected: aj.musica_archivo === i.nombre }, i.nombre)));
  c.append(h("p", { class: "suave" }, t("mu_intro")), zonaSubir(t("mu_subir"), "audio/*,.mp3,.wav,.m4a,.aac,.ogg,.oga,.opus,.flac,.wma,.amr,.weba,.3ga", async fs => { await subirArchivos("musica", null, fs); rec(); }),
    items.length ? h("div", { style: "margin-top:16px" },
      h("div", { class: "fila" }, h("label", {}, t("mu_elegida")), h("div", { style: "min-width:260px" }, sel)),
      h("div", { style: "margin-top:12px" }, items.map(i => h("div", { class: "fila", style: "padding:6px 0;border-bottom:1px solid var(--linea)" },
        h("span", { style: "flex:1" }, i.nombre, " ", h("span", { class: "suave chico" }, kb(i.tam))),
        h("audio", { controls: true, preload: "none", style: "height:34px", src: `${base()}/archivo/musica?nombre=${encodeURIComponent(i.nombre)}` }),
        h("button", { class: "peligro", onclick: async () => { await api("DELETE", `${base()}/archivos/musica?nombre=${encodeURIComponent(i.nombre)}`); rec(); } }, "×")))))
      : h("div", { class: "vacio" }, t("mu_ninguna")));
  const sons = await api("GET", `${base()}/archivos/sonidos`);
  c.append(h("div", { class: "tarjeta", style: "margin-top:22px" }, h("h3", { style: "margin-top:0" }, t("mu_sonidos")), h("p", { class: "suave chico" }, t("mu_sonidos_ayuda")),
    zonaSubir(t("mu_sonidos_subir"), "audio/*,.mp3,.wav,.m4a,.aac,.ogg,.oga,.opus,.flac,.wma,.amr,.weba,.3ga", async fs => { await subirArchivos("sonidos", null, fs); rec(); }),
    sons.length ? h("div", { style: "margin-top:12px" }, sons.map(i => h("div", { class: "fila", style: "padding:6px 0;border-bottom:1px solid var(--linea)" },
      h("span", { style: "flex:1" }, i.nombre, " ", h("span", { class: "suave chico" }, kb(i.tam))),
      h("audio", { controls: true, preload: "none", style: "height:34px", src: `${base()}/archivo/sonidos?nombre=${encodeURIComponent(i.nombre)}` }),
      h("button", { class: "peligro", onclick: async () => { await api("DELETE", `${base()}/archivos/sonidos?nombre=${encodeURIComponent(i.nombre)}`); rec(); } }, "×")))) : null));
}

// ---------------------------------------------------------------- videos
// carpetas de videos terminados (una por formato) como cuadritos, igual que en Clips y palabras clave
function carpetasVideos(grupos, etqF, tarjeta, est) {
  S.abiertos = S.abiertos || {};
  let porFila = 4;
  try { porFila = Math.max(1, Math.min(10, +localStorage.getItem("rm_por_fila") || 4)); } catch (e) {}
  const clave = S.pid + ":vid";
  const abierta = () => (S.abiertos[clave] && grupos[S.abiertos[clave]]) ? S.abiertos[clave] : "";
  const rejilla = h("div", { class: "rejilla-carpetas" });
  let panel = null, vista = false;
  const efectivas = () => { const w = rejilla.clientWidth || window.innerWidth; const max = w < 460 ? 1 : w < 700 ? 2 : w < 900 ? 3 : w < 1100 ? 4 : w < 1300 ? 6 : 10; return Math.max(1, Math.min(porFila, max)); };
  const ajustar = () => {
    if (!rejilla.isConnected) { if (vista) window.removeEventListener("resize", ajustar); return; }
    vista = true;
    const n = efectivas();
    rejilla.style.setProperty("--cols", n);
    if (!panel) return;
    const tiles = [...rejilla.querySelectorAll(".carpeta-tile")];
    const idx = tiles.findIndex(x => x.dataset.k === abierta());
    if (idx < 0) { panel.remove(); return; }
    tiles[Math.min(tiles.length - 1, idx - (idx % n) + n - 1)].after(panel);
  };
  window.addEventListener("resize", ajustar);
  const abrir = k => { S.abiertos[clave] = abierta() === k ? "" : k; est.repintar(); };
  const selFila = h("select", { style: "width:auto", onchange: e => { porFila = +e.target.value; try { localStorage.setItem("rm_por_fila", porFila); } catch (x) {} ajustar(); } },
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => h("option", { value: n, selected: n === porFila }, String(n))));
  const claves = Object.keys(grupos).sort();
  claves.forEach(f => rejilla.append(h("div", { class: "carpeta-tile" + (abierta() === f ? " abierta" : ""), "data-k": f, onclick: () => abrir(f) },
    h("div", { class: "ct-top" }, h("span", { class: "ct-ico" }, abierta() === f ? "📂" : "📁")),
    h("div", { class: "ct-nom", title: etqF(f) }, etqF(f)), h("div", { class: "ct-sub" }, `${grupos[f].length} ${t("vi_n")}`))));
  const k = abierta();
  if (k) {
    panel = h("div", { class: "carpeta-panel" },
      h("div", { class: "fila", style: "margin-bottom:10px" }, h("b", {}, etqF(k)), h("div", { class: "espacio" }),
        h("button", { class: "chico", onclick: () => abrir(k) }, t("cl_cerrar_carpeta"))),
      h("div", { class: "videos" + (/^(horizontal|personalizado)/.test(k) ? " ancho" : "") }, grupos[k].map(tarjeta)));
    rejilla.append(panel);
  }
  setTimeout(ajustar, 30);
  return h("div", {}, h("div", { class: "fila", style: "margin:18px 0 10px" }, h("label", { class: "chico suave" }, t("cl_por_fila")), selFila), rejilla);
}
function avisoGuardado(r) {
  if (typeof G !== "undefined") G.descargado = true;
  const abrir = ruta => api("POST", "/api/abrir_ruta", { ruta }).catch(() => {});
  modal([h("h2", {}, "✅ " + t("vi_guardado_t")),
    h("p", {}, t("vi_guardado_en")),
    h("p", { style: "word-break:break-all;font-weight:600" }, r.ruta),
    h("div", { class: "fila", style: "justify-content:flex-end;margin-top:14px" },
      h("button", { onclick: () => abrir(r.carpeta) }, "📂 " + t("vi_abrir_descargas")),
      h("button", { onclick: () => abrir(r.ruta) }, "▶ " + t("vi_ver_video")),
      h("button", { class: "primario", onclick: cerrarModal }, t("entendido")))]);
}
// Pantalla completa propia: la tecla Esc (o la ✕, o un clic en el fondo) la cierra y vuelves a la lista de videos tal como estaba.
function verPantallaCompleta(src, desde) {
  document.querySelectorAll(".visor-video").forEach(x => x.remove());
  let entro = false, cerrado = false;
  const v = h("video", { controls: true, autoplay: true, controlsList: "nodownload nofullscreen", src });
  const cerrar = () => {
    if (cerrado) return; cerrado = true;
    document.removeEventListener("keydown", tecla, true); document.removeEventListener("fullscreenchange", cambio);
    try { v.pause(); } catch (e) {}
    caja.remove();
    if (document.fullscreenElement) { try { document.exitFullscreen(); } catch (e) {} }
  };
  const tecla = e => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); cerrar(); } };
  const cambio = () => { if (document.fullscreenElement === caja) entro = true; else if (entro) cerrar(); };       // si salió de pantalla completa por otro lado (la tecla Esc de Windows), también se cierra
  const caja = h("div", { class: "visor-video", onclick: e => { if (e.target === caja) cerrar(); } }, v,
    h("button", { class: "x-visor", title: t("cerrar") + " (Esc)", "aria-label": t("cerrar"), onclick: cerrar }, "✕"));
  document.body.append(caja);
  v.addEventListener("loadedmetadata", () => { if (desde > 0 && desde < v.duration) v.currentTime = desde; }, { once: true });
  v.play().catch(() => {});
  document.addEventListener("keydown", tecla, true); document.addEventListener("fullscreenchange", cambio);
  try { const r = caja.requestFullscreen && caja.requestFullscreen(); if (r && r.catch) r.catch(() => {}); } catch (e) {}
}
async function pVideos(c, rec, limite) {
  let v = await api("GET", `${base()}/videos`);
  if (limite) v = v.slice(0, limite);
  const lugar = h("div", { class: "suave chico", style: "margin:-6px 0 12px;word-break:break-all" });
  api("GET", `${base()}/videos_ruta`).then(r => { lugar.textContent = t("vi_estan_en") + " " + r.ruta; }).catch(() => {});
  c.append(h("div", { class: "fila", style: "margin-bottom:14px" }, h("button", { onclick: () => api("POST", `${base()}/abrir`, { sub: "videos_finalizados" }) }, "📂 " + t("abrir_carpeta")), h("span", { class: "suave chico" }, t("recordatorio"))), lugar);
  if (!v.length) { c.append(h("div", { class: "vacio" }, t("vi_ninguno"))); return; }
  const etqF = f => { const o = S.cat.ajustes.find(a => a.clave === "formato_video").opciones.find(o => o[0] === f.split("/")[0]); return f ? (o ? (S.idioma === "en" ? o[2] : o[1]).replace(/ \(.*$/, "") : t("vi_personalizado")) + (f.includes("/") ? " · " + f.split("/")[1] : "") : t("vi_sin_formato"); };
  c.append(listaBuscable({
    items: v.map(x => ({ ...x, nombre: x.nombre })), texto: x => x.nombre,
    borrar: async nombres => { const r = await api("POST", `${base()}/videos/borrar`, { nombres }); await refrescarProductos(); rec(); return r.borrados; },
    pintar: (vis, est) => {
      const tarjeta = x => {
        const f = x.formato || "";

          const nombreV = h("div", { class: "chico", style: "word-break:break-all;margin:6px 0 4px" }, x.titulo);
          const borrarV = async () => { if (!await confirmar(t("borrar") + " “" + x.nombre + "”?")) return; await api("DELETE", `${base()}/video?nombre=${encodeURIComponent(x.nombre)}`); await refrescarProductos(); rec(); };
          const nodo = h("div", { class: "vcard" + (est.sel.has(x.nombre) ? " sel" : "") },
            (() => {
              const src = `${base()}/video?nombre=${encodeURIComponent(x.nombre)}`;
              const vid = h("video", { controls: true, controlsList: "nodownload nofullscreen", preload: "metadata", style: "aspect-ratio:" + ({ vertical: "9/16", retrato: "4/5", cuadrado: "1/1", horizontal: "16/9" }[f.split("/")[0]] || "auto"), src });
              const abrirGrande = () => { const t0 = vid.currentTime; vid.pause(); verPantallaCompleta(src, t0); };
              vid.addEventListener("dblclick", e => { e.preventDefault(); abrirGrande(); });
              return h("div", { class: "vwrap" }, vid, h("button", { class: "btn-pantalla", title: t("vi_pantalla"), "aria-label": t("vi_pantalla"), onclick: abrirGrande }, "⛶"));
            })(),
            est.modo ? h("div", { class: "capa", onclick: () => tocarSel(est, x.nombre, nodo) }) : null,
            nombreV,
            est.modo ? null : h("div", { class: "fila", style: "gap:6px" },
              h("button", { class: "chico primario ver-carpeta", title: t("vi_mostrar_ayuda"), onclick: async () => { if (typeof G !== "undefined") G.descargado = true; await api("POST", `${base()}/video/mostrar`, { nombre: x.nombre }); } }, "📂 " + t("vi_mostrar")),
              h("button", { class: "chico", onclick: () => compartirVideo(x) }, "↗ " + t("compartir")),
              h("button", { class: "chico peligro", onclick: borrarV }, t("borrar"))));
          if (!est.modo) renombrable(nodo, nombreV, x.nombre.replace(/^.*\//, "").replace(/\.mp4$/, ""),
            async v => { await api("POST", `${base()}/video/renombrar`, { nombre: x.nombre, nuevo: v }); rec(); }, [[t("borrar"), borrarV, true]]);
          return nodo;
      };
      const grupos = {};
      vis.forEach(x => (grupos[x.formato || ""] = grupos[x.formato || ""] || []).push(x));
      const recientes = vis.slice(0, 8);
      return [h("div", {}, h("h3", { style: "margin:18px 0 8px" }, "🕘 " + t("vi_ultimos") + " ", h("span", { class: "suave chico" }, `(${recientes.length})`)),
        h("div", { class: "videos-fila" }, recientes.map(x => h("div", { class: "vfila-item" }, tarjeta(x), h("div", { class: "suave chico" }, etqF(x.formato || "")))))),
        carpetasVideos(grupos, etqF, tarjeta, est)];
    } }));
}

// ---------------------------------------------------------------- logos y capas (con transparencia)
const ACEPTA_CAPAS = "image/*,video/*,.png,.gif,.webp,.jpg,.jpeg,.webm,.mov,.mp4,.svg,.pdf,.ai";
async function pCapas(c, rec) {
  let capas = await api("GET", `${base()}/capas`);
  const img = h("img", { class: "capas-previa", alt: "" });
  let sec = 0;
  const previa = async () => {
    const n = ++sec;
    try { const r = await fetch(`${base()}/previa`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ valores: {} }) });
      if (n === sec && r.ok) img.src = URL.createObjectURL(await r.blob()); } catch (e) {}
  };
  let tm = null;
  const guardar = () => { clearTimeout(tm); tm = setTimeout(async () => { try { await api("PUT", `${base()}/capas`, { capas }); previa(); } catch (e) { toast(String(e.message || e), true); } }, 450); };
  const POS = ["arriba_izq", "arriba_centro", "arriba_der", "medio_izq", "centro", "medio_der", "abajo_izq", "abajo_centro", "abajo_der"];
  const campo = (etq, valor, min, max, paso, alCambiar, unidad) => h("label", { class: "capa-campo" }, h("span", {}, etq),
    h("span", { class: "fila", style: "gap:6px;flex-wrap:nowrap" }, h("input", { type: "number", min, max, step: paso, value: valor, style: "width:84px", oninput: e => alCambiar(e.target.value === "" ? 0 : +e.target.value) }), unidad ? h("span", { class: "suave chico" }, unidad) : null));
  const tarjeta = cap => {
    const mini = h("div", { class: "capa-mini" }, h("img", { src: `${base()}/capa_mini?nombre=${encodeURIComponent(cap.archivo)}`, alt: "", onerror: e => e.target.replaceWith(h("span", { class: "suave" }, "🎞")) }));
    const cambia = (k, v) => { cap[k] = v; guardar(); };
    return h("div", { class: "tarjeta capa-card" + (cap.activa ? "" : " apagada") },
      h("div", { class: "fila", style: "flex-wrap:nowrap;align-items:flex-start;gap:14px" }, mini,
        h("div", { style: "flex:1;min-width:0" },
          h("div", { class: "fila", style: "justify-content:space-between;flex-wrap:nowrap" },
            h("b", { style: "word-break:break-all" }, cap.archivo, " ", h("span", { class: "chico suave" }, cap.tipo === "animada" ? t("capa_animada") : "")),
            h("div", { class: "fila", style: "flex-wrap:nowrap;gap:10px" },
              h("label", { class: "fila chico", style: "gap:6px;flex-wrap:nowrap" }, h("span", { class: "sw" }, h("input", { type: "checkbox", checked: cap.activa, onchange: e => { cambia("activa", e.target.checked); e.target.closest(".capa-card").classList.toggle("apagada", !e.target.checked); } }), h("span")), t("capa_mostrar")),
              h("button", { class: "chico peligro", onclick: async () => { if (!await confirmar(t("borrar") + " “" + cap.archivo + "”?")) return; await api("DELETE", `${base()}/archivos/capas?nombre=${encodeURIComponent(cap.archivo)}`); capas = capas.filter(x => x !== cap); await api("PUT", `${base()}/capas`, { capas }); rec(); } }, t("borrar")))),
          h("div", { class: "capa-cols" },
            h("div", {}, h("div", { class: "chico suave", style: "margin:8px 0 4px" }, t("capa_donde")),
              h("div", { class: "capa-pos" }, POS.map(p => h("button", { type: "button", title: t("capa_p_" + p), class: "capa-pos-b" + (cap.pos === p ? " on" : ""), onclick: e => { cap.pos = p; guardar(); e.target.parentNode.querySelectorAll("button").forEach(b => b.classList.remove("on")); e.target.classList.add("on"); } }, "●")))),
            h("div", { class: "capa-campos" },
              h("label", { class: "capa-campo" }, h("span", {}, t("capa_tam") + ": ", h("b", {}, cap.ancho + "%")), h("input", { type: "range", min: 3, max: 100, value: cap.ancho, style: "accent-color:var(--acento)", oninput: e => { cap.ancho = +e.target.value; e.target.previousSibling.lastChild.textContent = cap.ancho + "%"; guardar(); } })),
              h("label", { class: "capa-campo" }, h("span", {}, t("capa_opac") + ": ", h("b", {}, cap.opacidad + "%")), h("input", { type: "range", min: 5, max: 100, value: cap.opacidad, style: "accent-color:var(--acento)", oninput: e => { cap.opacidad = +e.target.value; e.target.previousSibling.lastChild.textContent = cap.opacidad + "%"; guardar(); } })),
              h("div", { class: "fila", style: "gap:14px" }, campo(t("capa_desde"), cap.desde, 0, 3600, 0.5, v => cambia("desde", v), "s"), campo(t("capa_hasta"), cap.hasta, 0, 3600, 0.5, v => cambia("hasta", v), "s")),
              h("div", { class: "chico suave" }, t("capa_hasta_ayuda")),
              h("div", { class: "fila", style: "gap:14px" }, campo(t("capa_dx"), cap.dx, -2000, 2000, 10, v => cambia("dx", v), "px"), campo(t("capa_dy"), cap.dy, -4000, 4000, 10, v => cambia("dy", v), "px")))))));
  };
  c.append(h("div", { class: "capas-fila" },
    h("div", { class: "capas-izq" },
      h("p", { class: "suave" }, t("capa_intro")),
      zonaSubir(t("capa_subir"), ACEPTA_CAPAS, async fs => { await subirArchivos("capas", null, fs); rec(); }),
      h("p", { class: "chico suave", style: "margin:8px 0 14px" }, t("capa_formatos")),
      capas.length ? capas.map(tarjeta) : h("div", { class: "vacio" }, t("capa_ninguna"))),
    h("div", { class: "previa" }, h("h3", { style: "margin-top:0" }, t("es_previa")), img, h("p", { class: "chico suave" }, t("capa_previa_nota")))));
  previa();
}

// ---------------------------------------------------------------- compartir un video terminado
async function compartirVideo(x) {
  const ir = async (destino, aviso) => {
    try { const r = await api("POST", `${base()}/video/compartir`, { nombre: x.nombre, destino }); toast(r.copiado ? t("sh_copiado") : (aviso || t("sh_listo"))); }
    catch (e) { toast(e.message || t("act_error"), true); }
  };
  const op = (icono, titulo, ayuda, fn) => h("button", { class: "comp-op", onclick: fn }, h("span", { class: "comp-ic" }, icono), h("span", {}, h("b", {}, titulo), h("span", { class: "chico suave", style: "display:block" }, ayuda)));
  const nativo = (typeof navigator !== "undefined" && navigator.canShare && navigator.share) ? op("📲", t("sh_otras"), t("sh_otras_a"), async () => {
    try {
      const b = await (await fetch(`${base()}/video?nombre=${encodeURIComponent(x.nombre)}`)).blob();
      const f = new File([b], x.nombre.replace(/^.*\//, ""), { type: "video/mp4" });
      if (navigator.canShare({ files: [f] })) await navigator.share({ files: [f] }); else toast(t("sh_no_nativo"), true);
    } catch (e) { if (e && e.name !== "AbortError") toast(t("sh_no_nativo"), true); }
  }) : null;
  const tx = (await api("GET", `${base()}/video/texto?nombre=${encodeURIComponent(x.nombre)}`).catch(() => ({ texto: "" }))).texto || "";
  const area = h("textarea", { style: "width:100%;min-height:150px", spellcheck: false }); area.value = tx;
  const copiarTxt = async () => { try { await navigator.clipboard.writeText(area.value); } catch (e) { area.select(); document.execCommand("copy"); } toast(t("sh_txt_copiado")); };
  modal([h("h2", {}, "↗ " + t("compartir")), h("p", { class: "suave chico", style: "word-break:break-all" }, x.titulo || x.nombre),
    h("div", { class: "comp-ops" },
      op("💬", "WhatsApp Web", t("sh_wa_a"), () => ir("whatsapp")),
      op("📋", t("sh_copiar"), t("sh_copiar_a"), () => ir("copiar", t("sh_no_copia"))),
      op("📸", "Instagram", t("sh_sitio_a"), () => ir("instagram")),
      op("🎵", "TikTok", t("sh_sitio_a"), () => ir("tiktok")),
      op("👍", "Facebook", t("sh_sitio_a"), () => ir("facebook")),
      op("▶️", "YouTube", t("sh_sitio_a"), () => ir("youtube")),
      op("📂", t("sh_carpeta"), t("sh_carpeta_a"), () => ir("carpeta")),
      nativo),
    tx ? h("div", { class: "tarjeta", style: "margin:14px 0 6px" }, h("b", {}, "✍️ " + t("sh_txt_titulo")), h("div", { class: "chico suave", style: "margin:2px 0 6px" }, t("sh_txt_ayuda")), area,
      h("div", { class: "acciones", style: "margin-top:8px;justify-content:flex-start" }, h("button", { class: "primario", onclick: copiarTxt }, "📋 " + t("sh_txt_copiar")))) : null,
    h("div", { class: "acciones" }, h("button", { onclick: cerrarModal }, t("cerrar_modal")))], { ancha: true });
}

// ---------------------------------------------------------------- papelera
async function pPapelera(c, rec) {
  const items = await api("GET", `${base()}/papelera`);
  c.append(h("p", { class: "suave" }, t("pa_intro")));
  if (!items.length) { c.append(h("div", { class: "vacio" }, "🗑 " + t("pa_vacia"))); return; }
  const est = { q: "", sel: new Set() };
  const mb = b => b > 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1e3)) + " KB";
  const cuerpo = h("div", {});
  const btnR = h("button", { class: "chico primario" }), btnB = h("button", { class: "chico peligro" });
  const accion = async (a, ids) => { const r = await api("POST", `${base()}/papelera/${a}`, { ids }); await refrescarProductos(); toast(a === "restaurar" ? t("pa_restaurados", { n: r.n }) : t("pa_borrados", { n: r.n })); rec(); };
  const cuenta = () => { btnR.textContent = t("pa_restaurar", { n: est.sel.size }); btnB.textContent = t("pa_borrar", { n: est.sel.size }); btnR.disabled = btnB.disabled = !est.sel.size; };
  const pintar = () => {
    cuerpo.innerHTML = "";
    const vis = items.filter(i => i.etiqueta.toLowerCase().includes(est.q.toLowerCase()));
    if (!vis.length) poner(cuerpo, h("div", { class: "vacio chico" }, t("bus_nada")));
    vis.forEach(i => poner(cuerpo, h("label", { class: "fila-pap" },
      h("input", { type: "checkbox", checked: est.sel.has(i.nombre), onchange: e => { e.target.checked ? est.sel.add(i.nombre) : est.sel.delete(i.nombre); cuenta(); } }),
      h("span", { class: "pap-n" }, h("b", {}, i.etiqueta), h("span", { class: "suave chico" }, ` · ${t("pa_sec_" + i.seccion) || i.seccion} · ${mb(i.tam)}` + (i.detalle ? ` · ${i.detalle}` : ""))),
      h("span", { class: "suave chico" }, t("pa_quedan", { d: i.dias })))));
    cuenta();
  };
  btnR.onclick = () => accion("restaurar", [...est.sel]);
  btnB.onclick = async () => { if (await confirmar(t("pa_conf_borrar", { n: est.sel.size }), t("pa_borrar_s"))) accion("borrar", [...est.sel]); };
  c.append(h("div", { class: "fila", style: "margin:8px 0" },
    h("input", { type: "text", placeholder: "🔍 " + t("bus_ph"), style: "flex:1;min-width:150px;max-width:340px", oninput: e => { est.q = e.target.value; pintar(); } }),
    h("button", { class: "chico", onclick: () => { items.filter(i => i.etiqueta.toLowerCase().includes(est.q.toLowerCase())).forEach(i => est.sel.add(i.nombre)); pintar(); } }, t("sel_todo")),
    btnR, btnB, h("div", { class: "espacio" }),
    h("button", { class: "chico peligro", onclick: async () => { if (await confirmar(t("pa_conf_vaciar"), t("pa_vaciar"))) accion("vaciar", []); } }, t("pa_vaciar"))), cuerpo);
  pintar();
}

// ---------------------------------------------------------------- estilo
let V = {}, sucio = false, secPrev = 0, tmPrev;
function aHex(c) { try { const x = document.createElement("canvas").getContext("2d"); x.fillStyle = "#000"; x.fillStyle = c; return x.fillStyle.startsWith("#") ? x.fillStyle : "#000000"; } catch (e) { return "#000000"; } }
function formaMini(f) {    // dibujito de cada forma de burbuja (solo CSS)
  if (!f) return h("div", { class: "fm fm-igual" }, "＝");
  return h("div", { class: "fm fm-" + f }, h("i", { class: "pico" }));
}
const SECCIONES_SENCILLAS = ["titulo", "subtitulos", "frase_final", "usuario", "burbujas", "audio"];
async function pEstilo(c, rec) {
  let sonidosEstilo = await api("GET", `${base()}/archivos/sonidos`).catch(() => []);
  const BASE = base();   // el producto de ESTA pantalla (si cambias de producto antes de que guarde, guarda en el correcto)
  V = await api("GET", `${BASE}/ajustes`); sucio = false;
  const img = h("img", { alt: "" });
  const capaPrev = h("div", { class: "previa-capa" });
  const lienzo = h("div", { class: "previa-lienzo" }, img, capaPrev);
  let cajas = null, arrastrando = false;
  const selCajas = new Set(), elsCajas = {};      // Shift + clic: elige varios elementos de la vista previa para moverlos juntos
  const NOM_CAJA = { titulo: "pv_titulo", subtitulos: "pv_subtitulos", cta: "pv_cta", usuario: "pv_usuario", burbuja_cliente: "pv_burb_cliente", burbuja_yo: "pv_burb_yo", barra: "pv_barra", marca_texto: "pv_marca_texto", marca_imagen: "pv_marca_imagen" };
  const CAT_CAJA = { titulo: "titulo", subtitulos: "subtitulos", cta: "frase_final", usuario: "usuario", burbuja_cliente: "burbujas", burbuja_yo: "burbujas", barra: "animaciones", marca_texto: "animaciones", marca_imagen: "animaciones" };
  // a qué ajustes corresponde mover cada elemento (en la franja, el título y la frase final no se mueven así)
  const CLAVES_CAJA = () => { const comp = !cajas || cajas._completa !== false;
    return { titulo: comp ? { x: "titulo_x", y: "titulo_y" } : null, cta: comp ? { x: "cta_x", y: "cta_y" } : null, usuario: { x: "usuario_x", y: "usuario_y" },
      subtitulos: { x: "subs_x", y: comp ? "subs_y_completa" : "subs_y" }, burbuja_yo: { x: "burbuja_yo_x", y: "burbuja_yo_y", esc: "burbuja_yo_escala", ancla: "der" },
      burbuja_cliente: { x: "burbuja_cliente_x", y: "burbuja_cliente_ajuste", esc: "burbuja_cliente_escala", ancla: "izq" }, barra: { y: "barra_y" },
      marca_texto: { x: "marca_x", y: "marca_y" }, marca_imagen: { x: "marca_img_x", y: "marca_img_y" } }; };
  const PCT_Y = new Set(["marca_y", "marca_img_y"]);        // alturas que se guardan en % del video
  const delta = (k, v) => PCT_Y.has(k) ? v / (cajas && cajas._tam ? cajas._tam[1] : 1920) * 100 : v;
  const ANCHO_TEXTO = { titulo: "titulo_ancho", subtitulos: "subs_ancho", cta: "cta_ancho" };
  const TAM_TEXTO = { titulo: "tam_texto_arriba", subtitulos: "subs_tam", cta: "tam_cta", usuario: "usuario_tam", marca_texto: "marca_tam", marca_imagen: "marca_img_pct" };
  const limite = (k, v) => { const a = S.cat.ajustes.find(x => x.clave === k) || {}; v = Math.round(v);
    if (a.min != null) v = Math.max(a.min, v); if (a.max != null) v = Math.min(a.max, v); return v; };
  function irCategoria(id) {
    let d = lista.querySelector(`details[data-cat="${id}"]`);
    if (!d && !S.avanzado) {                    // esa sección solo está en el modo completo: se enciende solo
      S.avanzado = true; const sw = $("#modo-completo"); if (sw) sw.checked = true; pintar();
      d = lista.querySelector(`details[data-cat="${id}"]`);
    }
    if (!d) return;
    d.open = true; d.scrollIntoView({ behavior: "smooth", block: "start" });
    d.classList.add("flash-cat"); setTimeout(() => d.classList.remove("flash-cat"), 1400);
  }
  // doble clic: usuario y frase final se escriben ahí mismo; título, subtítulos y burbujas llevan al guion (su texto es de cada guion)
  function escribirEn(nombre, el) {
    const k = nombre === "cta" ? "cta" : "usuario";
    const inp = h("input", { type: "text", class: "inp-previa", value: V[k] || "", placeholder: t(NOM_CAJA[nombre]) });
    let listo = false;
    const fin = ok => { if (listo) return; listo = true; if (ok && inp.value !== (V[k] || "")) { V[k] = inp.value; pintar(); mover(); } inp.remove(); };
    inp.addEventListener("keydown", e => { e.stopPropagation(); if (e.key === "Enter") fin(true); else if (e.key === "Escape") fin(false); });
    inp.addEventListener("blur", () => fin(true));
    inp.style.top = el.style.top; capaPrev.append(inp); inp.focus(); inp.select();
  }
  async function irAGuion(que) {
    if (sucio) await guardarAjustes(false);
    if (!guionSel) { try { const l = await api("GET", `${base()}/guiones`); const g = l.find(x => x.activo && x.tiene_audio !== false) || l[0]; if (g) guionSel = g.nombre; } catch (e) {} }
    S.pestana = "guiones"; guardarSesion(); producto();
    if (!guionSel) { toast(t("pv_elige_guion")); return; }
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 120));
      let el = null;
      if (que === "titulo") { const b = [...document.querySelectorAll("#contenido b")].find(x => x.textContent.trim() === t("gui_titulo_lbl")); el = b && b.closest(".tarjeta") && b.closest(".tarjeta").querySelector("input[type=text], input:not([type])"); }
      else if (que === "texto") el = document.querySelector("#contenido textarea");
      else el = [...document.querySelectorAll("#contenido h3")].find(x => x.textContent.trim() === t("bu_titulo"));
      if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); if (que !== "burbujas") el.focus(); return; }
    }
  }
  function pintarCajas() {
    capaPrev.innerHTML = "";
    if (!cajas || !cajas._tam) return;
    const [W, H] = cajas._tam, CL = CLAVES_CAJA();
    const area = n => cajas[n] ? (cajas[n][2] - cajas[n][0]) * (cajas[n][3] - cajas[n][1]) : 0;
    Object.keys(NOM_CAJA).sort((a, b) => area(b) - area(a)).forEach(nombre => {     // las más chicas encima, para poder tocarlas
      const b = cajas[nombre]; if (!b) return;
      const mueveBase = CL[nombre], esBurb = nombre.startsWith("burbuja");
      const el = h("div", { class: "caja-prev" + (mueveBase ? " mueve" : "") + (esBurb ? " burb" : ""), title: t(NOM_CAJA[nombre]),
        style: `left:${b[0] / W * 100}%;top:${b[1] / H * 100}%;width:${(b[2] - b[0]) / W * 100}%;height:${(b[3] - b[1]) / H * 100}%` },
        h("span", { class: "caja-et" }, t(NOM_CAJA[nombre])));
      // mover (arrastrar). Con Shift se mueve en línea recta (0°, 45°, 90°…); con Alt (solo burbujas) se mueven todas juntas
      elsCajas[nombre] = el; if (selCajas.has(nombre)) el.classList.add("elegida");
      el.addEventListener("pointerdown", e => {
        if (e.target.classList.contains("asa")) return;
        e.preventDefault(); el.setPointerCapture(e.pointerId);
        const r = img.getBoundingClientRect(), x0 = e.clientX, y0 = e.clientY;
        const juntos = selCajas.has(nombre) && selCajas.size > 1;         // si arrastras uno de los elegidos, se mueven todos
        const grupo = juntos ? [...selCajas].filter(n => elsCajas[n] && CL[n]) : [nombre];
        const mueveDe = n => n === nombre ? (esBurb && e.altKey ? { x: "burbuja_x", y: "burbuja_y" } : mueveBase) : CL[n];
        const ini = {}; grupo.forEach(n => { const m = mueveDe(n); if (m) Object.values(m).forEach(k => { if (k !== "izq" && k !== "der") ini[k] = +V[k] || 0; }); });
        const mueve = mueveDe(nombre);
        let movio = false, d = null;
        el.onpointermove = ev => {
          let dxs = ev.clientX - x0, dys = ev.clientY - y0;
          if (!movio && Math.hypot(dxs, dys) < 4) return;
          if (ev.shiftKey && !juntos) { const ang = Math.round(Math.atan2(dys, dxs) / (Math.PI / 4)) * (Math.PI / 4), len = Math.hypot(dxs, dys); dxs = len * Math.cos(ang); dys = len * Math.sin(ang); }
          movio = true; arrastrando = true;
          d = { x: dxs / r.width * W, y: dys / r.height * H };
          grupo.forEach(n => { const m = mueveDe(n), e2 = elsCajas[n]; if (!m || !e2) return; e2.classList.add("arrastra"); e2.style.transform = `translate(${m.x ? dxs : 0}px,${dys}px)`; });
        };
        el.onpointerup = ev => {
          el.onpointermove = el.onpointerup = null; grupo.forEach(n => elsCajas[n] && elsCajas[n].classList.remove("arrastra")); arrastrando = false;
          if (!movio) {
            if (ev.shiftKey) { selCajas.has(nombre) ? selCajas.delete(nombre) : selCajas.add(nombre); pintarCajas(); return; }   // Shift + clic: elegir o quitar
            if (selCajas.size) { selCajas.clear(); pintarCajas(); }
            clearTimeout(el._tc); el._tc = setTimeout(() => irCategoria(CAT_CAJA[nombre]), 260); return;
          }
          if (!d) { grupo.forEach(n => elsCajas[n] && (elsCajas[n].style.transform = "")); return; }
          grupo.forEach(n => { const m = mueveDe(n); if (!m) return;
            if (m.y) V[m.y] = limite(m.y, ini[m.y] + delta(m.y, d.y));
            if (m.x) V[m.x] = limite(m.x, ini[m.x] + d.x); });
          pintar(); mover();
        };
      });
      // cambiar tamaño (burbujas): asas arriba, al lado y en la esquina; siempre crece o se achica parejo, fija en su esquina de abajo
      if (esBurb && mueveBase && mueveBase.esc) {
        const izq = mueveBase.ancla === "izq";
        [["arriba", "n"], [izq ? "lado-d" : "lado-i", "e"], [izq ? "esq-d" : "esq-i", "c"]].forEach(([cls, tipo]) => {
          const asa = h("div", { class: "asa " + cls, title: t("pv_tam") }); el.append(asa);
          asa.addEventListener("pointerdown", e => {
            e.preventDefault(); e.stopPropagation(); asa.setPointerCapture(e.pointerId);
            const rb = el.getBoundingClientRect(), ax = izq ? rb.left : rb.right, ay = rb.bottom;
            const px0 = e.clientX, py0 = e.clientY, esc0 = +V[mueveBase.esc] || 100;
            const d0x = Math.abs(px0 - ax) || 1, d0y = Math.abs(ay - py0) || 1;
            let f = 1;
            asa.onpointermove = ev => {
              const fx = Math.abs(ev.clientX - ax) / d0x, fy = Math.abs(ay - ev.clientY) / d0y;
              f = tipo === "n" ? fy : tipo === "e" ? fx : Math.hypot(ev.clientX - ax, ay - ev.clientY) / Math.hypot(d0x, d0y);
              if (ev.shiftKey) f = Math.round(f * 20) / 20;             // con Shift, de 5 en 5 %
              f = Math.max(0.4, Math.min(2.2, f)); arrastrando = true;
              el.classList.add("arrastra"); el.style.transformOrigin = `${izq ? 0 : 100}% 100%`; el.style.transform = `scale(${f})`;
            };
            asa.onpointerup = () => {
              asa.onpointermove = asa.onpointerup = null; el.classList.remove("arrastra"); arrastrando = false;
              V[mueveBase.esc] = limite(mueveBase.esc, esc0 * f); pintar(); mover();
            };
          });
        });
      }
      // cambiar tamaño de la letra (título, subtítulos, frase final, usuario): punto en la esquina, arrastra para agrandar o achicar
      if (TAM_TEXTO[nombre]) {
        const kT = TAM_TEXTO[nombre];
        el.classList.add("txt-tam");
        const asa = h("div", { class: "asa esq-d", title: t("pv_tam") }); el.append(asa);
        asa.addEventListener("pointerdown", e => {
          e.preventDefault(); e.stopPropagation(); asa.setPointerCapture(e.pointerId);
          const rb = el.getBoundingClientRect(), cx = rb.left + rb.width / 2, cy = rb.top + rb.height / 2;
          const d0 = Math.hypot(e.clientX - cx, e.clientY - cy) || 1, v0 = +V[kT] || (kT === "marca_tam" ? +V.tam_texto_arriba || 110 : 80);
          let f = 1;
          asa.onpointermove = ev => {
            f = Math.max(0.4, Math.min(2.5, Math.hypot(ev.clientX - cx, ev.clientY - cy) / d0));
            if (ev.shiftKey) f = Math.round(f * 20) / 20;
            arrastrando = true; el.classList.add("arrastra"); el.style.transformOrigin = "50% 50%"; el.style.transform = `scale(${f})`;
          };
          asa.onpointerup = () => {
            asa.onpointermove = asa.onpointerup = null; el.classList.remove("arrastra"); arrastrando = false;
            V[kT] = limite(kT, v0 * f); pintar(); mover();
          };
        });
      }
      // cambiar el ancho de la zona del texto (título, subtítulos, frase final): puntos a los lados; el texto se acomoda dentro
      if (ANCHO_TEXTO[nombre] && mueveBase) {
        const kA = ANCHO_TEXTO[nombre];
        [["lado-i", -1], ["lado-d", 1]].forEach(([cls, lado]) => {
          const asa = h("div", { class: "asa " + cls, title: t("pv_ancho") }); el.append(asa);
          asa.addEventListener("pointerdown", e => {
            e.preventDefault(); e.stopPropagation(); asa.setPointerCapture(e.pointerId);
            const r = img.getBoundingClientRect(), x0 = e.clientX, a0 = +V[kA] > 0 ? +V[kA] : W - 120;
            let nuevo = a0;
            asa.onpointermove = ev => {
              nuevo = Math.max(200, Math.min(2160, a0 + 2 * lado * (ev.clientX - x0) / r.width * W));
              if (ev.shiftKey) nuevo = Math.round(nuevo / 20) * 20;
              arrastrando = true; el.classList.add("arrastra"); el.style.transformOrigin = "50% 50%"; el.style.transform = `scaleX(${nuevo / a0})`;
            };
            asa.onpointerup = () => {
              asa.onpointermove = asa.onpointerup = null; el.classList.remove("arrastra"); arrastrando = false;
              V[kA] = limite(kA, nuevo); pintar(); mover();
            };
          });
        });
      }
      el.addEventListener("dblclick", e => {
        e.preventDefault(); clearTimeout(el._tc);
        if (nombre === "usuario" || nombre === "cta") escribirEn(nombre, el);
        else irAGuion(nombre === "titulo" ? "titulo" : nombre === "subtitulos" ? "texto" : "burbujas");
      });
      capaPrev.append(el);
    });
  }
  async function guardarAjustes(manual) {
    const btn = $("#sg"), aviso = $("#aviso-sg");
    if (aviso) { aviso.style.color = ""; aviso.textContent = t("es_guardando"); }
    const r = await api("PUT", `${BASE}/ajustes`, { valores: V });
    const ks = Object.keys(r.errores);
    if (ks.length) { const m = ks.map(k => r.errores[k]).join(" · "); if (manual) toast(m, true); if ($("#aviso-sg")) { $("#aviso-sg").style.color = "var(--mal)"; $("#aviso-sg").textContent = m; } return; }
    if (manual) toast(t("es_ok"));
    sucio = false;
    if ($("#sg")) $("#sg").disabled = true;
    if ($("#aviso-sg")) { $("#aviso-sg").style.color = ""; $("#aviso-sg").textContent = t("auto_guardado") + " · " + horaCorta(); }
  }
  const mover = () => { sucio = true; $("#sg") && ($("#sg").disabled = false); $("#aviso-sg") && ($("#aviso-sg").style.color = "var(--mal)", $("#aviso-sg").textContent = t("es_sin_guardar")); clearTimeout(tmPrev); tmPrev = setTimeout(previa, 350); autoguardar("estilo:" + BASE, () => guardarAjustes(false)); };
  async function previa() {
    const n = ++secPrev;
    try { const r = await fetch(`${base()}/previa`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ valores: V }) });
      if (n === secPrev && r.ok) { const u = URL.createObjectURL(await r.blob()); img.src = u;
        try { cajas = JSON.parse(r.headers.get("X-Cajas") || "null"); } catch (e) { cajas = null; }
        if (!arrastrando) pintarCajas(); } } catch (e) {}
  }
  const ctl = a => {
    const k = a.clave, n = t => (S.idioma === "en" ? a.en : a.es);
    const set = v => { V[k] = v; mover(); };
    let control;
    if (SONIDO_CLAVES.includes(k)) {
      const sinSon = k === "burbuja_sonido" ? t("es_son_pop") : t("es_son_nada");
      const probar = () => { const v = V[k]; if (!v) return; new Audio(v.startsWith("@") ? `/api/sonido_base/${encodeURIComponent(v.slice(1))}` : `${base()}/archivo/sonidos?nombre=${encodeURIComponent(v)}`).play(); };
      const subir = botonSubir(t("es_son_subir"), "audio/*,.mp3,.wav,.m4a,.aac,.ogg,.oga,.opus,.flac,.wma,.amr,.weba,.3ga", async fs => {
        const nuevos = await subirArchivos("sonidos", null, fs);
        sonidosEstilo = await api("GET", `${base()}/archivos/sonidos`).catch(() => sonidosEstilo);
        if (nuevos.length) { set(String(nuevos[0].nombre || nuevos[0])); pintar(); }
      });
      control = h("div", { class: "ctl", style: "flex:1;flex-wrap:wrap" }, h("select", { style: "max-width:260px", onchange: e => set(e.target.value) },
        h("option", { value: "", selected: !V[k] }, sinSon),
        h("optgroup", { label: t("es_son_app") }, ["pop", "ding", "click", "whoosh"].map(x => h("option", { value: "@" + x, selected: V[k] === "@" + x }, t("es_sonb_" + x)))),
        sonidosEstilo.length ? h("optgroup", { label: t("es_son_mios") }, sonidosEstilo.map(x => h("option", { value: x.nombre, selected: V[k] === x.nombre }, x.nombre))) : null),
        h("button", { class: "chico", title: t("bu_probar"), onclick: probar }, "▶"), subir);
    } else if (a.tipo === "si_no") control = h("label", { class: "sw" }, h("input", { type: "checkbox", checked: V[k], onchange: e => set(e.target.checked) }), h("span"));
    else if (a.tipo === "entero" || a.tipo === "decimal") {
      const paso = a.tipo === "entero" ? 1 : 0.05;
      const num = h("input", { class: "num", type: "number", value: V[k], step: paso, min: a.min ?? undefined, max: a.max ?? undefined });
      const rng = (a.min != null && a.max != null) ? h("input", { type: "range", min: a.min, max: a.max, step: paso, value: V[k] }) : null;
      num.addEventListener("input", () => { if (num.value === "") return; V[k] = +num.value; if (rng) rng.value = num.value; mover(); });
      if (rng) rng.addEventListener("input", () => { num.value = rng.value; V[k] = +rng.value; mover(); });
      control = h("div", { class: "ctl", style: "flex:1" }, rng, num, a.unidad ? h("span", { class: "suave chico" }, a.unidad) : null);
    } else if (a.tipo === "color") {
      const txt = h("input", { type: "text", value: V[k], style: "width:130px", placeholder: t("auto") });
      const pk = h("input", { type: "color", value: aHex(V[k] || "#000000") });
      pk.addEventListener("input", () => { txt.value = pk.value; V[k] = pk.value; mover(); });
      txt.addEventListener("input", () => { V[k] = txt.value; if (!txt.value || /^#[0-9a-f]{6}$/i.test(txt.value)) { if (txt.value) pk.value = txt.value; mover(); } });
      control = h("div", { class: "ctl" }, pk, txt);
    } else if (a.tipo === "fuente") {
      const id = "f_" + k;
      const subirF = botonSubir(t("es_fuente_subir"), ".ttf,.otf", async fs => {
        const fd = new FormData(); [...fs].forEach(f => fd.append("archivos", f));
        const r = await enviarConProgreso("/api/fuentes", fd, null);
        (r.errores || []).forEach(e => toast(e, true));
        S.cat.fuentes = r.todas; S.fuentesPropias = r.propias;
        if ((r.subidas || []).length) { set(r.subidas[0]); toast(t("subidos") + ": " + r.subidas.length); pintar(); }
      });
      control = h("div", { class: "ctl", style: "flex:1;flex-wrap:wrap" }, h("input", { type: "text", list: id, value: V[k], placeholder: t("elegir_fuente"), oninput: e => set(e.target.value.trim()) }),
        h("datalist", { id }, S.cat.fuentes.map(f => h("option", { value: f }))), subirF,
        k === "fuente" ? h("div", { class: "suave chico", style: "width:100%" }, t("es_fuente_ayuda")) : null,
        (S.fuentesPropias || []).length && k === "fuente" ? h("div", { class: "chips-fuentes" }, (S.fuentesPropias || []).map(n => h("span", { class: "chip-fuente" }, n.replace(/\.[^.]+$/, ""),
          h("button", { class: "x", title: t("borrar"), onclick: async () => { const r = await api("POST", "/api/fuentes/borrar", { nombre: n }); S.cat.fuentes = r.todas; S.fuentesPropias = r.propias; pintar(); } }, "×")))) : null);
    } else if (a.tipo === "opcion") {
      const alCambiar = k !== "formato_video" ? (e => set(e.target.value)) : (async e => {
        const nuevo = e.target.value, antes = V[k];
        if (nuevo === "personalizado") { set(nuevo); return; }
        if (!(await confirmar(t("fm_confirmar"), t("es_aplicar")))) { e.target.value = antes; return; }
        await api("PUT", `${base()}/ajustes`, { valores: V });
        await api("POST", `${base()}/formato`, { formato: nuevo });
        toast(t("fm_listo")); rec();
      });
      if (k.startsWith("burbuja_forma")) {      // forma de las burbujas: se elige viendo un dibujito de cada una
        const fila = h("div", { class: "forma-ops" });
        const pintarF = () => { fila.replaceChildren(...a.opciones.map(o => h("button", { type: "button", class: "forma-op" + (V[k] === o[0] ? " on" : ""), title: S.idioma === "en" ? o[2] : o[1],
          onclick: () => { set(o[0]); pintarF(); } }, formaMini(o[0]), h("span", {}, S.idioma === "en" ? o[2] : o[1])))); };
        pintarF();
        return h("div", { class: "ajuste" }, h("label", { class: "n" }, n()), h("div", { class: "ayuda" }, S.idioma === "en" ? a.ayuda_en : a.ayuda_es), fila);
      }
      control = h("select", { style: "max-width:260px", onchange: alCambiar }, a.opciones.map(o => h("option", { value: o[0], selected: V[k] === o[0] }, S.idioma === "en" ? o[2] : o[1])));
    } else if (a.tipo === "lista") {
      const cur = new Set(String(V[k] || "").split(",").filter(Boolean));
      const nombres = { ...S.cat.transiciones, ...S.cat.efectos };
      control = h("div", { class: "checks" }, a.opciones.map(o => h("label", {}, h("input", { type: "checkbox", checked: cur.has(o), onchange: e => { e.target.checked ? cur.add(o) : cur.delete(o); V[k] = a.opciones.filter(x => cur.has(x)).join(","); mover(); } }), nombres[o] ? nombres[o][S.idioma] : o)));
    } else control = h("input", { type: "text", value: V[k], oninput: e => set(e.target.value) });
    return h("div", { class: "ajuste" }, h("label", { class: "n" }, n()), h("div", { class: "ayuda" }, S.idioma === "en" ? a.ayuda_en : a.ayuda_es), control);
  };
  const lista = h("div", {});
  const pintar = () => {
    const yaAbiertos = lista.children.length ? new Set([...lista.querySelectorAll("details[open]")].map(d => d.dataset.cat)) : null;
    lista.innerHTML = "";
    const abierto = yaAbiertos || new Set(["titulo"]);
    S.cat.categorias.forEach(cat => {
      if (!S.avanzado && !SECCIONES_SENCILLAS.includes(cat.id)) return;      // modo sencillo: solo lo esencial
      const aj = S.cat.ajustes.filter(a => a.categoria === cat.id && a.clave !== "musica_archivo" && (S.avanzado || a.nivel === "basico"));
      if (!aj.length) return;
      const det = h("details", { class: "cat tarjeta", "data-cat": cat.id, open: abierto.has(cat.id) }, h("summary", {}, S.idioma === "en" ? cat.en : cat.es), aj.map(ctl));
      det.addEventListener("toggle", () => {      // una sola sección abierta a la vez: la pantalla queda corta y ordenada
        if (det.open) lista.querySelectorAll("details[open]").forEach(o => { if (o !== det) o.open = false; });
      });
      lista.append(det);
    });
  };
  pintar();
  const estilos = await api("GET", "/api/estilos");
  const selE = h("select", { style: "flex:1" }, estilos.map(e => h("option", { value: e }, e)));
  c.append(h("div", { class: "estilo" },
    h("div", {},
      h("div", { class: "tarjeta", style: "margin-bottom:14px" },
        h("b", {}, t("es_listos")), h("div", { class: "chico suave", style: "margin:2px 0 8px" }, t("es_listos_ayuda")),
        h("div", { class: "estilos-listos" }, Object.entries(S.cat.estilos_listos || {}).map(([id, e]) => h("button", { type: "button", class: "estilo-listo", title: S.idioma === "en" ? e.den : e.des,
          onclick: async () => {
            if (!(await confirmar(t("es_listo_conf", { n: S.idioma === "en" ? e.en : e.es }), t("es_aplicar")))) return;
            await api("PUT", `${base()}/ajustes`, { valores: e.valores }); toast(t("es_aplicado")); rec(); } },
          h("span", { class: "sw-listo" }, [e.valores.color_texto, e.valores.subs_color_activo, e.valores.color_burbuja_yo].map(col => h("i", { style: "background:" + col }))),
          h("b", {}, S.idioma === "en" ? e.en : e.es)))),
        h("div", { class: "fila", style: "margin-top:14px" }, h("b", {}, t("es_estilos")),
          estilos.length ? [selE, h("button", { onclick: async () => { const r = await api("POST", `${base()}/estilos/aplicar`, { nombre: selE.value }); toast(t("es_aplicado")); rec(); } }, t("es_aplicar")),
            h("button", { class: "peligro", onclick: async () => { await api("DELETE", `/api/estilos/${encodeURIComponent(selE.value)}`); rec(); } }, "×")] : null,
          h("button", { onclick: async () => { const r = await pedirTexto(t("es_guardar_estilo"), t("es_nombre_estilo")); if (!r) return; await api("POST", "/api/estilos", { nombre: r.valor, valores: V, producto: S.pid }); toast(t("es_estilo_guardado")); rec(); } }, t("es_guardar_estilo"))),
        h("div", { class: "chico suave", style: "margin-top:8px" }, t("es_estilo_ayuda"))),
      h("div", { class: "fila", style: "margin-bottom:12px" },
        h("button", { class: "primario", id: "sg", disabled: true, hidden: true, onclick: () => guardarAjustes(true) }, t("es_guardar")),
        h("span", { id: "aviso-sg", class: "chico suave" }, t("auto_guardado_inicio")),
        h("div", { class: "espacio" }),
        h("label", { class: "fila chico" }, h("span", { class: "sw" }, h("input", { type: "checkbox", id: "modo-completo", checked: S.avanzado, onchange: e => { S.avanzado = e.target.checked; pintar(); } }), h("span")), t("es_avanzado"))),
      lista),
    h("div", { class: "previa" }, h("h3", { style: "margin-top:0" }, t("es_previa")),
      h("label", { class: "chico fila", style: "gap:6px;margin:0 0 6px;align-items:center" }, h("input", { type: "checkbox", class: "chk-ver-marcas", checked: !!V._ver_marcas, onchange: e => { V._ver_marcas = e.target.checked; previa(); } }), t("pv_ver_marcas")), lienzo, h("p", { class: "chico suave" }, t("es_previa_nota")), h("p", { class: "chico suave" }, t("es_previa_toca")))));
  previa();
}

// ---------------------------------------------------------------- arranque
async function historial() {
  const app = $("#app"); app.innerHTML = "";
  let filtro = S.pid || "", q = "";
  const caja = h("div", {});
  const nombreProd = id => (S.productos.find(p => p.id === id) || {}).nombre || id;
  const pintar = async () => {
    const todos = await api("GET", "/api/historial" + (filtro ? `?producto=${encodeURIComponent(filtro)}` : ""));
    const ql = q.trim().toLowerCase();
    const hs = !ql ? todos : todos.filter(e => [e.fecha, e.usuario, nombreProd(e.producto_id), e.video, e.formato, e.guion, e.estilo].join(" ").toLowerCase().includes(ql));
    caja.innerHTML = "";
    if (!todos.length) { caja.append(h("div", { class: "vacio" }, t("hi_ninguno"))); return; }
    if (!hs.length) { caja.append(h("div", { class: "vacio chico" }, t("bus_nada"))); return; }
    const th = k => h("th", {}, t(k));
    caja.append(h("div", { class: "tabla-scroll" }, h("table", { class: "tabla" },
      h("thead", {}, h("tr", {}, ["hi_fecha", "hi_hora", "hi_usuario", "hi_producto", "hi_video", "hi_formato", "hi_guion", "hi_estilo"].map(th))),
      h("tbody", {}, hs.map(e => h("tr", {},
        h("td", {}, e.fecha), h("td", {}, (e.hora || "").slice(0, 5)), h("td", {}, e.usuario), h("td", {}, nombreProd(e.producto_id)),
        h("td", { style: "word-break:break-all" }, e.video), h("td", {}, (e.formato || "") + (e.medidas ? ` (${e.medidas})` : "")),
        h("td", {}, (e.guion || "") + (e.guion_elegido ? " ✋" : "")), h("td", {}, e.estilo)))))),
      h("p", { class: "chico suave" }, t("hi_nota")));
  };
  const sel = h("select", { style: "max-width:260px", onchange: e => { filtro = e.target.value; pintar(); } },
    h("option", { value: "" }, t("hi_todos")), S.productos.map(p => h("option", { value: p.id, selected: p.id === filtro }, p.nombre)));
  app.append(h("div", { class: "fila", style: "margin-bottom:12px" },
    h("button", { onclick: () => { S.vista = null; render(); } }, "← " + t("hi_volver")),
    h("h1", { style: "margin:0 0 0 8px" }, "📋 " + t("historial")), h("div", { class: "espacio" }),
    h("input", { type: "text", class: "inp-buscar-hist", placeholder: "🔍 " + t("bus_ph"), style: "max-width:240px", oninput: e => { q = e.target.value; pintar(); } }), sel,
    h("button", { onclick: () => { location.href = "/api/historial.csv" + (filtro ? `?producto=${encodeURIComponent(filtro)}` : ""); } }, t("hi_excel"))),
    h("p", { class: "suave" }, t("hi_intro")), caja);
  pintar();
}
// ---------------------------------------------------------------- preguntas frecuentes
const FAQ = [["general", [1, 2, 3, 4, 5, 26, 31]], ["planes", [6, 7, 8, 9, 10, 28, 30]], ["creditos", [11, 12]], ["claves", [13, 14, 15, 16, 29]],
  ["voz", [17, 18, 19]], ["datos", [20, 21, 22]], ["problemas", [23, 24, 25, 27]]];
function faq() {
  const app = $("#app"); app.innerHTML = "";
  let q = "";
  const cuerpo = h("div", {});
  const pintar = () => {
    cuerpo.innerHTML = "";
    const ql = q.trim().toLowerCase();
    let hay = 0;
    FAQ.forEach(([sec, ids]) => {
      const vis = ids.filter(n => !ql || (t("faq_q" + n, { m: S.marca }) + " " + t("faq_a" + n, { m: S.marca })).toLowerCase().includes(ql));
      if (!vis.length) return;
      hay += vis.length;
      cuerpo.append(h("h3", { style: "margin:22px 0 8px" }, t("faq_sec_" + sec)),
        ...vis.map(n => h("details", { class: "faq-item", open: !!ql && vis.length <= 3 }, h("summary", {}, t("faq_q" + n, { m: S.marca })), h("p", {}, t("faq_a" + n, { m: S.marca })))));
    });
    if (!hay) cuerpo.append(h("div", { class: "vacio chico" }, t("faq_nada")));
  };
  app.append(h("div", { class: "fila", style: "margin-bottom:12px" },
      h("button", { onclick: () => { S.vista = null; render(); } }, "← " + t("faq_volver")),
      h("h1", { style: "margin:0 0 0 8px" }, "❓ " + t("faq_titulo"))),
    h("p", { class: "suave" }, t("faq_intro")),
    h("input", { type: "text", class: "inp-buscar-faq", placeholder: "🔍 " + t("faq_buscar_ph"), style: "max-width:420px", oninput: e => { q = e.target.value; pintar(); } }),
    cuerpo);
  pintar();
}
function abrirFaq() { cerrarModal(); S.vista = "faq"; render(); }
// pie de página con los derechos y el aviso legal
function pie() {
  const f = $("#pie"); if (!f) return;
  const ahora = new Date().getFullYear(), ini = S.anioInicio || ahora;
  const anios = ahora > ini ? `${ini}–${ahora}` : `${ini}`;
  f.innerHTML = "";
  poner(f, h("div", {}, `© ${anios} ${S.titular || S.marca}. ${t("pie_derechos")}`),
    h("div", {}, h("span", {}, `${S.marca} v${S.version || ""}`), " · ", h("button", { class: "link", onclick: abrirFaq }, t("faq_titulo")), " · ", h("button", { class: "link", onclick: avisoLegal }, t("pie_legal")),));
}
function fmtSeg(s) { return s >= 60 ? t("min_s", { m: Math.floor(s / 60), s: Math.round(s % 60) }) : t("seg_s", { s: Math.round(s) }); }
async function cargarPlan() { try { S.plan = await api("GET", "/api/plan"); } catch (e) {} return S.plan; }
const durTxt = sg => sg >= 3600 && sg % 3600 === 0 ? t("dur_h", { n: sg / 3600 }) : sg >= 60 && sg % 60 === 0 ? t("dur_min", { n: sg / 60 }) : fmtSeg(sg);
// tarjetas con los planes y sus precios (el plan Pro se destaca: cuesta poco más que el Básico y da mucho más)
function tarjetasPlanes(P) {
  const pp = P.precios_planes || {}, LS = P.planes || {};
  if (!pp.basico || !LS.basico) return null;
  const sl = v => v ? v : t("plan_sin_limite");
  const cal = c => ({ 720: "720p", 1080: "1080p", 2160: "4K" }[c] || c);
  const carta = (id, rec) => {
    const L = LS[id], pr = pp[id];
    const lineas = [t("pp_videos", { n: sl(L.videos_mes) }), t("pp_calidad", { c: cal(L.calidad) }), t("pp_duracion", { d: L.duracion ? durTxt(L.duracion) : t("plan_sin_limite") }),
      t("pp_usuarios", { p: sl(L.productos) }), t("pp_guiones", { n: sl(L.guiones) }), L.marca_agua ? t("pp_con_marca") : t("pp_sin_marca"), L.voz_elevenlabs ? t("pp_el") : null,
      L.multiformato ? t("pp_multi") : null, L.plantillas_nicho ? t("pp_plant") : null, L.uso_clientes ? t("pp_clientes") : null].filter(Boolean);
    return h("div", { class: "plan-card" + (rec ? " rec" : "") + (P.plan === id ? " actual" : "") },
      rec ? h("div", { class: "cinta" }, "⭐ " + t("pp_rec")) : (P.plan === id ? h("div", { class: "cinta suave" }, "✓ " + t("pp_tu_plan")) : null),
      h("b", {}, L.nombre),
      pr ? [h("div", { class: "precio" }, "$" + pr.mes, h("span", { class: "chico suave" }, " USD " + t("pp_mes"))),
        h("div", { class: "chico ahorro" }, t("pp_anual", { a: pr.anio }))] : h("div", { class: "precio" }, "$0", h("span", { class: "chico suave" }, " USD")),
      h("ul", {}, lineas.map(x => h("li", {}, x))));
  };
  return h("div", { style: "margin:14px 0" }, h("h3", { style: "margin:0 0 8px" }, t("pp_titulo")),
    h("div", { class: "rejilla-planes cuatro" }, carta("gratis"), carta("basico"), carta("pro", true), LS.agencia ? carta("agencia") : null),
    P.fundador ? h("div", { class: "tarjeta chico", style: "margin-top:10px" }, h("b", {}, "🏅 " + t("pp_fundador", { usd: P.fundador.usd, n: P.fundador.cupos })), h("div", { class: "suave" }, t("pp_fundador_txt"))) : null,
    P.equipos ? h("div", { class: "chico suave", style: "margin-top:8px" }, "👥 " + t("pp_equipos", { l: P.equipos.map(e => t("pp_equipo_n", { n: e[0], usd: e[1] })).join(" · ") })) : null,
    h("div", { class: "chico suave", style: "margin-top:6px" }, t("pp_nota") + " " + t("pp_garantia")),
    h("div", { style: "margin-top:6px" }, h("button", { class: "link", onclick: abrirFaq }, t("faq_btn"))));
}
// Tarjeta de membresía (como Canva o Netflix): plan, estado, desde cuándo, próxima renovación, uso del periodo y cómo administrarla
function tarjetaMembresia(P) {
  const lic = P.licencia, L = P.limites;
  const fecha = (iso, anio) => iso ? new Date(iso.length <= 10 ? iso + "T12:00:00" : iso).toLocaleDateString(S.idioma === "en" ? "en-US" : "es-MX", { day: "numeric", month: "long", ...(anio ? { year: "numeric" } : {}) }) : "";
  const gum = lic && lic.origen === "gumroad";
  const nombre = P.nombre;
  const estado = !lic ? "gratis" : (gum ? (lic.vigente && lic.estado === "activa" ? "activa" : (lic.estado === "cancelada" ? "cancelada" : (lic.estado === "pago_pendiente" ? "pago" : "inactiva"))) : "activa");
  const etiqueta = { gratis: t("mb_gratis"), activa: t("mb_activa"), cancelada: t("mb_cancelada"), pago: t("mb_pago"), inactiva: t("mb_inactiva") }[estado];
  const tope = L.videos_mes, usados = P.videos_usados, pct = tope ? Math.min(100, Math.round(usados * 100 / tope)) : 0;
  const filas = [];
  if (lic && lic.desde) filas.push([t("mb_desde"), fecha(lic.desde, true)]);
  if (gum && lic.periodo) filas.push([t("mb_factura"), lic.periodo === "anio" ? t("mb_anual") : lic.periodo === "vida" ? t("mb_vida") : t("mb_mensual")]);
  if (gum && estado === "activa" && lic.proximo_cobro) filas.push([t("mb_prox_cobro"), fecha(lic.proximo_cobro, true)]);
  if (gum && (estado === "cancelada" || estado === "pago") && lic.hasta) filas.push([t("mb_acceso_hasta"), fecha(lic.hasta, true)]);
  const ir = id => { const el = document.getElementById(id); if (el) el.scrollIntoView({ behavior: "smooth", block: "center" }); };
  return h("div", { class: "membresia estado-" + estado },
    h("div", { class: "mb-cab" }, h("div", {}, h("div", { class: "chico suave" }, t("mb_tu_plan")), h("div", { class: "mb-plan" }, nombre)), h("span", { class: "mb-estado" }, "● " + etiqueta)),
    filas.length ? h("div", { class: "mb-filas" }, filas.map(([k, v]) => h("div", {}, h("span", { class: "suave" }, k), h("b", {}, v)))) : null,
    h("div", { class: "mb-uso" },
      h("div", { class: "fila", style: "justify-content:space-between" }, h("span", {}, t("mb_videos")), h("b", {}, tope ? `${usados} / ${tope}` : String(usados))),
      tope ? h("div", { class: "mb-barra" }, h("i", { style: `width:${pct}%` + (pct >= 100 ? ";background:var(--mal)" : "") })) : null,
      h("div", { class: "chico suave" }, P.renueva_por_compra ? t("mb_reinicia_compra", { f: fecha(P.renueva) }) : t("mb_reinicia_gratis", { f: fecha(P.renueva) }))),
    gum ? h("div", { class: "chico", style: "margin-top:10px" }, t("lic_" + lic.estado, { p: nombre, f: fecha(lic.hasta, true), d: fecha(lic.verificar_antes, true) })) : null,
    h("div", { class: "acciones", style: "margin-top:12px;justify-content:flex-start" },
      h("button", { class: "primario", onclick: () => ir("tarjetas-planes") }, estado === "gratis" ? t("mb_mejorar") : t("mb_cambiar")),
      gum ? h("button", { onclick: () => P.url_suscripcion ? window.open(P.url_suscripcion, "_blank") : modal([h("h2", {}, t("lic_admin_titulo")), h("p", {}, t("lic_admin_txt")), h("p", { class: "chico suave" }, t("mb_cambio_nota")),
        h("div", { class: "acciones" }, h("button", { class: "primario", onclick: () => { cerrarModal(); miPlan(); } }, t("cerrar_modal")))]) }, t("mb_administrar")) : null,
      gum ? h("button", { onclick: async () => { const r = await api("POST", "/api/plan/verificar"); S.plan = r; cerrarModal(); toast(r.verificado ? t("lic_verificado") : t("lic_no_internet"), !r.verificado); miPlan(); } }, t("lic_verificar")) : null));
}
async function miPlan() {
  const P = await cargarPlan(); if (!P) return;
  const L = P.limites, sl = v => v ? v : t("plan_sin_limite");
  const fila = (k, v) => h("tr", {}, h("td", {}, t(k, { m: S.marca })), h("td", { style: "text-align:right" }, h("b", {}, v)));
  const calTxt = { 720: "720p", 1080: "1080p", 2160: "4K" }[L.calidad] || L.calidad;
  const clave = h("input", { type: "text", placeholder: t("plan_clave_ph"), style: "width:100%" });
  modal([h("h2", {}, t("plan_titulo")),
    tarjetaMembresia(P),
    h("p", { class: "chico suave" }, t("plan_cuenta_nota")),
    h("div", { id: "tarjetas-planes" }, tarjetasPlanes(P)),
    h("h3", {}, t("plan_lim")),
    h("table", { style: "width:100%" }, fila("plan_l_productos", sl(L.productos)), fila("plan_l_videos", sl(L.videos_mes)),
      fila("plan_l_duracion", L.duracion ? fmtSeg(L.duracion) : t("plan_sin_limite")), fila("plan_l_calidad", calTxt), fila("plan_l_guiones", sl(L.guiones)),
      fila("plan_l_carpetas", sl(L.carpetas)), fila("plan_l_archivos", sl(L.archivos)), fila("plan_l_marca", L.marca_agua ? t("plan_si") : t("plan_no")), fila("plan_l_elevenlabs", L.voz_elevenlabs ? t("plan_si") : t("plan_no"))),
    h("div", { class: "tarjeta", style: "margin:12px 0" }, h("b", {}, "🎟 " + t("cr_saldo", { n: P.creditos || 0 })), h("div", { class: "chico suave", style: "margin-top:4px" }, t("cr_que")),
      (P.paquetes_creditos || []).length ? h("div", { class: "paquetes-creditos", style: "margin-top:10px" }, h("div", { class: "chico suave" }, t("cr_paquetes")),
        h("div", { class: "rejilla-paq" }, P.paquetes_creditos.map(q => h("div", { class: "paq" + (q.mejor ? " mejor" : "") },
          q.mejor ? h("div", { class: "cinta" }, "⭐ " + t("cr_mejor")) : null,
          h("b", {}, t("cr_paq_n", { n: q.creditos })), h("div", { class: "precio" }, "$" + q.usd, h("span", { class: "chico suave" }, " USD")),
          h("div", { class: "chico suave" }, t("cr_paq_por", { p: q.por_video.toFixed(2) })), q.ahorro ? h("div", { class: "chico ahorro" }, t("cr_paq_ahorro", { s: q.ahorro })) : null)))) : null),
    h("h3", { style: "margin-top:14px" }, t("plan_clave")), clave, h("div", { class: "chico suave", style: "margin-top:4px" }, t("cr_clave_nota")),
    h("div", { class: "acciones" },
      P.compra ? h("a", { href: P.compra, target: "_blank", class: "boton" }, t("plan_comprar")) : null,
      P.compra_creditos ? h("a", { href: P.compra_creditos, target: "_blank", class: "boton" }, t("cr_comprar")) : null,
      P.plan !== "gratis" ? h("button", { onclick: async () => { await api("DELETE", "/api/plan"); await cargarPlan(); cerrarModal(); } }, t("plan_quitar")) : null,
      h("button", { onclick: cerrarModal }, t("cerrar_modal_cancelar")),
      h("button", { class: "primario", onclick: async () => { const r = await api("POST", "/api/plan/activar", { clave: clave.value }); S.plan = r; cerrarModal();
        toast(r.activado && r.activado.tipo === "reinicio" ? t("rst_hecho") : r.activado && r.activado.tipo === "creditos" ? t("cr_activados", { n: r.activado.valor, t: r.creditos }) : t("plan_activado", { n: r.nombre })); S.productos.length && refrescarProductos().then(render); } }, t("plan_activar"))),
    h("p", { class: "chico suave" }, t("plan_nota"))], { ancha: true });
}
// ---------------------------------------------------------------- actualizaciones
const ICONO_CAMBIO = { nuevo: "✨", cambio: "🔧", quitado: "🗑️" };
// lista de cambios agrupada por tipo. conTutorial = true: cada cambio con tema lleva su botón «Ver cómo» (solo tras actualizar, cuando el tutorial ya es el nuevo)
function listaCambios(cambios, conTutorial) {
  return ["nuevo", "cambio", "quitado"].filter(tp => cambios.some(c => c.tipo === tp)).map(tp =>
    h("div", { style: "margin:10px 0" }, h("b", {}, ICONO_CAMBIO[tp] + " " + t("nov_" + tp)),
      h("ul", { style: "margin:4px 0 0;padding-left:20px" }, cambios.filter(c => c.tipo === tp).map(c =>
        h("li", { style: "margin:4px 0" }, (S.idioma === "en" ? c.en : c.es) || c.es, " ",
          conTutorial && c.tema ? h("button", { class: "link chico", onclick: () => tour([c.tema], true) }, "▶ " + t("nov_ver_como")) : null)))));
}
function cambiosDe(r) {   // los cambios clasificados de la versión nueva; si no vienen, las frases sueltas cuentan como «nuevo»
  return (r.cambios && r.cambios.length) ? r.cambios : (r.novedades || []).map(x => ({ tipo: "nuevo", es: x, en: x, tema: "" }));
}
function ofertaActualizacion(r) {
  const cambios = cambiosDe(r);
  modal([h("h2", {}, t("act_titulo", { v: r.version })), h("p", { class: "suave" }, t("act_tienes", { a: r.actual })),
    cambios.length ? [h("p", {}, h("b", {}, t("act_que_cambia"))), listaCambios(cambios, false)] : null,
    r.auto ? h("p", { class: "chico suave" }, t("act_nota")) : null,
    h("div", { class: "acciones" },
      h("button", { onclick: cerrarModal }, t("act_luego")),
      r.auto ? h("button", { class: "primario", onclick: () => instalarActualizacion(r) }, t("act_ahora"))
        : r.descargar ? h("button", { class: "primario", onclick: () => { fetch("/api/actualizacion/descargar", { method: "POST" }); cerrarModal(); } }, t("nv_descargar")) : null)]);
}
// Descarga, comprueba e instala la versión nueva. Al terminar el programa se cierra y el instalador lo vuelve a abrir.
async function instalarActualizacion(r) {
  const barra = h("div", { style: "height:10px;border-radius:6px;background:var(--borde,#444);overflow:hidden;margin:10px 0" }, h("div", { style: "height:100%;width:0;background:var(--acento,#4b9)" }));
  const texto = h("p", {}, t("act_descargando", { p: 0 }));
  const acciones = h("div", { class: "acciones" });
  const pintar = (cancelable) => { acciones.innerHTML = ""; if (cancelable) acciones.append(h("button", { onclick: async () => { clearInterval(tm); try { await fetch("/api/actualizacion/cancelar", { method: "POST" }); } catch (e) {} cerrarModal(); } }, t("act_cancelar"))); };
  modal([h("h2", {}, t("act_titulo", { v: r.version })), texto, barra, acciones], { fijo: true });
  pintar(true);
  let tm = 0;
  const fallo = msg => { clearInterval(tm); texto.textContent = "⚠️ " + msg; barra.hidden = true; acciones.innerHTML = "";
    acciones.append(h("button", { onclick: cerrarModal }, t("cerrar_modal")), r.descargar ? h("button", { class: "primario", onclick: () => fetch("/api/actualizacion/descargar", { method: "POST" }) }, t("act_manual")) : null); };
  const lanzar = async forzar => {
    texto.textContent = t("act_instalando"); barra.hidden = true; acciones.innerHTML = "";
    const x = await fetch("/api/actualizacion/lanzar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ forzar: !!forzar }) });
    if (x.status === 409) { texto.textContent = "⚠️ " + t("act_ocupado");
      acciones.append(h("button", { onclick: cerrarModal }, t("act_luego")), h("button", { class: "primario", onclick: () => lanzar(true) }, t("act_forzar"))); return; }
    if (!x.ok) { let m = ""; try { m = (await x.json()).error; } catch (e) {} fallo(m || t("act_error")); }
  };
  try {
    const x = await fetch("/api/actualizacion/instalar", { method: "POST" });
    if (!x.ok) { let m = ""; try { m = (await x.json()).error; } catch (e) {} return fallo(m || t("act_error")); }
  } catch (e) { return fallo(t("act_error")); }
  tm = setInterval(async () => {
    try {
      const p = await fetch("/api/actualizacion/progreso").then(x => x.json());
      barra.firstChild.style.width = (p.pct || 0) + "%";
      if (p.fase === "descargando") texto.textContent = t("act_descargando", { p: p.pct || 0 });
      else if (p.fase === "verificando") texto.textContent = t("act_verificando");
      else if (p.fase === "error") fallo(p.msg || t("act_error"));
      else if (p.fase === "listo") { clearInterval(tm); lanzar(false); }
    } catch (e) {}
  }, 600);
}
async function avisarActualizacion() {
  try {
    const r = await fetch("/api/actualizacion").then(x => x.json());
    const caja = $("#novedad"); if (!caja) return;
    let ignorada = ""; try { ignorada = localStorage.getItem("rm_ignorar") || ""; } catch (e) {}
    if (!r.hay || ignorada === r.version) { caja.hidden = true; return; }
    caja.innerHTML = ""; caja.hidden = false;
    poner(caja, h("span", {}, "🎉 " + t("nv_hay", { v: r.version, a: r.actual })),
      r.auto ? h("button", { class: "primario chico", onclick: () => ofertaActualizacion(r) }, t("act_ahora"))
        : r.descargar ? h("button", { class: "primario chico", onclick: () => fetch("/api/actualizacion/descargar", { method: "POST" }) }, t("nv_descargar")) : null,
      cambiosDe(r).length ? h("button", { class: "chico", onclick: () => ofertaActualizacion(r) }, t("nv_ver")) : null,
      h("button", { class: "chico", title: t("nv_ocultar"), onclick: () => { try { localStorage.setItem("rm_ignorar", r.version); } catch (e) {} caja.hidden = true; } }, "✕"));
    if (!S.ofertaMostrada && $("#modal").classList.contains("oculto")) { S.ofertaMostrada = true; ofertaActualizacion(r); }      // una vez por apertura del programa
  } catch (e) {}
}
// Tras actualizar: «Qué hay de nuevo» con lo agregado, cambiado o quitado, y el tutorial de esa parte
async function novedadesTrasActualizar(vista) {
  try {
    const d = await api("GET", "/api/novedades?desde=" + encodeURIComponent(vista || ""));
    await api("POST", "/api/config", { version_vista: d.version });
    if (!d.cambios.length) return;
    const temas = [...new Set(d.cambios.filter(c => c.tipo !== "quitado" && c.tema).map(c => c.tema))];
    modal([h("h2", {}, t("nov_titulo", { v: d.version })), h("p", { class: "suave" }, t("nov_intro")), listaCambios(d.cambios, true),
      h("div", { class: "acciones" },
        temas.length ? h("button", { onclick: () => tour(temas) }, "▶ " + t("nov_tutorial")) : null,
        h("button", { class: "btn-practica-nov", onclick: iniciarPractica }, t("tour_b_muestra")),
        h("button", { class: "primario", onclick: cerrarModal }, t("nov_entendido")))]);
  } catch (e) {}
}
function avisoLegal() {
  modal([h("h2", {}, t("pie_legal")), ...t("legal_txt").split("\n\n").map(p => h("p", { class: "chico" }, p)),
    h("div", { class: "acciones" }, h("button", { class: "primario", onclick: cerrarModal }, t("cerrar_modal")))]);
}
function render() { barra(); pie(); guardarSesion(); botonAsistente(); if (S.vista === "faq") faq(); else if (S.vista === "historial") historial(); else if (S.pid) producto(); else inicio(); }
// destello: campanita brillante y suave + un soplo de chispas, generado con el audio del navegador (sin archivos)
function sonidoDestello(ctx, t0) {
  const sal = ctx.createGain(); sal.gain.value = 0.55; sal.connect(ctx.destination);
  [[1318.5, 0, 0.055], [1760, 0.05, 0.045], [2637, 0.1, 0.035], [3520, 0.16, 0.02]].forEach(([f, d, v]) => {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sine"; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t0 + d); g.gain.exponentialRampToValueAtTime(v, t0 + d + 0.015); g.gain.exponentialRampToValueAtTime(0.0001, t0 + d + 1.1);
    o.connect(g); g.connect(sal); o.start(t0 + d); o.stop(t0 + d + 1.2);
  });
  const n = Math.floor(ctx.sampleRate * 0.45), buf = ctx.createBuffer(1, n, ctx.sampleRate), dat = buf.getChannelData(0);
  for (let i = 0; i < n; i++) dat[i] = Math.random() * 2 - 1;
  const r = ctx.createBufferSource(); r.buffer = buf;
  const hp = ctx.createBiquadFilter(); hp.type = "highpass"; hp.frequency.setValueAtTime(3500, t0); hp.frequency.exponentialRampToValueAtTime(9000, t0 + 0.4);
  const gr = ctx.createGain(); gr.gain.setValueAtTime(0.0001, t0); gr.gain.exponentialRampToValueAtTime(0.03, t0 + 0.04); gr.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.42);
  r.connect(hp); hp.connect(gr); gr.connect(sal); r.start(t0); r.stop(t0 + 0.45);
}
// pantalla de bienvenida: primero aparece solo la V y luego se revela el logo completo
function bienvenida() {
  return new Promise(res => {
    const ov = h("div", { id: "bienvenida" }, h("div", { class: "bv-halo" }), h("img", { class: "bv-logo", src: "/web/logo.png", alt: "" }), h("div", { class: "bv-linea" }));
    document.body.append(ov);
    let fin = false;
    const salir = () => { if (fin) return; fin = true; res(); ov.classList.add("fuera"); setTimeout(() => ov.remove(), 800); };
    ov.addEventListener("click", salir);
    document.addEventListener("keydown", salir, { once: true });
    const quieta = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    setTimeout(salir, quieta ? 900 : 4000);
    // sonido sutil justo cuando el logo se revela (la animación no cambia). Si el navegador no permite sonido todavía, simplemente no suena.
    if (!quieta) { try {
      const AC = window.AudioContext || window.webkitAudioContext, ctx = new AC();
      const t1 = performance.now();
      const sonar = () => { if (ctx.state === "running" && !fin) sonidoDestello(ctx, ctx.currentTime + Math.max(0.02, 1.27 - (performance.now() - t1) / 1000)); };
      ctx.resume().then(sonar).catch(() => {});
      ov.addEventListener("click", () => ctx.close().catch(() => {}));
    } catch (e) {} }
  });
}
// Primera vez que se abre el programa: elige el idioma (se ve al instante). Los textos de esta ventana van en los dos idiomas porque todavía no se sabe cuál prefiere.
function elegirIdioma() {
  return new Promise(res => {
    const nav = String((navigator.languages && navigator.languages[0]) || navigator.language || "es").toLowerCase();
    let sel = nav.startsWith("en") ? "en" : "es";
    const op = (id, nombre, desc) => h("button", { class: "tema-op" + (sel === id ? " sel" : ""), "data-i": id, onclick: () => {
      sel = id; S.idioma = id; document.documentElement.lang = id;
      document.querySelectorAll(".tema-op[data-i]").forEach(x => x.classList.toggle("sel", x.dataset.i === id));
      document.getElementById("idi-continuar").textContent = id === "en" ? "Continue" : "Continuar";
    } }, h("b", { style: "font-size:1.15rem" }, nombre), h("span", { class: "chico suave" }, desc));
    S.idioma = sel;
    modal([h("h2", {}, "Elige tu idioma · Choose your language"), h("p", { class: "suave" }, "Puedes cambiarlo después en «Configuración». · You can change it later in “Settings”."),
      h("div", { class: "tema-ops dos" }, op("es", "Español", "Textos y ayuda en español"), op("en", "English", "Texts and help in English")),
      h("div", { class: "acciones" }, h("button", { class: "primario", id: "idi-continuar", onclick: async () => { try { await api("POST", "/api/config", { idioma: sel }); } catch (e) {} S.idioma = sel; document.documentElement.lang = sel; cerrarModal(); res(); } }, sel === "en" ? "Continue" : "Continuar"))], { fijo: true });
  });
}
// Primera vez que se abre el programa: elige la apariencia (se ve al instante) y queda guardada; después se cambia arriba en «Apariencia»
function elegirTema() {
  return new Promise(res => {
    const op = (id, txt, desc) => { const b = h("button", { class: "tema-op" + (S.tema === id ? " sel" : ""), "data-t": id, onclick: () => { aplicarTema(id); document.querySelectorAll(".tema-op").forEach(x => x.classList.toggle("sel", x.dataset.t === id)); } },
      h("div", { class: "tema-mini " + id }, h("i"), h("i"), h("i")), h("b", {}, txt), h("span", { class: "chico suave" }, desc)); return b; };
    modal([h("h2", {}, t("tema_pregunta_t")), h("p", { class: "suave" }, t("tema_pregunta_d")),
      h("div", { class: "tema-ops" }, op("oscuro", t("tema_oscuro"), t("tema_d_oscuro")), op("claro", t("tema_claro"), t("tema_d_claro")), op("auto", t("tema_auto"), t("tema_d_auto"))),
      h("div", { class: "acciones" }, h("button", { class: "primario", onclick: async () => { try { await api("POST", "/api/config", { tema: S.tema }); } catch (e) {} cerrarModal(); res(); } }, t("tema_continuar")))], { fijo: true });
  });
}
// Primera vez que se abre el programa: idioma y apariencia juntos, en una sola ventana (se ven al instante)
function elegirInicio(repetir) {
  return new Promise(res => {
    const nav = String((navigator.languages && navigator.languages[0]) || navigator.language || "es").toLowerCase();
    if (!repetir) { S.idioma = nav.startsWith("en") ? "en" : "es"; document.documentElement.lang = S.idioma; }
    const pintar = () => {
      const idi = (id, nombre) => h("button", { class: "tema-op" + (S.idioma === id ? " sel" : ""), onclick: () => { S.idioma = id; document.documentElement.lang = id; pintar(); } }, h("b", { style: "font-size:1.1rem" }, nombre));
      const tem = (id, txt, desc) => h("button", { class: "tema-op" + (S.tema === id ? " sel" : ""), onclick: () => { aplicarTema(id); pintar(); } },
        h("div", { class: "tema-mini " + id }, h("i"), h("i"), h("i")), h("b", {}, txt), h("span", { class: "chico suave" }, desc));
      modal([h("h2", {}, "Elige tu idioma · Choose your language"),
        h("div", { class: "tema-ops dos" }, idi("es", "Español"), idi("en", "English")),
        h("h3", { style: "margin:18px 0 4px" }, t("tema_pregunta_t")), h("p", { class: "suave chico", style: "margin:0 0 8px" }, t("tema_pregunta_d")),
        h("div", { class: "tema-ops" }, tem("oscuro", t("tema_oscuro"), t("tema_d_oscuro")), tem("claro", t("tema_claro"), t("tema_d_claro")), tem("auto", t("tema_auto"), t("tema_d_auto"))),
        h("div", { class: "acciones" }, h("button", { class: "primario", id: "idi-continuar", onclick: async () => { try { await api("POST", "/api/config", { idioma: S.idioma }); await api("POST", "/api/config", { tema: S.tema }); } catch (e) {} cerrarModal(); res(); if (repetir) { barra(); if (S.usuario) render(); else pantallaUsuarios(); } } }, t("tema_continuar")))], repetir ? {} : { fijo: true });
    };
    pintar();
  });
}
async function arrancar() {
  let recarga = false;
  try { recarga = sessionStorage.getItem("rm_entro") === "1"; } catch (e) {}   // F5 dentro de la misma ventana: no se repite la bienvenida
  const bv = recarga ? Promise.resolve() : bienvenida();
  const d = await api("GET", "/api/inicio");
  aplicarTema(d.tema); S.idioma = d.config.idioma || "es"; S.marca = d.marca; S.version = d.version; S.titular = d.titular; S.ventanaPropia = !!d.ventana_propia; S.anioInicio = d.anio_inicio; document.title = d.marca; document.documentElement.lang = S.idioma; pie(); cargarPlan();
  S.cat = await api("GET", "/api/catalogo");
  if (recarga && d.usuario) { await entrarUsuario(true); avisarActualizacion(); return; }
  await bv;
  if (!d.idioma_elegido || !d.tema_elegido) await elegirInicio();   // primera vez: idioma y apariencia en una sola ventana
  if (d.usuario) { try { await fetch("/api/usuarios/cerrar", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }); } catch (e) {} }
  S.usuario = null; S.pid = null; pantallaUsuarios(); avisarActualizacion();
}
// ---------------------------------------------------------------- aviso de «tus videos están listos» (funciona en cualquier pestaña)
let _ctxAviso = null;
function _desbloquearAudio() {          // el navegador solo deja sonar si la persona ya tocó la pantalla: se prepara en el primer toque
  try { const AC = window.AudioContext || window.webkitAudioContext; if (!_ctxAviso && AC) _ctxAviso = new AC(); if (_ctxAviso && _ctxAviso.state === "suspended") _ctxAviso.resume(); } catch (e) {}
}
["pointerdown", "keydown"].forEach(n => document.addEventListener(n, _desbloquearAudio, true));
function sonarAviso() {
  try { _desbloquearAudio(); if (_ctxAviso && _ctxAviso.state === "running") sonidoDestello(_ctxAviso, _ctxAviso.currentTime + 0.03); } catch (e) {}
}
let _tituloOriginal = null;
function avisoVideos(e) {
  const ok = !e.error && !e.cancelado, n = Math.max(1, e.total * Math.max(1, e.por_video || 1));
  if (e.cancelado && !e.error) return;                       // si la persona lo detuvo, no hace falta avisarle
  document.querySelectorAll(".notif-video").forEach(x => x.remove());
  const cerrar = () => { caja.remove(); if (_tituloOriginal) { document.title = _tituloOriginal; _tituloOriginal = null; } };
  const caja = h("div", { class: "notif-video" + (ok ? "" : " mal"), role: "alert" },
    h("button", { class: "x-notif", title: t("cerrar"), "aria-label": t("cerrar"), onclick: cerrar }, "✕"),
    ...(!ok && e.codigo ? [h("button", { class: "chico", style: "float:right;margin-right:6px", onclick: () => { cerrar(); detalleError({ error: e.error, codigo: e.codigo, paso: e.paso, paso_en: e.paso_en }); } }, t("err_ver"))] : []),
    h("div", { class: "notif-t" }, (ok ? "🎉 " : "⚠️ ") + (ok ? (n === 1 ? t("vid_uno") : t("vid_varios", { n })) : t("vid_error_t"))),
    h("div", { class: "notif-d" }, ok ? (n === 1 ? t("vid_txt") : t("vid_txt_n")) : String(e.error || "").slice(0, 200) + (e.codigo ? " · " + e.codigo : "")),
    ok && e.producto ? h("button", { class: "primario", onclick: () => { cerrar(); if (!S.usuario) return; S.pid = e.producto; S.pestana = "videos"; S.vista = null; cerrarModal(); render(); } }, t("vid_ver")) : null);
  document.body.append(caja);
  if (ok) {
    sonarAviso();
    if (!document.hasFocus()) { if (!_tituloOriginal) _tituloOriginal = document.title; document.title = "✅ " + t(n === 1 ? "vid_uno" : "vid_varios", { n }); }
  }
}
window.addEventListener("focus", () => { if (_tituloOriginal) { document.title = _tituloOriginal; _tituloOriginal = null; } });
let _vigiaN = null;                                          // trabajo que se está esperando
setInterval(async () => {
  let e; try { e = await fetch("/api/generar/estado").then(r => r.json()); } catch (x) { return; }
  if (e.activo) _vigiaN = e.n;
  else if (e.terminado && e.n && _vigiaN === e.n) { _vigiaN = null; avisoVideos(e); }
}, 2000);
window.addEventListener("beforeunload", e => { if (sucio) { e.preventDefault(); e.returnValue = ""; } });
arrancar();

// ---------------------------------------------------------------- mensajes flotantes (tooltips)
(function () {
  const norm = s => String(s || "").toLowerCase().replace(/\(.*?\)|\{.*?\}/g, "").replace(/^[^\p{L}\p{N}]+/u, "").replace(/\s+/g, " ").trim();
  const mapas = {};
  const mapa = () => {
    const L = S.idioma;
    if (!mapas[L]) { const m = {}; for (const k in (TIPS[L] || {})) { const et = (TEXTOS[L] || {})[k] || TEXTOS.es[k]; if (et) m[norm(et)] = TIPS[L][k]; } mapas[L] = m; }
    return mapas[L];
  };
  let caja = null, espera = null, actual = null;
  const ocultar = () => { clearTimeout(espera); espera = null; actual = null; if (caja) caja.style.display = "none"; };
  const buscar = el => {
    const e = el.closest("button, summary, select, .sw, .pestanas button, [data-tip], [title], a");
    if (!e) return [null, ""];
    if (e.hasAttribute("title") && e.getAttribute("title")) { e.dataset.tip = e.getAttribute("title"); e.removeAttribute("title"); }
    let txt = e.dataset.tip || "";
    if (!txt && (e.tagName === "BUTTON" || e.tagName === "A" || e.tagName === "SUMMARY")) {
      const tip = mapa()[norm(e.textContent)]; if (tip) txt = tip;
    }
    return [e, txt];
  };
  document.addEventListener("mouseover", ev => {
    if (!ev.target.closest) return;
    const [e, txt] = buscar(ev.target);
    if (e === actual) return;
    ocultar();
    if (!e || !txt || e.disabled && !e.dataset.tip) return;
    actual = e;
    espera = setTimeout(() => {
      if (!caja) { caja = h("div", { id: "tip", role: "tooltip" }); document.body.append(caja); }
      caja.textContent = txt; caja.style.display = "block";
      const r = e.getBoundingClientRect(), w = caja.offsetWidth, hh = caja.offsetHeight;
      let x = Math.max(8, Math.min(window.innerWidth - w - 8, r.left + r.width / 2 - w / 2));
      let y = r.bottom + 8; if (y + hh > window.innerHeight - 8) y = Math.max(8, r.top - hh - 8);
      caja.style.left = x + "px"; caja.style.top = y + "px";
    }, 1000);
  });
  ["mouseout", "mousedown", "scroll", "keydown", "wheel"].forEach(n => document.addEventListener(n, ev => { if (n === "mouseout" && ev.relatedTarget && actual && actual.contains(ev.relatedTarget)) return; ocultar(); }, true));
})();
