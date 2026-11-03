// Asistente de ayuda: busca la mejor respuesta entre las preguntas frecuentes y otras ya escritas. Sin IA y sin internet.
// Si no encuentra nada, ofrece "Contactar soporte" (arma un correo que la persona envía).
const AS_KB = [
  ["f1", "faq_q1", "faq_a1", "que es vibovapp programa sirve hace funciona what is does works"],
  ["f2", "faq_q2", "faq_a2", "incluye clips musica voces material derechos licencia copyright libre included royalty free"],
  ["f3", "faq_q3", "faq_a3", "internet conexion linea offline wifi sin internet connection online"],
  ["f4", "faq_q4", "faq_a4", "producto productos proyecto proyectos duplicar copia product duplicate"],
  ["f5", "faq_q5", "faq_a5", "formato formatos vertical horizontal cuadrado retrato tiktok reels instagram formats square"],
  ["f6", "faq_q6", "faq_a6", "plan gratis gratuito free prueba gratuita trial"],
  ["f7", "faq_q7", "faq_a7", "conviene basico cual elegir mejor recomiendan which choose best"],
  ["f8", "faq_q8", "faq_a8", "contador reinicia reinicio mes renueva videos del mes counter reset month renew"],
  ["f9", "faq_q9", "faq_a9", "precio precios impuestos iva incluyen cuesta cuestan costo cobran cuanto vale taxes price cost much", [["plan"]]],
  ["f10", "faq_q10", "faq_a10", "creditos caros plan barato por video cheaper credits expensive"],
  ["f11", "faq_q11", "faq_a11", "credito creditos que es paquete credit credits pack"],
  ["f12", "faq_q12", "faq_a12", "usar creditos gastar credito como uso use spend credit"],
  ["f13", "faq_q13", "faq_a13", "activar clave licencia pegar canjear codigo key activate license redeem code"],
  ["f14", "faq_q14", "faq_a14", "clave reinicio reiniciar reset key otra prueba"],
  ["f15", "faq_q15", "faq_a15", "compartir clave prestar otra persona share key lend"],
  ["f16", "faq_q16", "faq_a16", "perdi clave cambie computadora nueva pc lost key new computer perdida"],
  ["f17", "faq_q17", "faq_a17", "guion sin audio voz grabar generar voz narrar no tengo audio script no audio voice robotica robotic"],
  ["f18", "faq_q18", "faq_a18", "elevenlabs eleven labs voces clonar clon clonada clone voices"],
  ["f19", "faq_q19", "faq_a19", "microfono permiso grabar no deja grabar no graba microphone permission record"],
  ["f20", "faq_q20", "faq_a20", "donde guardan videos datos carpeta documentos ubicacion encuentro where stored folder saved find my videos"],
  ["f21", "faq_q21", "faq_a21", "privacidad internet suben nube datos seguros privacy upload cloud safe"],
  ["f22", "faq_q22", "faq_a22", "borre borrado error recuperar papelera restaurar deleted recover trash restore"],
  ["f23", "faq_q23", "faq_a23", "windows protegio pc smartscreen peligroso virus defender antivirus protected dangerous"],
  ["f24", "faq_q24", "faq_a24", "fallo falla algo fallo que hago problema crash log arranque not working failed"],
  ["f25", "faq_q25", "faq_a25", "publicar videos redes sociales instagram tiktok derechos comercial vender publish post social commercial"],
  ["f26", "faq_q26", "faq_a26", "cambiar personalizar se ven videos estilo apariencia customize look"],
  ["f27", "faq_q27", "faq_a27", "soporte contactar contacto correo email ayuda support contact"],
  ["f28", "faq_q28", "faq_a28", "cancelar cancelo cancelacion baja darme dejar cobro cobran cancel unsubscribe stop charging", [["plan"]]],
  ["f29", "faq_q29", "faq_a29", "verificar verificacion verifico online offline semana connection verify check", [["plan"]]],
  ["f30", "faq_q30", "faq_a30", "cambiar cambio subir mejorar bajar upgrade downgrade otro change switch", [["plan"]]],
  ["e1", "as_e1_q", "as_e1_a", "error falla fallo no se crea no genera generar video no funciona problema crear video fail failed error creating not working", [["contacto"]]],
  ["e2", "as_e2_q", "as_e2_a", "subir clips palabras clave temas tema imagenes carpeta clips keywords topics upload", [["tour", "clips"], ["tab", "clips"]]],
  ["e3", "as_e3_q", "as_e3_a", "subtitulos subtitulo letras no coinciden desfasados atrasados adelantados mal escritos sync captions subtitles mismatch", [["tab", "guiones"]]],
  ["e4", "as_e4_q", "as_e4_a", "musica cancion canciones fondo no se escucha sin musica music song background no sound", [["tab", "musica"]]],
  ["e5", "as_e5_q", "as_e5_a", "burbujas burbuja whatsapp chat mensajes persona bubbles agregar", [["tour", "burbujas"]]],
  ["e6", "as_e6_q", "as_e6_a", "color colores letra letras tipo fuente tamano posicion donde sale titulo subtitulos cambiar estilo font size position", [["tour", "estilo"], ["tab", "estilo"]]],
  ["e7", "as_e7_q", "as_e7_a", "actualizar actualizacion nueva version instalar desinstalar reinstalar update uninstall reinstall install"],
  ["e8", "as_e8_q", "as_e8_a", "marca agua watermark limite limites acabaron agotado videos mes llegaste upgrade subir plan limit", [["plan"]]],
  ["e9", "as_e9_q", "as_e9_a", "usuario usuarios cuenta perfil agregar cambiar otra persona users add profile account switch"],
  ["e10", "as_e10_q", "as_e10_a", "repiten repetido repetidos mismos clips siempre igual variedad repeat same clips"],
  ["e11", "as_e11_q", "as_e11_a", "hablar persona humano soporte contactar contacto correo email escribir support human person talk", [["contacto"]]],
  ["e12", "as_e12_q", "as_e12_a", "primer video empezar comenzar tutorial practica como funciona paso a paso start first video how to tutorial", [["practica"], ["tour", "empezar"]]],
  ["e13", "as_e13_q", "as_e13_a", "nombre nombres renombrar renombro renombra cambiar cambio carpeta carpetas rename name folder", [["tour", "producto"]]],
  ["e14", "as_e14_q", "as_e14_a", "tipografia tipografias letra letras fuente fuentes font fonts ttf otf subir propia mia agregar upload own custom", [["estilo"]]],
  ["e15", "as_e15_q", "as_e15_a", "sonido sonidos efecto efectos audio pop ding transicion subir propio mio mp3 wav sound sounds effect effects upload own custom transition", [["estilo"]]],
  ["p1", "faq_q13", "faq_a13", "comprar compra pagar pago membresia suscripcion buy purchase pay membership subscription", [["plan"]]],
];
const AS_PARADA = new Set(("el la los las un una unos unas de del al a en y o u que como cual cuales por para con sin mi mis tu tus su sus se me te lo le es son soy esta este esto estoy hay puedo puede pueden quiero quisiera hacer hago favor the is are my your it to of and or in on for with how do does can i you what").split(" "));
function asNorm(s) { return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9*\/ ]+/g, " "); }
function asTokens(s) {
  return asNorm(s).split(/\s+/).filter(w => w.length > 2 && !AS_PARADA.has(w)).map(w => w.replace(/(es|s)$/, m => w.length > 4 ? "" : m));
}
// -> [[puntos, entrada], ...] de mayor a menor
function asistenteBuscar(q) {
  const qt = asTokens(q);
  if (!qt.length) return [];
  const res = AS_KB.map(e => {
    const kw = asTokens(e[3]), pregunta = asTokens(t(e[1])), resp = asTokens(t(e[2]));
    let p = 0;
    qt.forEach(w => {
      if (kw.includes(w)) p += 3;
      else if (w.length >= 4 && kw.some(k => k.length >= 4 && (k.startsWith(w) || w.startsWith(k)))) p += 2;
      if (pregunta.includes(w)) p += 2;
      else if (resp.includes(w)) p += 0.5;
    });
    return [p, e, p - 0.02 * (kw.length + pregunta.length)];   // el tercer valor desempata: a igualdad gana la entrada más corta
  }).filter(x => x[0] > 0).sort((a, b) => b[2] - a[2]);
  return res;
}
let AS_LOG = [];   // la conversación se conserva mientras la app está abierta
function asistente() {
  const log = h("div", { class: "as-log" });
  const entrada = h("input", { type: "text", class: "inp-asistente", placeholder: t("as_ph"), style: "flex:1", onkeydown: e => { if (e.key === "Enter") enviar(); } });
  const caja = h("div", {});
  const cierra = () => cerrarModal();
  const ir = acc => {
    const [tipo, x] = acc;
    if (tipo === "contacto") return contactoSoporte();
    cierra();
    if (tipo === "plan") return miPlan();
    if (tipo === "faq") return abrirFaq();
    if (tipo === "practica") return iniciarPractica();
    if (tipo === "tour") return tour([x], true);
    if (tipo === "tab") { if (!S.pid) { toast(t("as_necesita_producto"), true); return; } S.pestana = x; guardarSesion(); S.vista = null; render(); }
  };
  const burbuja = (quien, contenido, acciones) => {
    const b = h("div", { class: "as-msg " + quien }, h("div", { class: "as-txt" }, contenido));
    if (acciones && acciones.length) b.append(h("div", { class: "as-acc" }, acciones.map(a => h("button", { class: "chico" + (a[0] === "contacto" ? " primario" : ""), onclick: () => ir(a) },
      a[0] === "tour" ? t("as_ac_tour") : a[0] === "plan" ? t("as_ac_plan") : a[0] === "faq" ? t("as_ac_faq") : a[0] === "practica" ? t("as_ac_practica") : a[0] === "contacto" ? t("as_ac_contacto") : t("as_ac_tab", { p: S.idioma === "en" ? ({ clips: "Clips & keywords", guiones: "Scripts", musica: "Music", estilo: "Style" }[a[1]] || a[1]) : ({ clips: "Clips y palabras clave", guiones: "Guiones", musica: "Música", estilo: "Estilo" }[a[1]] || a[1]) })))));
    return b;
  };
  const pintar = () => {
    log.innerHTML = "";
    log.append(burbuja("bot", t("as_saludo", { m: S.marca })));
    AS_LOG.forEach(m => log.append(m.quien === "yo" ? burbuja("yo", m.texto) : burbuja("bot", m.texto, m.acciones)));
    if (!AS_LOG.length) {
      log.append(h("div", { class: "chico suave", style: "margin:8px 0 4px" }, t("as_sugeridas")),
        h("div", { class: "as-chips" }, ["f13", "f17", "f11", "e1", "e5", "e6", "f20", "e12"].map(id => { const e = AS_KB.find(x => x[0] === id); return h("button", { class: "chico", onclick: () => preguntar(t(e[1]), e) }, t(e[1])); })));
    }
    setTimeout(() => { log.scrollTop = log.scrollHeight; }, 20);
  };
  const preguntar = (texto, directa) => {
    AS_LOG.push({ quien: "yo", texto });
    const r = directa ? [[99, directa]] : asistenteBuscar(texto);
    if (!r.length || r[0][0] < 3) {
      AS_LOG.push({ quien: "bot", texto: t("as_no_se"), acciones: [["faq"], ["contacto"]] });
    } else {
      const [, e] = r[0];
      let acciones = (e[4] || []).slice();
      const otras = r.slice(1, 3).filter(x => x[0] >= 3 && x[1][0] !== e[0]);
      let texto2 = t(e[2], { m: S.marca });
      if (otras.length) texto2 += "\n\n" + t("as_otras") + "\n• " + otras.map(x => t(x[1][1], { m: S.marca })).join("\n• ");
      if (!acciones.length) acciones = [["faq"]];
      AS_LOG.push({ quien: "bot", texto: texto2, acciones });
    }
    entrada.value = ""; pintar();
  };
  const enviar = () => { const v = entrada.value.trim(); if (v) preguntar(v); };
  caja.append(h("div", { class: "fila" }, h("h2", { style: "margin:0" }, "💬 " + t("as_titulo")), h("div", { class: "espacio" }), h("button", { class: "link", onclick: cierra }, t("cerrar") + " ✕")),
    h("div", { class: "chico suave", style: "margin:4px 0 8px" }, t("as_aviso")), log,
    h("div", { class: "fila", style: "margin-top:10px;flex-wrap:nowrap" }, entrada, h("button", { class: "primario", onclick: enviar }, t("as_enviar"))),
    h("div", { class: "fila", style: "margin-top:8px" }, h("button", { class: "link", onclick: abrirFaq }, t("faq_btn")), h("button", { class: "link", onclick: () => contactoSoporte() }, t("as_ac_contacto"))));
  modal([caja], { sinX: true }); pintar(); setTimeout(() => entrada.focus(), 50);
}
// Formulario para escribir a soporte: arma el correo con la descripción y datos técnicos (editable); la persona lo envía.
async function contactoSoporte() {
  let info = {};
  try { info = await api("GET", "/api/soporte/info"); } catch (e) { info = { correo: "", version: S.version || "", plan: "", log: "" }; }
  const desc = h("textarea", { class: "inp-soporte-desc", placeholder: t("as_c_desc_ph"), style: "min-height:110px", oninput: armar });
  const inc = h("input", { type: "checkbox", checked: true, style: "width:auto;flex:none", onchange: armar });
  const msg = h("textarea", { class: "inp-soporte-msg", style: "min-height:150px;font-size:.85em" });
  const aviso = h("div", { class: "chico", style: "margin-top:6px;min-height:1.2em" });
  function armar() {
    const dtec = inc.checked ? `\n\n--- ${t("as_c_tec")} ---\n${S.marca} v${info.version || S.version || ""} · ${info.plan || ""} · ${S.idioma} · ${navigator.platform || info.sistema || ""}\n${t("as_c_log")}${info.log ? "\n" + info.log : " —"}` : "";
    msg.value = desc.value.trim() + dtec;
    if (desc.value.trim().length >= 15) aviso.textContent = "";
  }
  const asunto = () => `${S.marca} v${info.version || ""} – ${t("as_c_titulo")}`;
  const valido = () => { if (desc.value.trim().length < 15) { aviso.style.color = "var(--mal)"; aviso.textContent = t("as_c_corto"); desc.focus(); return false; } return true; };
  const abrir = async via => { if (!valido()) return; await api("POST", "/api/soporte/abrir", { via, asunto: asunto(), cuerpo: msg.value }); aviso.style.color = ""; aviso.textContent = t("as_c_abierto"); };
  const copiar = async () => { if (!valido()) return; try { await navigator.clipboard.writeText(msg.value); } catch (e) { msg.select(); document.execCommand("copy"); } aviso.style.color = ""; aviso.textContent = t("as_c_copiado", { c: info.correo }); };
  armar();
  modal([h("div", { class: "fila" }, h("h2", { style: "margin:0" }, "✉️ " + t("as_c_titulo")), h("div", { class: "espacio" }), h("button", { class: "link", onclick: cerrarModal }, t("cerrar") + " ✕")),
    h("p", { class: "suave chico" }, t("as_c_intro")),
    h("label", { class: "chico", style: "font-weight:600" }, t("as_c_desc")), desc,
    h("label", { class: "fila chico", style: "margin:8px 0" }, inc, t("as_c_incluir")),
    h("label", { class: "chico", style: "font-weight:600" }, t("as_c_mensaje")), msg, aviso,
    h("div", { class: "acciones", style: "justify-content:flex-start;flex-wrap:wrap" },
      h("button", { class: "primario btn-soporte-gmail", onclick: () => abrir("gmail") }, "✉️ " + t("as_c_gmail")),
      h("button", { class: "btn-soporte-correo", onclick: () => abrir("mailto") }, t("as_c_correo")),
      h("button", { class: "btn-soporte-copiar", onclick: copiar }, t("as_c_copiar"))),
    h("p", { class: "chico suave" }, t("as_c_nota", { c: info.correo })),
    h("button", { class: "link", onclick: asistente }, t("as_c_volver"))], { sinX: true });
}
// botón flotante (abajo a la izquierda, para no tapar la práctica guiada que está a la derecha)
function botonAsistente() {
  let b = document.getElementById("btn-asistente");
  if (!S.usuario) { if (b) b.remove(); return; }
  if (!b) { b = h("button", { id: "btn-asistente", class: "btn-asistente", onclick: asistente }); document.body.append(b); }
  b.textContent = t("as_btn"); b.title = t("as_btn_tip");
}
