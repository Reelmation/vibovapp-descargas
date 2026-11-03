// Multimedia > «Mis videos en cámara»: carpetas de personas con sus videos, narrador y opciones. Todo se guarda solo.
Object.assign(TEXTOS.es, {
  gen_ultimos: "Últimos videos creados", gen_ver_todos: "Ver todos mis videos y carpetas",
  t_hablando: "Mis videos en cámara", t_multimedia: "Multimedia", t_palabras: "Palabras clave", t_guion: "Guion", t_estilodis: "Estilo y diseño", t_carpeta: "Carpeta",
  hd_intro: "Guarda aquí los videos donde se habla (tú o tus clientes), tal cual los grabaste. Se editan solos desde tus guiones: en la pestaña «Generar» cada video que armes cuenta como 1 guion y entra en la rotación con los demás.",
  hd_plan: "«Mis videos en cámara» está en los planes Básico, Pro y Agencia.", hd_ver_planes: "Ver planes",
  hd_persona: "Presentador", hd_nueva: "+ Agregar presentador", hd_subir: "Subir videos…", hd_sin: "Aún no hay videos.", hd_renombrar: "Renombrar", hd_borrar_p: "Quitar presentador",
  hd_conf_p: "¿Quitar a {n} y todos sus videos?", hd_conf_a: "¿Borrar este video?", hd_nombre: "Nombre del presentador", hd_subiendo: "Subiendo {n}… {p}%",
  hd_narr: "Narrador", hd_narr_a: "Una voz que narra sobre tus clips (sin que salga nadie). En el guion usa líneas «Narrador: …».", hd_narr_no: "Sin narrador",
  hd_mic_no: "No pude usar el micrófono.", hd_opc: "Cómo se editan", hd_usar: "Usar mis videos en cámara al generar",
  hd_silencios: "Quitar silencios y pausas largas", hd_muletillas: "Quitar muletillas (eh, mmm, um)", hd_zoom: "Alternar cortes con zoom", hd_broll: "Poner clips de mis carpetas cuando se diga una palabra clave", hd_colores: "Un color de subtítulo por persona",
  hd_texto: "📝 Sacar el texto", hd_texto_ayuda: "Escucha este video y escribe lo que dice como un guion, para que lo corrijas y marques frases.", hd_escuchando: "Escuchando… {p}%", hd_texto_listo: "Listo: el texto quedó en un guion nuevo.", hd_ir_guion: "Abrir el guion",
  hd_presentadores: "Presentadores", hd_guardado: "Guardado", hd_sin_motor: "Falta el motor de voz en esta instalación.",
  hd_tip: "Para que cada video salga con tu guion: escríbelo en «Guion» con líneas «{p}: …» y las palabras clave entre corchetes."
});
Object.assign(TEXTOS.en, {
  gen_ultimos: "Latest videos created", gen_ver_todos: "See all my videos and folders",
  t_hablando: "My on-camera videos", t_multimedia: "Media", t_palabras: "Keywords", t_guion: "Script", t_estilodis: "Style & design", t_carpeta: "Folder",
  hd_intro: "Keep here the videos where people talk (you or your clients), exactly as recorded. They are edited automatically from your scripts: in «Create videos» each one counts as 1 script and joins the rotation with the others.",
  hd_plan: "“My on-camera videos” is on the Basic, Pro and Agency plans.", hd_ver_planes: "See plans",
  hd_persona: "Presenter", hd_nueva: "+ Add presenter", hd_subir: "Upload videos…", hd_sin: "No videos yet.", hd_renombrar: "Rename", hd_borrar_p: "Remove presenter",
  hd_conf_p: "Remove {n} and all their videos?", hd_conf_a: "Delete this video?", hd_nombre: "Presenter's name", hd_subiendo: "Uploading {n}… {p}%",
  hd_narr: "Narrator", hd_narr_a: "A voice that narrates over your clips (nobody on screen). In the script use “Narrator: …” lines.", hd_narr_no: "No narrator",
  hd_mic_no: "I couldn't use the microphone.", hd_opc: "How they are edited", hd_usar: "Use my on-camera videos when creating",
  hd_silencios: "Remove silences and long pauses", hd_muletillas: "Remove filler sounds (uh, um, mmm)", hd_zoom: "Alternate zoom cuts", hd_broll: "Add clips from my folders when a keyword is said", hd_colores: "One subtitle color per person",
  hd_texto: "📝 Get the text", hd_texto_ayuda: "Listens to this video and writes what it says as a script, so you can fix it and mark phrases.", hd_escuchando: "Listening… {p}%", hd_texto_listo: "Done: the text is in a new script.", hd_ir_guion: "Open the script",
  hd_presentadores: "Presenters", hd_guardado: "Saved", hd_sin_motor: "The speech engine is missing in this installation.",
  hd_tip: "So each video follows your script: write it in «Script» with lines “{p}: …” and keywords in square brackets."
});
const HD = { prog: null, grab: null, voces: null, elVoces: null };
function _hdSubir(url, file, alProg) {
  return new Promise((res, rej) => {
    const x = new XMLHttpRequest(); x.open("POST", url);
    x.upload.onprogress = e => { if (e.lengthComputable) alProg(Math.round(e.loaded * 100 / e.total)); };
    x.onload = () => { try { const j = JSON.parse(x.responseText); x.status === 200 ? res(j) : rej(new Error(j.error || "Error")); } catch (e) { rej(new Error("Error " + x.status)); } };
    x.onerror = () => rej(new Error("No se pudo subir el archivo."));
    x.send(file);
  });
}
async function pHablando(c, recargar) {
  const U = `${base()}/hablando`;
  const D = await api("GET", U);
  if (!D.permitido) {
    c.append(h("div", { class: "tarjeta" }, h("p", {}, t("hd_plan")), h("button", { class: "primario", onclick: () => miPlan() }, t("hd_ver_planes"))));
    return;
  }
  const cfg = D.config;
  let tmr = null;
  const guardar = () => { clearTimeout(tmr); tmr = setTimeout(() => api("PUT", `${U}/config`, cfg).then(() => toast(t("hd_guardado"))).catch(() => {}), 350); };
  const nueva = nom => h("label", { style: "display:flex;gap:8px;align-items:center;margin:4px 0" }, h("input", { type: "checkbox", checked: !!cfg[nom[0]], onchange: e => { cfg[nom[0]] = e.target.checked; guardar(); } }), t(nom[1]));
  const subirVarios = async (persona, files) => {
    for (const f of files) {
      const barra = h("div", { class: "chico suave" }); c.prepend(barra);
      try {
        await _hdSubir(`${U}/subir?persona=${encodeURIComponent(persona)}&nombre=${encodeURIComponent(f.name)}`, f, p => { barra.textContent = t("hd_subiendo", { n: f.name, p }); });
      } catch (e) { toast(e.message, true); }
      barra.remove();
    }
    await refrescarProductos(); recargar();
  };
  const sacarTexto = async (persona, nombre, btn) => {
    try { await api("POST", `${U}/texto`, { persona, nombre, idioma: S.idioma === "en" ? "en" : "es" }); } catch (e) { return; }
    btn.disabled = true;
    const paso = async () => {
      const e = await fetch("/api/hablado/estado").then(r => r.json());
      if (e.activo) { btn.textContent = t("hd_escuchando", { p: Math.round(e.pct || 0) }); return setTimeout(paso, 900); }
      btn.disabled = false; btn.textContent = t("hd_texto");
      if (e.error) { toast(e.error, true); return; }
      await refrescarProductos();
      toast(t("hd_texto_listo"));
      if (e.resultado) { guionSel = e.resultado; S.pestana = "guiones"; guardarSesion(); proyecto(); }
    };
    paso();
  };
  const tarjetaPersona = p => {
    const inp = h("input", { type: "file", accept: "video/*,audio/*", multiple: true, style: "display:none", onchange: e => subirVarios(p.nombre, [...e.target.files]) });
    return h("div", { class: "tarjeta", style: "margin:8px 0" },
      h("div", { class: "fila" }, h("b", {}, "👤 " + p.nombre), h("div", { class: "espacio" }),
        h("button", { class: "chico", onclick: () => inp.click() }, t("hd_subir")), inp,
        puedeGrabar() ? h("button", { class: "chico", onclick: () => grabarVideo(fs => subirVarios(p.nombre, fs)) }, "🎥 " + t("grab_btn")) : null,
        h("button", { class: "chico", onclick: async () => { const r = await pedirTexto(t("hd_renombrar"), t("hd_nombre"), p.nombre); if (!r) return; await api("POST", `${U}/persona/renombrar`, { nombre: p.nombre, nuevo: r.valor }); recargar(); } }, t("hd_renombrar")),
        h("button", { class: "chico peligro", onclick: async () => { if (!await confirmar(t("hd_conf_p", { n: p.nombre }))) return; await api("DELETE", `${U}/persona?nombre=${encodeURIComponent(p.nombre)}`); await refrescarProductos(); recargar(); } }, t("hd_borrar_p"))),
      p.archivos.length ? h("div", {}, p.archivos.map(a => h("div", { class: "fila chico", style: "padding:2px 0" }, "🎞 " + a.nombre, h("span", { class: "suave" }, ` ${a.mb} MB`), h("div", { class: "espacio" }),
        h("button", { class: "chico btn-sacar-texto", title: t("hd_texto_ayuda"), onclick: ev => sacarTexto(p.nombre, a.nombre, ev.currentTarget) }, t("hd_texto")),
        h("button", { class: "link chico", onclick: async () => { if (!await confirmar(t("hd_conf_a"))) return; await api("DELETE", `${U}/archivo?persona=${encodeURIComponent(p.nombre)}&nombre=${encodeURIComponent(a.nombre)}`); await refrescarProductos(); recargar(); } }, "✕")))) : h("p", { class: "suave chico" }, t("hd_sin")));
  };
  const N = cfg.narrador;
  const cargarVoces = async () => {
    try {
      if (N.modo === "windows" && !HD.voces) { HD.voces = await api("GET", "/api/voces"); if (!N.voz) { N.voz = HD.voces.nombre || ((HD.voces.voces || [])[0] || {}).nombre || ""; guardar(); } }
      if (N.modo === "elevenlabs") { if (!HD.voces) HD.voces = await api("GET", "/api/voces"); if (HD.voces.el && HD.voces.el.conectado && !HD.elVoces) { HD.elVoces = await api("GET", "/api/elevenlabs/voces"); if (!N.elVoz) { N.elVoz = HD.voces.el_id || ((HD.elVoces.voces || [])[0] || {}).id || ""; guardar(); } } }
    } catch (e) {}
    recargar();
  };
  const grabar = async () => {
    try {
      const flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(flujo), trozos = [];
      rec.ondataavailable = e => { if (e.data.size) trozos.push(e.data); };
      rec.onstop = async () => { flujo.getTracks().forEach(x => x.stop()); HD.grab = null;
        const tipo = rec.mimeType || "audio/webm", ext = /ogg/.test(tipo) ? "ogg" : /mp4/.test(tipo) ? "m4a" : "webm";
        await subirVarios("Narrador", [new File(trozos, `narrador_${(D.narrador_archivos || []).length + 1}.${ext}`, { type: tipo })]); };
      rec.start(); HD.grab = rec; recargar();
    } catch (e) { toast(t("hd_mic_no"), true); }
  };
  const sel = (lbl, valor, ops, f) => h("label", { style: "display:block;margin:8px 0" }, h("div", { class: "suave chico" }, lbl), h("select", { onchange: e => f(e.target.value) }, ops.map(o => h("option", { value: o[0], selected: o[0] === valor }, o[1]))));
  const vel = () => h("label", { style: "display:block;margin:8px 0" }, h("div", { class: "suave chico" }, t("hb_vel")), h("input", { type: "range", min: -5, max: 5, value: N.velocidad || 0, oninput: e => { N.velocidad = +e.target.value; guardar(); } }));
  let cuerpoN = null;
  if (N.modo === "grabar") {
    const ent = h("input", { type: "file", accept: "audio/*,video/*", multiple: true, style: "display:none", onchange: e => subirVarios("Narrador", [...e.target.files]) });
    cuerpoN = h("div", {}, h("p", { class: "suave chico" }, t("hb_n_graba_ayuda")),
      h("div", { class: "fila", style: "gap:8px;flex-wrap:wrap" },
        HD.grab ? h("button", { class: "primario", onclick: () => HD.grab.stop() }, "⏹ " + t("hb_detener")) : h("button", { onclick: grabar }, "🔴 " + t("hb_grabar")),
        h("button", { onclick: () => ent.click() }, t("hb_subir_audio")), ent),
      ...(D.narrador_archivos || []).map(a => h("div", { class: "fila chico" }, "🎞 " + a.nombre, h("div", { class: "espacio" }),
        h("button", { class: "link chico", onclick: async () => { await api("DELETE", `${U}/archivo?persona=Narrador&nombre=${encodeURIComponent(a.nombre)}`); recargar(); } }, "✕"))));
  } else if (N.modo === "windows") {
    const vs = (HD.voces && HD.voces.voces) || [];
    cuerpoN = h("div", {}, vs.length ? sel(t("hb_voz"), N.voz, vs.map(v => [v.nombre, v.nombre + (v.cultura ? " (" + v.cultura + ")" : "")]), v => { N.voz = v; guardar(); }) : h("p", { class: "suave chico" }, (HD.voces && HD.voces.error) || "…"), vel());
  } else if (N.modo === "elevenlabs") {
    const V = HD.voces;
    if (!V) cuerpoN = h("p", { class: "suave chico" }, "…");
    else if (!V.el || !V.el.permitido) cuerpoN = h("p", { class: "suave chico" }, "⚠ " + t("hb_el_no"));
    else if (!V.el.conectado) cuerpoN = h("p", { class: "suave chico" }, "ℹ " + t("hb_el_conectar"));
    else cuerpoN = h("div", {}, HD.elVoces ? sel(t("hb_voz"), N.elVoz, (HD.elVoces.voces || []).map(v => [v.id, v.nombre]), v => { N.elVoz = v; guardar(); }) : h("p", { class: "suave chico" }, "…"), vel(), h("p", { class: "suave chico" }, t("hb_n_el_aviso")));
  }
  const modos = [["", "hd_narr_no"], ["grabar", "hb_n_grabar"], ["windows", "hb_n_win"], ["elevenlabs", "hb_n_el"]];
  c.append(...[
    h("p", { class: "suave" }, t("hd_intro")),
    D.motor && D.motor.ok === false ? h("p", { class: "aviso chico" }, "⚠ " + t("hd_sin_motor")) : null,
    h("h3", {}, "👥 " + t("hd_presentadores")),
    ...D.personas.map(tarjetaPersona),
    h("button", { onclick: async () => { const r = await pedirTexto(t("hd_nueva"), t("hd_nombre"), t("hd_persona") + " " + (D.personas.length + 1)); if (!r) return; await api("POST", `${U}/persona`, { nombre: r.valor }); recargar(); } }, t("hd_nueva")),
    h("div", { class: "tarjeta", style: "margin:12px 0" }, h("b", {}, "🎙 " + t("hd_narr")), h("p", { class: "suave chico", style: "margin:2px 0 8px" }, t("hd_narr_a")),
      h("div", { class: "fila", style: "gap:6px;flex-wrap:wrap" }, modos.map(([m, k]) => h("button", { class: "chico " + ((N.modo || "") === m ? "on" : ""), onclick: () => { N.modo = m; guardar(); cargarVoces(); } }, t(k)))), cuerpoN),
    h("div", { class: "tarjeta", style: "margin:12px 0" }, h("b", {}, "⚙ " + t("hd_opc")),
      nueva(["usar", "hd_usar"]), nueva(["silencios", "hd_silencios"]), nueva(["muletillas", "hd_muletillas"]), nueva(["zoom", "hd_zoom"]), nueva(["broll", "hd_broll"]), nueva(["colores", "hd_colores"])),
    h("p", { class: "suave chico" }, t("hd_tip", { p: (D.personas[0] || {}).nombre || t("hd_persona") + " 1" }))].filter(Boolean));
  if (N.modo && !HD.voces) cargarVoces();
}
